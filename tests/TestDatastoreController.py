# -*- coding: utf-8 -*-
import unittest
import tempfile
import shutil
import hashlib

from controllers.datastorecontroller import DatastoreController

class TestDatastoreController(unittest.TestCase):
	def setUp(self):
		self.tempdir = tempfile.mkdtemp()
		self.ds = DatastoreController()
		self.ds.set_driver(self.tempdir + "/acl.db")
		self.store = self.ds.get_store("test_store")

	def tearDown(self):
		shutil.rmtree(self.tempdir)

	def testSimplePutGet(self):
		for value in ['teststring', 3.14, 85324, u'åäö', 3.14159265358979323846264338327950288419716939937510]:
			self.store.put("name", value)
			self.assertEqual(value, self.store.get("name"))

	def testNonExistantKey(self):
		self.assertEqual(None, self.store.get("invalidkey"))

	def testBinaryData(self):
		data = ''
		for byte in range(0,255):
			data += chr(byte)

		before = hashlib.sha256(data).hexdigest()
		self.store.put("binaryblob", data)

		self.assertEqual(hashlib.sha256(self.store.get("binaryblob")).hexdigest(), before)
