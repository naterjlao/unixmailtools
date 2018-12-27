################################################################################
# File: Script.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Enock Gansou
#
# This is to implement IF THIS THEN THAT.
################################################################################

from pymongo import MongoClient
import mailbox
import hashlib

# Nate: Added propietary imports and config setup
################################################################################
# PROPIETARY IMPORTS
################################################################################
import Config
################################################################################
# CONFIGURATION SETUP
################################################################################
config = Config.get_config()
# Get the mongo database name
DATABASE_NAME = config['mongo_db_name']

# name of file table 
FILE_NAME = 'file'

# Enock: This is added to fix bug we found when parsing some emails
def mbox_reader(stream):
    data = stream.read()
    text = data.decode(encoding="utf-8")
    return mailbox.mboxMessage(text)

# Getting the appropiate filename we used to create the database
def get_info():
    client = MongoClient()
    db = client[DATABASE_NAME]
    collection = db[FILE_NAME]
    elem = collection.find_one()
    if elem is None:
        return None
    else:
        return elem['name']

# This returns all the ids of the email content
def get_results_ids(query_in_json):
    # Getting the appropiate table
    src_path = get_info()

    if(src_path == None):
        print("A valid mbox file has not been specified")
        return None
    else:
        # To store all the ids
        ids = []

        client = MongoClient()
        db = client[DATABASE_NAME]
        collection = db[src_path]
        results = list(collection.find(query_in_json))
        for result in results:
            ids.append(result['MessageID'])
        return ids

# This is a prototype function to show how input file content could be accessed
def do_something(ids):
    src_path = get_info()

    if(src_path == None):
        print("A valid mbox file has not been specified")
    else:

        # This is the input inbox file
        input_file = mailbox.mbox(src_path, factory=mbox_reader)

        for id_ in ids:
            # Reference copy
            email = input_file[id_]
            # OR Deep cody
            email = copy.deepcopy(input_file[id_])

        input_file.close()
