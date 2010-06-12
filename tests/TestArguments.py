import unittest

from models.arguments import Arguments

class TestArguments(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def testArgumentLengths(self):
		self.assertEqual(len(Arguments("a b c")), 3)
		self.assertEqual(len(Arguments("     a   b   c")), 3)
		self.assertEqual(len(Arguments("  	'a 	b' 	c d ")),3)
		self.assertEqual(len(Arguments("'a b' \"c d\" \"e f\"")), 3)

	def testArgumentValues(self):
		a = Arguments("a b c")
		self.assertEqual(a[1], 'b')

		a = Arguments("\tapa 'b c d' epa \"f   g\" l   h i   j")
		self.assertEqual(a[0], 'apa')
		self.assertEqual(a[1], 'b c d')
		self.assertEqual(a[2], 'epa')
		self.assertEqual(a[3], 'f   g')
		self.assertEqual(a[4], 'l')
		self.assertEqual(a[5], 'h')
		self.assertEqual(a.get_args_after(4), 'h i   j')
		self.assertEqual(a.get_args_after(2), '\"f   g\" l   h i   j')

	def testInvalidStrings(self):
		test_strings = [
			'This string is missing the last "quote',
			'This string is missing the last \'quote',
			'"This string has unmatched \'quotes',
		]

		for s in test_strings:
			self.assertRaises(Exception, Arguments, s)

	def testBoundaryChecks(self):
		a = Arguments("a b c 'd e f' 'g h'")

		self.assertRaises(IndexError, a.__getitem__, 5)
		self.assertRaises(IndexError, a.__getitem__, -6)
