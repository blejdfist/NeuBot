#!/usr/bin/env python
from simulator import Simulator

sim = Simulator()
sim.start()

sim.load_plugin("helloworld2")

while True:
	try:
		input = raw_input("Simulator# > ")
	except EOFError:
		print "quit"
		break

	if input == "quit":
		break

	sim.msg_channel(input)

sim.stop()
