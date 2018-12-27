################################################################################
# File: Search.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Enock Gansou
#
# Implementation of the table searching/querying (search, filter, etc...).
################################################################################

from pymongo import MongoClient
import mailbox
import multiprocessing
import time
import json
import os
import signal
import psutil
import Store
import hashlib
import chardet

################################################################################
# PROPIETARY IMPORTS
################################################################################
import Config
################################################################################
# CONFIGURATION SETUP
################################################################################
config = Config.get_config()
#Get the mongo database name
DATABASE_NAME = config['mongo_db_name']

# name of file table 
FILE_NAME = 'file'

# name of query table
QUERY_NAME = 'query'

# name of query table 
SEARCH_PROCESS_NAME = 'search_process'

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

# Search for specific keywords given a specific username 
# keywords: keywords we want to search through
def search_keywords_no_mbox(keywords, verbose=True): 
    src_path = get_info()
    
    if(src_path == None):
        if verbose: print("A valid mbox file has not been specified")
    else:  
        client = MongoClient()
        db = client[DATABASE_NAME]
        
        task = {"$text":{"$search": keywords}}
        
        # Collection to store the current search task in use
        collection = db[QUERY_NAME]
        collection.drop()
        task_to_string = json.dumps(task)
        collection.insert_one({'task' : task_to_string})
        
        collection = db[src_path]
        start_time = time.time()
        results = list(collection.find(task))
        if verbose: print("Mailtools search took approximately %s seconds" % (time.time() - start_time))
        if verbose: print("The search result contains " + str(len(results)) + " element(s)")

# Search in a list of pairs (field, value) given a specific username 
# content: a list of pairs (field, value) we want to search throug
def search_keywords_fields_no_mbox(content, verbose=True):
    src_path = get_info()
    
    if(src_path == None):
        if verbose: print("A valid mbox file has not been specified")
    else:  
        client = MongoClient()
        db = client[DATABASE_NAME]
    
        task = {}
        json_list = []
        for (field, value) in content:
            if field == "AttachStatus":
                 json_list.append({field : value})
            else:
                if field == "AttachName":
                    field = "Attachments.AttachName"
                if field == "AttachFormat":
                    field = "Attachments.AttachFormat"
                if field == "AttachContent":
                    field = "Attachments.AttachContent"  
                json_list.append({field : {"$regex" : ".*"+value+".*", "$options" : "si"}})
        task = { "$and" : json_list }
        
        # Collection to store the current search task in use
        collection = db[QUERY_NAME]
        collection.drop()
        task_to_string = json.dumps(task)
        #print(task_to_string)
        collection.insert_one({'task' : task_to_string})
    
        collection = db[src_path]
        start_time = time.time()
        results = list(collection.find(task))
        if verbose: print("Mailtools search took approximately %s seconds" % (time.time() - start_time))
        if verbose: print("The search result contains " + str(len(results)) + " element(s)")

        
# Search for specific keywords given a specific username 
# And Save results to Mbox file
# We must update this version with elasticSearch
# dst_path: where we want to store the results file
# keywords: the keywords we want to search through
def search_keywords_mbox(dst_path, keywords, verbose=True):   
    src_path = get_info() 
    if(src_path == None):
        if verbose: print("A valid mbox file has not been specified")
    else:  
        client = MongoClient()
        db = client[DATABASE_NAME]
  
        task = {"$text":{"$search": keywords}}
    
        # Collection to store the current search task in use
        collection = db[QUERY_NAME]
        collection.drop()
        task_to_string = json.dumps(task)
        collection.insert_one({'task' : task_to_string})
        
        # Create another process that will add the content to the results file
        #search_job(dst_path, src_path, task)
        p = multiprocessing.Process(target = search_job, name = 'Search', args = (dst_path, src_path, task, verbose))
        p.start()
        if verbose: print('The results file update will be executed as a background task with pid = ' + str(p.pid))

# Search in a list of pairs (field, value) given a specific username 
# And save results to Mbox file using another pr
# We must update this version with elasticSearch
# dst_path: where we want to store the results file
# content: a list of pairs (field, value) we want to search through
def search_keywords_fields_mbox(dst_path, content, verbose=True):
    
    src_path = get_info()
    
    if(src_path == None):
        if verbose: print("A valid mbox file has not been specified")
    else:  
    
        client = MongoClient()
        db = client[DATABASE_NAME]
        
        task = {}
        json_list = []
        for (field, value) in content:
            if field == "AttachStatus":
                 json_list.append({field : value})
            else:
                if field == "AttachName":
                    field = "Attachments.AttachName"
                if field == "AttachFormat":
                    field = "Attachments.AttachFormat"
                if field == "AttachContent":
                    field = "Attachments.AttachContent"  
                json_list.append({field : {"$regex" : ".*"+value+".*", "$options" : "si"}})
        task = { "$and" : json_list }
        
    
        # Collection to store the current search task in use
        collection = db[QUERY_NAME]
        collection.drop()
        task_to_string = json.dumps(task)
        collection.insert_one({'task' : task_to_string})
  
        # Create another process that will add the content to the results file
        p = multiprocessing.Process(target = search_job, name = 'Search', args = (dst_path, src_path, task,))
        p.start()
        if verbose: print('The results file update will be executed as a background task with pid = ' + str(p.pid)) 


# This function should not be used in CLI. Use the ones above
# This is the process that creates an mbox file based on the search query
# dst_path: the results filepath
# src_path: the source filepath
# task : the search query we want to use for the search process 
def search_job(dst_path, src_path, task, verbose=True):   
  
    client = MongoClient()
    db = client[DATABASE_NAME]
    
    # Kill old search process if one exists
    collection = db[SEARCH_PROCESS_NAME]
    if  collection.count() == 0:
        pid = os.getpid()
        collection.insert_one({'process' : pid, 'changed' :  'first change'})
    else:
        p_old_pid = collection.find_one()['process'] 
        try:
            p = psutil.Process(p_old_pid)
            p.kill()
            results_file = mailbox.mbox(dst_path, factory=mbox_reader)
            results_file.close()
            pid = os.getpid()
            collection.update(  
                {'process' : p_old_pid} , 
                { "$set" : {'process' : pid, 'changed' :  'Change again'} }
            )
            
        except:
            pid = os.getpid()
            collection.update(  
                {'process' : p_old_pid} , 
                { "$set" : {'process' : pid, 'changed' :  'No change'} }
            )
    
    # Results file 
    results_file = mailbox.mbox(dst_path, factory = mbox_reader)
    results_file.clear()
    
    # This is the input inbox file
    input_file = mailbox.mbox(src_path, factory = mbox_reader)
    
    collection = db[src_path]
    results = list(collection.find(task))
     
    for result in results:
        id_ = result["MessageID"]
        message = input_file[id_]
        try:
            results_file.add(message)
        except: 
            if verbose: print("Mailtools: mailbox module issue with email with id " + str(id_), flush=True)
            
    results_file.flush()
    results_file.close()
    
    input_file.close()
    
        
