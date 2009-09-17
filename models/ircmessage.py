# -*- coding: utf-8 -*-

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
# Copyright (c) 2007-2008, Jim Persson, All rights reserved.

import re
from ircuser import IRCUser

class IRCMessage:
	regexp_message = re.compile("^:(.*?) (.*?) (.*?) [:]{0,1}(.*)$")
	regexp_server  = re.compile("^:(.*?) (.*?) [:]{0,1}(.*)$")
	regexp_other   = re.compile("^([A-Za-z]*?) :(.*)$")

	def __init__(self, msg):
		self.raw_msg = msg
		self.source = None
		self.command = None
		self.destination = None
		self.params = None

		regexCallbacks = [
			(IRCMessage.regexp_message, self._parse_message),
			(IRCMessage.regexp_server,  self._parse_server),
			(IRCMessage.regexp_other,   self._parse_other),
		]

		for (regex, callback) in regexCallbacks:
			match = regex.match(msg)
			if match:
				callback(match.groups())
				return

		raise Exception("No match for " + msg)

	def __str__(self):
		return self.raw_msg

	def _parse_server(self, msg):
		print "Server %s" % (msg,)
		self.source = IRCUser(msg[0])
		self.command = msg[1]
		self.params = msg[2]

	def _parse_message(self, msg):
		print "Message %s" % (msg,)
		self.source = IRCUser(msg[0])
		self.command = msg[1]
		self.destination = msg[2]
		self.params = msg[3]

	def _parse_other(self, msg):
		print "Other %s" % (msg,)
		self.command = msg[0]
		self.params = msg[1]
