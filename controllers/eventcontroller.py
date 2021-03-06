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

from controllers.ircmessagecontroller import IRCMessageController
from controllers.aclcontroller        import ACLController
from controllers.configcontroller     import ConfigController

from lib.logger import Logger
from lib.util.singleton import Singleton

from models.arguments import Arguments

import threading
import re

## 
# The EventController handles events and calls the appropriate callbacks when the occur
#
# The callback functions are REQUIRED to be enclosed in class instances since
# the class instance (usually the module) is used to track which events are related
# so that they ca be freed when the module is unloaded
class EventController(Singleton):
    ## @brief Constructor
    def construct(self):
        self.commandCallbacks = {}  # "command" : [(object_instance, callback, privileged), ...]
        self.eventCallbacks = {}    # "event"   : [(object_instance, callback), ...]
        self.syseventCallbacks = {} # "sysevent": [(object_instance, callback), ...]

        # {obj: timer}
        self.moduleTimers = {}

        self.config = ConfigController()
        self.acl = ACLController()

        self.command_prefix = "!"

        # Number of active dispatched event threads
        self._pending_events = 0
        self._pending_events_lock = threading.RLock()
        self._pending_events_event = threading.Event()

    ##
    # Increment the number of active event threads
    def _increment_event_threads(self):
        with self._pending_events_lock:
            self._pending_events += 1
            self._pending_events_event.clear()

    ##
    # Decrement the number of active event threads
    # and signal any waiters if the number of event
    # threads reaches zero
    def _decrement_event_threads(self):
        with self._pending_events_lock:
            self._pending_events -= 1
            if self._pending_events == 0:
                self._pending_events_event.set()

    ##
    # Block until all dispatched events have finished.
    # This is primarily used by the simulator.
    def wait_for_pending_events(self):
        self._pending_events_event.wait()

    ## @brief Release callbacks registered by a module
    # @param obj Module instance for which callbacks should be released
    # @warning This should NEVER be called directly by a module
    def release_related(self, obj):
        for table in [self.commandCallbacks,
                      self.eventCallbacks,
                      self.syseventCallbacks]:

            for key in table.keys():
                entries = [entry for entry in table[key] if entry[0] == obj]

                for entry in entries:
                    table[key].remove(entry)

                if len(table[key]) == 0:
                    del table[key]

        # Stop timers
        if self.moduleTimers.has_key(obj):
            for timer in self.moduleTimers[obj]:
                timer.cancel()

            del self.moduleTimers[obj]

    ## @brief Run a specified function after a specified time
    # @param callback Function to call
    # @param interval Time to wait before calling the callback function
    # @param args (Optional) Tuple containing arguments in the order they should be passed
    # @param kwargs (Optional) Dict containing named arguments to pass to the callback
    def register_timer(self, callback, interval, args = (), kwargs = {}):
        def do_timeout(data):
            callback = data["callback"]
            try:
                callback(*data["args"], **data["kwargs"])
            except Exception as e:
                Logger.warning("Timer caught exception: %s" % e)

            # Free timer
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
        }

        if not hasattr(callback, "im_self"):
            raise Exception("Only class methods can be registered as timer callbacks")

        # Create timer object with associated data
        timer = threading.Timer(interval, do_timeout, kwargs = {"data": data})

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
        key = command.lower()

        if not self.commandCallbacks.has_key(key):
            self.commandCallbacks[key] = []

        self.commandCallbacks[key].append((callback.im_self, callback, privileged))

    ##
    # Retrieve all callbacks associated with a command
    # @param command Command to find associated callbacks for
    # @return List of tuples (classinstance, callback, privileged?)
    def get_command_callbacks(self, command):
        key = command.lower()

        if not self.commandCallbacks.has_key(key):
            return []

        return self.commandCallbacks[key]

    ##
    # Retrieve a list of all available commands
    def get_all_commands(self):
        return self.commandCallbacks.keys()

    ## @brief Dispatch a command
    # @param irc IRCController instance
    # @param msg IRCMessage instance
    # @param command The command. Example: "mycommand"
    # @param params Parameters to the command. Example: "param1 param2 param3"
    def dispatch_command(self, irc, msg, command, params):
        def dispatcher_command_thread(callback, interface, params):
            try:
                callback(interface, params)
            except:
                Logger.log_traceback(callback.im_self)
            finally:
                self._decrement_event_threads()

        params = Arguments(params)

        callbacks = self.get_command_callbacks(command)

        Logger.debug1("Found %d receiver(s) for command '%s'" % (len(callbacks), command))

        if callbacks:
            interface = IRCMessageController(irc, msg)

            for (obj, callback, privileged) in callbacks:
                try:
                    # This will abort instantly as soon as a command without access is found
                    if privileged:
                        if not self.acl.check_access(msg.source, command.lower()):
                            interface.reply("Access denied")
                            return

                    thread = threading.Thread(target = dispatcher_command_thread,
                                              kwargs = {"callback": callback, "interface": interface, "params": params})
                    self._increment_event_threads()
                    thread.start()
                except Exception as e:
                    Logger.log_traceback(callback.im_self)

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

    ##
    # Register a system event callback
    # @param event Event code
    # @param callback Callback function to receive the event
    def register_system_event(self, event, callback):
        key = str(event).upper()
        if not self.syseventCallbacks.has_key(key):
            self.syseventCallbacks[key] = []

        self.syseventCallbacks[key].append((callback.im_self, callback))

    ##
    # Dispatch an bot internal event
    # @param event Event code
    # @param params Parameters to send to the event handler (optional)
    def dispatch_system_event(self, event, params = []):
        key = str(event).upper()
        def dispatcher_event_thread(callback, params):
            try:
                callback(params)
            except:
                Logger.log_traceback(callback.im_self)

        if self.syseventCallbacks.has_key(key):
            for (_, callback) in self.syseventCallbacks[key]:
                thread = threading.Thread(target = dispatcher_event_thread, kwargs = {"callback": callback, "params": params})
                thread.start()

    ## @brief Dispatch an event
    # @param irc IRCController instance
    # @param msg IRCMessage instance. IRCMessage.command contains the event.
    def dispatch_event(self, irc, msg):
        def dispatcher_event_thread(callback, interface):
            try:
                callback(interface)
            except:
                Logger.log_traceback(callback.im_self)
            finally:
                self._decrement_event_threads()

        if not msg.command:
            return

        # Dispatch the event
        key = msg.command.upper()
        if self.eventCallbacks.has_key(key):
            interface = IRCMessageController(irc, msg)

            for (obj, callback) in self.eventCallbacks[key]:
                thread = threading.Thread(target = dispatcher_event_thread,
                                          kwargs = {"callback": callback, "interface": interface})
                self._increment_event_threads()
                thread.start()

        # Check if it may be a command
        if msg.command == "PRIVMSG":
            match = re.match("^%s([^ ]+)(?:$| (.*)$)" % self.command_prefix, msg.params)
            if match:
                command, params = match.groups()
                self.dispatch_command(irc, msg, command, params)
