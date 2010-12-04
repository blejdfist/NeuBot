import unittest
import os

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

        self.assertTrue(self.plugin.load_plugin('  normalplugin', 'test_plugins'))
        self.assertTrue(self.plugin.unload_plugin('normalplugin  '))

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

    def testLoadUnloadAllPlugins(self):
        self.assertEqual([], self.plugin.get_loaded_plugins())

        # Load a plugin
        self.assertTrue(self.plugin.load_plugin('normalplugin', 'test_plugins'))
        self.assertTrue(self.plugin.load_plugin('corecommands', 'core'))
        self.assertEqual(['corecommands', 'normalplugin'], self.plugin.get_loaded_plugins())

        # Unload all plugins
        self.plugin.unload_all()
        self.assertEqual([], self.plugin.get_loaded_plugins())

    def testLoadPluginWithoutEntry(self):
        self.assertRaises(PluginLoadError, self.plugin.load_plugin, 'pluginwithoutentry', 'test_plugins')

    def testReloadPlugin(self):
        class TestStub:
            def register_event(self, event, callback):
                # Trigger the callback
                self.value = callback(self)

            def release_related(self, *args):
                pass

        # Create our plugin
        code = [
            "from lib.plugin import Plugin",
            "class TestReloadPlugin(Plugin):",
            "    def __init__(self):",
            "        self._test_value = 'foo'",
            "        self.event.register_event('test', self.event_foo)",
            "    def event_foo(self, irc):",
            "        return self._test_value"
        ]
        plugin = open("test_plugins/testreloadplugin.py", "w")
        plugin.writelines("\n".join(code))
        plugin.close()

        teststub = TestStub()
        self.plugin.construct(eventcontroller = teststub)

        self.assertTrue(self.plugin.load_plugin('testreloadplugin', 'test_plugins'))
        self.assertEqual(teststub.value, 'foo')

        # Modify the line above that sets the value
        code[3] = "        self._test_value = 'bar'"
        plugin = open("test_plugins/testreloadplugin.py", "w")
        plugin.writelines("\n".join(code))
        plugin.close()

        # Delete the pyc-file, otherwise this might be loaded instead
        # This is simply because the tests runs so fast that Python thinks the pyc-file is up to date
        os.unlink("test_plugins/testreloadplugin.pyc")

        # Reload the plugin and make sure that our changes have taken effect
        self.assertTrue(self.plugin.reload_plugin('testreloadplugin', 'test_plugins'))
        self.assertEqual(teststub.value, 'bar')

        self.assertTrue(self.plugin.unload_plugin('testreloadplugin'))

        # Remove the test plugin
        os.unlink("test_plugins/testreloadplugin.pyc")
        os.unlink("test_plugins/testreloadplugin.py")

        # Reset the plugin controller
        self.plugin.construct()

    def testReloadNotLoadedPlugin(self):
        self.assertEqual([], self.plugin.get_loaded_plugins())

        self.assertTrue(self.plugin.reload_plugin('normalplugin', 'test_plugins'))
        self.assertEqual(['normalplugin'], self.plugin.get_loaded_plugins())

        self.assertTrue(self.plugin.unload_plugin('normalplugin'))
        self.assertEqual([], self.plugin.get_loaded_plugins())
