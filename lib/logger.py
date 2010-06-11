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
import logging
import time

# Initialize logging mechanism
class ColoredFormatter(logging.Formatter):
	def __init__(self, levels):
		self.levels = levels
		format = "%(asctime)s [%(levelname)-8s] %(message)s"
		logging.Formatter.__init__(self, format)

	def format(self, record):
		if self.levels.has_key(record.levelname):
			_, coloredname = self.levels[record.levelname]
			record.levelname = coloredname

		return logging.Formatter.format(self, record)

	def formatTime(self, record, datefmt):
		return logging.Formatter.formatTime(self, record, "%H:%M:%S")

class Logger:
	log_level = logging.INFO

	# Levels (numeric_level, display)
	levels = {
		'CRITICAL':(logging.FATAL,   "\033[41mFATAL\033[0m  "),
		'FATAL':   (logging.FATAL,   "\033[41mFATAL\033[0m  "),
		'ERROR':   (logging.ERROR,   "\033[31mERROR\033[0m  "),
		'WARNING': (logging.WARNING, "\033[33mWARNING\033[0m"),
		'INFO':    (logging.INFO,    "\033[34mINFO\033[0m   "),
		'DEBUGL1': (logging.DEBUG,   "\033[35mDEBUGL1\033[0m"),
		'DEBUGL2': (logging.DEBUG-1, "\033[35mDEBUGL2\033[0m"),
		'DEBUGL3': (logging.DEBUG-2, "\033[35mDEBUGL3\033[0m"),
	}

	def __init__(self):
		pass

	@classmethod
	def setup_logging(cls):
		console = logging.StreamHandler()
		console.setFormatter(ColoredFormatter(cls.levels))

		root_logger = logging.getLogger('')
		root_logger.addHandler(console)
		root_logger.setLevel(cls.log_level)

		logging.addLevelName(logging.DEBUG,   'DEBUGL1')
		logging.addLevelName(logging.DEBUG-1, 'DEBUGL2')
		logging.addLevelName(logging.DEBUG-2, 'DEBUGL3')

	@classmethod
	def set_loglevel(cls, level):
		numeric, _ = cls.levels[level.upper()]
		cls.log_level = numeric
		logging.getLogger('').setLevel(numeric)

	@classmethod
	def log_traceback(cls, instance):
		lines = traceback.format_exc().splitlines()

		for line in lines:
			if instance:
				Logger.warning(instance.__class__.__name__ + ": " + line)
			else:
				Logger.warning(line)

	@classmethod
	def info(cls, msg):
		logging.info(msg)

	@classmethod
	def debug(cls, msg):
		logging.log(logging.DEBUG, msg)

	@classmethod
	def debug1(cls, msg):
		logging.log(logging.DEBUG, msg)

	@classmethod
	def debug2(cls, msg):
		logging.log(logging.DEBUG-1, msg)

	@classmethod
	def debug3(cls, msg):
		logging.log(logging.DEBUG-2, msg)

	@classmethod
	def error(cls, msg):
		logging.error(msg)

	@classmethod
	def fatal(cls, msg):
		logging.fatal(msg)
		lines = traceback.format_exc().splitlines()

		for line in lines:
			logging.fatal(line)

		logging.fatal(msg)

	@classmethod
	def warning(cls, msg):
		logging.warning(msg)

Logger.setup_logging()
