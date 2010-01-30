from lib.db import Store

class DatastoreController:
	def __init__(self, uri):
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
			raise Exception("DatastoreController::__init__ Unknown driver '%s'" % drivername)

		self.store = protocols[drivername](path)

	def _db_yserial(self, path):
		from lib.db.drivers.yserialstore import YSerialStore
		store = YSerialStore(path)
		return store

	def get_store(self, dbname):
		return Store(self.store, dbname)
