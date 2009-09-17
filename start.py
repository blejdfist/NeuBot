#!/usr/bin/env python
import Config
from lib.util import CommandShell

def cmd_quit():
	print "Quit"

def cmd_master_add(hostmask):
	print "Add master %s" % hostmask

def cmd_master_del(hostmask):
	print "Del master %s" % hostmask

command_tree = {
	"quit": cmd_quit,
	"master": {
		"add": { "$hostmask": cmd_master_add },
		"del": { "$hostmask": cmd_master_del },
	}
}

shell = CommandShell(command_tree)

while True:
	try:
		shell.input("NeuerBot> ")
	except Exception, e:
		print "%s" % e
