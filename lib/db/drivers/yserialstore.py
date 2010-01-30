from y_serial import y_serial

class YSerialStore:
	def __init__(self, dbfile):
		self.db = y_serial.Main(dbfile)
		
	def put(self, name, key, value):
		try:
			self.db.insert(value, key, name)
		except Exception, e:
			raise Exception("YSerialStore::put error: %s" % e)

	def get(self, name, key):
		# It is ok if get fails, just return None
		try:
			return self.db.select(key, name)
		except:
			return None

	def drop(self, name):
		self.db.droptable(name)
