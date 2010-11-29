import unittest

from controllers.plugincontroller import PluginController, PluginLoadError, PluginUnloadError
from controllers.configcontroller import ConfigController

class TestPluginController(unittest.TestCase):
    def setUp(self):
        self.plugin = PluginController()
        self.config = ConfigController()

    def tearDown(self):
        self.plugin = None

    def testLoadInvalidPluginException(self):
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'nonexistantplugin')
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, '')

    def testLoadUnloadCore(self):
        self.assertTrue(self.plugin.load_plugin('corecommands', 'core'))

        # No need to specify path, it should work anyway
        self.assertTrue(self.plugin.unload_plugin('corecommands'))

        # To make sure that it was unloaded, load it again
        self.assertTrue(self.plugin.load_plugin('corecommands', 'core'))
        self.assertTrue(self.plugin.unload_plugin('corecommands'))

    def testLoadUnloadDuplicate(self):
        self.assertTrue(self.plugin.load_plugin('normalplugin', 'test_plugins'))
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'normalplugin', 'test_plugins')

        self.assertTrue(self.plugin.unload_plugin('normalplugin'))
        self.assertRaises(PluginUnloadError, self.plugin.unload_plugin, 'normalplugin')

    def testNormalPlugin(self):
        self.assertTrue(self.plugin.load_plugin('normalplugin', 'test_plugins'))
        self.assertTrue(self.plugin.unload_plugin('normalplugin'))

    def testBrokenPlugin(self):
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'pluginwithsyntaxerror', 'test_plugins')
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'pluginrasesininit', 'test_plugins')

    def testPluginPaths(self):
        # Make sure we have a know state
        old_value = self.config.get("plugin_paths")
        self.config.set("plugin_paths", ["plugins"])

        # This plugin is not in the default path and should not be found
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'normalplugin')

        # Now add it to the path
        self.config.set("plugin_paths", ["plugins", "test_plugins"])
        self.assertTrue(self.plugin.load_plugin('normalplugin'))
        self.assertTrue(self.plugin.unload_plugin('normalplugin'))

        # Restore previous value
        self.config.set("plugin_paths", old_value)
