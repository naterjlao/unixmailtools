################################################################################
# File: ifttt.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: George Petterson (gpetters@protonmail.com)
#
# Entrypoint into script logic
################################################################################
import copy
import mailbox
import threading

import ifttt_actions as actions
import ifttt_parse as parse
import Script

# Copy unmodified messages to new mbox
# Input: ids (array of message ID values), src (input mbox path), dst (output mbox path)
# Output: nothing
def copy_ids(ids, src, dst):
    to_box = mailbox.mbox(dst)
    from_box = mailbox.mbox(src)

    for i in ids:
        msg = from_box[i]
        to_box.add(msg)

    to_box.flush()

    from_box.close()
    to_box.close()

# Process a script
# Input: script (string representation of script file), path (mbox file path)
# Output: nothing
def process_script(script, path):

    def process_vartest(test, args, env):
        if test == "and":

            if len(args) <= 1:
                raise Exception("Too few arguments for 'and': %d" % len(args))

            for subtest in args:
                if not process_vartest(subtest[0], subtest[1:], env):
                    return False

            return True
        elif test == "or":

            if len(args) <= 1:
                raise Exception("Too few arguments for 'or': %d" % len(args))

            for subtest in args:
                if process_vartest(subtest[0], subtest[1:], env):
                    return True

            return False
        elif test == "not":

            if len(args) != 1:
                raise Exception("Incorrect number of arguments: 'not' expects 1, got %d" % len(args))

            return not process_vartest(args[0][1], args[0][2:], env)

        else:
            actions.test_variable(test, args, env)

    # Remove footer, parse header and body
    (header, body, footer) = parse.parse(script)

    # Process header
    new_actions = {}

    basic_env = {"create": actions.create, "copy": actions.copy, "set": actions.set_val, "forward": actions.forward, "reply": actions.reply, "send": actions.send, "write_attachments": actions.write_attachments}
    try:
        # Load script from footer
        exec(footer, basic_env)
    except:
        raise Exception("Bad footer")

    version = None
    header = parse.h_transform.transform(header)
    for statement in header:
        if statement[0] == "version":
            if version != None:
                raise Exception("Bad header - version defined twice")
            else:
                version = int(statement[1].value)
        else:
            [_, action, function] = statement
            try:
                new_actions[action.value] = eval(function.value, basic_env)
            except NameError:
                raise Exception("Bad header - action defined with nonexistent function")

    # Transform AST
    ast = parse.b_transform.transform(body)

    # Verify AST
    if not parse.verify(ast):
        raise Exception("")

    # Build query list
    (query_list, save_to) = parse.walk_ast(ast)

    # Run queries
    # TODO: threads?
    #path = Script.get_info()
    #src_box = mailbox.mbox(path)
    src_box = mailbox.mbox(path)

    actions.smtp_start('localhost')

    for (query, action_list, uses_msg) in query_list:

        script_ids = Script.get_results_ids(query)

        if script_ids == None:
            continue

        save_thread = None
        # Write results to file (this should happen in Enock's results process)
        if save_to != None:
            save_thread = threading.Thread(group=None, target=copy_ids, name=None, args=(script_ids, path, save_to))
            save_thread.start()

        over_env = {}
        for ids in script_ids:
            env = {"msg": None}
            env.update(basic_env)
            env.update(over_env)

            # If the actions use the message we load it from the mbox file
            if uses_msg:

                src_box.lock()
                src_msg = copy.copy(src_box[ids])
                src_box.unlock()

                env["msg"] = src_msg

            # Step through actions, performing each with the environment
            action_list.reverse()
            while action_list:
                action = action_list.pop()
                if action[0] == "var_test":
                    alist = action[1:]
                    alist.reverse()
                    for s in alist:
                        action_list.append(s)
                elif action[0] == "if" or action[0] == "elif":
                    test = action[1][1].value
                    #args = tuple(x for x in action[1][2:])
                    args = tuple(x for x in action[1][2:])
                    alist = action[2]
                    if process_vartest(test, args, env):
                        while action_list != [] and (action_list[-1][0] == "elif" or  action_list[-1][0] == "else"):
                            action_list.pop()
                        action_list.extend(alist[::-1])
                elif action[0] == "else":
                    alist = action[1]
                    action_list.extend(alist[::-1])
                else:
                    (_, name, args) = action
                    #actions.apply_action(name.value, tuple((a.value if not isinstance(a, tuple) else (a[1].value, a[2].value)) for a in args), env, new_actions, over_env)
                    actions.apply_action(name.value, tuple((a if not isinstance(a, tuple) else (a[1], a[2])) for a in args), env, new_actions, over_env)

        if save_thread != None:
            save_thread.join()

    src_box.flush()
    src_box.close()

    actions.smtp_stop()

# Easter egg
# Input: msg_from (From value), msg_to (To value), body (message body)
# Output: nothing
def purtilo(msg_from, msg_to, body):
    actions.smtp_start('localhost')

    msg = mailbox.mboxMessage()
    msg["To"] = msg_to
    msg["From"] = msg_from
    msg["Subject"] = "CHANGE IS INEVITABLE?"

    msg.set_payload(body)

    actions.smtp.send_message(msg)

    actions.smtp_stop()
