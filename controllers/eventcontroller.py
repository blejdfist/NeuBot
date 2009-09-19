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

from controllers import IRCMessageController

import threading
import traceback

"""
	register_event(callback, event)
	register_command(callback, command, privileged = False)
	register_event_regexp(callback, event, param_regexp)
	register_timer(callback, interval, oneshot, args, kwargs)
"""

## @brief Register and dispatch event- and command callbacks
class EventController:
	## @brief Constructor
	def __init__(self):
		self.commandCallbacks = {}
		self.eventCallbacks = {}

		# {obj: timer}
		self.moduleTimers = {}

		self.config = None
		self.acl = None

	## @brief Set the configuration to use
	def SetConfig(self, config):
		self.config = config

	## @brief Set the ACL handler to use
	def SetACL(self, acl):
		self.acl = acl

	## @brief Release callbacks registered by a module
	# @param obj Module instance for which callbacks should be released
	# @warning This should NEVER be called directly by a module
	# @todo Hide this from the modules
	def release_related(self, obj):
		# Free command callbacks
		for command in self.commandCallbacks.keys():
			for entry in self.commandCallbacks[command]:
				(cbobj, callback, privileged) = entry
				if cbobj == obj:
					self.commandCallbacks[command].remove(entry)
					if len(self.commandCallbacks[command]) == 0:
						del self.commandCallbacks[command]

		# Free event callbacks
		for event in self.eventCallbacks.keys():
			for entry in self.eventCallbacks[event]:
				(cbobj, callback) = entry
				if cbobj == obj:
					self.eventCallbacks[event].remove(entry)
					if len(self.eventCallbacks[event]) == 0:
						del self.eventCallbacks[event]

		# Stop timers
		if self.moduleTimers.has_key(obj):
			for timer in self.moduleTimers[obj]:
				timer.cancel()

			del self.moduleTimers[obj]

	## @brief Run a specified function after a specified time
	# @param interval Time to wait before calling the callback function
	# @param callback Function to call
	# @param oneshot True if you only want the timer to fire once, False to make a periodic timer
	# @param args (Optional) Tuple containing arguments in the order they should be passed 
	# @param kwargs (Optional) Dict containing named arguments to pass to the callback
	# @todo If the callback function raises an exception the timer won't be removed
	def register_timer(self, interval, callback, oneshot = True, args = (), kwargs = {}):
		def do_timeout(data):
			callback = data["callback"]
			oneshot  = data["oneshot"]
			callback(*data["args"], **data["kwargs"])

			# Free timer
			if oneshot:
				if self.moduleTimers.has_key(callback.im_self):
					for timer in self.moduleTimers[callback.im_self]:
						if timer == threading.currentThread():
							self.moduleTimers[callback.im_self].remove(timer)

					if len(self.moduleTimers[callback.im_self]) == 0:
						del self.moduleTimers[callback.im_self]

		data = {
			"callback": callback,
			"args"  : args,
			"kwargs": kwargs,
			"oneshot": oneshot
		}

		if not hasattr(callback, "im_self"):
			raise Exception("Only class methods can be registered as timer callbacks")

		# Create timer object with associated data
		timer = threading.Timer(interval, do_timeout, kwargs = {"data": data})
		#timer = threading.Timer(interval, do_timeout, oneShot = oneshot, kwargs = {"data": data})

		# Insert timer in list of active timers
		if not self.moduleTimers.has_key(callback.im_self):
			self.moduleTimers[callback.im_self] = []
		self.moduleTimers[callback.im_self].append(timer)

		# Dispatch timer
		timer.start()

	## @brief Register command callback
	# @param command Command excluding command prefix. Example: "mycommand"
	# @param callback Function to execute when this command is dispatched
	# @param privileged Whether or not the command is privileged or not and subject to ACL
	#
	# @note
	# <pre>
	# Callback functions should have the form
	# def callback(ModuleInterface, params)
	# Where params will be the parameters of the command. Example: "!mycommand param1 param2 param3" will yield "param1 param2 param3"
	# </pre>
	def register_command(self, command, callback, privileged = False):
		key = command.upper()
		if not self.commandCallbacks.has_key(key):
			self.commandCallbacks[key] = []

		self.commandCallbacks[key].append((callback.im_self, callback, privileged))


	## @brief Dispatch a command
	# @param irc IRCHandler instance
	# @param msg IRCMessage instance
	# @param command The command. Example: "mycommand"
	# @param params Parameters to the command. Example: "param1 param2 param3"
	def DispatchCommand(self, irc, msg, command, params):
		key = command.upper()

		if self.commandCallbacks.has_key(key):
			interface = ModuleInterface(irc, msg)

			# Check access
			masters = self.config.Bot["masters"]
			masterAccess = reduce(lambda x,y : x or y, [msg.source.matches(hostmask) for hostmask in masters])
			

			for (obj, callback, privileged) in self.commandCallbacks[key]:
				try:
					# This will abort instantly as soon as a command without access is found
					if privileged and not masterAccess:
						if not self.acl.CheckAccess(msg.source, command.lower()):
							interface.Reply("Access denied")
							return

					callback(interface, params)
				except Exception, e:
					interface.Reply(e)
					print traceback.format_exc()
					

	## @brief Register event callback
	# Register callback for an IRC-event, this could be any command the server sends, including numerics.
	# @param callback Function to execute when this event is dispatched
	# @param event Event to register. Example: "PRIVMSG", "PART", "QUIT", "001"
	#
	# @note
	# <pre>
	# Callback functions should have the form
	# def callback(IRCMessageController)
	# </pre>
	def register_event(self, event, callback):
		key = str(event).upper()
		if not self.eventCallbacks.has_key(key):
			self.eventCallbacks[key] = []

		self.eventCallbacks[key].append((callback.im_self, callback))

	## @brief Dispatch an event
	# @param irc IRCController instance
	# @param msg IRCMessage instance. IRCMessage.command contains the event.
	def dispatch_event(self, irc, msg):
		def dispatcher_thread(callback, interface):
			try:
				callback(interface)
			except Exception, e:
				print traceback.format_exc()
				interface.reply(e)

		if not msg.command:
			return

		key = msg.command.upper()
		if self.eventCallbacks.has_key(key):
			interface = IRCMessageController(irc, msg)

			for (obj, callback) in self.eventCallbacks[key]:
				thread = threading.Thread(target = dispatcher_thread, kwargs = {"callback": callback, "interface": interface})
				thread.start()
