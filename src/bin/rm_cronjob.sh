#!/bin/bash
################################################################################
# File: rm_cronjob.sh
# Path: /usr/lib/mailtools/bin
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Deletes a cronjob with a specified id.
# 
# Usage:
#	rm_cronjob.sh <id>
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
if [[ "$#" -eq "1" ]] ; then
	id=$1
	
	# Pull current crontab and remove the line with the specified id
	crontab -l 2>/dev/null | sed "/$ID_PREFIX_TAG-$id/d" | crontab -
else
	printf "ERROR: Invalid number of commands\n"
	printf "Usage: rm_cronjobs.sh <id>\n"
fi
