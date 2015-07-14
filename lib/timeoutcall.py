#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This file is part of Hubbot.

Copyright (C) 2015 Red Hat, Inc.

Hubbot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Hubbot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Hubbot.  If not, see <http://www.gnu.org/licenses/>
"""

import os
import signal
import subprocess

def run_check(args, cwd = None, shell = False, kill_tree = True, timeout = -1, env = None):
    ret,stdout,stderr = run(args, cwd, shell, kill_tree, timeout, env)
    if ret != 0:
        raise subprocess.CalledProcessError(ret, args)
    return stdout

def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1, env = None):
    """
    Run a command, forcibly kill it on timeout (in seconds)
    """

    class TimedOut(Exception):
        pass
    def alarm_handler(sig, frame):
        raise TimedOut

    p = subprocess.Popen(args, shell = shell, cwd = cwd,
                         stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = env)
    if timeout > 0:
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        if timeout > 0:
            signal.alarm(0)
    except TimedOut:
        """ Operation timed out """
        pids = [p.pid]
        if kill_tree:
            pids.extend(get_process_children(p.pid))
        for pid in pids:
            """
            process might have stopped already
            avoid OSError: no such process
            """
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        return -9, '', ''
    return p.returncode, stdout, stderr

def get_process_children(pid):
    p = subprocess.Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True,
                          stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]
