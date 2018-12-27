#!/usr/bin/env python3
################################################################################
# File: mailtools
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Frontend to the mailtools command line interface. Parses arguements that the
# user gives to the command. The configuration file for mailtools is also loaded
# at this time.
# Tutorials:
#	https://docs.python.org/3/howto/argparse.html (argparse for argument parsing)
#	https://argcomplete.readthedocs.io/en/latest/#activating-global-completion
################################################################################

################################################################################
# PACKAGE INFORMATION
################################################################################

VERSION = "1.3.1-stable"
INFO_HEADER = \
	"UNIX MAILTOOLS\n"\
	+ "Mail Management Utilities for Unix-based Systems.\n"\
	+ "\"Search is Inevitable.\"\n"\
	+ "Version: {}".format(VERSION)
EXEC_DIR = "/usr/lib/mailtools/bin/"

################################################################################
# NON-PROPIETARY IMPORTS
################################################################################

import os
import sys
import getpass
import subprocess
import pprint
import argparse		# For parsing the cli arguments
import argcomplete	# For Bash completion
import subprocess	# For calling other scripts

################################################################################
# ARGUMENT PARSER
################################################################################

# Create the parser object.
# Syntax: 
#	add_argument(short_flag, long_flag, help="help_text", required?, type?, count?)
# Tutorial: https://docs.python.org/3/howto/argparse.html
parser = argparse.ArgumentParser()

### VERBOSITY SETTINGS ###
# mailtools can run on three verbosity settings 0 - quiet, 1 - normal, 2 - debug
verbosity_args = parser.add_mutually_exclusive_group()

# Quiet Execution - no terminal printout
verbosity_args.add_argument("--quiet",help="run silently",action="store_true")

# Verbose Execution - print everything
verbosity_args.add_argument("--verbose",help="sets verbose mode",action="store_true")

### OPTIONAL ARGUMENTS ###
optional_args = parser.add_mutually_exclusive_group()

# Info: printout the user's mailtools configuration
optional_args.add_argument("--info",help="print out info",action="store_true")

# Use: use and process the specified mailbox instead of the default
optional_args.add_argument("--use",help="specify the mbox file for processing",\
	metavar='MBOX')

# Reset: deletes (resets the mongo database)
optional_args.add_argument("--reset",help="reset mail database",action="store_true")

# Setup: sets (or resets) the user's current mailtools configuration
optional_args.add_argument("--reset_config",help="reset user configuration",\
	action="store_true")

# Easter Egg: sends a 'CHANGE IS INEVITABLE' email to localhost
optional_args.add_argument("--thanks",help="send a Thank You note to the localhost",\
	action="store_true")

### MAIN ACTION ARGUMENTS ###

action_subparsers = parser.add_subparsers(dest='action')

################################################################################
# Search: Search current mailbox with the specified query
################################################################################
search_parser = action_subparsers.add_parser('search',\
	help='search current mailbox with a given query')

### Query Options ###
query_options = search_parser.add_argument_group(title='Query Options')
# --negate
query_options.add_argument('--negate',\
	help='return the negation of the search query',\
	action="store_true")
# --exact_string
query_options.add_argument('--exact_string',\
	help='search for the exact string without regex matching',\
	action="store_true")
	
### Parameters ###
search_param = search_parser.add_argument_group(title='Search Parameters')
search_param.add_argument('-s',help='search by Subject field',metavar='SUBJECT')
search_param.add_argument('-b',help='search by Body field',metavar='BODY')
search_param.add_argument('-f',help='search by From field',metavar='FROM')
search_param.add_argument('-t',help='search by To field',metavar='TO')
search_param.add_argument('-rt',help='search by Reply-To field',metavar='REPLY-TO')
search_param.add_argument('-cc',help='search by CC field',metavar='CC')
search_param.add_argument('-bcc',help='search by BCC field',metavar='BCC')
search_param.add_argument('-d',help='search by Date field',metavar='TIMESTAMP')
search_param.add_argument('-p',help='search by Priority field',metavar='PRIORITY')
search_param.add_argument('-atn',help='search by Attachment Name field',\
	metavar='ATTACH_NAME')
search_param.add_argument('-atf',help='search by Attachment Format field',\
	metavar='ATTACH_FORMAT')
search_param.add_argument('-ats',help='search by Attachment Status field',\
	metavar='ATTACH_STATUS')
search_param.add_argument('--field',help='search for VALUE using a user specified FIELD',\
	nargs=2,metavar=('FIELD','VALUE'))

### Search Options ###
search_options = search_parser.add_argument_group(title='Search Options')
search_options.add_argument('-o','--output',help='save results mbox to specified FILE',\
	metavar='FILE')
