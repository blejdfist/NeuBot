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

from lib.util.commandparser import CommandParser, CommandError
from lib.util.tableformatter import TableFormatter

from lib import Plugin

from controllers.aclcontroller import ACLController

class ACLCommands(Plugin):
    def __init__(self):
        self.author = "Jim Persson"
        self.name = "ACL Commands (Core)"

        self.acl = ACLController()
        self.parseTree = {
            "add": {
                "user":  {"$username"  : self.add_user},
                "group": {"$groupname" : self.add_group},
            },

            "del": {
                "user":  {"$username"  : self.del_user},
                "group": {"$groupname" : self.del_group},
            },

            "user": {
                "$username": {
                    "show": self.show_user,
                    "addmask": {"$hostmask": self.user_add_hostmask},
                    "delmask": {"$hostmask": self.user_del_hostmask}
                }
            },

            "group": {
                "$groupname": {
                    "show": self.show_group,
                    "adduser": {"$username": self.group_add_user},
                    "deluser": {"$username": self.group_del_user}
                }
            },

            "access": {
                "$context": {
                    "allow":  {"$aro": self.access_allow},
                    "deny" :  {"$aro": self.access_deny},
                    "remove": {"$aro": self.access_remove},
                    "clear": self.access_clear
                }
            },

            "show": {
                "users": self.get_users,
                "groups": self.get_groups
            }
        }

        self.event.register_command("acl", self.cmd_acl, True)

    def add_user(self, username):
        self.acl.add_user(username)
        return ["Added user %s" % username]

    def add_group(self, groupname):
        self.acl.add_group(groupname)
        return ["Added group %s" % groupname]

    def del_user(self, username):
        self.acl.del_user(username)
        return ["Deleted user %s" % username]

    def del_group(self, groupname):
        self.acl.del_group(groupname)
        return ["Deleted group %s" % groupname]

    def user_add_hostmask(self, username, hostmask):
        self.acl.user_add_hostmask(username, hostmask)
        return ["Added hostmask %s to user %s" % (hostmask, username)]

    def user_del_hostmask(self, username, hostmask):
        self.acl.user_del_hostmask(username, hostmask)
        return ["Removed hostmask %s to user %s" % (hostmask, username)]

    def group_add_user(self, username, groupname):
        self.acl.group_add_user(username, groupname)
        return ["User %s is now a member of group %s" % (username, groupname)]

    def group_del_user(self, username, groupname):
        self.acl.group_del_user(username, groupname)
        return ["User %s is no longer a member of group %s" % (username, groupname)]

    def show_user(self, username):
        info = self.acl.get_user_info(username)

        data = []

        data += ["User: %s" % username]

        data += ["Associated Hostmasks:"]
        result = info["hostmasks"]
        if len(result) == 0:
            haveHostmask = False
            data += ["  None"]
        else:
            haveHostmask = True
            for row in result:
                data += ["  " + row]

        data += ["Group Memberships:"]
        result = info["groups"]
        if result is None:
            data += ["  None"]
        else:
            for row in result:
                data += ["  " + row]

        data += ["Command Access:"]
        if haveHostmask:
            result = info["access"]
            for (context, group) in result:
                if group is None:
                    data += ["  %s (direct access)" % (context)]
                else:
                    data += ["  %s (member in '%s')" % (context, group)]
        else:
            data += ["  No hostmasks for this user, unable to grant access"]

        return data

    def show_group(self, groupname):
        members = self.acl.get_group_members(groupname)

        users = TableFormatter([""]*5, "Group Members")
        members.sort()
        members.reverse()
        while len(members) != 0:
            row = []
            for _ in range(0, 5):
                if len(members) != 0:
                    user = members.pop()
                    row.append(user)

            row += [""]*(5-len(row))
            users.add_row(row)

        return users.get_table()

    def get_users(self):
        users = self.acl.get_users()

        return ["Found %d users:" % len(users)] + users

    def get_groups(self):
        groups = self.acl.get_groups()

        return ["Found %d groups" % len(groups)] + groups

    def access_allow(self, context, aro):
        self.acl.access_allow(context, aro)

        return ["%s now have access to '%s'" % (aro, context)]

    def access_deny(self, context, aro):
        self.acl.access_deny(context, aro)

        return ["Denied access to '%s' for %s'" % (context, aro)]

    def access_remove(self, context, aro):
        self.acl.access_remove(context, aro)

        return ["Ok"]

    def access_clear(self, context):
        self.acl.access_clear(context)

        return ["Ok"]

    def cmd_acl(self, irc, params):
        """
        Available operations
            add [user|group] <name>
            del [user|group] <name>
            user <username> [show | addmask <hostmask> | delmask <hostmask>]
            group <groupname> [show | adduser <username> | deluser <username>]
            access <context> [allow|deny|remove] <group_or_user>
            access <context> clear
            show [users|groups]"""

        try:
            result = CommandParser(self.parseTree).parse(str(params))
            if result:
                for line in result:
                    irc.reply(line)

        except CommandError as e:
            irc.reply(e)

        except Exception as e:
            irc.reply(e)
