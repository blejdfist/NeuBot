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
# Copyright (c) 2010, Jim Persson, All rights reserved.

##
# Gets passed to command and event callbacks by the dispatcher in @link controllers.eventcontroller.EventController EventController @endlink
# It contains convenient functions to reply to messages received
# All unknown method calls are delegated to the current @link controllers.irccontroller.IRCController IRCController @endlink
class IRCMessageController:
	def __init__(self, irccontroller, ircmessage):
		self.server = irccontroller
		self.message = ircmessage

	##
	# Reply to the message using a PRIVMSG
	# @param message Message
	def reply(self, message):
		if self.server.nick == self.message.destination:
			self.server.privmsg(self.message.source.nick, message)
		else:
			self.server.privmsg(self.message.destination, message)

	##
	# Reply to the message using a NOTICE
	# @param message Message
	def reply_notice(self, message):
		self.server.notice(self.message.destination, message)

	##
	# Delegate all other methods to the @link controllers.irccontroller.IRCController IRCController @endlink
	def __getattr__(self, attr):
		# Delegate methods to the IRCController
		return getattr(self.server, attr)
		
