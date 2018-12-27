#!/bin/bash
################################################################################
# File: user_setup.sh
# Path: /usr/lib/mailtools/bin
# Language: Bash
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Setup script that runs when mailtools is first executed. Setups the .mailtools
# directory in the user's $home.
################################################################################

printf "Running mailtools user_setup.sh for $USER\n"

# Add argument completer code to bashrc
echo 'source /usr/lib/mailtools/bin/arg_complete_mailtools.sh' >> $HOME/.bashrc

# Create .mailtools directory
mkdir -v $HOME/.mailtools

# Copy blank config
cp -rvf /usr/lib/mailtools/etc/config.yml $HOME/.mailtools/config.yml

# Create directory for mailscript jobs
mkdir -v $HOME/.mailtools/mailscript_jobs

# Create an empty results mbox
touch $HOME/.mailtools/results

# Create mail directory for mail clients (ie. Thunderbird) and create a symbolic
# link to the results file in .mailtools
mkdir -v $HOME/mail 2> /dev/null
ln -s $HOME/.mailtools/results $HOME/mail/Mailtools


################################################################################
# GENERATE USER CONFIGURATION
################################################################################
echo "user: $USER" >> $HOME/.mailtools/config.yml
echo "home: $HOME" >> $HOME/.mailtools/config.yml

echo "# SMTP PORT (usually 25)" >> $HOME/.mailtools/config.yml
echo "smtp_port: 25" >> $HOME/.mailtools/config.yml

echo "# Default user mailbox (ie. Inbox)" >> $HOME/.mailtools/config.yml
echo "default_mailbox: /var/mail/$USER" >> $HOME/.mailtools/config.yml

echo "# Search results location (mbox file)" >> $HOME/.mailtools/config.yml
echo "results: $HOME/.mailtools/results" >> $HOME/.mailtools/config.yml

echo "# Attachment location (directory)" >> $HOME/.mailtools/config.yml
echo "attachments: $HOME/.mailtools/attachments" >> $HOME/.mailtools/config.yml

echo "# Mongo database name" >> $HOME/.mailtools/config.yml
echo "mongo_db_name: mailtools-$USER" >> $HOME/.mailtools/config.yml

