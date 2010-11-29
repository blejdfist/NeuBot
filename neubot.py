#!/usr/bin/env python
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

from controllers.irccontroller import IRCController
from controllers.eventcontroller import EventController
from controllers.plugincontroller import PluginController
from controllers.configcontroller import ConfigController
from controllers.datastorecontroller import DatastoreController
from controllers.ircnetscontroller import IRCNetsController

from lib.logger import Logger

from models import Channel
from models import Server

import threading

##
# @mainpage NeuBot Developer Documentation
#
# @section module Writing modules
#
# Module skeleton
# @code
# from lib import Plugin
# class MyModule(Plugin):
#     def __init__(self):
#         self.name = "Skeleton Module"
#         self.author = "Jim Persson"
#         self.version = "1.0"
#
#         # Register commands
#         self.event.register_command("mycommand",         self.cmd_mycommand)
#         self.event.register_command("privilegedcommand", self.cmd_privilegedcommand, True)
#
#         # Register an event
#         self.event.register_event("PRIVMSG", self.event_privmsghook)
#
#         # Register a timer
#         self.event.register_timer(self.timer_timeout, 10)
#
#         # Put a value in the data store
#         self.store.put("a_list", [1,2,3,4])
#
#     # This method is called when the plugin is unloaded
#     # it's VERY important that you clean up any threads etc that the plugin is using here
#     def cleanup(self):
#         pass
#
#     def cmd_mycommand(self, irc, params):
#         """Does nothing special"""
#         irc.reply("Params: " + params)
#
#     def cmd_privilegedcommand(self, irc, params):
#         """This command is privileged"""
#         # Retrieve a value from the data store and display it to the user
#         tmp = self.store.get("a_list")
#         irc.reply(tmp)
#
#     def event_privmsghook(self, irc):
#         irc.reply("Message from " + irc.message.source)
#
#     def timer_timeout(self):
#         # Timer fired
#         pass
# @endcode
# 
# When a module is instantiated it is automatically given a few attributes
# <ul>
#   <li>self.event @link controllers.eventcontroller.EventController EventController @endlink</li>
#   <li>self.store @link lib.db.store.Store Store @endlink (Wrapper around @link controllers.datastorecontroller.DatastoreController DatastoreController @endlink)</li>
#   <li>self.plugin @link controllers.plugincontroller.PluginController PluginController @endlink - Be careful with this one</li>
#   <li>self.config @link controllers.configcontroller.ConfigController ConfigController @endlink</li>
# </ul>
#
# When a command callback is called it is given two arguments
# <ul>
#   <li>irc @link controllers.ircmessagecontroller.IRCMessageController IRCMessageController @endlink - Wrapper around the IRCController along with some convenience functions</li>
#   <li>params @link models.arguments.Arguments Argments @endlink - The arguments to the command preparsed and packaged</li>
# </ul>
#
# Command documentation for callbacks can be put in the __doc__ for that command by writing the help in a triple-quote enclosed comment
# in the method header
# @code
# def cmd_mycommand(self, irc, params):
#     """
#     This is the documentation for this command.
#     It can be on multiple lines if needed."""
#     irc.reply("Hello!")
# @endcode
#
# @section useful_classes Useful classes
# <ul>
#   <li>@link controllers.ircmessagecontroller.IRCMessageController IRCMessageController @endlink - Gets passed as the first argument to command callbacks
#   <li>@link controllers.irccontroller.IRCController IRCController @endlink - Methods not handled by IRCMessageController is taken care by the current IRCController
# </ul>

## 
# Bot entrypoint
class NeuBot:
    """NeuBot"""
    def __init__(self):
        self.eventcontroller   = EventController()
        self.plugincontroller  = PluginController()
        self.ircnetscontroller = IRCNetsController()

        self.config = ConfigController()
        self.config.reload()

        self.quit_event = threading.Event()
        self.eventcontroller.register_system_event("BOT_QUIT", self.system_quit)

    def system_quit(self, params):
        self.quit_event.set()

    def start(self):
        # Initialize data store
        DatastoreController().set_driver(self.config.get('datastore'))

        Logger.set_loglevel(self.config.get('log.level'))

        for plugin in self.config.get('coreplugins'):
            Logger.info("Loading core plugin '%s'" % plugin)
            self.plugincontroller.load_plugin(plugin, 'core')

        for plugin in self.config.get('plugins'):
            Logger.info("Loading plugin '%s'" % plugin)
            self.plugincontroller.load_plugin(plugin)

        if len(self.config.get('ircnets')) == 0:
            raise Exception("There has to be at least one ircnet to connect to")

        for net in self.config.get('ircnets'):
            irc = IRCController(self.eventcontroller)

            # Add channels
            for (channel_name, channel_key) in net['channels']:
                channel = Channel(channel_name, channel_key)
                irc.channels.append(channel)

            # Add servers
            if len(net['servers']) == 0: 
                raise Exception("There must be at least one server defined")

            for (hostname, port, use_ssl, use_ipv6) in net['servers']:
                server = Server(hostname, port, use_ssl, use_ipv6)
                irc.servers.append(server)

            irc.ircnet   = net['ircnet']
            irc.nick     = net['nick']
            irc.altnicks = net['altnicks']
            irc.name     = net['name']
            irc.ident    = net['ident']

            Logger.info("Connecting to %s..." % irc.ircnet)
            irc.connect()

            self.ircnetscontroller.add_ircnet(irc.ircnet, irc)

    def stop(self):
        self.ircnetscontroller.disconnect_all()

if __name__ == "__main__":
    bot = None
    try:
        Logger.info("Initializing...")

        bot = NeuBot()
        bot.start()

        while not bot.quit_event.isSet():
            bot.quit_event.wait(1)

    except KeyboardInterrupt:
        Logger.info("Keyboard interrupt detected. Shutting down.")

    except Exception as e:
        Logger.fatal("Fatal error: %s" % e)

    finally:
        if bot:
            bot.stop()
