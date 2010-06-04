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
import shutil

from lib import Plugin
from lib import Logger
from lib.util import Singleton

from controllers.datastorecontroller import DatastoreController
from controllers.eventcontroller     import EventController
from controllers.configcontroller    import ConfigController
from controllers.ircnetscontroller   import IRCNetsController

class PluginLoadError(Exception):
	pass

class PluginUnloadError(Exception):
	pass

##
# Handler of loading/unloding plugins
class PluginController(Singleton):
	def construct(self):
		self.loaded_plugins = {}
		self.eventcontroller = EventController()
		self.config = ConfigController()

	##
	# Unload all loaded plugins
	def unload_all(self):
		for plugin in self.loaded_plugins.keys():
			self.unload_plugin(plugin)

	##
	# Reload a plugin by name
	# @note The plugin will be unloaded but not loaded again if it's in a non-standard path
	def reload_plugin(self, name):
		name = name.strip()

		try:
			self.unload_plugin(name)
		except:
			pass

		return self.load_plugin(name)

	def unload_plugin(self, name):
		name = name.strip().lower()

		if not self.loaded_plugins.has_key(name):
			raise PluginUnloadError("No such plugin loaded")

		basename, instance, import_name = self.loaded_plugins[name]

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
			if module.startswith(import_name):
				del sys.modules[module]

		return True

	def find_plugin(self, name, search_dir):
		if search_dir:
			search_dirs = [search_dir]
		else:
			search_dirs = self.config.get('plugin_paths')

		ignore = shutil.ignore_patterns("*.pyc", "__init__.py")

		Logger.debug2("Trying to find plugin %s" % name)
		for search_dir in search_dirs:
			Logger.debug3("Searching path %s for plugin %s" % (search_dir, name))
			for root, dirs, files in os.walk(search_dir):
				ignored_files = ignore(root, files)
				files = filter(lambda x : x not in ignored_files, files)

				# We don't want to recurse
				dirs[:] = []

				# Replace path separators with dots to allow
				# it to be loaded directly
				root = root.replace(os.sep, ".")

				for filename in files:
					base = filename.partition(".")[0]
					path = root + "." + base
					if base.lower() == name.lower():
						Logger.debug("Candidate plugin '%s'" % path)
						return path

	##
	# Load a specified plugin
	# @param name Name of plugin file (case insensitive)
	# @param search_dir Directory too look for plugin. If not specified, plugin_path
	#                   from the configuration will be used
	def load_plugin(self, name, search_dir = None):
		name = name.strip()
		import_name = None

		if self.loaded_plugins.has_key(name):
			raise PluginLoadError("Plugin is already loaded")

		import_name = self.find_plugin(name, search_dir)

		if not import_name:
			raise PluginLoadError("No such plugin")

		basename = import_name.rpartition(".")[2]

		try:
			mod = __import__(import_name)
			cls = getattr(mod, basename)
		except Exception, e:
			# Remove the system-entry
			if import_name and sys.modules.has_key(import_name):
				del sys.modules[import_name]

			Logger.log_traceback(self)
			raise PluginLoadError("Failed to load " + import_name)

		# Find the plugin entry point
		for objname in dir(cls):
			obj = getattr(cls, objname)
			if objname != 'Plugin' and type(obj) == types.ClassType and issubclass(obj, Plugin):
				Logger.debug("Plugin entry is '%s'" % objname)
				instance = new.instance(obj)

				# Initialize plugin instance
				instance.store  = DatastoreController().get_store(basename)
				instance.event  = self.eventcontroller
				instance.config = self.config
				instance.nets   = IRCNetsController()
				instance.plugin = self
				instance.__init__()

				self.loaded_plugins[basename.lower()] = (basename, instance, import_name)

				return True

		raise PluginLoadError("Unable to find entry point")

