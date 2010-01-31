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

	def is_debug():
		return Logger._debug

	def log(msg, level = 'NORMAL'):
		level_str = level.ljust(7)
		timeString = time.strftime("%H:%M:%S")

		colors = {
			'NORMAL': 0,
			'INFO':   34,
			'WARNING':33,
			'ERROR':  31,
			'DEBUG':  35,
			'FATAL':  41,
		}
		level = "\033[%dm%s\033[0m" % (colors[level], level_str)
		print "%s [%s]: %s" % (timeString, level, msg)

	def log_traceback(cls):
		if Logger._debug:
			lines = traceback.format_exc().splitlines()

			for line in lines:
				if cls:
					Logger.debug(cls.__class__.__name__ + ": " + line)
				else:
					Logger.debug(line)

	def info(msg):
		Logger.log(msg, 'INFO')

	def debug(msg):
		if Logger._debug:
			Logger.log(msg, 'DEBUG')

	def error(msg):
		Logger.log(msg, 'ERROR')

	def fatal(msg):
		lines = traceback.format_exc().splitlines()

		for line in lines:
			Logger.log(line, 'FATAL')

		Logger.log(msg, 'FATAL')

	def warning(msg):
		Logger.log(msg, 'WARNING')

	enable_debug = Callable(enable_debug)
	is_debug= Callable(is_debug)
	log_traceback = Callable(log_traceback)
	log     = Callable(log)
	debug   = Callable(debug)
	info    = Callable(info)
	error   = Callable(error)
	warning = Callable(warning)
	fatal   = Callable(fatal)

