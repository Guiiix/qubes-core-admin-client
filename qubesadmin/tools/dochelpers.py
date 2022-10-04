#
# The Qubes OS Project, https://www.qubes-os.org/
#
# Copyright (C) 2010-2015  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2014-2015  Wojtek Porczyk <woju@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""Documentation helpers.

This module contains classes and functions which help to maintain documentation,
particularly our custom Sphinx extension.
"""

import argparse
import io
import os
import re

import docutils
import docutils.nodes
import docutils.parsers.rst
import docutils.parsers.rst.roles
import docutils.statemachine
import sphinx
import sphinx.errors
import sphinx.locale
import sphinx.util.docfields
from sphinx.util import logging

import qubesadmin.tools

try:
    log = logging.getLogger(__name__)
except AttributeError:
    log = None

SUBCOMMANDS_TITLE = 'COMMANDS'
OPTIONS_TITLE = 'OPTIONS'


def make_rst_section(heading, char):
    """Format a section header in rst"""
    return '{}\n{}\n\n'.format(heading, char[0] * len(heading))


def prepare_manpage(command):
    """Build a man page skeleton"""
    parser = qubesadmin.tools.get_parser_for_command(command)
    stream = io.StringIO()
    stream.write('.. program:: {}\n\n'.format(command))
    stream.write(make_rst_section(
        ':program:`{}` -- {}'.format(command, parser.description), '='))
    stream.write(""".. warning::

   This page was autogenerated from command-line parser. It shouldn't be 1:1
   conversion, because it would add little value. Please revise it and add
   more descriptive help, which normally won't fit in standard ``--help``
   option.

   After rewrite, please remove this admonition.\n\n""")

    stream.write(make_rst_section('Synopsis', '-'))
    usage = ' '.join(parser.format_usage().strip().split())
    if usage.startswith('usage: '):
        usage = usage[len('usage: '):]

    # replace METAVARS with *METAVARS*
    usage = re.sub(r'\b([A-Z]{2,})\b', r'*\1*', usage)

    stream.write(':command:`{}` {}\n\n'.format(command, usage))

    stream.write(make_rst_section('Options', '-'))

    for action in parser._actions:  # pylint: disable=protected-access
        stream.write('.. option:: ')
        if action.metavar:
            stream.write(', '.join(
                '{}{}{}'.format(option, '=' if option.startswith('--') else ' ',
                                action.metavar) for option in
                sorted(action.option_strings)))
        else:
            stream.write(', '.join(sorted(action.option_strings)))
        stream.write('\n\n   {}\n\n'.format(action.help))

    stream.write(make_rst_section('Authors', '-'))
    stream.write("""\
| Joanna Rutkowska <joanna at invisiblethingslab dot com>
| Rafal Wojtczuk <rafal at invisiblethingslab dot com>
| Marek Marczykowski <marmarek at invisiblethingslab dot com>
| Wojtek Porczyk <woju at invisiblethingslab dot com>

