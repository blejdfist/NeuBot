##
# @class Singleton
# Implement a singleton
# Inherit this class to become a singleton.
# REMEMBER: For every new instance the __init__ function will still be used
class Singleton(object):
	_instance = None

	def __new__(cls, *args, **kwargs):
		if cls._instance is None:
			cls._instance = object.__new__(cls, *args, **kwargs)

			if hasattr(cls._instance, "construct"):
				cls._instance.construct()

		return cls._instance

