# -*- coding: utf-8 -*-
## @package plugincontroller
# Handler of loading/unloading plugins

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

import new
import sys
import os
import types
import traceback

from lib import Plugin
from lib import Logger
from lib.util import Singleton

from controllers.datastorecontroller import DatastoreController
from controllers.eventcontroller     import EventController
from controllers.configcontroller    import ConfigController

##
# Handler of loading/unloding plugins
class PluginController(Singleton):
	def construct(self):
		self.loaded_plugins = {}
		self.eventcontroller = EventController()

	def unload_all(self):
		for plugin in self.loaded_plugins.keys():
			self.unload_plugin(plugin)

	def reload_plugin(self, name):
		name = name.strip()

		try:
			self.unload_plugin(name)
		except:
			pass

		return self.load_plugin(name)

	def unload_plugin(self, name, search = "plugins"):
		name = name.strip().lower()

		if not self.loaded_plugins.has_key(name):
			raise Exception("No such plugin loaded")

		basename, instance = self.loaded_plugins[name]

		# Release events related to this plugin
		self.eventcontroller.release_related(instance)

		# Try to call Cleanup if it exists
		try:
			instance.cleanup()
		except:
			pass

		# Delete instance
		del instance
		del self.loaded_plugins[name]

		for module in sys.modules.keys():
			if module.startswith("%s.%s" % (search, basename)):
				del sys.modules[module]

	def find_plugin(self, name, search_dir = "plugins"):
		# List of all plugins
		plugins = os.listdir(search_dir)
		
		# Try to intelligently find the plugin
		for plugin in plugins:
			pluginname = plugin.lower()
			basename = plugin.partition(".")[0]

			if pluginname.find(".pyc") != -1: 
				continue

			if pluginname.find(".") == 0:
				continue

			if basename.lower() != name.lower():
				continue

			Logger.debug("Candidate plugin '%s'" % plugin)

			return basename

	def load_plugin(self, name, search_dir = "plugins"):
		name = name.strip()
		import_name = None
		try:
			if self.loaded_plugins.has_key(name):
				raise Exception("Plugin is already loaded")

			basename = self.find_plugin(name, search_dir)

			if not basename:
				raise Exception("No such plugin")

			import_name = "%s.%s" % (search_dir, basename)
			mod = __import__(import_name)
			cls = getattr(mod, basename)

			# Find the plugin entry point
			for objname in dir(cls):
				obj = getattr(cls, objname)
				if objname != 'Plugin' and type(obj) == types.ClassType and issubclass(obj, Plugin):
					Logger.debug("Plugin entry for is '%s'" % objname)
					instance = new.instance(obj)

					# Initialize plugin instance
					instance.store  = DatastoreController().get_store(basename)
					instance.event  = self.eventcontroller
					instance.config = ConfigController()
					instance.plugin = self
					instance.__init__()

					self.loaded_plugins[basename.lower()] = (basename, instance)

					return True

			raise Exception("Unable to find entry point")

		except Exception, e:
			# Remove the system-entry
			if import_name and sys.modules.has_key(import_name):
				del sys.modules[import_name]

			Logger.log_traceback(self)
			raise Exception("Unable to load plugin: %s (%s)" % (name, e))
