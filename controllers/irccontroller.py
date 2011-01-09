# -*- coding: utf-8 -*-
## @package controllers.irccontroller
# Handler for a IRC-connection

# This file is part of NeuBot.
#
# NeuBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2010, Jim Persson, All rights reserved.

from models.channel import Channel
from models.ircmessage import IRCMessage
from controllers.usercontroller import UserController
from controllers.configcontroller import ConfigController
from lib.net.netsocket import AsyncBufferedNetSocket, ConnectionFailedException
from lib.logger import Logger
from lib.util.irccommanddispatcher import IRCCommandDispatcher

import ircdef
import re
import random
import time
import threading
import Queue

##
# Handles an IRC-connection
class IRCController:
    def __init__(self, eventcontroller):
        self._connected = False
        self._connection = None
        self._eventcontroller = eventcontroller
        self._usercontroller = UserController()

        self._config = ConfigController()

        # Message entry count (used for priority queue ordering)
        self._send_entry_count = 0

        # Attributes
        self._ircnet = None
        self._channels = {}
        self._servers = []
        self._currentserverindex = 0
        self._nick = None
        self._altnicks = []
        self._currentnick = None
        self._currentaltnickindex = 0
        self._name = None
        self._ident = None

        self._pendingnick = None

        # Detected users
        self._users = []

        # Automatically auto connect unless we say otherwise
        self._autoreconnect = True

        # Output data queue
        self._output_queue = Queue.PriorityQueue()

        # Last PONG
        self._last_ping_pong_ts = 0

        # Thread events
        self._keepalive_thread_exit_event = None
        self._writer_thread_exit_event = None

        # Register events
        self._eventcontroller.register_event("PING",  self._event_ping)
        self._eventcontroller.register_event("PONG",  self._event_pong)
        self._eventcontroller.register_event("433",   self._event_nickinuse)
        self._eventcontroller.register_event("JOIN",  self._event_join)
        self._eventcontroller.register_event("PART",  self._event_part)
        self._eventcontroller.register_event("KICK",  self._event_kick)
        self._eventcontroller.register_event("QUIT",  self._event_quit)
        self._eventcontroller.register_event("NICK",  self._event_nick)
        self._eventcontroller.register_event("TOPIC", self._event_topic)

        self._eventcontroller.register_event(ircdef.RPL_TOPIC,    self._event_topic_reply)
        self._eventcontroller.register_event(ircdef.RPL_NAMREPLY, self._event_channel_names)
        self._eventcontroller.register_event(ircdef.RPL_WHOREPLY, self._event_who_reply)
        self._eventcontroller.register_event(ircdef.RPL_MYINFO,   self._event_registration)

    def _schedule_reclaimnick(self):
        # Schedule bot to rejoin channel
        reclaim_nick_time = self._config.get('irc.reclaim_nick_time')
        Logger.info("Scheduling reclaim of nick in %d seconds" % (reclaim_nick_time,))
        kwargs = {
            "nick": self._nick,
        }
        self._eventcontroller.register_timer(self.set_nick, reclaim_nick_time, kwargs = kwargs)

    def _schedule_rejoin(self, channel):
        # Schedule bot to rejoin channel
        rejoin_channel_time = self._config.get('irc.rejoin_channel_time')
        Logger.debug2("Scheduling rejoin of channel %s in %d seconds" % (channel.name, rejoin_channel_time))
        kwargs = {
            "channel": channel.name,
            "key": channel.password,
        }
        self._eventcontroller.register_timer(self.join, rejoin_channel_time, kwargs = kwargs)

    def _event_topic(self, irc):
        channel_name = irc.message.destination

        channel = self._channels.get(channel_name)
        if channel:
            channel.topic = irc.message.params
        else:
            Logger.warning("Got topic for unregistered channel %s." % channel_name)

    def _event_topic_reply(self, irc):
        match = re.match("^(.*?) :(.*)$", irc.message.params)
        if not match:
            return

        channel_name, topic = match.groups()
        channel = self._channels.get(channel_name)

        if channel:
            channel.topic = irc.message.params
        else:
            Logger.warning("Got topic reply for unregistered channel %s." % channel_name)

    ##
    # Called when someone changes his/her nick
    def _event_nick(self, irc):
        user = irc.message.source
        new_nick = irc.message.params

        # Since the user object was created throught our UserController
        # we need to tell it to change the nickname
        # otherwise the hostmask will not match the next time the user does something
        # which will result in a dead entry in the UserController
        user.change(nick = new_nick)

    ##
    # Handle server reply from WHO-command
    def _event_who_reply(self, irc):
        match = re.match("(.*?) (.*?) (.*?) (.*?) (.*?) (.*?) :[0-9]+ (.*)", irc.message.params)
        if not match:
            Logger.warning("Invalid RPL_WHOREPLY received")
            return

        chan, ident, host, server, nick, modes, real_name = match.groups()
        whostring = "%s!%s@%s" % (nick, ident, host)

        user = self._usercontroller.get_user(whostring)

        # Find the channel among the one we monitor
        # @todo Implement comparison functions in IRChannel so that we can use find() here
        channel = self._channels.get(chan)
        if channel:
            channel.add_user(user)

    def _event_quit(self, irc):
        # User quit so remove him/her from all channels
        for channel in self._channels.itervalues():
            channel.del_user(irc.message.source)

        # Also remove user from global nick list
        self._usercontroller.del_user(irc.message.source)

    def _event_join(self, irc):
        who = irc.message.source
        channel_name = irc.message.params

        # Find the channel
        channel = self._channels.get(channel_name)

        if channel is None:
            Logger.info("%s joined unregistered channel %s. Adding channel." % (who.nick, channel_name))
            channel = Channel(channel_name)

        if who.nick == self._currentnick:
            # We joined a channel
            Logger.info("Joined " + channel_name)

            # We are in this channel
            channel.is_joined = True

            # Send WHO-message to learn about the users in this channel
            self.send_raw("WHO " + channel_name)
        else:
            # It was someone else
            channel.add_user(who)
            Logger.info("User %s joined %s" % (who.nick, channel_name))

    def _event_part(self, irc):
        who = irc.message.source
        channel_name = irc.message.params

        # Find the channel
        channel = self._channels.get(channel_name)

        if channel is None:
            Logger.warning("%s parted unknown channel %s" % (who.nick, channel_name))
            return

        if who.nick == self._currentnick:
            # We parted a channel
            channel.is_joined = False
            Logger.info("Parted " + channel_name)
        else:
            # It was someone else
            channel.del_user(who)
            Logger.info("User %s parted %s" % (who.nick, channel_name))

    def _event_channel_names(self, irc):
        match = re.match("([=\*@]) ([&#\+!]\S+) :(.*)", irc.message.params)
        if not match:
            Logger.warning("Invalid RPL_NAMREPLY from server")
            return

        chan_type, chan_name, chan_users = match.groups()
        #if chan_type == "@":   chan_type = "SECRET"
        #elif chan_type == "*": chan_type = "PRIVATE"
        #elif chan_type == "=": chan_type = "PUBLIC"

        status = {
            "@": "OP",
            "+": "VOICE",
        }

        for nick in chan_users.split():
            nick_status = "NORMAL"

            if status.has_key(nick[0]):
                nick_status = status[nick[0]]
                nick = nick[1:]

    def _event_kick(self, irc):
        channel_name = irc.message.destination
        who = irc.message.source
        got_kicked = irc.message.params

        if got_kicked.find(":") != -1:
            got_kicked = got_kicked.split(":")[0].strip()

        # Find the channel
        channel = self._channel.get(channel_name)

        if channel is None:
            Logger.warning("%s kicked from unknown channel %s" % (got_kicked, channel_name))
            return

        if got_kicked == self._currentnick:
            # We got kicked
            channel.is_joined = False
            Logger.info("Kicked from %s by %s" % (channel_name, who))
            self._schedule_rejoin(channel)
        else:
            # It was someone else
            channel.del_user(got_kicked)
            Logger.info("User %s got kicked from %s" % (got_kicked, channel_name))

    def _event_ping(self, irc):
        self.pong_server(irc.message.params)
        self._last_ping_pong_ts = time.time()

    def _event_pong(self, irc):
        self._last_ping_pong_ts = time.time()

    def _event_nickinuse(self, irc):
        if self._currentnick == None:
            if len(self._altnicks) == 0:
                altnick = self._nick

                while altnick == self._nick:
                    pos = random.randint(0, len(self._nick)-1)
                    c = chr(random.randint(0x41, 0x51))
                    altnick = self._nick[0:pos-1] + c + self._nick[pos:]
            else:
                altnick = self._altnicks[self._currentaltnickindex]
                self._currentaltnickindex += 1

            if self._currentaltnickindex == len(self._altnicks):
                self._currentaltnickindex = 0

            self.set_nick(altnick)
        else:
            if self._config.get('irc.reclaim_nick_if_lost'):
                self._schedule_reclaimnick()

    def _event_registration(self, irc):
        self._currentnick = self._pendingnick
        self.join_all_channels()

        # We didn't get the nick we wanted
        if self._currentnick != self._nick and self._config.get('irc.reclaim_nick_if_lost'):
            self._schedule_reclaimnick()

    def _handle_data(self, line, socket):
        try:
            # The IRCMessage needs our usercontroller so that it
            # can cache users that it sees in it
            line = unicode(line, 'utf-8', 'ignore')

            Logger.debug3("RECV[%s]: %s" % (self._ircnet, line.strip()))

            message = IRCMessage(line, self._usercontroller)
            self._eventcontroller.dispatch_event(self, message)

        except Exception as e:
            Logger.warning("Exception: %s" % e)

    def _handle_connect(self, socket):
        self._connected = True

        self._currentnick = None

        self.send_raw("USER %s 9 * :%s" % (self._ident, self._name))
        self.set_nick(self._nick)

        # Reset PONG-timer
        self._last_ping_pong_ts = time.time()

        # Dispatch keepalive-thread
        self._keepalive_thread_exit_event = threading.Event()
        self._keepalive_thread = threading.Thread(target = self._thread_keepalive)
        self._keepalive_thread.start()

        # Dispatch writer-thread
        self._writer_thread_exit_event = threading.Event()
        self._writer_thread = threading.Thread(target = self._thread_writer)
        self._writer_thread.start()

    def _handle_disconnect(self, socket):
        Logger.info("IRC connection closed")
        self._connected = False

        # Tear down keepalive-thread
        self._keepalive_thread_exit_event.set()
        self._keepalive_thread.join()

        # Tear down writer-thread
        self._writer_thread_exit_event.set()
        self._writer_thread.join()

        # Empty send queue
        self._output_queue = Queue.PriorityQueue()

        # Flag all channels as not joined
        for channel in self._channels.itervalues():
            channel.is_joined = False

        # If we want to reconnect, automatically schedule a reconnect
        if self._autoreconnect:
            reconnect_time = self._config.get('irc.reconnect_time')
            Logger.info("Will reconnect in %d seconds..." % reconnect_time)
            self._eventcontroller.register_timer(self.connect, reconnect_time)

    ##
    # Writer thread
    def _thread_writer(self):
        rate = 0

        while self.is_connected() and not self._writer_thread_exit_event.is_set():
            try:
                while rate < self._config.get('irc.rate_limit_burst_max'):
                    _, _, data = self._output_queue.get(timeout=1.0)
                    Logger.debug3("SEND[%s]: %s" % (self._ircnet, data.strip(),))
                    self._connection.send(data)
                    self._output_queue.task_done()

                    rate += 1
                else:
                    rate -= 1 if rate > 0 else 0
                    self._writer_thread_exit_event.wait(self._config.get('irc.rate_limit_wait_time'))

            except Queue.Empty as e:
                rate -= 1 if rate > 0 else 0

        Logger.debug2("Writer thread stopping")

    def join_all_channels(self):
        for channel in self._channels.itervalues():
            if not channel.is_joined:
                self.join(channel.name, channel.password)

    def send_raw(self, data, priority = 5):
        if type(data) == unicode:
            data = data.encode('utf-8')

        if len(data) > 512:
            Logger.warning("Sending data longer than 512 bytes. Length = %d bytes" % (len(data),))

        # Remove any newlines
        data = data.replace('\n', '').replace('\r', '')

        self._send_entry_count += 1
        self._output_queue.put((priority, self._send_entry_count, data + "\r\n"))

    def get_ircnet_name(self):
        return self._ircnet

    def is_connected(self):
        return self._connected

    def _thread_keepalive(self):
        Logger.debug("Keepalive-thread started")
        pong_disconnect_time = self._config.get("irc.pong_disconnect_time")
        pong_timeout = self._config.get("irc.pong_timeout")

        while self.is_connected() and not self._keepalive_thread_exit_event.is_set():
            time_since_ping_pong = time.time() - self._last_ping_pong_ts

            if time_since_ping_pong > pong_disconnect_time:
                Logger.info("No PING PONG for more than %d seconds. Reconnecting." % (pong_disconnect_time,))
                self.reconnect()
                break
            elif time_since_ping_pong > pong_timeout:
                Logger.debug3("No PONG for %d seconds. Sending PING." % (time_since_ping_pong,))
                self.ping_server()

            self._keepalive_thread_exit_event.wait(10)

        Logger.debug("Keepalive-thread stopping")

    def connect(self):
        if self._currentserverindex == len(self._servers):
            self._currentserverindex = 0

        # We were asked to connect, so we want to automatically reconnect if disconnected
        self._autoreconnect = True

        server = self._servers[self._currentserverindex]
        self._currentserverindex += 1

        Logger.info("%s: Connecting to %s..." % (self._ircnet, server))

        self._connection = AsyncBufferedNetSocket(server.hostname, server.port, server.use_ssl, server.use_ipv6)

        # Setup callbacks
        self._connection.OnConnect    = self._handle_connect
        self._connection.OnDisconnect = self._handle_disconnect
        self._connection.OnData       = self._handle_data

        try:
            self._connection.connect()
        except ConnectionFailedException:
            # We failed to connect, schedule a retry
            reconnect_time = self._config.get('irc.reconnect_time')
            Logger.error("Failed to connect to %s (%s), retrying in %s seconds..." % (self._ircnet, server, reconnect_time))
            self._eventcontroller.register_timer(self.connect, reconnect_time)


    def disconnect(self):
        # We might have reconnection/rejoin/reclaim-timers running
        # so we need to release them so that the user may shutdown the bot if he/she wants to
        self._eventcontroller.release_related(self)

        # We were asked to disconnect, so we don't want to autoreconnect
        self._autoreconnect = False
        self._connection.disconnect()

    def reconnect(self):
        # If we are reconnecting, we want to autoreconnect when the connection is closed
        self._autoreconnect = True
        self._connection.disconnect()

    def set_nick(self, nick):
        self._pendingnick = nick

        if self.is_connected():
            self.send_raw("NICK " + nick, priority = 4)

    ##
    # Set the topic of a channel
    # @param channel Channel
    # @param topic The new topic
    def set_topic(self, channel, topic):
        self.send_raw("TOPIC %s :%s" % (channel, topic), priority = 4)

    ##
    # Send a private message to a channel or nick
    # @param destination Channel or nick
    # @param message Message to send
    def privmsg(self, destination, message):
        self.send_raw("PRIVMSG %s :%s" % (destination, message))

    ##
    # Send a notice to a channel or nick
    # @param destination Channel or nick
    # @param message Message to send
    def notice(self, destination, message):
        self.send_raw("NOTICE %s :%s" % (destination, message))

    ##
    # Join a channel
    # @param channel Channel to join
    # @param key Channel password (optional)
    def join(self, channel, key = None):
        if key:
            cmd = "JOIN %s :%s" % (channel, key)
        else:
            cmd = "JOIN " + channel

        Logger.info("Joining channel %s" % channel)

        dispatcher = IRCCommandDispatcher(self, self._eventcontroller)
        success = dispatcher.send_command_and_wait(
            cmd,
            success_codes = [
                                ircdef.RPL_ENDOFNAMES,
                                ircdef.RPL_TOPIC,
                            ],
            failure_codes = [
                                ircdef.ERR_CHANNELISFULL,
                                ircdef.ERR_INVITEONLYCHAN,
                                ircdef.ERR_BANNEDFROMCHAN,
                                ircdef.ERR_BADCHANNELKEY,
                                ircdef.ERR_NEEDMOREPARAMS,
                                ircdef.ERR_NOSUCHCHANNEL,
                                ircdef.ERR_BADCHANMASK,
                                ircdef.ERR_TOOMANYCHANNELS,
                                ircdef.ERR_TOOMANYTARGETS,  # Duplicate channel (sync problem/netsplit)
                            ]
        )

        # The join failed, reschedule it for later
        if not success:
            Logger.info("Failed to join channel %s. Will retry later." % channel)
            chan = Channel(channel, key)
            self._schedule_rejoin(chan)

    ##
    # Leave a channel
    # @param channel Channel to leave
    def part(self, channel):
        self.send_raw("PART " + channel)

    ##
    # Quit from server
    # @param message Quit message (optional)
    def quit(self, message = None):
        if message:
            self.send_raw("QUIT :" + message, priority = 0)
        else:
            self.send_raw("QUIT", priority = 0)

    def pong_server(self, tag = None):
        if tag:
            self.send_raw("PONG :" + tag, priority = 0)
        else:
            self.send_raw("PONG *", priority = 0)

    def ping_server(self):
        self.send_raw("PING *", priority = 0)

    ##
    # Wait for output queue to be emptied
    def flush_output(self):
        self._output_queue.join()

    ##
    # Add a channel that the IRCController should join
    # @param channel models.Channel object
    def add_channel(self, channel):
        self._channels[channel.name] = channel

    ##
    # Add a server that the IRCController may use
    # @param server models.Server object
    def add_server(self, server):
        self._servers.append(server)

    def get_current_nick(self):
        return self._nick
