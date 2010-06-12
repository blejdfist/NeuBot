##
# @class SimpleStringLexer
# Extremely basic. No fancy LALR business!
class SimpleStringLexer:
	def __init__(self, s):
		self.whitespace = ' \t\r\n'
		self.quotes = '\'"'

		self._pos = 0
		self._state_substring = False
		self._str = s.strip()
		self._length = len(self._str)

	def _eat_whitespace(self):
		# Eat whitespace
		while self._pos != self._length and self._str[self._pos] in self.whitespace:
			self._pos += 1

	##
	# Get the substring, call this when the position is currently on
	# a quote-character
	def _get_substring(self):
		if self._pos == self._length:
			raise Exception("Invalid substring")

		quote_char = self._str[self._pos]
		substring = ""

		# Skip quote char
		self._pos += 1

		# Eat substring until we hit the end or find the end quote
		while self._pos != self._length and self._str[self._pos] != quote_char:
			if self._str[self._pos] != quote_char:
				substring += self._str[self._pos]

			self._pos += 1

		if self._pos == self._length or self._str[self._pos] != quote_char:
			raise Exception("Cannot find end of quoted string")

		self._pos += 1

		return substring

	def _get_token(self):
		if self._pos == self._length:
			return None

		token = ""

		while self._pos != self._length and self._str[self._pos] not in self.whitespace:
			token += self._str[self._pos]
			self._pos += 1

		return token

	##
	# Get next token
	def _next(self):
		if self._pos == self._length:
			return None

		# Check if this is a quoted string
		if self._str[self._pos] in self.quotes:
			result = self._get_substring()
		else:
			result = self._get_token()

		return result

	##
	# Split string and return a list of tuples with the part values
	def split(self):
		result = []
		while True:
			startpos = self._pos
			part = self._next()
			stoppos = self._pos

			self._eat_whitespace()

			if part is None:
				return result

			result.append((part, startpos, stoppos))
