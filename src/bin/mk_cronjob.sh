#!/bin/bash
################################################################################
# File: mk_cronjob.sh
# Path: /usr/lib/mailtools/bin
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Creates a cronjob with a specified id.
#
# Usage:
#	mk_cronjob.sh <id> '<time>' '<action>'
# 
# Example:
#	mk_cronjob.sh 1234 '0 5 * * 1' 'mailtools --update'
#
# Note:
#	The time specifiers (ie. m,h,...) are specified in the 'crontab' utility.
#
# Cronjobs are placed in the /var/spool/cron directory and are accessed via the
# command 'crontab'. IDs for cronjobs are specified by a comment string after the
# action command:
#
# Format:
#	<m> <h> <dom> <mon> <dow> <action> #mt-<id>
#
# Example:
#	0 5 * * 1 mailtools --update #mt-1234
################################################################################

ID_PREFIX_TAG='#mt'

# Check arguments
if [[ "$#" -eq "3" ]] ; then
	id=$1
	time=$2
	action=$3

	# Check if first parameter is an integer
	if [[ $id =~ ^-?[0-9]+$ ]] ; then
		printf "creating cronjob $id\n"
		
		# Pulls the existing crontab, append id commentline and command
		(crontab -l 2>/dev/null; echo "$time $action $ID_PREFIX_TAG-$id") | crontab -
	else
		printf "ERROR: ID must be an integer\n"
	fi
else
	printf "ERROR: Invalid number of commands\n"
	printf "Usage: mk_cronjobs.sh <id> '<time>' '<action>'\n"
fi
