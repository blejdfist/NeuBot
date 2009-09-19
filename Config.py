
altnicks = ["NeuBot_", "NeuBot__"]

EFNet = {
	"ircnet": "JimNet",
	"nick": "NeuBot",
	"altnicks": altnicks,
	"name": "The Neuest bot",
	"ident": "neubot",

	# List of servers that can be used for this network
	# Format is: (hostname, port, use_ssl, use_ipv6)
	"servers": [
		("localhost", 6667, False, False),
		("wendy.local", 6667, False, False),
	],

	# List of channels to join
	# Format is: (channel_name, password)
	"channels": [
		("#test", None),
		("#test2", None),
	]
}

Bot = {
	"ircnets": 		[EFNet],
	"debug": 		False,
	"masters":		[
		"*!blejdfist@nurd.se", 
		"MrSimulator!Simulator@simulator.tld"
	],
	"plugins": [
	]
}
