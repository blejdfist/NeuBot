import readline
from commandparser import CommandParser

class CommandShell:
	def __init__(self, parseTree):
		self.parseTree = parseTree
		self.parser = CommandParser(parseTree)

		readline.parse_and_bind("tab: complete")
		readline.set_completer(self._tab_completer)
		readline.set_completer_delims(" ")

	def _traverse_tree(self, tree, tokens):
		result = []

		if len(tokens) == 0:
			for key in tree.keys():
				if type(key) == str and key[0] != "$":
					result.append(key + " ")

			return result

		for key in tree.keys():
			if type(key) == str and key[0] != "$":
				if key.lower().startswith(tokens[0].strip().lower()):
					result.append(key + " ")

		if tree.has_key(tokens[0].strip()):
			if len(result) > 1:
				return result
			else:
				return self._traverse_tree(tree[tokens[0].strip().lower()], tokens[1:])
		else:
			return result

		return []

	def _tab_completer(self, text, state):
		tokens = readline.get_line_buffer().split()
		result = self._traverse_tree(self.parseTree, tokens)
		result.append(None)

		return result[state]

	def input(self, prompt):
		data = raw_input(prompt)

		if data:
			return self.parser.parse(data)
