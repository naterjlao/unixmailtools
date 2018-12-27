################################################################################
# File: ifttt_actions.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Authors: George Petterson (gpetters@protonmail.com)
#
# Action handler for Scripts
################################################################################
import inspect
import os
import mailbox

from smtplib import SMTP
from email.message import Message
from email.header import decode_header
from email.mime.multipart import MIMEMultipart

# Mapping from builtin actions to the appropriate functions
builtin_actions = {"create": "create", "copy": "copy", "set": "set_val", "send": "send", "reply": "reply", "forward": "forward", "write-attachments": "write_attachments", "write-msg": "write_msg", "set-var": "set_var"}

variable_tests = {"equals": "var_equals", "defined": "var_defined"}

smtp = SMTP()

def smtp_start(host, port=0):
    smtp.connect(host, port)

def smtp_stop():
    smtp.quit()

# Entrypoint into variable tests
# Input: test (variable test name), args (argument tuple), env (environment dict)
# Output: nothing
def test_variable(test, args, env):

    if test not in variable_tests:
        raise Exception("Unknown test %s" % test)

    fun = eval(variable_tests[test])

    arg_count = len(inspect.signature(fun).parameters)
    if arg_count != len(args)+1:
        raise Exception("Argument count mismatch: %s expected %d but got %d" % (action, arg_count, len(args)))

    return fun(*args, env)

# Entrypoint into the action functions
# Input: action (action name), args (argument tuple), env (environment dict), custom_actions (action name -> function dict)
#        over_env (environment dict for set variables)
# Output: nothing
def apply_action(action, args, env, custom_actions, over_env):

    # Function to be called
    fun = ""

    # Ensure action exists
    if action in custom_actions:
        args = tuple(((x[0].value, x[1].value) if isinstance(x, tuple) else x.value) for x in args)
        fun = custom_actions[action]
    elif action in builtin_actions:
        fun = eval(builtin_actions[action])
    else:
        raise Exception("Invalid action %s" % action)

    # Ensure arg counts match
    arg_count = len(inspect.signature(fun).parameters)
    if arg_count != len(args)+1:
        raise Exception("Argument count mismatch: %s expected %d but got %d" % (action, arg_count, len(args)))

    if action == "set-var": # Setting variables persists between environments
        fun(*args, over_env)
        fun(*args, env)
    else:
        # Evaluate function on arguments[o8]
        fun(*args, env)

# Checks that value is of the appropriate type, raises an exception otherwise
def assert_msg(m, env):
    if not ((not isinstance(m, tuple)) and (m in env) and (isinstance(env[m], mailbox.mboxMessage))):
        raise Exception("Invalid message %s" % str(m))
def assert_string(v):
    if not ((not isinstance(v, tuple)) and (v.type == "STRING")):
        raise Exception("Invalid string %s" % str(v))
def assert_identifier(v):
    if not((not isinstance(v, tuple)) and (v.type == "IDENTIFIER")):
        raise Exception("Invalid identifier %s" % str(v))
def assert_number(v):
    if not((not isinstance(v, tuple)) and (v.type == "NUMBER")):
        raise Exception("Invalid number %s" % str(v))
def assert_field(v):
    if not((isinstance(v, tuple)) and len(v) == 2 and (v[0].type == "IDENTIFIER") and (v[1].type == "IDENTIFIER")):
        raise Exception("Invalid field %s" % str(v))

# Parse string value
def parse_str(v):
    assert_string(v)
    if len(v) < 2 or v.value[0] != "\"" or v.value[-1] != "\"":
        raise Exception("Invalid string %s" % v)
    else:
        return v.value[1:-1]
# Parse identifier value
def parse_identifier(v):
    assert_identifier(v)
    return v.value
# Parse number value
def parse_number(v):
    assert_number(v)
    try:
        return float(v)
    except:
        raise Exception("Invalid number %s" % v)
# Parse field name
def parse_field(v):
    assert_field(v)
    if len(v) == 2:
        (msg, field) = v
        assert_identifier(msg)
        assert_identifier(field)
        return (msg.value, field.value)
    else:
        raise Exception("Invalid field %s" % v)

