################################################################################
# File: Store.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: Enock Gansou
#
# Mailbox database storing.
################################################################################

import email
import mailbox
import NoSQL
import os
import datetime
import time
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
ATTACHMENT_PATH = config['attachments']

# Enock: This is added to fix bug we found when parsing some emails
def mbox_reader(stream):
    data = stream.read()
    text = data.decode(encoding="utf-8")
    return mailbox.mboxMessage(text)

# Getting the body content
def get_body(msg):
    if msg.is_multipart():
        return(get_body(msg.get_payload(0)))
    else:
        return msg.get_payload(None, True).__str__()
       

# Getting all attachments
# All attachments are sent to a folder including txt files
def get_attachments(msg, file, attach_id):   
    lst = []  
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        # Nate - added second conditional, need to check inline CD
        if (part.get('Content-Disposition') is None) or (part.get('Content-Disposition') == 'inline'): 
            continue  
            
        filename = part.get_filename()
        
        if bool(filename): 
            name, format_ = os.path.splitext(part.get_filename())
            content = part.get_payload(decode=True)        
        
            # Copy the content of the attachments to an external file.
            
            # Directory where attachments would be saved
            attach_dir = ATTACHMENT_PATH + '/' + file + '/'+ attach_id + '/'
    
            if not os.path.exists(attach_dir):
                os.makedirs(attach_dir)
                
            filepath = os.path.join(attach_dir,  filename)
                
            with open(filepath, 'wb') as f:
                f.write(content)
                
            content = attach_dir
            
            lst.append((name, format_, content))  
              
    return lst

        
# Create the database associated with a specific user
# file: the file containing all emails (mbox file)
def user_database(file,verbose=True):
    
    file = os.path.abspath(file)
    input_file = mailbox.mbox(file, factory=mbox_reader)
   
    last_modified_date = os.path.getmtime(file)
        
    # 0 means we do not need to create the table 
    if NoSQL.create_table(file, last_modified_date) == 0: 
        if verbose: print('Mailtools database is already updated')
        collection = NoSQL.use_old_table(file)
         
    # Otherwise we must create a (new) table 
    else:
        collection = NoSQL.use_new_table(file)
        
        start_time = time.time()
        id_ = 0
        
        for message in input_file: 
            # Differents parts of an email we want to search on
            messageID = id_ 
            from_ = message['From']
            to = message['To']
            reply_to = message['Reply-To']
            date = message['Date']
            subject =  message['Subject']
            if (not subject is None): subject = subject.__str__()
            cc = message['Cc']
            bcc = message['Bcc'] 
            priority = message['Priority']
            body = get_body(message)
        
          
            attach = os.path.basename(file)
            attach_dir = ATTACHMENT_PATH + '/' + attach + '/'
            
            attachments = get_attachments(message, attach, str(id_))
        
            # Add content to table/database
            NoSQL.email_to_table(collection, messageID, from_, to, reply_to, date, subject, cc, bcc, priority, body, attachments)
          
            id_ += 1
        
        if verbose: print("Mailtools database update took approximately %s seconds" % (time.time() - start_time))
        input_file.close()
       
        
        
