#!/bin/bash
################################################################################
# File: user_teardown.sh
# Path: /usr/lib/mailtools/bin
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Teardown script that runs when the user runs 'mailtools --setup'. Removes the
# '$home/.mailtools/config.yml' configuration file and removes the installed 
# symbolic link '$home/mail/Mailtools' if there exists one.
################################################################################

printf "Deleting mailtools files for $USER\n"

# Remove argument completer code referece
#sed -i s/'source \/usr\/lib\/mailtools\/bin\/arg_complete_mailtools.sh'// $HOME/.bashrc
grep -v 'source /usr/lib/mailtools/bin/arg_complete_mailtools.sh' $HOME/.bashrc > $HOME/.bashrc.tmp
cat $HOME/.bashrc.tmp > $HOME/.bashrc
rm $HOME/.bashrc.tmp

# Remove all .mailtools directories from all users
rm -rvf $HOME/.mailtools/config.yml 2> /dev/null

# Remove all symbolic links to $home/.mailtools/results
rm -rvf $HOME/mail/Mailtools 2> /dev/null

