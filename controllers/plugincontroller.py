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

from lib.plugin import Plugin
from lib.logger import Logger
from lib.util.singleton import Singleton

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
    def construct(self, eventcontroller = None, configcontroller = None):
        self._loaded_plugins = {}

        if eventcontroller:
            self._eventcontroller = eventcontroller
        else:
            self._eventcontroller = EventController()

        if configcontroller:
            self._config = configcontroller
        else:
            self._config = ConfigController()

    ##
    # Unload all loaded plugins
    def unload_all(self):
        for plugin in self._loaded_plugins.keys():
            self.unload_plugin(plugin)

    ##
    # Reload a plugin by name
    # @note The plugin will be unloaded but not loaded again if it's in a non-standard path
    def reload_plugin(self, name, search_dir = None):
        try:
            self.unload_plugin(name)
        except:
            pass

        return self.load_plugin(name, search_dir)

    def unload_plugin(self, name):
        name = name.strip().lower()

        if not self._loaded_plugins.has_key(name):
            raise PluginUnloadError("No such plugin loaded")

        basename, instance, import_name = self._loaded_plugins[name]

        # Release events related to this plugin
        self._eventcontroller.release_related(instance)

        # Try to call Cleanup if it exists
        try:
            instance.cleanup()
        except:
            pass

        # Delete instance
        del instance
        del self._loaded_plugins[name]

        for module in sys.modules.keys():
            if module.startswith(import_name):
                del sys.modules[module]

        return True

    ##
    # Retrieve the names of all loaded plugins
    def get_loaded_plugins(self):
        return self._loaded_plugins.keys()

    ##
    # Generator for all candidate plugins
    # This will search through the given directory (or the plugin_paths if not specified)
    # and yield all candidate plugins in the form (path, name)
    #
    # @param search_dir Optional search directory. If not specified the plugin_paths from the
    #                   configuration will be used
    def plugin_candidates(self, search_dir = None):
        if search_dir:
            search_dirs = [search_dir]
        else:
            search_dirs = self._config.get('plugin_paths')

        ignore = shutil.ignore_patterns("*.pyc", "__init__.py", ".*")
        for search_dir in search_dirs:
            for root, dirs, files in os.walk(search_dir):
                ignored_files = ignore(root, files)
                files = [f for f in files if f not in ignored_files]

                # Look for plugins contained in directories
                for directory in dirs:
                    path = root + "." + directory
                    yield (root, directory)

                # We don't want to recurse
                dirs[:] = []

                # Replace path separators with dots to allow
                # it to be loaded directly
                root = root.replace(os.sep, ".")

                # Look for plugins containes as single files
                for filename in files:
                    base = filename.partition(".")[0]
                    path = root + "." + base
                    yield (root, base)

    ##
    # Find a plugin by name
    #
    # @param name Name of the plugin to search for
    # @param search_dir Optional search directory. If not specified the plugin_paths from the
    #                   configuration will be used
    def find_plugin(self, name, search_dir = None):
        for path, candidate_name in self.plugin_candidates(search_dir):
            if candidate_name.lower() == name.lower():
                module_name = path + "." + candidate_name
                Logger.debug("Candidate plugin '%s'" % module_name)
                return module_name

    ##
    # Load a specified plugin
    # @param name Name of plugin file (case insensitive)
    # @param search_dir Directory too look for plugin. If not specified, plugin_path
    #                   from the configuration will be used
    def load_plugin(self, name, search_dir = None):
        name = name.strip()
        import_name = None

        if self._loaded_plugins.has_key(name):
            raise PluginLoadError("Plugin is already loaded")

        import_name = self.find_plugin(name, search_dir)

        if not import_name:
            raise PluginLoadError("No such plugin")

        basename = import_name.rpartition(".")[2]

        try:
            mod = __import__(import_name)
            cls = getattr(mod, basename)
        except Exception as e:
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
                instance.event  = self._eventcontroller
                instance.config = self._config
                instance.nets   = IRCNetsController()
                instance.plugin = self
                instance.__init__()

                self._loaded_plugins[basename.lower()] = (basename, instance, import_name)

                return True

        del sys.modules[import_name]
        raise PluginLoadError("Unable to find entry point")

