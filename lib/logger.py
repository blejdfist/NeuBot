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

import traceback
import time

class Callable:
	def __init__(self, foo):
		self.__call__ = foo

class Logger:
	_debug = False

	def enable_debug(enable = True):
		Logger._debug = enable

	def log(msg, level = 'NORMAL'):
		timeString = time.strftime("%c")
		print "%s [%s]: %s" % (timeString, level, msg)

	def info(msg):
		Logger.log(msg, 'INFO')

	def debug(msg):
		if Logger._debug:
			Logger.log(msg, 'DEBUG')

	def error(msg):
		Logger.log(msg, 'ERROR')

	def fatal(msg):
		print traceback.format_exc()
		Logger.log(msg, 'FATAL')

	def warning(msg):
		Logger.log(msg, 'WARNING')

	enable_debug = Callable(enable_debug)
	log     = Callable(log)
	debug   = Callable(debug)
	info    = Callable(info)
	error   = Callable(error)
	warning = Callable(warning)
	fatal   = Callable(fatal)