search_options.add_argument('--list_field',help='printout the FIELD values listed from results',\
	metavar='FIELD',action='append')
search_options.add_argument('--attachments',help='save attachments to ATTACH_DIR directory',\
	metavar='ATTACH_DIR')
search_options.add_argument('--reply',help='send a quick reply to all addresses in the results',\
	action='store_true')
search_options.add_argument('--forward',\
	help='foward the mail results to one or more RECIPIENT email addresses',\
	metavar='RECIPIENT',nargs='+')

################################################################################
# Process: Processes a mailscript file
################################################################################
process_parser = action_subparsers.add_parser('process',help='execute a mailscript')

# --file <Required> Multiple files can be passed
process_parser.add_argument('--file',\
	help='<Required> process a mailscript file',\
	metavar='FILEPATH',action='append',required=True)
	
### Options ###
process_parser.add_argument('--cron',help='save script and run as a cron job',\
	metavar='TIME')

################################################################################
# PARSING STAGE
################################################################################

# Tab completion
argcomplete.autocomplete(parser)
# Parse the passed arguments (to read value, cal 'args.<arg_name>', ie. 'args.i')
args = parser.parse_args()

################################################################################
# PACKAGE CONFIGURATION INITIALIZATION
################################################################################

# Call the user_setup.sh if /home/user/.mailtools directory does not exists or if
# --reset_config is passed.
if (not os.path.exists("/home/{}/.mailtools".format(getpass.getuser())))\
	or (args.reset_config == True):
	subprocess.call(EXEC_DIR + "user_teardown.sh")
	subprocess.call(EXEC_DIR + "user_setup.sh")

################################################################################
# PROPIETARY IMPORTS
################################################################################

sys.path.append(EXEC_DIR)
import Config
import Process
import Script
import Search
import Store
import ifttt

################################################################################
# HELPER FUNCTIONS
################################################################################

################################################################################
# Get the absolute path string based off a relative path.
################################################################################
def get_abs_path(filepath):
	cwd = os.getcwd()
	return os.path.join(cwd,filepath)

################################################################################
# Allow the user to input multiline strings.
################################################################################
def input_multi_line(prompt=None):
	if prompt != None: print(prompt)
	
	# Prompt the user for input, end with Ctrl-D
	content = ""
	while True:
		try:
			line = input()
		except EOFError:
			break
		content += line + "\n"
	return content
		
################################################################################
# MAIN
################################################################################

# Set verbosity level
if (args.quiet == True or (args.action == 'search' and args.list_field != None)):
	verbosity = 0
elif (args.verbose == True):
	verbosity = 2
else:
	verbosity = 1

# Pull configuration
config = Config.get_config()

# Information printout - print the current configuration of mailtools
if (args.info == True):
	print(INFO_HEADER)
	print("\nUser Configuration:")
	pprint.PrettyPrinter(indent=4).pprint(config)

# Reset the mongo database
elif (args.reset == True):
	if (input("Reset mailtools database? (y|n): ") == 'y'):
		# Perform the command 'mongo data --eval db.dropDatabase()'
		# This deletes the data database from mongo
		subprocess.call(['mongo',config['mongo_db_name'],'--eval','db.dropDatabase()'])
	else:
		print("Reset cancelled")

# Easter egg
elif (args.thanks == True):
	thanks = open('/usr/lib/mailtools/etc/banner.txt','r').read()
	ifttt.purtilo(config['user']+'@[127.0.0.1]',config['user']+'@[127.0.0.1]',thanks)

