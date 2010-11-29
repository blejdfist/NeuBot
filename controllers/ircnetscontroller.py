# -*- coding: utf-8 -*-
## @package controllers.configcontroller
# @brief Configuration handling

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

from lib.util import Singleton

##
# Contains the configuration
class IRCNetsController(Singleton):
    def construct(self):
        self.ircnets = {}

    def add_ircnet(self, name, irccontroller):
        self.ircnets[name] = irccontroller

    def get_ircnet(self, name):
        if self.ircnets.has_key(name):
            return self.ircnets[name]

    def get_ircnet_names(self):
        return self.ircnets.keys()

    def disconnect_all(self):
        for ircnet in self.ircnets.keys():
            self.ircnets[ircnet].disconnect()
