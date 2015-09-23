from time import strftime
from bs4 import BeautifulSoup
import requests
import socket
import os

''' Assign Program Wide Variables
'''
SERVER = 'irc.rizon.net'
PORT = 6667
CHANNEL = '#canaids'

NICK = 'TheLost'
USER = NICK # Change this if you want a different username for your bot than its Nick.
REALNAME = 'Lost In Potatolation'
MODE = 0	# Generally you don't want to change this

MASTER = 'Kalq'

LOG_DIR = 'logs'

''' Establishing Socket Connection
'''
ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ircsock.connect((SERVER, PORT))

handle = ircsock.makefile(mode='rw', buffering=1, encoding='UTF-8', newline='\r\n') # makefile function allows us to treat the irc socket as a file from which we can read and write to.

def log(command, sender, dest = None, params = None, source = None):
	''' Designed to log any conversation in all channels the bot is connected to as well as private messages to the bot itself.
	'''

	path = os.path.join(LOG_DIR, dest) # Defines the path where the logs will be saved. dest is defined by the channel the message is posted on, or the bot itself

	# Creates the log directory if it doesn't already exist
	if not os.path.exists(path):
		os.makedirs(path)

	# Defines the date and time
	date = strftime('%Y-%m-%d')
	time = strftime('%H:%M:%S')

	# Defines the variable to which we can append the logs
	log = open(os.path.join(path, date + '.log'), 'a')

	if command == '/me': # Checks to see if the sender is using the '/me' in his irc client. Determined by the handle_ctcp function.
		print('[' + time + ']', sender, params, file=log)
	elif command == 'PRIVMSG':
		print('[' + time + ']', sender, '>>>', params, file=log)
	elif command == 'JOIN':
		print('[' + time + '] *', sender, '(', source, ') has joined', dest, file=log)
	elif command == 'PART':
		if params is None:
			print('[' + time + '] *', sender, '(', source, ') has left', dest, file=log)
		else:
			print('[' + time + '] *', sender, '(', source, ') has left', dest, '(', params, ')', file=log)

	log.close()

def handle_commands(dest, command):
	if command[1:].startswith('def '):
		search = command.split(' ', 1)[1]
		html = requests.get('https://www.wordnik.com/words/' + search)
		soup = BeautifulSoup(html.text)
		
		try:
			definition = soup.abbr.parent.get_text()
			print('PRIVMSG', dest, ':' + definition, file=handle)
			log('PRIVMSG', NICK, dest = dest, params = definition)
		except:
			print('PRIVMSG', dest, ':Word Not Found', file=handle)	

''' The IRC protocol provides for 3 initial commands when connecting to a new server. The PASS command is optional depending on if the irc server is private. The NICK and USER commands are required.
'''
def set_nick(nick):
	print('NICK', nick, file=handle) # Sends the NICK command to the server with the appropriate parameters.

def connect(nick, user, mode, realname, password = None):
	if password:
		print(PASS, password, file=handle) # Checks if the password parameter is giver to connect to the server and sends it.
	
	set_nick(nick)
	print('USER', user, mode, '* :'+realname, file=handle) # Sends the USER command to the server with the appropriate parameters.

def join(channel, key = None):
	if key is None:
		print('JOIN', channel, file=handle)
	else:
		print('JOIN', channel, key, file=handle) # The JOIN command has an optional <key> parameter depending on whether the channel being connected to requires it.

def quit(reason = "Quit"):
	''' The QUIT command exits the server. Therefore we close the socket connected to the server
	'''

	print('QUIT', reason, file=handle)
	ircsock.close()

def private_message(to, msg):
	''' The PRIVMSG command sends a message to a user or channel that the bot is connected to
	'''

	print('PRIVMSG', to, ':'+ msg, file=handle)

def notice(to, msg):
	''' The NOTICE command sends a message to a user or channel
	'''

	print('NOTICE', to, ':'+ msg, file=handle)

def handle_ctcp(sender, dest, message):
	''' This function handles the various CTCP commands used in IRC.
	'''

	message = message[1:].strip('\x01').split(' ', 1) # Strips the message of the hexadecimal CTCP codes and splits them into the command and any potential parameters.

	if message[0] == 'ACTION': # The '/me' command
		log('/me', sender, dest = dest, params = message[1])

connect(NICK, USER, MODE, REALNAME)
join(CHANNEL)

for line in handle:
	line = line.strip() # Strips the line of any excess whitespace or newlines or tabs or what have you.
	print(line)

	prefix = None
	if line[0] == ':': # Almost every command from an irc server will start with a ':'. Notable exception are PINGs.
		(prefix, line) = line[1:].split(' ', 1) # The 'prefix' contains the source of the command. The 'line' is the command and any parameters involved. ie: 'PRIVMSG #channel :Hello World
	(command, params) = line.split(' ', 1)	# Simply splits the command from it's paraments. i.e: PRIVMSG, JOIN etc.


	if command == 'PING':
		print('PONG', params, file=handle) # Respond to the irc server with an equivalent PONG of the PING they sent.
	elif command == 'PRIVMSG':		
		sender = prefix.split('!', 1)[0] # Determines the Nick of the sender via the source in the 'prefix' variable
		(dest, message) = params.split(' ', 1) # All PRIVMSG commands contain an intial destination (#channel, Nick) and then the message itself
		if message[0:2] == ':\x01': # Checks to see if the message starts with a hexidecimal ctcp code. Let's the handle_ctcp function deal with its uniqueness.
			handle_ctcp(sender, dest, message)
		else:
			log(command, sender, dest = dest, params = message[1:])
			if message[1] == '.':
				handle_commands(dest, message[1:])
	
	elif command == 'JOIN':
		(sender, source) = prefix.split('!', 1)
		log(command, sender, dest = params[1:], source = source)
	
	elif command == 'PART':
		(sender, source) = prefix.split('!', 1)

		if ' ' in params:
			(dest, message) = params.split(' ', 1)
			log(command, sender, dest = dest, params = message[1:], source = source)
		else:
			log(command, sender, dest = params, source = source)

	
