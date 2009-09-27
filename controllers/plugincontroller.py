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

import new
import sys
import traceback
#from Lib.ModuleInitInterface import ModuleInitInterface
#from Lib.TableFormatter import TableFormatter

class PluginInfo:
	def __init__(self):
		self.instance = None
		self.detail = {
			"description": None,
			"author": None,
			"version": 0.0,
			"name": None
		}

class PluginInterface:
	def __init__(self):
		self.eventcontroller = None

class PluginController:
	def __init__(self, eventcontroller):
		self.loaded_plugins = {}
		self.eventcontroller = eventcontroller

	def unload_all(self):
		for plugin in self.loaded_plugins.keys():
			self.unload_plugin(plugin)

#	def GetModuleInstance(self, name):
#		if self._plugins.has_key(name):
#			return self._plugins[name].instance
#		else:
#			return None

#	def GetPlugins(self):
#		if len(self._plugins) == 0:
#			return ["No plugins are loaded"]
#
#		table = TableFormatter(["Plugin", "Name", "Version", "Author"])
#
#		for plugin in self._plugins:
#			detail = self._plugins[plugin].detail
#			table.AddRow([plugin, detail["name"], detail["version"], detail["author"]])
#
#		return table.GetTable()

	def reload_plugin(self, name):
		name = name.strip()

		try:
			self.unload_plugin(name)
		except:
			pass

		self.load_plugin(name)

#	def UnloadCorePlugin(self, name):
#		self.UnloadPlugin(name, "CoreModules")

	def unload_plugin(self, name, search = "plugins"):
		name = name.strip()
		if not self.loaded_plugins.has_key(name):
			raise Exception("No such plugin")

		plugin = self.loaded_plugins[name]

		# Release events related to this plugin
		self.eventcontroller.release_related(plugin.instance)

		# Try to call Cleanup if it exists
		try:
			plugin.instance.cleanup()
		except:
			pass

		# Delete entry and instance
		del plugin.instance
		del self._plugins[name]

		for module in sys.modules.keys():
			if module.startswith("%s.%s" % (search, name)):
				del sys.modules[module]

#	def LoadCorePlugin(self, name):
#		self.LoadPlugin(name, "CoreModules")

	def load_plugin(self, name, search = "plugins"):
		name = name.strip()
		try:
			if self.loaded_plugins.has_key(name):
				raise Exception("Plugin is already loaded")

			mod = __import__("%s.%s" % (search, name))
			cls = getattr(mod, name)
			entry = getattr(cls, "PluginEntry")

			plugin = PluginInfo()
			self.loaded_plugins[name] = plugin
			plugin.instance = new.instance(entry)

			# @TODO Fixa interface
			interface = PluginInterface()
			interface.eventcontroller = self.eventcontroller

			try:
				plugin.instance.__init__(interface)
			except Exception, e:
				raise e

			try:
				(shortname, desc, version, author) = plugin.instance.GetDetails()
				plugin.detail["name"]        = shortname
				plugin.detail["description"] = desc
				plugin.detail["author"]      = author
				plugin.detail["version"]     = version
			except:
				pass

		except Exception, e:
			print traceback.format_exc()
			raise Exception("Unable to load plugin: %s (%s)" % (name, e))

#	def GetDetails(self, name):
#		name = name.strip()
#		if not self._plugins.has_key(name):
#			raise Exception("No such plugin")
#
#		return self._plugins[name].detail
