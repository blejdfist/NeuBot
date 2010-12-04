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
# Copyright (c) 2010, Jim Persson, All rights reserved.

import readline
import copy

##
# @class CommandShell
# Implements readline functionality with tab-completion
# To function it needs a command-tree dict containing the command structure. 
# 
# <pre>
# parse_tree_example = {
#     'hello' : None
#     'show' : {
#         'all': None,
#         'one': None,
#     }
# }
# shell = CommandShell()
# parser = CommandParser()
# input = shell.input("Prompt> ")
# if result:
#     result = parser.parse(input)
# </pre>
#
# Parse trees can contain expansions functions that dynamically generate more
# options when requested
# <pre>
# @CommandShell.expander
# def user_options():
#     return {'user1': None, 'user2': None}
# 
# @CommandShell.expander
# def group_options():
#     return {'normal': None, 'admins': None}
# 
# parse_tree_dynamic = {
#     'show': { 'user': user_options, 'group': group_options }
# }
# shell = CommandShell()
# shell.set_parse_tree(parse_tree_dynamic)
# shell.input("Prompt> ")
# </pre>
class CommandShell:
    class expander:
        def __init__(self, func):
            self._function = func

        def __call__(self, *args):
            return self._function(*args)

    ##
    # Initialize the CommandShell with a specific parsetree
    # @param parseTree Parse tree to use
    def __init__(self):
        self._parse_tree = None
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._tab_completer)
        readline.set_completer_delims(" ")

    def set_parse_tree(self, tree):
        self._parse_tree = tree

    def _traverse_tree(self, tree, tokens):
        result = []

        if tree is None:
            return result

        # Find all expanders at this level and expand them
        for key in tree.keys():
            # If it is an expander instance we will call it
            # and return the result
            if isinstance(tree[key], CommandShell.expander):
                tree[key] = tree[key]()

        # No more tokens. Check where we are.
        if len(tokens) == 0:
            # If we have a dictionary, return all 
            # possible strings
            if type(tree) is dict:
                for key in tree.keys():
                    if type(key) == str:
                        result.append(key + " ")

            return result

        for key in tree.keys():
            if type(key) == str:
                if key.lower().startswith(tokens[0].strip().lower()):
                    result.append(key + " ")

        if tree.has_key(tokens[0].strip()):
            return self._traverse_tree(tree[tokens[0].strip().lower()], tokens[1:])
        else:
            return result

        return []

    def _tab_completer(self, text, state):
        if self._parse_tree is None:
            return [None]

        tokens = readline.get_line_buffer().split()
        try:
            result = self._traverse_tree(self._tree_copy, tokens)
        except Exception as e:
            print e

        result.append(None)

        return result[state]

    ##
    # Prompt the user for input
    #
    # @param Appearance of the prompt
    def input(self, prompt):
        # Create a new deep copy of the parse tree to prevent
        # expansions from actually modifying the parse tree
        self._tree_copy = copy.deepcopy(self._parse_tree)
        return raw_input(prompt)
