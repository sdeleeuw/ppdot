#!/usr/bin/python

"""
ppdot - Simple Graphviz pre-processor written in Python
Copyright (C) 2014 - 2016  Sander de Leeuw <s.deleeuw@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import unicode_literals
from __future__ import print_function

import argparse
import codecs
import os


comment_indicator = '//-'
command_indicator = '//!'
undo_indent_indicator = '<<'

macro_set = []
style_set = {}

output = None


def process_file(filename):

    with codecs.open(filename, 'r', encoding='utf-8') as file_obj:
        string = file_obj.read()

    process_string(string)

    return os.linesep.join(output)


def process_string(string):

    lines = string.splitlines()
    process_lines(lines)

    return os.linesep.join(output)


def process_lines(lines):

    global output
    output = []

    is_previous_line_blank = True

    for line in lines:

        # strip line separator and whitespace
        line = line.rstrip(os.linesep)
        stripped = line.strip()

        is_current_line_blank = not len(stripped)

        # skip repeating blank lines
        if is_current_line_blank and is_previous_line_blank:
            pass

        # skip comments
        elif stripped.startswith(comment_indicator):
            pass

        # process commands
        elif stripped.startswith(command_indicator):
            stripped = stripped[len(command_indicator):].lstrip()
            process_command(stripped)

        # process graphviz data
        else:

            # undo indent on request
            if stripped.startswith(undo_indent_indicator):
                line = stripped[len(undo_indent_indicator):].lstrip()

            process_graphviz(line)
            is_previous_line_blank = is_current_line_blank

    return os.linesep.join(output)


def process_command(line):

    # split command (first word) from arguments (remainder)
    command = line.split(' ', 1)[0]
    args_str = line[len(command):].lstrip()

    if command == 'include':
        # args_str contains the filename to include
        include_file(args_str)

    elif command == 'define':
        # args_str contains the macro definition:
        # <name> <value>
        name, value = tuple(arg.strip() for arg in args_str.split(' ', 1))
        register_macro(name, value)

    elif command == 'style':
        # args_str contains the style definition:
        # <style> | <attribute> | <value> | <target>

        # apply macros to style definition
        args_str = apply_macros(args_str)

        try:
            args = tuple(arg.strip() for arg in args_str.split('|'))
            register_style(*args)

        except TypeError:
            print('DEBUG: command={}, args_str={}'.format(command, args_str))
            raise

    elif command == 'copy':
        # args_str contains source and destination styles and target filter:
        # <src> <dst> <target filter>
        src, dst, target_filter = tuple(arg.strip() for arg in args_str.split('|'))
        copy_style(src, dst, target_filter)

    else:
        raise Exception('Invalid command: {}'.format(command))


def process_graphviz(line):

    line = apply_macros(line)
    line = apply_styles(line)

    output.append(line)


def include_file(filename):

    # lookup user's home directory
    home = os.path.expanduser('~')

    # accept shell-ish directory variables
    filename = filename.replace('$HOME', home)
    filename = filename.replace('$MACROS', '{}/.ppdot/macros'.format(home))
    filename = filename.replace('$STYLES', '{}/.ppdot/styles'.format(home))

    # process included file
    process_file(filename)


def register_macro(name, value):

    # replace macro if exists
    for index, (n, v) in enumerate(macro_set):
        if n == name:
            macro_set[index] = (name, value)

    # append macro if not exists
    else:
        macro_set.append((name, value))


def apply_macros(line):

    result = line

    # iterate macros reversed to allow nesting
    for name, value in reversed(macro_set):

        # search and replace, that is all
        result = result.replace(name, value)

    return result


def register_style(style, attr, value, target):

    # add style on first assignment
    if style not in style_set.keys():
        style_set[style] = {}

    # add attribute on first assignment
    if attr not in style_set[style].keys():
        style_set[style][attr] = {}

    # update style properties
    if 'graph'[0] in target:
        style_set[style][attr]['graph_value'] = value
    if 'node'[0] in target:
        style_set[style][attr]['node_value'] = value
    if 'edge'[0] in target:
        style_set[style][attr]['edge_value'] = value


def copy_style(src, dst, target_filter):

    for target in ['graph', 'node', 'edge']:

        if target[0] not in target_filter:
            continue

        for attr in style_set[src].keys():

            key = '{}_value'.format(target)

            if key not in style_set[src][attr]:
                continue

            value = style_set[src][attr][key]
            register_style(dst, attr, value, target[0])


def apply_styles(line):

    result = line

    # iterate through style-target combinations
    for style in style_set.keys():
        for target in ['graph', 'node', 'edge']:

            # useful example: n:color_green
            search_for = '{}:{}'.format(target[0], style)
            replace_with = ''

            # construct attr=value statement list for the current target
            for attr in style_set[style].keys():

                key = '{}_value'.format(target)

                if key not in style_set[style][attr]:
                    continue

                value = style_set[style][attr][key]

                if len(replace_with):
                    replace_with = '{}, {}={}'.format(replace_with, attr, value)
                else:
                    replace_with = '{}={}'.format(attr, value)

            # search and replace, that ... never mind
            result = result.replace(search_for, replace_with)

    return result


def jupyter_draw(ppdot_str, format='png', prog='dot'):

    from pygraphviz import AGraph
    from IPython.display import Image

    # convert ppdot to dot format
    dot_str = process_string(ppdot_str)

    # create graph and render image
    graph = AGraph(string=dot_str)
    data = graph.draw(format=format, prog=prog)

    # pass image to IPython/Jupyter
    image = Image(data=data)

    return image



# entry point

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')

    script_args = parser.parse_args()

    result = process_file(script_args.filename)
    print(result)
