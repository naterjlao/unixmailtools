################################################################################
# File: Process.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Enock Gansou
#
# Implementation of emails processing. This performs some actions based on the
# search results.
################################################################################

from pymongo import MongoClient
import json
import multiprocessing
import os
import smtplib,  email,  mailbox
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import hashlib
import getpass
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import sys, traceback
from copy import deepcopy

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
SMTP_PORT = int(config['smtp_port'])

# name of file table 
FILE_NAME = 'file'

# name of query table 
QUERY_NAME = 'query'

# froms table: this is to store all emails we want to send to. This will help us avoid duplicates
FROM_NAME = 'froms'

# Encoding settings
def mbox_reader(stream):
    data = stream.read()
    text = data.decode(encoding="utf-8")
    return mailbox.mboxMessage(text)

# Getting the input filename and the search task currently in use in Mailtools 
def get_info():
	# Connect to database
    client = MongoClient()
    db = client[DATABASE_NAME]
    collection = db[FILE_NAME]
    elem1 = collection.find_one()
    collection = db[QUERY_NAME]
    elem2 = collection.find_one()
    
    # See if anything has been specified about the input filename or the current search task
    if elem1 == None or elem2 == None:
        return None
    else:
        src_path = elem1['name']
        task_to_string = elem2['task']
        return src_path, task_to_string

# This is the only function to use in CLI to save all search results to a specific file.  
# The next function is a "helper" function.
# This saves the current search results based on the filepath specified by the user
# target_filepath : Filepath where the search results to be saved.
def save_search(target_filepath, verbose=True):
    result = get_info()
    if result == None:
        raise Exception("A search task and/or a valid mbox file have not been specified")
    else:
        src_path, task_to_string = result
        
        # Create another process that will add the content to the new file
        p = multiprocessing.Process(target = save_search_job, args = (src_path, target_filepath, task_to_string, verbose))
        p.start()
        if verbose: print('Search saving will be executed as a background task with pid = ' +  str(p.pid))

# This is the mbox file creation task that will run as a background task (helper function)
def save_search_job(src_path, target_filepath, task_to_string, verbose=True):
    client = MongoClient()
    db = client[DATABASE_NAME]
    
    target_file = mailbox.mbox(target_filepath, factory = mbox_reader)
    #target_file.clear()
    
    # This is the input inbox file
    input_file = mailbox.mbox(src_path, factory = mbox_reader)
    
    collection = db[src_path]
    task = json.loads(task_to_string)
    results = list(collection.find(task))
     
    for result in results: 
        id_ = result["MessageID"]
        message = input_file[id_]
        try:
            target_file.add(message)  
        except: 
            print("Mailtools: mailbox module issue with email with id " + str(id_), flush=True)
    
    target_file.flush()
    target_file.close()
    input_file.close()

# This is the only function to use in CLI to get all attachments from the search results. 
# The next two functions are "helper" functions.
# Saving all attachments to a file
# target_filepath : Filepath where all attachments will be saved.
def get_attachments(target_filepath, verbose=True):
	# Here, we get the input filename and search task in use.
    result = get_info()
    # if one of them is missing, we should stop there.
    if result == None:
        raise Exception("A search task and/or a valid mbox file have not been specified")
    else:
        src_path, task_to_string = result
        
        # Here, we create another process that will execute the task we would like to accomplish
        #get_attachments_job(src_path, target_filepath, task_to_string)
        p = multiprocessing.Process(target = get_attachments_job, args = (src_path, target_filepath, task_to_string, verbose))
        p.start()
        if verbose: print('Getting attachments will be executed as a background task with pid = ' +  str(p.pid))
    
# This is the getting attachments task that will run as a background task (helper function)
def get_attachments_job(src_path, target_filepath, task_to_string, verbose=True):
    client = MongoClient()
    db = client[DATABASE_NAME]
    
    input_file = mailbox.mbox(src_path, factory = mbox_reader)
   
    collection = db[src_path]
    task = json.loads(task_to_string)
    results = list(collection.find(task))
    
    for result in results: 
        id_ = result["MessageID"]
        message = input_file[id_]
        get_attachments_msg(message, target_filepath, verbose)
        
    input_file.close()
    
# Getting all attachments for each email (helper function)
def get_attachments_msg(msg, file_, verbose=True):
    
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if (part.get('Content-Disposition') is None) or (part.get('Content-Disposition') == 'inline'): 
            continue  
        
        filename = part.get_filename() 
        
        if bool(filename):
 
            # Directory where attachments would be saved
            attach_dir = file_ + '/'
            content = part.get_payload(decode=True)
            if not os.path.exists(attach_dir):
                os.makedirs(attach_dir)
                
            filepath = os.path.join(attach_dir,  filename)
                
            with open(filepath, 'wb') as f:
                f.write(content)
                
                
