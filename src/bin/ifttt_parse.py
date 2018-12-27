################################################################################
# File: ifttt_parse.py
# Path: /usr/lib/mailtools/bin
# Language: Python3
# Author: George Petterson (gpetters@protonmail.com)
#
# Script parsing tools
################################################################################
import re

from lark import Lark, Transformer

# Tokenizes header
class HeaderTransformer(Transformer):
    def header(self, items):
        return items
    def action_definition(self, items):
        return ["define"] + items
    def version_statement(self, items):
        return ["version"] + items

# Tokenizes body
class BodyTransformer(Transformer):
    def if_else_chain(self, items):
        return ["ifelse"] + items
    def if_statement(self, items):
        return  ["if"] + items
    def else_statement(self, items):
        return ["if"] + items
    def match_statement(self, items):
        return ("match", items[0], tuple(items[1:]))
    def action_list(self, items):
        return ["actions"] + items
    def action_statement(self, items):
        return ("action", items[0], tuple(items[1:]))
    def argument(self, items):
        return items[0]
    def msg_field(self, items):
        return ('field',) + tuple(items)
    def variable_test(self, items):
        return ("var_test", items)
    def var_if(self, items):
        return ("if", items[0], items[1])
    def var_elif(self, items):
        return ("elif", items[0], items[1])
    def var_else(self, items):
        return ("else", items[0])
    def var_test(self, items):
        return ('test',) + tuple(items)

b_transform = BodyTransformer()
h_transform = HeaderTransformer()

# Body grammar
body_parser = Lark(r"""
if_else_chain: if_statement else_statement*

if_statement: "if" match_statement "{" if_else_chain "}"
    |  "if" match_statement "{" action_list "}"

else_statement: "else" "if" match_statement "{" if_else_chain "}"
    |  "else" "if" match_statement "{" action_list "}"

match_statement: "(" IDENTIFIER (match_statement | argument)* ")"

action_list: (action_statement | variable_test)+

action_statement: "(" IDENTIFIER argument* ")"

variable_test: var_if (var_elif)* (var_else)?

var_if: "if" var_test "{" action_list "}"
var_elif: "else" "if" var_test "{" action_list "}"
var_else: "else" "{" action_list "}"

var_test: "(" TEST IDENTIFIER argument* ")"
    |  "(" LOGIC_TEST var_test+ ")"

TEST: ("equal" | "defined")

LOGIC_TEST: ("and" | "or" | "not")

argument: STRING
    |  NUMBER
    |  IDENTIFIER
    |  msg_field
    |  REGEX

COMMENT: /;.*/

msg_field: IDENTIFIER "." IDENTIFIER

REGEX: /\/.*\//

IDENTIFIER: /[A-Za-z]([A-Za-z0-9]|-|_)*/

%import common.WS
%import common.NUMBER -> NUMBER
%import common.ESCAPED_STRING -> STRING

%ignore WS
%ignore COMMENT
""", start="if_else_chain")

# Header grammar
header_parser = Lark(r"""
header: "%%%" version_statement action_definition* "%%%"

action_definition: "(" "define" IDENTIFIER IDENTIFIER+ ")"

version_statement: "(" "version" NUMBER ")"

IDENTIFIER: /[A-Za-z]([A-Za-z0-9]|-|_)*/
COMMENT: /;.*/
%import common.NUMBER -> NUMBER
%import common.WS

%ignore COMMENT
%ignore WS
""", start="header")


# Remove header and footer, process those
# Input: script (string representation of script)
# Output: header (header's abstract syntax tree), ast (body's abstract syntax tree), footer (string representation of the footer)
def parse(script):
    ast = None
    footer = ""

    # Remove header
    d1 = script.find("%%%")
    d2 = script.find("%%%", d1+3)

    if d1 < 0 or d2 < 0:
        raise Exception("Bad header - improperly formatted")

    header = script[d1:d2+3]
    script = script[d2+3:]

    try:
        header = header_parser.parse(header)
    except:
        raise Exception("Bad header - improperly formatted")

    # Remove footer
    dl1 = script.find("~~~")
    dl2 = script.find("~~~", dl1+3)

    if dl1 < 0 or dl2 < 0:
        footer = ""
    else:
        footer = script[dl1+3:dl2]
        script = script[:dl1]

    try:
        ast = body_parser.parse(script)
    except:
        raise Exception("Bad body - improperly formatted")

    return (header, ast, footer)

