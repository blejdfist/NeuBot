from lib.util.simplestringlexer import SimpleStringLexer

##
# @class Arguments
# Wrapper that splits command line arguments in a shell-like fashion.
# This makes it easier to split arguments that use quoted substrings
#
# Example:
# <pre>
# >>> from models.arguments import Arguments
# >>> arg = Arguments('tell #channel "Hi guys!"')
# >>> len(arg)
# 3
# >>> arg[0]
# 'tell'
# >>> arg[1]
# '#channel'
# >>> arg[2]
# 'Hi guys!'
# >>> arg[0:]
# ['tell', '#channel', 'Hi guys!']
# </pre>
class Arguments:
	def __init__(self, str):
		if str:
			self._str = str.strip()
			try:
				self._splitted = SimpleStringLexer(str).split()
			except:
				self._splitted = []
		else:
			self._str = ""
			self._splitted = []

	##
	# Get unprocessed argument string after a numbered argument.
	# Ex. get_args_after(1) on 'a "b c" d e f' yields 'd e f'
	#     get_args_after(1) on 'a b c d e f' yields 'c d e f'
	# @param i Index of parsed arguments after which will be returned
	def get_args_after(self, i):
		_, start, _ = self._splitted[i+1]
		return self._str[start:]

	def __str__(self):
		return self._str

	def __repr__(self):
		return "<Arguments %s>" % self._str

	def __getitem__(self, n):
		return self._splitted[n][0]

	def __getslice__(self, i, j):
		return [s for (s, _, _) in self._splitted[i:j]]

	def __len__(self):
		return len(self._splitted)
