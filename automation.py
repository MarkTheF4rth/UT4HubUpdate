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
    please address the advanced options of the config file to use this script
    please leave the update script in the same folder as this file
"""

__author__ = "MII#0255"
__credits__ = ["MII#0255", "skandalouz#1109"]
__license__ = "MIT"
__version__ = "3.2.0"
__mainainer__ = "MII#0255"

import os           # runs user-given command
import sys          # command line args
import psutil       # manages processes
import logging      # saves all changes to log
import time
from updatescript import Update

class logprint():
    """sends all print statements to log"""
    def initialise(self, log_filename):
        self.logger = logging.getLogger('updatescript')
        self.logfile = logging.FileHandler(log_filename)
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


class Admin(Update):
   def automation_main(self, args):
       """main function, makes suitable changes"""
       self.uprint.initialise(self.config['log_path'])
   
       if self.hub_check() and '-f' not in args:
           return
   
       if '-l' not in args:
           self.uprint.disable_logs()
   
       self.hub_stop()
   
       remaining_args = list(set(['-r', '-i', '-p']).intersection(set(args)))
       self.update_main(remaining_args)
   
       os.system(self.config['start_command'])
   
   
   def hub_check(self):
       """checks if the hub is running (does not count lobby instance)
       return true if so, if a ghost process is stumbled on, will kill it"""
   
       for pid in psutil.pids():
           p = psutil.Process(pid)
           if p.name() == self.config['ut_process_name'] and '-server' in p.cmdline():
               if p.ppid() == 1: # ghost process that should be killed
                   p.kill()
                   continue
   
               return True
   
   
   def hub_stop(self):
       """destroy the lobby instance, game instances should fall in line"""
       for pid in psutil.pids():
           p = psutil.Process(pid)
           if p.name() == 'screen' and "LinuxServer" in p.cmdline():
               p.kill()
   

if __name__ == "__main__":
    lprint = logprint()
    automation_update = Admin(lprint)
    automation_update.automation_main(sys.argv[1:])