# Build up the tuple ([(query, action_list, uses_msg)], save_to) by walking AST
# Note: uses_msg is a boolean we use to save time so we don't load from disk if we don't have to
# Similarly, save_to is the file the user has request we save to using the (save-to) action - it defaults to None

# Process body AST
# Input: ast (the syntax tree representation of a script body)
# Output: query_list (list of MongoDB queries, lists of actions, and whether the query uses the message), save_to (string path of mbox to save unmodified messages or None)
def walk_ast(ast):

    save_to = None

    # Recursively process an action list
    def walk_alist(alist, tree):
        nonlocal save_to
        for action in tree:
            if action[0] == "var_test":
                sublist = []
                for action in action[1]:
                    if action[0] == "else":
                        (type, subactions) = action
                        child_list = []
                        walk_alist(child_list, subactions[1:])
                        a = (type, child_list)
                        sublist.append(a)
                    else:
                        (type, test, subactions) = action
                        child_list = []
                        walk_alist(child_list, subactions[1:])
                        a = (type, ('test',) + tuple(test[1:]), child_list)
                        sublist.append(a)
                alist.append(["var_test"] + sublist)
            else:
                (_, act, args) = action
                if act == "save-to":
                    if args[0].value[0] == "\"" and args[0].value[-1] == "\"":
                        save_to = args[0].value[1:len(args[0].value)-1]
                    else:
                        raise Exception("Invalid syntax: save-to must take a string")
                else:
                    alist.append(action)

    # Recursively process a query
    def tuple_to_json(query):

        match = query[0]

        if match == "and":
            if len(query[1:]) < 2:
                raise Exception("Too few arguments to 'and' match")

            return {"$and": [tuple_to_json(x) for x in query[1:]]}
        elif match == "or":
            if len(query[1:]) < 2:
                raise Exception("Too few arguments to 'or' match")

            return {"$or": [tuple_to_json(x) for x in query[1:]]}
        elif match == "not":
            if len(query[1:]) != 1:
                raise Exception("Too many arguments to 'not' match")

            return {"$not": tuple_to_json(query[1])}
        elif match == "match": # Substring match
            [_, field, val] = query

            val = val[1:-1]

            return {field.value: {"$regex": re.escape(val)}}
        elif match == "exact-match": # Exact string match
            (_, field, val) = query

            val = val[1:-1]

            return {field.value: val}
        elif match == "regex-match": # Regular expression match
            (_, field, val) = query

            if val[0] != '/' or val[-1 ] != '/':
                raise Exception("Invalid regex: [%s]" % val)

            val = val[1:-1]

            return {field.value: {"$regex": val}}
        elif match == "has-attachments": # If the email has any attachments

            return {"AttachStatus": True}
        elif match == "file-attached": # If a file with NAME is attached
            [_, field, val] = query

            return {"AttachName": {"$regex": re.escape(val)}}
        else:
            raise Exception("Invalid match %s" % match)

    # Return True iff an action list uses the 'msg' field
    def uses_msg(action_list):
        for action in action_list[1:]:
            if action[0] == "var_test":
                for a in action[1]:
                    if uses_msg(a[(1 if a[0] == "else" else 2)]):
                        return True
            else:
                (_, name, args) = action
                for arg in ((name,) + args):
                    if isinstance(arg, tuple) and arg[0] == "field":
                        return True
                    elif arg.value == "msg":
                        return True

        return False

    # Clean up a query
    def querify(x):
        if isinstance(x, tuple) and x[0] == "match":
            [_, m, a] = x
            a = tuple(querify(x) for x in a)
            return (m.value,) + a
        elif isinstance(x, tuple) and x[0] == "field":
            return x[2]
        else:
            return x

    stack = []
    retlist= []
    
    stack.append((ast, ()))
    while stack:
        (tree, query) = stack.pop()

        if tree[0] == "ifelse":
            for ifs in tree[1:]:

                iquery = querify(ifs[1])

                stack.append((ifs, (iquery if query == () else ("and", query, iquery))))

        elif tree[0] == "if":
            stack.append((tree[2], query))

        elif tree[0] == "actions":
            alist = []
            walk_alist(alist, tree[1:])
            retlist.append((tuple_to_json(query), alist, uses_msg(tree)))

    return (retlist, save_to)
