#!/usr/bin/python

"""
ppdot - Simple Graphviz pre-processor written in Python
Copyright (C) 2014  Sander de Leeuw <s.deleeuw@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import unicode_literals
from __future__ import print_function

import codecs
import os
import sys

cmd_indicator = '//!'
undo_indent_indicator = '<<'

home_dir = os.path.expanduser('~')
macros_dir = os.path.expanduser('~/.ppdot/macros')
styles_dir = os.path.expanduser('~/.ppdot/styles')

macros_set = []
styles_set = {}


def process_file(filename):

    is_prev_line_blank = True

    # process file line by line
    with codecs.open(filename, 'r', encoding='utf-8') as file_obj:
        for line in file_obj:

            # remove line seperator
            line = line.rstrip(os.linesep)

            # remove leading and trailing whitespace
            stripped = line.strip()

            if stripped.startswith(cmd_indicator):

                # line contains preprocessor command
                stripped = stripped[len(cmd_indicator):].lstrip()
                process_command(stripped)

            else:

                # line contains graphviz data
                process_graphviz(line, is_prev_line_blank)

                # remember if line is blank
                is_prev_line_blank = not len(line)


def process_command(line):

    # split command (first word) from arguments
    cmd = line.split(' ', 1)[0]
    arg_str = line[len(cmd):].lstrip()

    if cmd == 'include':
        # arg_str contains the filename to include
        include_file(arg_str)

    elif cmd == 'define':
        # arg_str contains the macro definition:
        # <name> <value>
        name, value = [arg.strip() for arg in arg_str.split(' ', 1)]
        register_macro(name, value)

    elif cmd == 'style':

        # arg_str contains the style definition:
        # <style> | <attribute> | <value> | <target>

        try:
            arg_list = [arg.strip() for arg in arg_str.split('|')]
            register_style(*arg_list)

        except TypeError:
            print('filename: {0}{3}  cmd: {1}{3}  arg_str: {2}{3}'.format(
                filename, cmd, arg_str, os.linesep))
            raise

    else:
        raise Exception('Invalid command: {}'.format(cmd))


def process_graphviz(line, is_prev_line_blank=False):

    stripped = line.strip()

    # skip extra empty lines
    if is_prev_line_blank and not len(line):
        return

    # remove indentation if indicated
    if stripped.startswith(undo_indent_indicator):
        output = stripped[len(undo_indent_indicator):].lstrip()
    else:
        output = line

    # apply macros
    output = apply_macros(output)

    # apply styles
    output = apply_styles(output)

    # print to stdout
    print(output)


def include_file(filename):

    # accept shell-ish directory variables
    filename = filename.replace('$HOME', home_dir)
    filename = filename.replace('$MACROS', macros_dir)
    filename = filename.replace('$STYLES', styles_dir)

    # process included file
    process_file(filename)


def register_macro(name, value):

    # replace macro if exists
    for index, (n, v) in enumerate(macros_set):
        if n == name:
            macros_set[index] = (name, value)

    # append macro if not exists
    else:
        macros_set.append((name, value))


def apply_macros(line):

    output = line

    # iterate macros reversed to allow nesting
    for name, value in reversed(macros_set):

        # search and replace, that is all
        output = output.replace(name, value)

    return output


def register_style(style, attr, value, target):

    # add style on first assignment
    if not style in styles_set.keys():
        styles_set[style] = {}

    # add attribute on first assignment
    if not attr in styles_set[style].keys():
        styles_set[style][attr] = {}

    # update style properties
    if 'graph'[0] in target:
        styles_set[style][attr]['graph_value'] = value
    if 'node'[0] in target:
        styles_set[style][attr]['node_value'] = value
    if 'edge'[0] in target:
        styles_set[style][attr]['edge_value'] = value


def apply_styles(line):

    output = line

    # iterate through style-target combinations
    for style in styles_set.keys():
        for target in ['graph', 'node', 'edge']:

            # useful example: n:color_green
            search_for = '{}:{}'.format(target[0], style)
            replace_with = ''

            # construct attr=value statement list for the current target
            for attr in styles_set[style].keys():

                key = '{}_value'.format(target)

                if key not in styles_set[style][attr]:
                    continue

                value = styles_set[style][attr][key]

                if len(replace_with):
                    replace_with = '{}, {}={}'.format(replace_with, attr, value)
                else:
                    replace_with = '{}={}'.format(attr, value)

            # search and replace, that ... never mind
            output = output.replace(search_for, replace_with)

    return output


# entry point

if len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    print('usage: {} <filename>'.format(sys.argv[0]))
    sys.exit(1)

process_file(filename)