# Create blank message
def create(msg, env):

    msg = parse_identifier(msg)

    if msg in env:
        raise Exception("Tried to create message %s but it already exists" % msg)

    env[msg] = mailbox.mboxMessage()

# Copy one message to another
def copy(src, dst, env):

    src = parse_identifier(src)
    dst = parse_identifier(dst)
    assert_msg(src, env)
    assert_msg(dst, env)

    env[dst] = copy.copy(env[src])

# Set the value of a message's field in environment
def set_val(field, val, env):

    field = parse_field(field)
    if val.type == "NUMBER":
        val = parse_number(val)
    else:
        val = parse_str(val)

    (msg, field) = field
    if msg in env:
        if field != "Body":
            del env[msg][field]
            env[msg][field] = val
        else:
            msg = env[msg]
            while msg.is_multipart():
                msg = msg.get_payload(0)
            msg.set_payload(val)

# Forward message
def forward(msg, to, env):

    msg = parse_identifier(msg)
    to = parse_str(to)
    assert_msg(msg, env)

    msg = env[msg]
    msg["From"] = msg["To"]
    msg["To"] = to

    del msg["Received"]
    del msg["X-Received"]

    smtp.sendmail(msg["From"], msg["To"], msg)

# Reply to msg1 with msg2
def reply(msg1, msg2, env):

    msg1 = parse_identifier(msg1)
    msg2 = parse_identifier(msg2)
    assert_msg(msg1, env)
    assert_msg(msg2, env)

    msg1 = env[msg1]
    msg2 = env[msg2]

    new_body = msg1.get_payload()
    if not msg1.is_multipart():
        if new_body == None:
            new_body = []
        else:
            tmpmsg = Message()
            tmpmsg.set_payload(new_body)
            new_body = [tmpmsg]

    body = msg2.get_payload()
    if not msg2.is_multipart() and body != None:
        tmpmsg = Message()
        tmpmsg.set_payload(body)
        body = [tmpmsg]

    mimemsg = MIMEMultipart('alternative')

    for m in (new_body if body == None else body + new_body):
        mimemsg.attach(m)

    mimemsg["From"] = msg1["To"]
    mimemsg["To"] = msg1["From"]

    if len(msg1["Subject"]) < 3 or (msg1["Subject"][0:3] != "Re:" and msg1["Subject"][0:3] != "RE:"):
        mimemsg["Subject"] = "Re:" + msg1["Subject"]
    else:
        mimemsg["Subject"] = msg1["Subject"]

    smtp.send_message(mimemsg)

# Send message
def send(msg, env):

    assert_msg(msg, env)
    msg = parse_identifier(msg)

    smtp.send_message(env[msg])

# Write all attachments of msg to path
def write_attachments(msg, path, env):

    msg = parse_identifier(msg)
    path = parse_str(path)
    assert_msg(msg, env)
    msg = env[msg]

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if (part.get('Content-Disposition') is None) or (part.get('Content-Disposition') == 'inline'):
            continue

        file = part.get_filename()

        if file == None:
            continue
        else:
            file = str(decode_header(file)[0][0].decode())

        if path[-1] != "/":
            path += "/"

        if not os.path.exists(path):
            os.makedirs(path)

        with open(os.path.join(path, file), 'wb') as f:
            f.write(part.get_payload(decode=True))

# Write a modified email to the given mbox file
def write_msg(msg, path, env):

    path = parse_str(path)
    msg = parse_identifier(msg)

    assert_msg(msg, env)

    # Open the file
    box = None
    try:
        box = mailbox.mbox(path)
    except:
        raise Exception("File %s is invalid mbox or does not exist" % path)

    # Write the message
    box.add(env[msg])

    # Close the file
    box.close()

# Set an arbitrary variable in the environment
def set_var(var, val, env):
    var = parse_identifier(var)
    try:
        val = parse_str(val)
    except:
        val = parse_number(val)

    env[var] = val

# Test an arbitrary variable's value
def var_equals(var, val, env):
    var = parse_identifier(var)
    val = parse_str(val)

    return (var in env) and (env[var] == val)

# Test if the variable exists
def var_defined(var, env):
    var = parse_identifier(var)

    return var in env
