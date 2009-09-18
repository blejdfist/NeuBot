from models import Network, Channel, IRCMessage
from lib.net.netsocket import AsyncBufferedNetSocket, ConnectionFailedException
from lib.logger import Logger
from lib.util import IRCCommandDispatcher

import threading
import ircdef

class IRCController:
	def __init__(self, eventcontroller):
		self.connected = False
		self.connection = None
		self.eventcontroller = eventcontroller

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

		# Automatically auto connect unless we say otherwise
		self.autoreconnect = True

		self.rejoin_time = 10
		self.reconnect_time = 10

		## Callback when a message is received: MessageHandler(controllers.MessageController)
		self.MessageHandler = None

		# Register events
		self.eventcontroller.register_event("PING",     self.event_ping)
		self.eventcontroller.register_event("433",      self.event_nickinuse)
		self.eventcontroller.register_event("004",      self.event_registration)
		self.eventcontroller.register_event("JOIN",     self.event_join)
		self.eventcontroller.register_event("PART",     self.event_part)
		self.eventcontroller.register_event("KICK",     self.event_kick)
		self.eventcontroller.register_event("QUIT",     self.event_quit)

		# Nicklist when joining channel
		#:irc.foonet.com 353 NeuBot = #test :NeuBot jim 
		#:irc.foonet.com 366 NeuBot #test :End of /NAMES list.

		# Nickchanges, own and others

	def schedule_rejoin(self, channel):
		# Schedule bot to rejoin channel
		Logger.Info("Scheduling rejoin of channel " + channel.name)
		kwargs = {
			"channel": channel.name,
			"key": channel.password,
		}
		self.eventcontroller.register_timer(self.rejoin_time, self.join, kwargs = kwargs)

	def event_quit(self, irc):
		for chan in self.channels:
			try:
				chan.del_user(irc.message.source)
			except:
				pass

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
			channel.is_joined = True
			Logger.Debug("I joined " + channel_name)
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
		print irc.message.params

	def event_registration(self, irc):
		self.join_all_channels()

	def _handle_data(self, line, socket):
		try:
			message = IRCMessage(line)
			self.eventcontroller.dispatch_event(self, message)

			if self.MessageHandler:
				try:
					self.MessageHandler(self, message)
				except Exception, e:
					Logger.Warning("Message handler threw exception: %s" % e)

		except Exception, e:
			Logger.Warning("Exception: %s" % e)

	def _handle_connect(self, socket):
		# Determine nick
		if self.currentnick is None:
			self.currentnick = self.nick

		self.send_raw("USER %s 9 * :%s" % (self.ident, self.name))
		self.send_raw("NICK " + self.currentnick)

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

	def connect(self): #, server, port, use_ssl = False, use_ipv6 = False):
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
		self.currentnick = nick

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
