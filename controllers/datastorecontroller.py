# -*- coding: utf-8 -*-
## @package controllers.datastorecontroller
# Tuple data store abstraction layer

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

from lib.db import Store
from lib.util import Singleton

##
# Tuple data store abstraction layer
class DatastoreController(Singleton):
	def set_driver(self, uri):
		defaultdriver = "yserial"
		protocols = {
			"sqlite":  self._db_yserial,
			"file":    self._db_yserial,
			"yserial": self._db_yserial,
			#"mongodb":self._db_mongodb,
		}

		if uri.find("://") != -1:
			(drivername, _, path) = uri.partition("://")
		else:
			drivername = defaultdriver
			path = uri

		if not protocols.has_key(drivername):
			raise Exception("DatastoreController::set_driver Unknown driver '%s'" % drivername)

		self.store = protocols[drivername](path)

	def _db_yserial(self, path):
		from lib.db.drivers.yserialstore import YSerialStore
		store = YSerialStore(path)
		return store

	def get_store(self, dbname):
		if not hasattr(self, 'store'):
			raise Exception("DatastoreController::get_store Data store is not initialized")

		return Store(self.store, dbname)
