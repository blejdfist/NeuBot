from lib import Logger

import ircdef
import re

class FakeSocket:
	def __init__(self, server_name, bot_nick, bot_ident, bot_host):
		# Asynchronous callback methods
		self.OnConnect    = None
		self.OnDisconnect = None
		self.OnData       = None

		self.server_name = server_name
		self.bot_nick = bot_nick
		self.bot_ident = bot_ident
		self.bot_host = bot_host

		self.sim_nick = "MrSim"
		self.sim_ident = "mrsim"
		self.sim_host = "example.org"

	##
	# Simulate raw data from the server
	# 
	# @param data Raw data that seems to come from the server
	def server_raw(self, data):
		self.OnData(data, self)

	##
	# Simulate a server response and feed it into the bot
	# 
	# @param code Numeric code or command
	# @param params Parameters to the code
	def server_response(self, code, params):
		data = ":%s %s %s" % (self.server_name, str(code), params)
		self.server_raw(data)

	##
	# Simulate data being sent by simulator user
	# Example: server_use_response("PRIVMSG", "#channel :Hello")
	#
	# @param code Command from the user
	# @param params Parameters to the command
	def server_user_response(self, code, params):
		data = ":%s!%s@%s %s %s" % (self.sim_nick, self.sim_ident, self.sim_host, code, params)
		print data
		self.server_raw(data)

	def connect(self):
		self.OnConnect(self)
		self.server_response(ircdef.RPL_MYINFO, "FakeIRC iowghraAsORTVSxNCWqBzvdHtGp lvhopsmntikrRcaqOALQ")

	def disconnect(self):
		self.OnDisconnect(self)

	def send(self, data):
		params = data.split()
		if len(params) == 0:
			return

		cmd = params[0]

		if cmd == "JOIN":
			self.server_user_response("JOIN", ":" + params[1])
			self.server_user_response(ircdef.RPL_ENDOFNAMES, "%s :/End of /NAMES list." % params[1])
		elif cmd == "WHO":
			self.server_response(ircdef.RPL_WHOREPLY, "%s %s %s %s %s %s H :0 %s" % (
				self.bot_nick,
				params[1],
				self.bot_ident,
				self.bot_host,
				self.server_name,
				self.bot_nick,
				"The NeuBot"))

			self.server_response(ircdef.RPL_ENDOFWHO, "%s %s :End of /WHO list." % (self.bot_nick, params[1],))

		elif cmd == "PRIVMSG":
			match = re.match("PRIVMSG (.*?) :(.*)", data)
			channel, message = match.groups()

			print "[%s:%s] %s" % (self.bot_nick, channel, message)
		else:
			Logger.debug("Unhandled: " + data.strip())
