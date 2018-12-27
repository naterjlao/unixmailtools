#!/bin/bash
################################################################################
# File: sudo_teardown.sh
# Path: /usr/lib/mailtools/bin
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Teardown script that runs when mailtools in uninstalled from the system.
# Undoes the actions of user_setup.sh. Note that this destructively deletes all
# associated mailtools files from ALL users.
################################################################################

printf "Deleting mailtools files for all users\n"

# Remove argument completer code reference
ls /home/ | xargs -I{} sh -c \
	"grep -v 'source /usr/lib/mailtools/bin/arg_complete_mailtools.sh' /home/{}/.bashrc > /home/{}/.bashrc.tmp; \
	cat /home/{}/.bashrc.tmp > /home/{}/.bashrc; \
	rm /home/{}/.bashrc.tmp"

# Remove all .mailtools directories from all users
rm -rvf /home/*/.mailtools

# Remove all symbolic links to $home/.mailtools/results
rm -rvf /home/*/mail/Mailtools

