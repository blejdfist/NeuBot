# -*- coding: utf-8 -*-

# This file is part of NeuBot.
#
# NeuBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2007-2008, Jim Persson, All rights reserved.

class CommandError(Exception):
    pass

## @brief Parse a command string and execute functions depending on result
class CommandParser:
    ## @brief Constructor
    # @param parse_tree Parse tree to use when parsing commands.
    # this should be a multilevel string indexed dictionary where every parameter in the command
    # is a sublevel. The leafs should be function pointers to be executed when the leaf is reached.
    # Variables can be defined as "$nameofvariable" and will automatically be matched if nothing else in that
    # level is matched. The final function is then called with the named variables.
    # Example:
    # <pre>
    # parseTree = {
    #   "set": { "name": { "$name": SetNameFunction } }
    # }
    # </pre>
    # When given the string "set name borat" the function 'SetNameFunction' will be called with the
    # parameter "name" set to "borat".
    def __init__(self, parse_tree):
        self.parse_tree = parse_tree

    def parse(self, string, data = None):
        if string is None:
            raise Exception("Syntax error. No parameters supplied.")

        args = string.split()
        if data is None:
            return self.parse_recurse(args, self.parse_tree, {})
        else:
            return self.parse_recurse(args, self.parse_tree, {"data": data})

    def parse_recurse(self, arguments, tree, variables):
        if tree == []:
            raise Exception("End of parse tree")

        if hasattr(tree, "__call__"):
            if arguments == []:
                return tree(**variables)
            else:
                raise Exception("Too many parameters")

        if arguments == []:
            raise Exception("Not enough parameters")

        arg  = arguments[0]
        rest = arguments[1:]

        if tree.has_key(arg):
            return self.parse_recurse(rest, tree[arg], variables)

        # Only one item in this subtree, and it's not matching, it should be a variable
        if len(tree.keys()) == 1:
            name = tree.keys()[0]
            if name[0] == "$":
                varname = name[1:]
                variables[varname] = arg
                return self.parse_recurse(rest, tree[name], variables)
            else:
                raise Exception("Syntax error")

        raise Exception("Syntax error. Unknown parameter '%s'" % (arg))