# MBox ingestion and manipulation
else:
	# If --use is specified, replace default mailbox_path
	if (args.use != None):
		# Find absolute path for processing
		mailbox_path = get_abs_path(args.use)
	else:
		mailbox_path = config['default_mailbox']
		
	# Check if the file exists
	if (os.path.isfile(mailbox_path)):
		if verbosity > 0: print("Using mailbox {}".format(mailbox_path))
		
		# Set to true, if mbox is successfully processed
		ingest_success = False
		
		try:
			Store.user_database(mailbox_path,verbose = verbosity > 0)
			ingest_success = True
		except Exception as err:
			print("Mail Ingest ERROR: " + str(err))
		
		########################################################################
		# SEARCH
		########################################################################
		if (args.action == 'search' and ingest_success == True):
			
			# Generate a search query based on the user field options
			query = []
			
			# Optional regex pre/post-fixes for search queries
			prefix = ''
			postfix = ''
			
			# Exact string match
			if (args.exact_string == True):
				prefix = '^' + prefix
				postfix = postfix + '$'
			
			# Regex negation
			if (args.negate == True):
				prefix = '^((?!' + prefix
				postfix = postfix + ').)*$'
			
			# Generate search query
			if (args.s != None):
				query.append(('Subject',(prefix + args.s + postfix)))
			if (args.b != None):
				query.append(('Body',(prefix + args.b + postfix)))
			if (args.f != None):
				query.append(('From',(prefix + args.f + postfix)))
			if (args.t != None):
				query.append(('To',(prefix + args.t + postfix)))
			if (args.rt != None):
				query.append(('Reply-to',(prefix + args.rt + postfix)))
			if (args.cc != None):
				query.append(('Cc',(prefix + args.cc + postfix)))
			if (args.bcc != None):
				query.append(('Bcc',(prefix + args.bcc + postfix)))
			if (args.d != None):
				query.append(('Date',(prefix + args.d + postfix)))	
			if (args.p != None):
				query.append(('Priority',(prefix + args.p + postfix)))	
			if (args.atn != None):
				query.append(('AttachName',(prefix + args.atn + postfix)))	
			if (args.atf != None):
				query.append(('AttachFormat',(prefix + args.atf + postfix)))	
			if (args.ats != None):
				query.append(('AttachStatus',int(args.ats)))		
			if (args.field != None):
				query.append((args.field[0],(prefix + args.field[1] + postfix)))	
			
			# If no search parameters are specified, dump everything
			if (len(query) <= 0):
				query.append(('Subject','.*')) # Match all regex
			
			# Verbosity printout
			if verbosity > 1:
				print('Search query:')
				print(query)
				
			# Send to the output file in .mailtools
			results_file = config['results']
			verbose = verbosity > 0
			
			# Run the search query
			try:
				Search.search_keywords_fields_mbox(results_file,query,verbose=verbose)
			except Exception as err:
				print("Search ERROR: " + str(err))
			
			### OPTIONAL POST-ACTIONS ###
			
			# Save results to a user-specified mbox file
			if (args.output != None):
				# Get absolute path and save results to destination
				output_path = get_abs_path(args.output)
	
				try:
					Process.save_search(output_path,verbose=verbose)
				except Exception as err:
					print("Search ERROR: " + str(err))
			
			# Printout the user specified field from every mail in results
			if (args.list_field != None):
				try:
					field_output = Process.get_field(args.list_field, verbose=verbose)
					
					# Printout the fields in csv format to terminal
					for result in field_output:
						print("\'" + "\',\'".join(result) + "\'")
				except Exception as err:
					print("Search ERROR: " + str(err))
			
			# Save the attachments to a user-specified folder
			if (args.attachments != None):
				# Get absolute path and save results to destination
				output_path = get_abs_path(args.attachments)
		
				try:
					Process.get_attachments(output_path,verbose=verbose)
				except Exception as err:
					print("Search ERROR: " + str(err))
			
			# Quick reply to the senders of each email in the results file
			if (args.reply == True):
				# Prompt the user for the email field
				subject = input("Subject:")
				body = input_multi_line()
				
				try:
					Process.send(subject,body,[],verbose=verbose)
				except Exception as err:
					print("Search ERROR: " + str(err))
			
			# Forward the messages to a specified recipient
			if (args.forward != None):
				try:
					Process.forward(args.forward,verbose=verbose)
				except Exception as err:
					print("Search ERROR: " + str(err))

		########################################################################
		# RUN PROCESS
		########################################################################
		elif (args.action == 'process' and ingest_success == True):
			
			# Process each mailscript in the provided list
			for mscript in args.file:
				
				# Find the absolute path to the file
				mailscript_path = get_abs_path(mscript)
				
				# If file is found, run script process
				if (os.path.isfile(mailscript_path)):
					
					# Normal execution. Run script normally in-place
					if (args.cron == None):
						script = ""
						with open(mailscript_path) as file:
							script = file.read()
						
						# Pretty print exceptions
						try:
							ifttt.process_script(script,mailbox_path)
						except Exception as err:
							print("Process ERROR: " + str(err))
					
					# If --cron is specified, create a cronjob
					else:
						subprocess.call(['cp','-rvf',mailscript_path,\
							"/home/{}/.mailtools/mailscript_jobs".format(getpass.getuser())])
						subprocess.call([EXEC_DIR + 'mk_cronjob.sh','123',\
							'{}'.format(args.cron),\
							'mailtools process --file /home/{}/.mailtools/mailscript_jobs/{}'.format(getpass.getuser(),mscript)])
				
				else:
					print("ERROR: {} not found".format(mailscript_path))
	else:
		print("ERROR: mailbox {} not found".format(mailbox_path))

