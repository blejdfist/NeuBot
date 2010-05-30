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

class Logger:
	log_level = 3

	# Levels (numeric_level, display)
	levels = {
		'INFO':    (0,"\033[34mINFO\033[0m   "),
		'WARNING': (1,"\033[33mWARNING\033[0m"),
		'ERROR':   (2,"\033[31mERROR\033[0m  "),
		'FATAL':   (3,"\033[41mFATAL\033[0m  "),
		'DEBUGL1': (4,"\033[35mDEBUGL1\033[0m"),
		'DEBUGL2': (5,"\033[35mDEBUGL2\033[0m"),
		'DEBUGL3': (6,"\033[35mDEBUGL3\033[0m"),
	}

	def __init__(self):
		pass

	@classmethod
	def enable_debug(cls, enable = True):
		if enable:
			Logger.set_loglevel('DEBUGL1')
		else:
			Logger.set_loglevel('FATAL')

	@classmethod
	def set_loglevel(cls, level):
		numeric, _ = cls.levels[level.upper()]
		cls.log_level = numeric

	@classmethod
	def is_debug(cls):
		return cls.log_level >= 4

	@classmethod
	def log(cls, msg, level = 'INFO'):
		time_str = time.strftime("%H:%M:%S")
		numeric_level, level_display = cls.levels[level]

		if numeric_level <= cls.log_level:
			print "%s [%s]: %s" % (time_str, level_display, msg)

	@classmethod
	def log_traceback(cls, instance):
		lines = traceback.format_exc().splitlines()

		for line in lines:
			if cls:
				Logger.warning(instance.__class__.__name__ + ": " + line)
			else:
				Logger.warning(line)

	@classmethod
	def info(cls, msg):
		Logger.log(msg, 'INFO')

	@classmethod
	def debug(cls, msg):
		Logger.log(msg, 'DEBUGL1')

	@classmethod
	def debug1(cls, msg):
		Logger.log(msg, 'DEBUGL1')

	@classmethod
	def debug2(cls, msg):
		Logger.log(msg, 'DEBUGL2')

	@classmethod
	def debug3(cls, msg):
		Logger.log(msg, 'DEBUGL3')

	@classmethod
	def error(cls, msg):
		Logger.log(msg, 'ERROR')

	@classmethod
	def fatal(cls, msg):
		lines = traceback.format_exc().splitlines()

		for line in lines:
			Logger.log(line, 'FATAL')

		Logger.log(msg, 'FATAL')

	@classmethod
	def warning(cls, msg):
		Logger.log(msg, 'WARNING')
