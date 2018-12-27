#!/usr/bin/env python3
################################################################################
# File: Config.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Nathaniel Lao (nlao@terpmail.umd.edu)
#
# Defines a method that pulls the user's current configuration.
# For more information:
#	https://martin-thoma.com/configuration-files-in-python/
################################################################################

import yaml		# For reading the configuration file
import getpass	# Get current user

# Default configuration is found in /home/user/.mailtools/config.yml
DEFAULT_CONFIG = "/home/{}/.mailtools/config.yml".format(getpass.getuser())

################################################################################
# Reads the configuration file as specified by the path and returns the
# configuration object where values can be accessed by the following syntax:
#	get_config(foo)[field]
################################################################################
def get_config(config_path=DEFAULT_CONFIG):
	with open(config_path,'r') as config_file:
		return yaml.load(config_file)
