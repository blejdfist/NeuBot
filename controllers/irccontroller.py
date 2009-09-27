from models import Network, Channel, IRCMessage, IRCUser
from controllers import UserController
from lib.net.netsocket import AsyncBufferedNetSocket, ConnectionFailedException
from lib.logger import Logger
from lib.util import IRCCommandDispatcher

import ircdef
import re
import random

class IRCController:
	def __init__(self, eventcontroller):
		self.connected = False
		self.connection = None
		self.eventcontroller = eventcontroller
		self.usercontroller = UserController()

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
		self.autoreclaimnick = True

		self.rejoin_time = 10
		self.reclaim_time = 10
		self.reconnect_time = 10

		# Register events
		self.eventcontroller.register_event("PING",     self.event_ping)
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

		self.eventcontroller.register_command("test", self.command_test)

	def schedule_reclaimnick(self):
		# Schedule bot to rejoin channel
		Logger.Info("Scheduling reclaim of nick")
		kwargs = {
			"nick": self.nick,
		}
		self.eventcontroller.register_timer(self.reclaim_time, self.set_nick, kwargs = kwargs)

	def schedule_rejoin(self, channel):
		# Schedule bot to rejoin channel
		Logger.Info("Scheduling rejoin of channel " + channel.name)
		kwargs = {
			"channel": channel.name,
			"key": channel.password,
		}
		self.eventcontroller.register_timer(self.rejoin_time, self.join, kwargs = kwargs)

	def command_test(self, irc, params):
		irc.reply("Command works. Arguments: %s" % params)

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

	def event_nick(self, irc):
		user = irc.message.source
		new_nick = irc.message.params
		user.change(nick = new_nick)

	def event_who_reply(self, irc):
		match = re.match("(.*?) (.*?) (.*?) (.*?) (.*?) (.*?) :[0-9]+ (.*)", irc.message.params)
		if not match:
			Logger.Warning("Invalid RPL_WHOREPLY received")
			return

		chan, ident, host, server, nick, modes, real_name = match.groups()
		whostring = "%s!%s@%s" % (nick, ident, host)

		user = self.usercontroller.get_user(whostring)

		# Find the channel among the one we monitor
		for channel in self.channels:
			if channel.name == chan:
				# Found, now add the user to that channel
				channel.add_user(user)

	def event_quit(self, irc):
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
			Logger.Warning("%s joined unknown channel %s" % (who.nick, channel_name))
			return

		if who.nick == self.currentnick:
			# We joined a channel
			Logger.Debug("I joined " + channel_name)

			# Send WHO-message to learn about the users in this channel
			self.send_raw("WHO " + channel_name)
		else:
			# It was someone else
			channel.add_user(who)
			Logger.Debug("User %s joined %s" % (who.nick, channel_name))

	def event_part(self, irc):
		who = irc.message.source
		channel_name = irc.message.params
		channel = None

		for chan in self.channels:
			if chan.name == channel_name:
				channel = chan
				break

		if channel is None:
			Logger.Warning("%s parted unknown channel %s" % (who.nick, channel_name))
			return

		if who.nick == self.currentnick:
			# We parted a channel
			channel.is_joined = False
			Logger.Debug("I parted " + channel_name)
		else:
			# It was someone else
			channel.del_user(who)
			Logger.Debug("User %s parted %s" % (who.nick, channel_name))

	def event_channel_names(self, irc):
		match = re.match("([=\*@]) ([&#\+!]\S+) :(.*)", irc.message.params)
		if not match:
			Logger.Warning("Invalid RPL_NAMREPLY from server")
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
			Logger.Warning("%s kicked from unknown channel %s" % (got_kicked, channel_name))
			return

		if got_kicked == self.currentnick:
			# We got kicked
			channel.is_joined = False
			Logger.Debug("I got kicked from " + channel_name)
			self.schedule_rejoin(channel)
		else:
			# It was someone else
			channel.del_user(got_kicked)
			Logger.Debug("User %s got kicked from %s" % (got_kicked, channel_name))

	def event_ping(self, irc):
		self.pong_server(irc.message.params)

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
			if self.autoreclaimnick:
				self.schedule_reclaimnick()

	def event_registration(self, irc):
		self.currentnick = self.pendingnick
		self.join_all_channels()

		# We didn't get the nick we wanted
		if self.currentnick != self.nick and self.autoreclaimnick:
			self.schedule_reclaimnick()

	def _handle_data(self, line, socket):
		try:
			message = IRCMessage(line, self.usercontroller)
			self.eventcontroller.dispatch_event(self, message)

		except Exception, e:
			Logger.Warning("Exception: %s" % e)

	def _handle_connect(self, socket):
		self.connected = True

		self.currentnick = None

		self.send_raw("USER %s 9 * :%s" % (self.ident, self.name))
		self.set_nick(self.nick)

	def _handle_disconnect(self, socket):
		Logger.Info("IRC connection closed")

		# Flag all channels as not joined
		for channel in self.channels:
			channel.is_joined = False

		# If we want to reconnect, automatically schedule a reconnect 
		if self.autoreconnect:
			Logger.Info("Will reconnect in %d seconds..." % self.reconnect_time)
			self.eventcontroller.register_timer(self.reconnect_time, self.connect)

	def join_all_channels(self):
		for channel in self.channels:
			if not channel.is_joined:
				self.join(channel.name, channel.password)

	def send_raw(self, data):
		self.connection.send(data + "\r\n")

	def is_connected(self):
		return self.connected

	def connect(self):
		if self.currentserverindex == len(self.servers):
			self.currentserverindex = 0

		# We were asked to connect, so we want to automatically reconnect if disconnected
		self.autoreconnect = True

		server = self.servers[self.currentserverindex]
		self.currentserverindex += 1

		Logger.Info("%s: Connecting to %s..." % (self.ircnet, server))

		self.connection = AsyncBufferedNetSocket(server.hostname, server.port, server.use_ssl, server.use_ipv6)

		# Setup callbacks
		self.connection.OnConnect    = self._handle_connect
		self.connection.OnDisconnect = self._handle_disconnect
		self.connection.OnData       = self._handle_data

		try:
			self.connection.connect()
		except ConnectionFailedException, e:
			# We failed to connect, schedule a retry
			Logger.Error("Failed to connect to %s (%s), retrying in %s seconds..." % (self.ircnet, server, self.reconnect_time))
			self.eventcontroller.register_timer(self.reconnect_time, self.connect)


	def disconnect(self):
		# We were asked to disconnect, so we don't want to autoreconnect
		self.autoreconnect = False
		self.connection.disconnect()

	def set_nick(self, nick):
		self.pendingnick = nick

		if self.is_connected():
			self.send_raw("NICK " + nick)

	def set_topic(self, channel, topic):
		self.send_raw("TOPIC %s :%s" % (channel, topic))

	def privmsg(self, destination, message):
		self.send_raw("PRIVMSG %s :%s" % (destination, message))

	def notice(self, destination, message):
		self.send_raw("NOTICE %s :%s" % (destination, message))

	def join(self, channel, key = None):
		if key:
			#self.send_raw("JOIN %s :%s" % (channel, key))
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
							]
		)

		# The join failed, reschedule it for later
		if not success:
			chan = Channel(channel, key)
			self.schedule_rejoin(chan)

	def part(self, channel):
		self.send_raw("PART " + channel)

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
