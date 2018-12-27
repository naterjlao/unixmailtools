################################################################################
# File: NoSQL.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Enock Gansou
#
# Database structure implementation.
################################################################################

from pymongo import MongoClient
import hashlib

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

# name of files table 
FILES_NAME = 'files'

# This function helps determine whether we need to create
# a new search table
# 1 is returned if the table needs to created, otherwise 0
def create_table(filename, last_modified_date):
    client = MongoClient()
    # Database 
    db = client[DATABASE_NAME]
    
    # Collection to store the name of filepath in use
    collection = db[FILE_NAME]
    collection.drop()
    collection.insert_one({'name' : filename})
    
    # Collection to store the name of all the filepaths used so far
    collection = db[FILES_NAME]
    
    if  collection.find_one({'name' : filename}) is None:
        collection.insert_one({'name' : filename, 'date' : last_modified_date})
        return 1
    else:
        date = collection.find_one({'name' : filename})['date']
        if date == last_modified_date: 
            return 0
        else: 
            collection.update(  
                {'name' : filename} , 
                { "$set" : {'name' : filename, 'date' : last_modified_date} }
            )
            return 1

# Generate a collection associated with the filename containing emails
def use_old_table(filename):
    client = MongoClient()
    db = client[DATABASE_NAME]
    collection = db[filename]
    
    return collection

# Generate a collection associated with the filename containing emails
def use_new_table(filename):
    client = MongoClient()
    # Database 
    db = client[DATABASE_NAME]
    
    # Collection emails to store emails
    collection = db[filename]
    collection.drop()
    collection.create_index([('$**', 'text')])
    
    return collection
  
        
    
# Add an email information to the collection/table
def email_to_table(collection, messageID, from_, to, reply_to, date, subject, cc, bcc, priority, body, attachments):
   
    email = {
        "MessageID" : messageID,       
    } 
    
    if (not (from_ is None)):
        email.update({"From" : from_})
    if (not (to is None)):
        email.update({"To" : to})
    if (not (reply_to is None)):
        email.update({"ReplyTo" : reply_to})
    if (not (date is None)):
        email.update({"Date" : date})
    if (not (subject is None)):
        email.update({"Subject" : subject})
    if (not (cc is None)):
        email.update({"Cc" : cc})
    if (not (bcc is None)):
        email.update({"Bcc" : bcc})
   
    if (not (priority is None)):
        email.update({"Priority" : priority})
         
    if (not (body is None)): email.update({"Body" : body}) 
    
    # Attach status help us determine whether mail contains attachments (1) or not (0)
    if(attachments == []):
        email.update({"AttachStatus" : 0})
    else:
        email.update({"AttachStatus" : 1})
   
    attach = []
    for (name, format_, content) in attachments:
        attachment = {
            'AttachName' : name, 
            'AttachFormat' : format_, 
            'AttachContent' : content
        }
        attach.append(attachment)
        
    email.update({ "Attachments" : attach }) 
   
    collection.insert_one(email)

