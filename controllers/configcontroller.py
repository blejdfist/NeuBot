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

from lib.util import Singleton
import sys

##
# Contains the configuration
class ConfigController(Singleton):
	def __init__(self):
		if not hasattr(self, 'botconfig'):
			self.load()

	def load(self):
		if hasattr(self, "botconfig"):
			del self.botconfig

		if sys.modules.has_key('config'):
			del sys.modules['config']

		mod = __import__("config")
		self.botconfig = mod.Bot

	##
	# Get the value for a configuration option
	# @param key Configuration option
	# @return Option value
	def get(self, key):
		if self.botconfig.has_key(key):
			return self.botconfig[key]

		return None
