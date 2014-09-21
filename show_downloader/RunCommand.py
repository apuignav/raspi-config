#!/usr/bin/env python
# =============================================================================
# @file run_command.py
# @author Albert Puig Navarro (albert.puig@cern.ch)
# @date 2011-07-25
# =============================================================================
"""
"""

__author__ = "Albert Puig (albert.puig@cern.ch)"

def run_command(cmd, *args):
    """Run given command with args on the command line.

    @arg  cmd: command to execute
    @type cmd: string
    @arg  args: arguments of the command
    @type args: list

    @return: list of lines of the output

    """
    import subprocess
    return [line for line in subprocess.Popen([cmd]+list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].split('\n') if line]

def run_command_with_pipe(cmd1, args1, cmd2, args2):
    """Run given command piping its result to another one.

    Sequence run is equivalent to:
        $ cmd1 args1 | cmd2 args2

    @arg  cmd1: first command to run
    @type cmd1: string
    @arg  args1: arguments of the first command
    @type args1: list
    @arg  cmd2: second command to run
    @type cmd2: string
    @arg  args2: arguments of the second command
    @type args2: list

    @return: list of lines of the output

    """
    import subprocess
    if not args1:
        args1 = []
    if not args2:
        args2 = []
    if not isinstance(args1, (tuple, list)):
        args1 = [args1]
    if not isinstance(args2, (tuple, list)):
        args2 = [args2]
    #print "About to execute: %s | %s" %(' '.join([cmd1]+args1), ' '.join([cmd2]+args2))
    p1 = subprocess.Popen([cmd1]+args1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen([cmd2]+args2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    # return p2.communicate()[0].split('\n')
    return [line for line in p2.communicate()[0].split('\n') if line]

# EOF
