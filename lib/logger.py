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

	def EnableDebug(enable = True):
		Logger._debug = enable

	def Log(msg, level = 'NORMAL'):
		timeString = time.strftime("%c")
		print "%s [%s]: %s" % (timeString, level, msg)

	def Info(msg):
		Logger.Log(msg, 'INFO')

	def Debug(msg):
		if Logger._debug:
			Logger.Log(msg, 'DEBUG')

	def Error(msg):
		Logger.Log(msg, 'ERROR')

	def Fatal(msg):
		print traceback.format_exc()
		Logger.Log(msg, 'FATAL')

	def Warning(msg):
		Logger.Log(msg, 'WARNING')

	EnableDebug = Callable(EnableDebug)
	Log     = Callable(Log)
	Debug   = Callable(Debug)
	Info    = Callable(Info)
	Error   = Callable(Error)
	Warning = Callable(Warning)
	Fatal   = Callable(Fatal)

