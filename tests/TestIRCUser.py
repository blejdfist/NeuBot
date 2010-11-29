import unittest

from models import IRCUser

class TestIRCUser(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testMatchHostmask(self):
        identity = IRCUser('nick!ident@host.name.tld')

        self.assertTrue(identity.is_matching('nick!ident@host.name.tld'))
        self.assertTrue(identity.is_matching('*!ident@host.name.tld'))
        self.assertTrue(identity.is_matching('nick!*@host.name.tld'))
        self.assertTrue(identity.is_matching('nick!ident@*.name.tld'))

        self.assertFalse(identity.is_matching('nick2!ident@host.name.tld'))

