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

import sqlite3

from lib import Logger
#from Lib.TableFormatter import TableFormatter

class ACLController:
	def __init__(self):
		self.db = "data/acl.db"

		try:
			conn = sqlite3.connect(self.db)
			#cursor = conn.cursor()

			# ACL
			fp = open("resources/acl/acl.sql", "r")
			data = fp.read()
			fp.close()

			# Triggers
			fp = open("resources/acl/triggers.sql", "r")
			data += fp.read()
			fp.close()

			conn.executescript(data)
			conn.commit()

			if not self._user_exists("any"):
				self.add_user("any")
				self.user_add_hostmask("any", "*!*@*")
				#conn.execute("INSERT INTO acl_aro (name, type) VALUES ('any', 'user')")
				#conn.execute("INSERT INTO acl_user_hostmasks (aro_name, hostmask) VALUES ('any', '*!*@*')")
				#conn.commit()
		except Exception, e:
			print e
			Logger.fatal("Unable to create ACL database")

	def check_access(self, identity, context):
		result = self._query("SELECT hostmask FROM list_access WHERE context = ?", (context,))
		if result:
			for (row,) in result:
				if identity.is_matching(row):
					return True

		return False

	def _query(self, querystring, parameters = ()):
		conn  = sqlite3.connect(self.db)
		cursor = conn.cursor()
		
		try:
			cursor.execute(querystring, parameters)
			result = cursor.fetchall()
			conn.commit()

			return result
		except Exception, e:
			Logger.warning("Query error (%s) %s: %s" % (querystring, parameters, e))
			return None

	def _user_exists(self, username):
		result = self._query("SELECT name FROM acl_aro WHERE name = ? AND type = 'user'", (username,))
		if not result is None:
			if len(result) != 0:
				return True

		return False

	def _group_exists(self, groupname):
		result = self._query("SELECT name FROM acl_aro WHERE name = ? AND type = 'group'", (groupname,))
		if not result is None:
			if len(result) != 0:
				return True

		return False

	def add_group(self, groupname):
		if self._group_exists(groupname):
			raise Exception("Group already exists")

		if self._query("INSERT INTO acl_aro (name, type) VALUES (?, ?)", (groupname, "group")) is None:
			raise Exception("Unable to add group %s" % (groupname))

	def del_group(self, groupname):
		if not self._GroupExists(groupname):
			raise Exception("No such group")

		if self._query("DELETE FROM acl_aro WHERE name = ? AND type = 'group'", (groupname,)) is None:
			raise Exception("Unable to remove group %s" % (groupname))

	def add_user(self, username):
		if self._user_exists(username):
			raise Exception("User already exists")

		if self._query("INSERT INTO acl_aro (name, type) VALUES (?, ?)", (username, "user")) is None:
			raise Exception("Unable to add user %s" % (username))

	def del_user(self, username):
		if not self._user_exists(username):
			raise Exception("No such user")

		if self._query("DELETE FROM acl_aro WHERE name = ? AND type = 'user'", (username,)) is None:
			raise Exception("Unable to remove user %s" % (username))

	def user_add_hostmask(self, username, hostmask):
		if not self._user_exists(username):
			raise Exception("No such user")

		if self._query("INSERT INTO acl_user_hostmasks (aro_name, hostmask) VALUES (?, ?)", (username, hostmask)) is None:
			raise Exception("Unable to add hostmask")

	def user_del_hostmask(self, username, hostmask):
		if not self._user_exists(username):
			raise Exception("No such user")

		if self._query("DELETE FROM acl_user_hostmasks WHERE aro_name = ? AND hostmask = ?", (username, hostmask)) is None:
			raise Exception("Unable to remove hostmask")

	def group_add_user(self, username, groupname):
		if not self._user_exists(username):
			raise Exception("No such user")

		if not self._GroupExists(groupname):
			raise Exception("No such group")

		result = self._query("SELECT aro_name_1 FROM acl_memberships WHERE aro_name_1 = ? AND aro_name_2 = ?", (username,groupname))
		if not result is None:
			if len(result) != 0:
				raise Exception("User %s is already a member of %s" % (username, groupname))

		if self._query("INSERT INTO acl_memberships (aro_name_1, aro_name_2) VALUES (?, ?)", (username, groupname)) is None:
			raise Exception("Unable to add user to group")

	def group_del_user(self, username, groupname):
		if not self._user_exists(username):
			raise Exception("No such user")

		if not self._GroupExists(groupname):
			raise Exception("No such group")

		result = self._query("SELECT aro_name_1 FROM acl_memberships WHERE aro_name_1 = ? AND aro_name_2 = ?", (username,groupname))
		if not result is None:
			if len(result) != 1:
				raise Exception("User %s is not a member %s" % (username, groupname))

		if self._query("DELETE FROM acl_memberships WHERE aro_name_1 = ? AND aro_name_2 = ?", (username, groupname)) is None:
			raise Exception("Unable to remove user from group")

	def access_allow(self, context, aro):
		isGroup = self._group_exists(aro)
		isUser  = self._user_exists(aro)
		if not isGroup and not isUser:
			raise Exception("No such user or group")

		# Add context if it doesn't exist
		context = context.lower()
		self._query("INSERT INTO acl_aco (name) VALUES (?)", (context,))

		# Clear any old access
		self._query("DELETE FROM acl_access WHERE aro_name = ? AND aco_name = ?", (aro, context))

		if self._query("INSERT INTO acl_access (aro_name, aco_name, access) VALUES (?, ?, 1)", (aro, context)) is None:
			raise Exception("Unable to grant access")

	def access_deny(self, context, aro):
		isGroup = self._group_exists(aro)
		isUser  = self._user_exists(aro)
		if not isGroup and not isUser:
			raise Exception("No such user or group")

		# Add context if it doesn't exist
		context = context.lower()
		self._query("INSERT INTO acl_aco (name) VALUES (?)", (context,))

		# Clear any old access
		self._query("DELETE FROM acl_access WHERE aro_name = ? AND aco_name = ?", (aro, context))

		if self._query("INSERT INTO acl_access (aro_name, aco_name, access) VALUES (?, ?, 0)", (aro, context)) is None:
			raise Exception("Unable to deny access")

	def access_remove(self, context, aro):
		isGroup = self._group_exists(aro)
		isUser  = self._user_exists(aro)
		if not isGroup and not isUser:
			raise Exception("No such user or group")

		self._query("DELETE FROM acl_access WHERE aro_name = ? AND aco_name = ?", (aro, context))

	def access_clear(self, context):
		self._query("DELETE FROM acl_aco WHERE name = ?", (context.lower(),))

	def get_user_info(self, username):
		if not self._user_exists(username):
			raise Exception("No such user")

		info = {
			"username": username,
			"hostmasks": [],
			"groups": [],
			"access": []
		}

		# Get hostmasks
		result = self._query("SELECT hostmask FROM user_hostmasks WHERE username = ?", (username, ))
		if not result is None:
			info["hostmasks"] = [row[0] for row in result]

		# Get group memberships
		result = self._query("SELECT groupname FROM user_groups WHERE username = ?", (username, ))
		if not result is None:
			info["groups"] = [row[0] for row in result]

		# Get command access
		result = self._query("SELECT aro_name, username, context FROM list_access WHERE username = ? OR aro_name = ? GROUP BY context", (username, username))
		if not result is None:
			for (access_aro, member_username, context) in result:
				if member_username is None:
					info["access"].append((context, None))
				else:
					info["access"].append((context, access_aro))

		return info

	def group_get_members(self, groupname):
		result = self._query("SELECT aro_name_1 FROM acl_memberships WHERE aro_name_2 = ?", (groupname,))

		if result is None or len(result) == 0:
			raise Exception("No such group. Or group have no members")
		else:
			return [row[0] for row in result]

	def get_users(self):
		result = self._query("SELECT name FROM acl_aro WHERE type = 'user'")

		if not result is None and len(result) != 0:
			return [row[0] for row in result]
		else:
			raise Exception("There are no users")

	def get_groups(self):
		result = self._query("SELECT name FROM acl_aro WHERE type = 'group'")

		if not result is None and len(result) != 0:
			return [row[0] for row in result]
		else:
			raise Exception("There are no groups")
