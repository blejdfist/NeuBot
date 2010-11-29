##
# @class SimpleStringLexer
# Extremely basic. No fancy LALR business!
class SimpleStringLexer:
    def __init__(self, s):
        self.whitespace = ' \t\r\n'
        self.quotes = '\'"'
        self.escape_char = '\\'

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
        quote_char = self._str[self._pos]
        substring = ""

        # Skip quote char
        self._pos += 1

        # Eat substring until we hit the end or find the end quote
        while self._pos != self._length and self._str[self._pos] != quote_char:
            if self._str[self._pos] == self.escape_char:
                substring += self._parse_escaped_character()
            elif self._str[self._pos] != quote_char:
                substring += self._str[self._pos]

            self._pos += 1

        if self._pos == self._length or self._str[self._pos] != quote_char:
            raise Exception("Cannot find end of quoted string")

        self._pos += 1

        return substring

    def _get_token(self):
        token = ""

        while self._pos != self._length and self._str[self._pos] not in self.whitespace:
            if self._str[self._pos] == self.escape_char:
                token += self._parse_escaped_character()
            else:
                token += self._str[self._pos]

            self._pos += 1

        return token

    def _parse_escaped_character(self):
        if self._pos == self._length+1:
            raise Exception("Invalid escape sequence")

        # Skip escape-character
        self._pos += 1

        chars = {
            '\\': '\\',
            '"': '"',
            "'": "'",
        }

        the_char = self._str[self._pos]

        if the_char not in chars:
            raise Exception("Invalid escape sequence")

        return chars[the_char]

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
