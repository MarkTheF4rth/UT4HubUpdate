#!/usr/bin/env python3

"""A script designed to automate the update script contained in this package

Using this script requires the non-default psutil python library

When run, the script will shut down the server, run updates, then restart the
server. To automate, run this script in crontab (on linux machines)

Options:
(no options) : if no games on the hub are running, will shut down the lobby
    instance, run the update script, then run the given command

-f : will shut down the hub no matter what is running, then run the given command
-l : will log downloaded and removed content

NOTES:
    please leave the update script in the same folder as this file
"""

import os           # runs user-given command
import sys          # command line args
import psutil       # manages processes
import logging      # saves all changes to log
import updatescript as us

__author__ = "MII#0255"
__credits__ = ["MII#0255", "skandalouz#1109"]
__license = "MIT"
__version__ = "1.0.0"
__mainainer__ = "MII#0255"

#TODO THESE MUST BE CHANGED TO SUITABLE VALUES
us.PRIVCODE = "abcd"
us.SERVER_TOKEN = "abcd"
us.HIDE_DEFAULTS = True
us.REFERENCE_FILENAME = 'references.txt'
LOG_FILENAME = 'update_log.log'
UTSTARTCMD = "./startscript.sh" # command to run when process finishes

# Advanced Options
UTPROCN = "UE4Server-Linux-Shipping"
UTPROCCMD = "/home/server/LinuxServer/Engine/Binaries/Linux/UE4Server-Linux-Shipping"
us.PURGE_OLD = True # WARNING: set to false if you do not want unlisted paks deleted
us.ALLOWED_RULES = '1,2,3,4' # comma separated ruleset numbers, leave blank to have server defaults

us.HOME_PATH = os.path.split(os.path.realpath(__file__))[0]
us.PAK_PATH = os.path.join(us.HOME_PATH, "LinuxServer/UnrealTournament/Content/Paks/")
us.INI_PATH = os.path.join(us.HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/LinuxServer/Game.ini")
us.RULESET_PATH = os.path.join(us.HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/Rulesets/rulesets.json")

class logprint():
    """sends all print statements to log"""
    def __init__(self):
        self.logger = logging.getLogger('updatescript')
        self.logfile = logging.FileHandler(LOG_FILENAME)
        formatter = logging.Formatter('%(asctime)s :  %(message)s')
        self.logfile.setFormatter(formatter)
        self.logger.addHandler(self.logfile)
        self.print_output = False
        self.logger.warning('')
        self.logger.warning('--------- NEW INSTANCE ---------')

    def disable_logs(self):
        """sets log priorities to the highest possible, thus
        disabling any non-critical logs"""
        self.logfile.setLevel(logging.CRITICAL)
        self.print_output = True

    def wrap(self, string, colour=None):
        """replaces the wrap function of colprint, does nothing"""
        return string

    def __call__(self, string, colour=None):
        """logs certain colours, ignore otherwise"""
        if colour == 'fail':
            self.logger.critical(string)
        else:
            self.logger.warning(string)

        if self.print_output:
            print(string)

us.CPRINT = logprint()

def admin_main(args):
    """main function, makes suitable changes"""

    if hub_check() and '-f' not in args:
        return

    if '-l' not in args:
        us.CPRINT.disable_logs()

    hub_stop()

    remaining_args = list(set(['-r', '-i', '-p']).intersection(set(args)))
    us.update_main(remaining_args)

    os.system(UTSTARTCMD)


def hub_check():
    """checks if the hub is running (does not count lobby instance)
    return true if so, if a ghost process is stumbled on, will kill it"""

    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == UTPROCN and UTPROCCMD in p.cmdline():
            if p.ppid() == 1: # ghost process that should be killed
                p.kill()
                continue

            return True


def hub_stop():
    """destroy the lobby instance, game instances should fall in line"""
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == UTPROCN and "ut-entry?game=lobby" in p.cmdline():
            p.kill()

if __name__ == "__main__":
    admin_main(sys.argv[1:])
