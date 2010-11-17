# -*- coding: utf-8 -*-
## @package controllers.configcontroller
# @brief Configuration handling

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

import sys

from lib.util import Singleton
from lib.logger import Logger

##
# Contains the configuration
class ConfigController(Singleton):
	def construct(self):
		self.config = {}

		self.reload()

	def load_defaults(self):
		self.config = {
			"debug": False,
			"ircnets": [],
			"datastore": "yserial://datastore.db",
			"masters": [],
			"coreplugins": ["aclcommands", "corecommands"],
			"plugins": [],
			"plugin_paths": ["plugins"],
			"log.level": "FATAL",

			"irc.pong_timeout":            180,		# Time of no ping/pong until bot sends it's own PING to server
			"irc.pong_disconnect_time":    300,		# Time of no ping/pong until bot tries to reconnect
			"irc.reclaim_nick_time":       30,		# Time to wait before trying to reclaim lost nick
			"irc.rejoin_channel_time":     10,		# Time to wait before trying to rejoin channel
			"irc.reconnect_time":          60,		# Time to wait before trying to reconnect to server
			"irc.reclaim_nick_if_lost":    True,	# Should the bot try to reclaim a lost nick?
			"irc.rate_limit_burst_max":    8,		# Maximum number of messages that will be sent in a burst before rate limits are applied
			"irc.rate_limit_wait_time":    3,		# When burst limit is reached, how long should we wait before continuing
		}

	def reload(self):
		self.load_defaults()

		if sys.modules.has_key('config'):
			del sys.modules['config']

		try:
			mod = __import__("config")

			# Overwrite any defaults
			for key in mod.Bot.keys():
				self.config[key] = mod.Bot[key]

			del mod
		except ImportError as e:
			Logger.warning("No configuration found. Using defaults.")

	##
	# Get the value for a configuration option
	# @param key Configuration option
	# @return Option value
	def get(self, key):
		if self.config.has_key(key):
			return self.config[key]

		return None
