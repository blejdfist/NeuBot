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

	def testBoundaryChecks(self):
		a = Arguments("a b c 'd e f' 'g h'")

		self.assertRaises(IndexError, a.__getitem__, 5)
		self.assertRaises(IndexError, a.__getitem__, -6)

	def testEscapeCharacters(self):
		a = Arguments("a b c \\\"")
		self.assertEqual(a[3], '"')

		a = Arguments("a b c \"\\\"\"")
		self.assertEqual(a[3], '"')

		a = Arguments("\\\"")
		self.assertEqual(a[0], '"')

		a = Arguments("\\\\")
		self.assertEqual(a[0], '\\')

		a = Arguments("\\n")
		self.assertEqual(str(a), "\\n")
		self.assertRaises(IndexError, a.__getitem__, 0)

		a = Arguments("a \"Quoted \\\"string\\\"\"")
		self.assertEqual(a[1], 'Quoted "string"')

		a = Arguments("Hello \"Quoted\\\"\"")

	def testInvalidEscapeSequences(self):
		invalid_sequences = [
			"Hello \\",      # Escape character at last position
			"Hello\\nthere",
			"Hello\\q",
		]

		for sequence in invalid_sequences:
			a = Arguments(sequence)
			self.assertEqual(len(a), 0)
			self.assertEqual(str(a), sequence)

	def testSlices(self):
		a = Arguments("a b c d e")
		self.assertEqual(a[1:4], ["b", "c", "d"])

		a = Arguments("'a b' c 'd f g' h i j")
		self.assertEqual(a[1:4], ["c", "d f g", "h"])

	def testEmptyString(self):
		a = Arguments("")
		self.assertEqual(str(a), "")
		self.assertEqual(len(a), 0)
		self.assertEqual(a[0:], [])


	def testInvalidQuotedString(self):
		invalid_quoted_strings = [
			'This string is missing the last "quote',
			'This string is missing the last \'quote',
			'"This string has unmatched \'quotes',
		]

		for s in invalid_quoted_strings:
			a = Arguments(s)
			self.assertEqual(len(a), 0)
			self.assertEqual(str(a), s)
