#!/usr/bin/python

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

macros = []
styles = {}


def process_file(filename):

    is_prev_line_blank = True

    # process file line by line
    with codecs.open(filename, 'r', encoding='utf-8') as file_obj:
        for line in file_obj:

            # remove line seperators
            line = line.rstrip(os.linesep)

            # remove leading and trailing whitespace
            stripped = line.strip()

            if stripped.startswith(cmd_indicator):

                # line contains preprocessor command
                stripped = stripped[len(cmd_indicator):].lstrip()
                process_command_line(stripped)

            else:

                # line contains graphviz statements
                process_graphviz_line(line, is_prev_line_blank)

                # remember if line is blank for next iteration
                is_prev_line_blank = not len(line)


def process_command_line(line):

    cmd = line.split(' ', 1)[0]
    arg_str = line[len(cmd):].lstrip()

    if cmd == 'include':
        process_include_command(arg_str)

    elif cmd == 'define':
        name, value = [arg.strip() for arg in arg_str.split(' ', 1)]
        process_define_command(name, value)

    elif cmd == 'style':

        try:
            arg_list = [arg.strip() for arg in arg_str.split('|')]
            process_style_command(*arg_list)

        except TypeError:
            print('filename: {0}{3}  cmd: {1}{3}  arg_str: {2}{3}'.format(filename, cmd, arg_str, os.linesep))
            raise

    else:
        raise Exception('Invalid command: {}'.format(cmd))


def process_include_command(filename):

    # accept shell-ish directory variables
    filename = filename.replace('$HOME', home_dir)
    filename = filename.replace('$MACROS', macros_dir)
    filename = filename.replace('$STYLES', styles_dir)

    # process included file
    process_file(filename)


def process_define_command(name, value):

    # replace macro if exists
    for index, (n, v) in enumerate(macros):
        if n == name:
            macros[index] = (name, value)

    # append macro if not exists
    else:
        macros.append((name, value))


def process_style_command(style_name, attr_name, attr_value, target):

    # add style on first assignment
    if not style_name in styles.keys():
        styles[style_name] = {}

    # add attribute on first assignment
    if not attr_name in styles[style_name].keys():
        styles[style_name][attr_name] = {}

    # update style properties
    if 'g' in target:
        styles[style_name][attr_name]['graph_value'] = attr_value
    if 'n' in target:
        styles[style_name][attr_name]['node_value'] = attr_value
    if 'e' in target:
        styles[style_name][attr_name]['edge_value'] = attr_value


def process_graphviz_line(line, is_prev_line_blank=False):

    stripped = line.strip()

    # skip extra empty lines
    if is_prev_line_blank and not len(line):
        return

    # remove indentation on request
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


def apply_macros(line):

    output = line

    # iterate macros reversed to allow nesting
    for name, value in reversed(macros):

        # search and replace, that is all
        output = output.replace(name, value)

    return output


def apply_styles(line):

    output = line

    # iterate through style-target combinations
    for style_name in styles.keys():
        for target in ['g', 'n', 'e']:

            # useful example: n:color_green
            search_for = '{}:{}'.format(target, style_name)
            replace_with = ''

            # construct attr_name=attr_value statement list for the current target
            for attr_name in styles[style_name].keys():

                if target == 'g' and 'graph_value' in styles[style_name][attr_name]:
                    value = styles[style_name][attr_name]['graph_value']
                elif target == 'n' and 'node_value' in styles[style_name][attr_name]:
                    value = styles[style_name][attr_name]['node_value']
                elif target == 'e' and 'edge_value' in styles[style_name][attr_name]:
                    value = styles[style_name][attr_name]['edge_value']
                else:
                    continue

                if len(replace_with):
                    replace_with = '{}, {}={}'.format(replace_with, attr_name, value)
                else:
                    replace_with = '{}={}'.format(attr_name, value)

            # search and replace, that ... never mind
            output = output.replace(search_for, replace_with)

    return output


if len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    print('usage: {} <filename>'.format(sys.argv[0]))
    sys.exit(1)

process_file(filename)

