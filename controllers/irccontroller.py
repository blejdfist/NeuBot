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

from models import Network, Channel, IRCMessage, IRCUser
from controllers.usercontroller import UserController
from controllers.configcontroller import ConfigController
from lib.net.netsocket import AsyncBufferedNetSocket, ConnectionFailedException
from lib.logger import Logger
from lib.util import IRCCommandDispatcher

import ircdef
import re
import random
import time
import threading

##
# Handles an IRC-connection
class IRCController:
	def __init__(self, eventcontroller):
		self.connected = False
		self.connection = None
		self.eventcontroller = eventcontroller
		self.usercontroller = UserController()

		self.config = ConfigController()

		# Attributes
		self.ircnet = None
		self.channels = []
		self.servers = []
		self.currentserverindex = 0
		self.nick = None
		self.altnicks = []
		self.currentnick = None
		self.currentaltnickindex = 0
		self.name = None
		self.ident = None

		self.pendingnick = None

		# Detected users
		self.users = []

		# Automatically auto connect unless we say otherwise
		self.autoreconnect = True

		# Last PONG
		self.last_ping_pong_ts = 0
		self.keepalive_thread_exit_event = None

		# Register events
		self.eventcontroller.register_event("PING",     self.event_ping)
		self.eventcontroller.register_event("PONG",     self.event_pong)
		self.eventcontroller.register_event("433",      self.event_nickinuse)
		self.eventcontroller.register_event("JOIN",     self.event_join)
		self.eventcontroller.register_event("PART",     self.event_part)
		self.eventcontroller.register_event("KICK",     self.event_kick)
		self.eventcontroller.register_event("QUIT",     self.event_quit)
		self.eventcontroller.register_event("NICK",     self.event_nick)
		self.eventcontroller.register_event("TOPIC",    self.event_topic)

		self.eventcontroller.register_event(ircdef.RPL_TOPIC,    self.event_topic_reply)
		self.eventcontroller.register_event(ircdef.RPL_NAMREPLY, self.event_channel_names)
		self.eventcontroller.register_event(ircdef.RPL_WHOREPLY, self.event_who_reply)
		self.eventcontroller.register_event(ircdef.RPL_MYINFO,   self.event_registration)

	def schedule_reclaimnick(self):
		# Schedule bot to rejoin channel
		reclaim_nick_time = self.config.get('irc.reclaim_nick_time')
		Logger.info("Scheduling reclaim of nick in %d seconds" % (reclaim_nick_time,))
		kwargs = {
			"nick": self.nick,
		}
		self.eventcontroller.register_timer(self.set_nick, reclaim_nick_time, kwargs = kwargs)

	def schedule_rejoin(self, channel):
		# Schedule bot to rejoin channel
		rejoin_channel_time = self.config.get('irc.rejoin_channel_time')
		Logger.info("Scheduling rejoin of channel %s in %d seconds" % (channel.name, rejoin_channel_time))
		kwargs = {
			"channel": channel.name,
			"key": channel.password,
		}
		self.eventcontroller.register_timer(self.join, rejoin_channel_time, kwargs = kwargs)

	def event_topic(self, irc):
		for channel in self.channels:
			if channel.name == irc.message.destination:
				channel.topic = irc.message.params

	def event_topic_reply(self, irc):
		match = re.match("^(.*?) :(.*)$", irc.message.params)
		if not match:
			return

		chan_name, topic = match.groups()
		for channel in self.channels:
			if channel.name == chan_name:
				channel.topic = topic
				return

	##
	# Called when someone changes his/her nick
	def event_nick(self, irc):
		user = irc.message.source
		new_nick = irc.message.params

		# Since the user object was created throught our UserController
		# we need to tell it to change the nickname
		# otherwise the hostmask will not match the next time the user does something
		# which will result in a dead entry in the UserController
		user.change(nick = new_nick)

	##
	# Handle server reply from WHO-command
	def event_who_reply(self, irc):
		match = re.match("(.*?) (.*?) (.*?) (.*?) (.*?) (.*?) :[0-9]+ (.*)", irc.message.params)
		if not match:
			Logger.warning("Invalid RPL_WHOREPLY received")
			return

		chan, ident, host, server, nick, modes, real_name = match.groups()
		whostring = "%s!%s@%s" % (nick, ident, host)

		user = self.usercontroller.get_user(whostring)

		# Find the channel among the one we monitor
		# @todo Implement comparison functions in IRChannel so that we can use find() here
		for channel in self.channels:
			if channel.name == chan:
				# Found, now add the user to that channel
				channel.add_user(user)

	def event_quit(self, irc):
		# User quit so remove him/her from all
		# channels
		for chan in self.channels:
			try:
				chan.del_user(irc.message.source)
			except:
				pass

		# Also remove user from global nick list
		self.usercontroller.del_user(irc.message.source)

	def event_join(self, irc):
		who = irc.message.source
		channel_name = irc.message.params
		channel = None

		for chan in self.channels:
			if chan.name == channel_name:
				channel = chan
				break

		if channel is None:
			Logger.warning("%s joined unknown channel %s" % (who.nick, channel_name))
			return

		if who.nick == self.currentnick:
			# We joined a channel
			Logger.info("Joined " + channel_name)

			# Send WHO-message to learn about the users in this channel
			self.send_raw("WHO " + channel_name)
		else:
			# It was someone else
			channel.add_user(who)
			Logger.info("User %s joined %s" % (who.nick, channel_name))

	def event_part(self, irc):
		who = irc.message.source
		channel_name = irc.message.params
		channel = None

		for chan in self.channels:
			if chan.name == channel_name:
				channel = chan
				break

		if channel is None:
			Logger.warning("%s parted unknown channel %s" % (who.nick, channel_name))
			return

		if who.nick == self.currentnick:
			# We parted a channel
			channel.is_joined = False
			Logger.info("Parted " + channel_name)
		else:
			# It was someone else
			channel.del_user(who)
			Logger.info("User %s parted %s" % (who.nick, channel_name))

	def event_channel_names(self, irc):
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

	def event_kick(self, irc):
		channel_name = irc.message.destination
		who = irc.message.source
		got_kicked = irc.message.params

		if got_kicked.find(":") != -1:
			got_kicked = got_kicked.split(":")[0].strip()

		channel = None

		for chan in self.channels:
			if chan.name == channel_name:
				channel = chan
				break

		if channel is None:
			Logger.warning("%s kicked from unknown channel %s" % (got_kicked, channel_name))
			return

		if got_kicked == self.currentnick:
			# We got kicked
			channel.is_joined = False
			Logger.info("Kicked from %s by %s" % (channel_name, who))
			self.schedule_rejoin(channel)
		else:
			# It was someone else
			channel.del_user(got_kicked)
			Logger.info("User %s got kicked from %s" % (got_kicked, channel_name))

	def event_ping(self, irc):
		self.pong_server(irc.message.params)
		self.last_ping_pong_ts = time.time()

	def event_pong(self, irc):
		self.last_ping_pong_ts = time.time()

	def event_nickinuse(self, irc):
		if self.currentnick == None:
			if len(self.altnicks) == 0:
				altnick = self.nick

				while altnick == self.nick:
					pos = random.randint(0, len(self.nick)-1)
					c = chr(random.randint(0x41, 0x51))
					altnick = self.nick[0:pos-1] + c + self.nick[pos:]
			else:
				altnick = self.altnicks[self.currentaltnickindex]
				self.currentaltnickindex += 1

			if self.currentaltnickindex == len(self.altnicks):
				self.currentaltnickindex = 0

			self.set_nick(altnick)
		else:
			if self.config.get('irc.reclaim_nick_if_lost'):
				self.schedule_reclaimnick()

	def event_registration(self, irc):
		self.currentnick = self.pendingnick
		self.join_all_channels()

		# We didn't get the nick we wanted
		if self.currentnick != self.nick and self.config.get('irc.reclaim_nick_if_lost'):
			self.schedule_reclaimnick()

	def _handle_data(self, line, socket):
		try:
			# The IRCMessage needs our usercontroller so that it
			# can cache users that it sees in it
			line = unicode(line, 'utf-8', 'ignore')
			message = IRCMessage(line, self.usercontroller)
			self.eventcontroller.dispatch_event(self, message)

		except Exception, e:
			Logger.warning("Exception: %s" % e)

	def _handle_connect(self, socket):
		self.connected = True

		self.currentnick = None

		self.send_raw("USER %s 9 * :%s" % (self.ident, self.name))
		self.set_nick(self.nick)

		# Reset PONG-timer
		self.last_ping_pong_ts = time.time()

		# Dispatch keepalive-thread
		self.keepalive_thread_exit_event = threading.Event()
		self.keepalive_thread = threading.Thread(target = self.thread_keepalive)
		self.keepalive_thread.start()

	def _handle_disconnect(self, socket):
		Logger.info("IRC connection closed")
		self.connected = False

		# Tear down keepalive-thread
		self.keepalive_thread_exit_event.set()

		# Flag all channels as not joined
		for channel in self.channels:
			channel.is_joined = False

		# If we want to reconnect, automatically schedule a reconnect 
		if self.autoreconnect:
			reconnect_time = self.config.get('irc.reconnect_time')
			Logger.info("Will reconnect in %d seconds..." % reconnect_time)
			self.eventcontroller.register_timer(self.connect, reconnect_time)

	def join_all_channels(self):
		for channel in self.channels:
			if not channel.is_joined:
				self.join(channel.name, channel.password)

	def send_raw(self, data):
		if type(data) == unicode:
			data = data.encode('utf-8')

		self.connection.send(data + "\r\n")

	def is_connected(self):
		return self.connected

	def thread_keepalive(self):
		Logger.debug("Keepalive-thread started")
		pong_disconnect_time = self.config.get("irc.pong_disconnect_time")
		pong_timeout = self.config.get("irc.pong_timeout")

		while self.is_connected() and not self.keepalive_thread_exit_event.isSet():
			time_since_ping_pong = time.time() - self.last_ping_pong_ts

			if time_since_ping_pong > pong_disconnect_time:
				Logger.info("No PING PONG for more than %d seconds. Reconnecting." % (pong_disconnect_time,))
				self.reconnect()
				break
			elif time_since_ping_pong > pong_timeout:
				Logger.info("No PONG for %d seconds. Sending PING." % (time_since_ping_pong,))
				self.ping_server()

			self.keepalive_thread_exit_event.wait(10)

		Logger.debug("Keepalive-thread stopping")

	def connect(self):
		if self.currentserverindex == len(self.servers):
			self.currentserverindex = 0

		# We were asked to connect, so we want to automatically reconnect if disconnected
		self.autoreconnect = True

		server = self.servers[self.currentserverindex]
		self.currentserverindex += 1

		Logger.info("%s: Connecting to %s..." % (self.ircnet, server))

		self.connection = AsyncBufferedNetSocket(server.hostname, server.port, server.use_ssl, server.use_ipv6)

		# Setup callbacks
		self.connection.OnConnect    = self._handle_connect
		self.connection.OnDisconnect = self._handle_disconnect
		self.connection.OnData       = self._handle_data

		try:
			self.connection.connect()
		except ConnectionFailedException, e:
			# We failed to connect, schedule a retry
			reconnect_time = self.config.get('irc.reconnect_time')
			Logger.error("Failed to connect to %s (%s), retrying in %s seconds..." % (self.ircnet, server, reconnect_time))
			self.eventcontroller.register_timer(self.connect, reconnect_time)


	def disconnect(self):
		# We might have reconnection/rejoin/reclaim-timers running
		# so we need to release them so that the user may shutdown the bot if he/she wants to
		self.eventcontroller.release_related(self)

		# We were asked to disconnect, so we don't want to autoreconnect
		self.autoreconnect = False
		self.connection.disconnect()

	def reconnect(self):
		# If we are reconnecting, we want to autoreconnect when the connection is closed
		self.autoreconnect = True
		self.connection.disconnect()

	def set_nick(self, nick):
		self.pendingnick = nick

		if self.is_connected():
			self.send_raw("NICK " + nick)

	##
	# Set the topic of a channel
	# @param channel Channel
	# @param topic The new topic
	def set_topic(self, channel, topic):
		self.send_raw("TOPIC %s :%s" % (channel, topic))

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

		dispatcher = IRCCommandDispatcher(self, self.eventcontroller)
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
			chan = Channel(channel, key)
			self.schedule_rejoin(chan)

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
			self.send_raw("QUIT :" + message)
		else:
			self.send_raw("QUIT")

	def pong_server(self, tag = None):
		if tag:
			self.send_raw("PONG :" + tag)
		else:
			self.send_raw("PONG *")

	def ping_server(self):
		self.send_raw("PING *")
