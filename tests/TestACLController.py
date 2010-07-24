import unittest
import tempfile
import shutil

from controllers.aclcontroller import ACLController
from controllers.configcontroller import ConfigController
from models import IRCUser

class TestACLController(unittest.TestCase):
	def setUp(self):
		self.tempdir = tempfile.mkdtemp()
		self.acl = ACLController(self.tempdir + "/acl.db")

	def tearDown(self):
		shutil.rmtree(self.tempdir)

	def testCreateDeleteUsers(self):
		self.acl.add_user('bill')
		self.acl.add_user('bob')
		self.acl.add_user('anna')
		self.acl.add_user('linda')

		self.assertRaises(Exception, self.acl.add_user, 'linda')
		self.assertRaises(Exception, self.acl.del_user, 'user_that_doesnt_exist')

	def testAddDelHostMask(self):
		self.acl.add_user('theuser')
		self.acl.user_add_hostmask('theuser', '*!test@domain.tld')
		self.acl.user_add_hostmask('theuser', '*!testfisk@otherdomain.tld')

		self.assertRaises(Exception, self.acl.user_add_hostmask, 'theuser', 'invalid hostmask')
		self.assertRaises(Exception, self.acl.user_add_hostmask, 'theuser', '*!*invalid hostmask')
		self.assertRaises(Exception, self.acl.user_add_hostmask, 'theuser', 'invalid!hostmask')
		self.assertRaises(Exception, self.acl.user_add_hostmask, 'theuser', '')
		self.assertRaises(Exception, self.acl.user_add_hostmask, 'user_that_doesnt_exist', 'anyhostmask')
		self.assertRaises(Exception, self.acl.user_del_hostmask, 'user_that_doesnt_exist', 'anyhostmask')
		self.assertRaises(Exception, self.acl.user_del_hostmask, 'theuser', 'hostmask_that_doesnt_exist')

		self.acl.user_del_hostmask('theuser', '*!testfisk@otherdomain.tld')

	def testAddDelGroups(self):
		self.acl.add_group("mygroup")
		self.acl.del_group("mygroup")

		self.acl.add_group("duplicate")
		self.assertRaises(Exception, self.acl.add_group, "duplicate")

		self.assertRaises(Exception, self.acl.del_group, "nonexistant")

	def testMatchHostmasks(self):
		self.acl.add_user('theuser')
		self.acl.user_add_hostmask('theuser', 'TheUser!ident@host.tld')

		self.acl.add_user('superuser')
		self.acl.user_add_hostmask('superuser', 'SuperUser!superident@superhost.tld')

		self.acl.add_user('baduser')
		self.acl.user_add_hostmask('baduser', 'BadUser!bad@user.tld')

		identityNormal = IRCUser('TheUser!ident@host.tld')
		identitySuper  = IRCUser('SuperUser!superident@superhost.tld')
		identityBad    = IRCUser('BadUser!bad@user.tld')

		self.assertRaises(Exception, self.acl.access_allow, 'secret', 'nosuchuser')
		self.acl.access_allow('secret', 'superuser')

		self.assertFalse(self.acl.check_access(identityNormal, 'secret'))
		self.assertTrue(self.acl.check_access(identitySuper, 'secret'))
		self.assertFalse(self.acl.check_access(identitySuper, 'SECRET'))
		self.assertFalse(self.acl.check_access(identitySuper, 'secret2'))

		# Test group access
		self.acl.add_group('superusers')
		self.acl.group_add_user('superuser', 'superusers')

		self.acl.add_group('normalusers')
		self.acl.group_add_user('theuser', 'normalusers')

		# "any"-group
		self.acl.access_allow('foreveryone', 'any')
		self.assertTrue(self.acl.check_access(identityNormal, 'foreveryone'))

		# Exclusion (Ticket #1)
		#self.assertTrue(self.acl.check_access(identityBad, 'foreveryone'))
		#self.acl.access_deny('foreveryone', 'baduser')
		#self.assertFalse(self.acl.check_access(identityBad, 'foreveryone'))

		# Group membership
		self.acl.access_allow('supersecret', 'superusers')
		self.assertTrue(self.acl.check_access(identitySuper, 'supersecret'))
		self.assertFalse(self.acl.check_access(identityNormal, 'supersecret'))
		self.assertFalse(self.acl.check_access(identityBad, 'supersecret'))

	def testMasterAccess(self):
		config = ConfigController()
		config.load_defaults()
		config.get('masters').append("*!master@masterhost.tld")

		identityMaster = IRCUser('iamthemaster!master@masterhost.tld')
		identityNormal = IRCUser('TheUser!ident@host.tld')

		self.assertTrue(self.acl.check_access(identityMaster, 'something'))
		self.assertFalse(self.acl.check_access(identityNormal, 'something'))

