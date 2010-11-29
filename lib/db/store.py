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

##
# Wrapper around the DatastorageController
class Store:
    ##
    # @param driver Driver class to delegate requests to
    # @param databasename Name of the "bucket". ex plugins_myplugin
    def __init__(self, driver, databasename):
        for method in ["put", "get", "drop"]:
            if not getattr(driver, method):
                raise Exception("Driver does not implement all necessary interfaces")

        self.db = databasename
        self.driver = driver

    ##
    # Put a value in the store
    # @param key Key for the value
    # @param value The actual value
    def put(self, key, value):
        self.driver.put(self.db, key, value)

    ##
    # Retrieve a value by key from the store
    # @param key Key for the value
    # @return The value associated with the supplied key
    def get(self, key):
        return self.driver.get(self.db, key)

    ##
    # Delete the store completely
    def drop(self):
        self.driver.drop(self.db)