.. vim: ts=3 sw=3 et tw=80
""")

    return stream.getvalue()


class OptionsCheckVisitor(docutils.nodes.SparseNodeVisitor):
    """ Checks if the visited option nodes and the specified args are in sync.
    """

    def __init__(self, command, args, document):
        assert isinstance(args, set)
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.command = command
        self.args = args

    def visit_desc(self, node):
        """ Skips all but 'option' elements """
        # pylint: disable=no-self-use
        if not node.get('desctype', None) == 'option':
            raise docutils.nodes.SkipChildren

    def visit_desc_name(self, node):
        """ Checks if the option is defined `self.args` """
        if not isinstance(node[0], docutils.nodes.Text):
            raise sphinx.errors.SphinxError('first child should be Text')

        arg = str(node[0])
        try:
            self.args.remove(arg)
        except KeyError:
            raise sphinx.errors.SphinxError(
                'No such argument for {!r}: {!r}'.format(self.command, arg))

    def check_undocumented_arguments(self, ignored_options=None):
        """ Call this to check if any undocumented arguments are left.

            While the documentation talks about a
            'SparseNodeVisitor.depart_document()' function, this function does
            not exists. (For details see implementation of
            :py:meth:`NodeVisitor.dispatch_departure()`) So we need to
            manually call this.
        """
        if ignored_options is None:
            ignored_options = set()
        left_over_args = self.args - ignored_options
        if left_over_args:
            raise sphinx.errors.SphinxError(
                'Undocumented arguments for command {!r}: {!r}'.format(
                    self.command, ', '.join(sorted(left_over_args))))


class CommandCheckVisitor(docutils.nodes.SparseNodeVisitor):
    """ Checks if the visited sub command section nodes and the specified sub
        command args are in sync.
    """

    def __init__(self, command, sub_commands, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.command = command
        self.sub_commands = sub_commands

    def visit_section(self, node):
        """ Checks if the visited sub-command section nodes exists and it
            options are in sync.

            Uses :py:class:`OptionsCheckVisitor` for checking
            sub-commands options
        """
        # pylint: disable=no-self-use
        title = str(node[0][0])
        if title.upper() == SUBCOMMANDS_TITLE:
            return

        sub_cmds = [title]
        if '{' in title:
            sub_cmds = title.strip('{}').split(',')

        for cmd in sub_cmds:
            sub_cmd = self.command + ' ' + cmd

            try:
                args = self.sub_commands[cmd]
                options_visitor = OptionsCheckVisitor(
                    sub_cmd, args, self.document)
                node.walkabout(options_visitor)
                options_visitor.check_undocumented_arguments(
                    {'--help', '--quiet', '--verbose', '-h', '-q', '-v'})
                del self.sub_commands[cmd]
            except KeyError:
                raise sphinx.errors.SphinxError(
                    'No such sub-command {!r}'.format(sub_cmd))

    def visit_Text(self, node):
        """ If the visited text node starts with 'alias: ', all the provided
            comma separted alias in this node, are removed from
            `self.sub_commands`
        """
        # pylint: disable=invalid-name
        text = str(node).strip()
        if text.startswith('aliases:'):
            aliases = {a.strip() for a in text.split('aliases:')[1].split(',')}
            for alias in aliases:
                assert alias in self.sub_commands
                del self.sub_commands[alias]

    def check_undocumented_sub_commands(self):
        """ Call this to check if any undocumented sub_commands are left.

            While the documentation talks about a
            'SparseNodeVisitor.depart_document()' function, this function does
            not exists. (For details see implementation of
            :py:meth:`NodeVisitor.dispatch_departure()`) So we need to
            manually call this.
        """
        if self.sub_commands:
            raise sphinx.errors.SphinxError(
                'Undocumented commands for {!r}: {!r}'.format(
                    self.command, ', '.join(sorted(self.sub_commands.keys()))))


class ManpageCheckVisitor(docutils.nodes.SparseNodeVisitor):
    """ Checks if the sub-commands and options specified in the 'COMMAND' and
        'OPTIONS' (case insensitve) sections in sync the command parser.
    """

    def __init__(self, app, command, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        try:
            parser = qubesadmin.tools.get_parser_for_command(command)
        except ImportError:
            msg = 'cannot import module for command'
            if log:
                log.warning(msg)
            else:
                # Handle legacy
                app.warn(msg)

            self.parser = None
            return
        except AttributeError:
            raise sphinx.errors.SphinxError('cannot find parser in module')

        self.command = command
        self.parser = parser
        self.options = set()
        self.sub_commands = {}
        self.app = app

        # pylint: disable=protected-access
        for action in parser._actions:
            if action.help == argparse.SUPPRESS:
                continue

            if issubclass(action.__class__,
                          qubesadmin.tools.AliasedSubParsersAction):
                for cmd, cmd_parser in action._name_parser_map.items():
                    self.sub_commands[cmd] = set()
                    for sub_action in cmd_parser._actions:
                        if sub_action.help != argparse.SUPPRESS:
                            self.sub_commands[cmd].update(
                                sub_action.option_strings)
            else:
                self.options.update(action.option_strings)

    def visit_section(self, node):
        """ If section title is OPTIONS or COMMANDS dispatch the apropriate
            `NodeVisitor`.
        """
        if self.parser is None:
            return

        section_title = str(node[0][0]).upper()
        if section_title == OPTIONS_TITLE:
            options_visitor = OptionsCheckVisitor(self.command, self.options,
                                                  self.document)
            node.walkabout(options_visitor)
            options_visitor.check_undocumented_arguments()
        elif section_title == SUBCOMMANDS_TITLE:
            sub_cmd_visitor = CommandCheckVisitor(
                self.command, self.sub_commands, self.document)
            node.walkabout(sub_cmd_visitor)
            sub_cmd_visitor.check_undocumented_sub_commands()


def check_man_args(app, doctree, docname):
    """ Checks the manpage for undocumented or obsolete sub-commands and
        options.
    """
    dirname, command = os.path.split(docname)
    if os.path.basename(dirname) != 'manpages':
        return

    msg = 'Checking arguments for {!r}'.format(command)
    if log:
        log.info(msg)
    else:
        # Handle legacy
        app.info(msg)
    doctree.walk(ManpageCheckVisitor(app, command, doctree))


def break_to_pdb(app, *_dummy):
    """DEBUG"""
    if not app.config.break_to_pdb:
        return
    import pdb
    pdb.set_trace()


def setup(app):
    """Setup Sphinx extension"""
    app.add_config_value('break_to_pdb', False, 'env')

    app.connect('doctree-resolved', break_to_pdb)
    app.connect('doctree-resolved', check_man_args)

# vim: ts=4 sw=4 et