# This is the only function to use in CLI to send emails back to from field addresses in the search results. 
# subject: the subject of the email
# body: the body of the email
# attach_filepaths: this is a list of attachment filepaths. ['./audio.mp3', './picture.jpeg']. Empty array means no attachments
# from_addr : optional address we want to send from. By default, this is set to the localhost's email address.
def send(subject, body, attach_filepaths, from_addr=None, verbose=True): 
    result = get_info()
    if result == None:
        raise Exception("A search task and/or a valid mbox file have not been specified")
    else:
        src_path, task_to_string = result
        
        # Here, we create another process that will execute the task we would like to accomplish
        send_job(src_path, task_to_string, from_addr, subject, body, attach_filepaths, verbose=verbose)
                
# Helper function for sending emails            
def send_job(src_path, task_to_string, from_addr, subject, body, attach_filepaths, verbose=True): 
    
    # Access the database
    client = MongoClient()
    db = client[DATABASE_NAME]
    
    # Table where we will store all the from address emails and check for duplicates that 
    # we will send back the email to.
    collection_ = db[FROM_NAME]
    collection_.drop()
    
    # Search again using the saved query
    collection = db[src_path]
    task = json.loads(task_to_string)
    results = list(collection.find(task))
    
    # Retrieve only the address
    to_addr_list = []
    for result in results: 
        from_ = result["From"]
        if not from_ is None:
            from_ = from_.split('<')
            from_ = from_[len(from_) - 1]
            from_ = from_.split('>')
            from_ = from_[0]
            if collection_.find_one({'user' : from_}) is None:
                collection_.insert_one({'user' : from_})
                to_addr_list.append(from_)
                
    # This is to construct the actual email to be send to each from adress
    msg = MIMEMultipart()
    msg['To'] = ', '.join(to_addr_list)
    msg["Subject"] = subject
    # add in the body for the email
    msg.attach(MIMEText(body, 'plain'))
    # add in the attachments for the email
    for filename in attach_filepaths:
        try :
            attachment = open(filename, 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            basename = os.path.basename(filename)
            part.add_header('Content-Disposition', 'attachment; filename= ' + basename)
            msg.attach(part) 
        except:
            print('ERROR: The attachment with filepath ' + filename + ' could not be handled by Mailtools.')
            continue
    
    
    # Connect with localhost mailserver
    with smtplib.SMTP('localhost', SMTP_PORT) as server:
    
        # Set the From field for the email
        localhost_email = config['user'] + '@' + server.local_hostname
        msg["From"] = from_addr if from_addr != None else localhost_email
        
        # Send the message
        server.send_message(msg)
    
    
# This is the only function to use in CLI to forward emails. 
# to_addr_list: The list of addresses we want to forward emails in the search results to.
# from_addr : optional address we want to send from. By default, this is set to the localhost's email address.
def forward(to_addr_list, from_addr = None, verbose=True):
    result = get_info()
    
    if result == None:
        raise Exception("A search task and/or a valid mbox file have not been specified")
    else:
        src_path, task_to_string = result
        
        # Create process
        forward_job(src_path, task_to_string, from_addr, to_addr_list, verbose=verbose)
        
# Forwarding emails (helper functions)
def forward_job(src_path, task_to_string, from_addr, to_addr_list, verbose=True):
    
    client = MongoClient()
    db = client[DATABASE_NAME]
     
    # Input inbox file
    input_file = mailbox.mbox(src_path)
    collection = db[src_path]
    task = json.loads(task_to_string)
    results = list(collection.find(task))
        
    # Connect with localhost mailserver
    with smtplib.SMTP('localhost', SMTP_PORT) as server: 
        # Email address of the localhost
        localhost_email = config['user'] + '@' + server.local_hostname

        for result in results: 
            id_ = result["MessageID"]
            
            try: 
                msg_string = str(input_file[id_])
                
                msg = email.message_from_string(msg_string)
                msg.replace_header('From', (localhost_email if from_addr == None else from_addr))
                msg.replace_header('To', (', '.join(to_addr_list)))
                
                server.send_message(msg)
                if verbose: print('Mailtools sucessfully sent the email')       
            except:
                print("Mailtools could not send email with id: " + str(id_))
                continue

# This is the only function to use in CLI to print all the fields. 
# field: the field(s) of interest. Eg : 'From'
# Returns a 2D list of field values per email
def get_field(field, verbose=True):
    result = get_info()
    
    if result == None:
        raise Exception("A search task and/or a valid mbox file has not been specified")
    else:
        src_path, task_to_string = result
        
        # Create singleton if necessary
        if (type(field) != list):
        	field = [field]
        
        # Here, we create another process that will execute the task we would like to accomplish
        return get_field_job(src_path, task_to_string, field, verbose=verbose)
        
# Generating fields (helper)
# Returns a 2D list of field values per email
def get_field_job(src_path, task_to_string, fields, verbose=True):
    
    client = MongoClient()
    db = client[DATABASE_NAME]
     
    collection = db[src_path]
    task = json.loads(task_to_string)
    results = list(collection.find(task))

    # Return a 2D list of field values per email
    output = []
    for result in results:
        current = []
        for field in fields:
            current.append(str(result[field]))
        output.append(current)
    return output
        
        
    
            

