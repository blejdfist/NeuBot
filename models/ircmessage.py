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
	# From a user
	regexp_usermsg1 = re.compile("^:(.*?!.*?@.*?) (.*?) [:]{0,1}(.*)$")
	regexp_usermsg2 = re.compile("^:(.*?!.*?@.*?) (.*?) (.*?) [:]{0,1}(.*)$")
	
	# From the server
	regexp_server1   = re.compile("^:(.*?) (.*?) [:]{0,1}(.*)$")
	regexp_server2   = re.compile("^:(.*?) (.*?) (.*?) [:]{0,1}(.*)$")

	# Other (ERROR for example)
	regexp_other    = re.compile("^([A-Za-z]*?) :(.*)$")

	def __init__(self, msg, usercontroller = None):
		self.raw_msg = msg
		self.source = None
		self.command = None
		self.destination = None
		self.params = None
		self.usercontroller = usercontroller

		regexCallbacks = [
			(IRCMessage.regexp_usermsg2, self._parse_usermsg2),
			(IRCMessage.regexp_usermsg1, self._parse_usermsg1),
			(IRCMessage.regexp_server2,  self._parse_server2),
			(IRCMessage.regexp_server1,  self._parse_server1),
			(IRCMessage.regexp_other,    self._parse_other),
		]

		for (regex, callback) in regexCallbacks:
			match = regex.match(msg)
			if match:
				callback(match.groups())
				return

		raise Exception("No match for " + msg)

	def __str__(self):
		return self.raw_msg

	def _parse_usermsg1(self, msg):
		#print "usrmsg1 %s" % (msg,)
		# If we have a usercontroller, use it
		if self.usercontroller:
			self.source = self.usercontroller.get_user(msg[0])
		else:
			self.source = IRCUser(msg[0])
		self.command = msg[1]
		self.params = msg[2]

	def _parse_usermsg2(self, msg):
		#print "usrmsg2 %s" % (msg,)
		# If we have a usercontroller, use it
		if self.usercontroller:
			self.source = self.usercontroller.get_user(msg[0])
		else:
			self.source = IRCUser(msg[0])
		self.command = msg[1]
		self.destination = msg[2]
		self.params = msg[3]

	def _parse_server1(self, msg):
		#print "Server1 %s" % (msg,)
		# If we have a usercontroller, use it
		if self.usercontroller:
			self.source = self.usercontroller.get_user(msg[0])
		else:
			self.source = IRCUser(msg[0])
		self.command = msg[1]
		self.params = msg[2]

	def _parse_server2(self, msg):
		#print "Server2 %s" % (msg,)
		# If we have a usercontroller, use it
		self.source = msg[0]
		self.command = msg[1]
		self.destination = msg[2]
		self.params = msg[3]

	def _parse_other(self, msg):
		self.command = msg[0]
		self.params = msg[1]
