# -*- coding: iso-8859-1 -*-
import os
import subprocess

basedir = os.path.dirname(__file__)
wokdir = os.path.dirname(basedir)
wok_cmd = os.path.join(wokdir, "wok")


def run (cmd, verbosity=0, **kwargs):
    """Run command without error checking.
    @return: command return code"""
    if kwargs.get("shell"):
        # for shell calls the command must be a string
        cmd = " ".join(cmd)
    return subprocess.call(cmd, **kwargs)


def run_checked (cmd, ret_ok=(0,), **kwargs):
    """Run command and raise OSError on error."""
    retcode = run(cmd, **kwargs)
    if retcode not in ret_ok:
        msg = "Command `%s' returned non-zero exit status %d" % (cmd, retcode)
        raise OSError(msg)
    return retcode
