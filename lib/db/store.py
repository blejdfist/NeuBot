##
# @class Store
# Database delegator
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

	def put(self, key, value):
		self.driver.put(self.db, key, value)

	def get(self, key):
		return self.driver.get(self.db, key)

	def drop(self):
		self.driver.drop(self.db)
