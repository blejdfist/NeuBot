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

class TableFormatter:
	def __init__(self, colums, header = ""):
		self.columns = colums
		self.data   = []
		self.header = header

		self._columnSizes = []
		for i in range(0, len(self.columns)):
			self._columnSizes.append(len(self.columns[i]))

	def add_row(self, data):
		if len(data) != len(self.columns):
			raise Exception("Data of incorrect size")

		# Calculate the new maximum column sizes
		for i in range(0, len(data)):
			if not data[i]:
				data[i] = "-"

			if len(data[i]) > self._columnSizes[i]:
				self._columnSizes[i] = len(data[i])

		self.data.append(data)

	def get_table(self, columnHeaders = True):
		result = []
		header = ""

		if columnHeaders:
			for i in range(0, len(self.columns)):
				header = header + self.columns[i] + ' '*(self._columnSizes[i]-len(self.columns[i])+1)

			result.append(header)

		if len(self.header) > 0:
			result.append(self.header)

		if columnHeaders or len(self.header) > 0:
			result.append('-'*(sum(self._columnSizes)+len(self._columnSizes)-1))

		for row in self.data:
			rowStr = ""
			for i in range(0, len(row)):
				rowStr = rowStr + row[i] + ' '*(self._columnSizes[i]-len(row[i])+1)

			result.append(rowStr)

		return result
