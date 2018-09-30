#!/usr/bin/env python3


"""A simple script to update UT4 hubs
Options:
(no options) : if PORT is not taken (hub isn't running) do all updates
-r           : only update rulesets
-i           : only update ini's
-p           : only update paks

you may use any of these in combination with each other to produce the desired result

NOTE: IF YOU ARE USING THE ADMIN SCRIPT, YOU DO NOT NEED TO EDIT THIS ONE
"""

import os
import sys                      # command-line args
import hashlib                  # md5sum
import re                       # parse references
import urllib.request           # download
import tempfile                 # ini rewriting
import shutil


__author__ = "MII#0255"
__credits__ = ["MII#0255", "skandalouz#1109", "Scoob#7073"]
__license__ = "MIT"
__version__ = "2.1.0"
__maintainer__ = "MII#0255"


#TODO THESE MUST BE CHANGED TO THE SUITABLE VALUES
PRIVCODE = "abcd"
SERVER_TOKEN = "abcd"
HIDE_DEFAULTS = True
REFERENCE_FILENAME = 'references.txt' # references section of game ini
BACKLOG_FILENAME = 'backlog.txt'      # history file to prevent paks from being constantly re-assessed


#Advanced Options
PURGE_OLD = True # WARNING: set to false if you do not want unlisted paks deleted
ALLOWED_RULES = ''

HOME_PATH = 'os.path.split(os.path.realpath(__file__))[0]'
PAK_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Content/Paks/")
INI_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/LinuxServer/Game.ini")
RULESET_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/Rulesets/rulesets.json")

open(BACKLOG_FILENAME, 'a').close() # create backlog txt file

class colprint:
    def __init__(self):
        self.empty = ''
        self.okblue = '\033[94m' # header
        self.green = '\033[92m' # confirmation
        self.lightred = '\033[93m' # warnings
        self.cyan = '\033[36m' # locations
        self.yellow = '\033[33m' # outdated content
        self.magenta = '\033[35m' # action
        self.fail = '\033[91m'    # critical failure
        self.header = '\033[95m'  #   |
        self.bold = '\033[1m'     #   |
        self.underline = '\033[4m'#   |

        self.endc = '\033[0m' # applied to end of string

    def wrap(self, string, colour='empty'):
        return (getattr(self, colour) + string + self.endc)

    def __call__(self, string, colour='empty'):
        print(self.wrap(string, colour))

CPRINT = colprint()


def update_main(args):
    """runs the update, based on validation and user input"""

    output = validate()

    if not args: # update everything if theres no arguments
        CPRINT('No arguments specified, running full update', 'okblue')
        args = args + ['-r', '-i', '-p']

    references = download_references() # always get latest references

    if '-p' in args:
        if output[0]:
            download_new_paks(references)

        else:
            # invalid pak directory path error message
            CPRINT('please make sure that PAK_PATH points to a valid'
                    'directory', 'lightred')

    if '-i' in args:
        if output[1]:
            overwrite_game_ini(references)

        else:
            # invalid ini path error message
            CPRINT('please make sure that INI_PATH points to your game ini',
                    'lightred')

    if '-r' in args: # update rulesets
        if not output[2]:
            CPRINT('Saving ruleset under new file:'
                    '{}'.format(CPRINT.wrap(RULESET_PATH, 'orange')))

        update_rulesets()


def validate():
    """checks file paths and makes sure the program is able to run"""
    # checks file locations
    pak_check = os.path.exists(PAK_PATH)
    ini_check = os.path.isfile(INI_PATH)
    rules_check = os.path.isfile(RULESET_PATH)

    # checks utcc credentials
    passres = True
    errorcode = urllib.error.HTTPError
    try:
        urllib.request.urlopen('http://utcc.unrealpugs.com/rulesets/download?privateCode={}'.format(PRIVCODE))
    except errorcode:
        CPRINT('PRIVCODE is incorrect, please fix this before using this script again', 'fail')
        passres = False

    try:
        urllib.request.urlopen('https://utcc.unrealpugs.com/server/{}/supersecretreferencesurl'.format(SERVER_TOKEN))
    except errorcode:
        CPRINT('SERVER_TOKEN is incorrect, please fix this before using this script again', 'fail')
        passres = False

    if not passres:
        sys.exit()


    return pak_check, ini_check, rules_check




def update_rulesets():
    """ a new ruleset file based on the info given above"""
    CPRINT('')
    CPRINT('Downloading rulesets', 'magenta')
    url = 'http://utcc.unrealpugs.com/'
    inp = [SERVER_TOKEN]
    endpoint = 'server/{}/rulesets?'

    if ALLOWED_RULES: # if there are any allowed rules, switch to individual ruleset endpoint
        inp = [PRIVCODE, ALLOWED_RULES]
        endpoint = 'rulesets/download?privateCode={}&rulesets={}&'

    url_string = url+endpoint
    
    if HIDE_DEFAULTS:
        url_string += "hideDefaults"

    CPRINT(url_string.format(*inp), 'green')
    open(RULESET_PATH, 'a') # create file if it isn't already there
    urllib.request.urlretrieve(url_string.format(*inp), RULESET_PATH)
    CPRINT('Ruleset downloaded to', CPRINT.wrap(RULESET_PATH, 'cyan'))



def download_references():
    """downloads the latest ini configuration to "list.txt" and extracts its contents
        NOTE: this will download to cwd"""
    CPRINT('')
    CPRINT('Downloading references', 'magenta')
    path = os.path.join(HOME_PATH, REFERENCE_FILENAME)
    url_string = "https://utcc.unrealpugs.com/server/{}/supersecretreferencesurl"
    urllib.request.urlretrieve(url_string.format(SERVER_TOKEN), path)

    with open('references.txt', 'r') as reference_file:
        CPRINT('References saved to ' + CPRINT.wrap(path, 'cyan'))
        return reference_file.readlines()
    
def xfind_paks():
    """returns a dictionary of name:(path, checksum) reading the current pak files
    cross references against current references to see which paks don't need to be updated"""
    CPRINT('')
    CPRINT('Checking current pak files and their checksums (this may take '
            'a while)', 'magenta')
    file_list = [x for x in os.listdir(PAK_PATH) if x.endswith('.pak')]
    file_list.remove('UnrealTournament-LinuxServer.pak') # don't mess with the main pak
    info = {}

    edit_times = {x : [os.path.getmtime(os.path.join(PAK_PATH, x))] for x in file_list}

    with open(BACKLOG_FILENAME, 'r') as backlog:
        for pak in backlog.readlines():
            pak = pak.split()
            if pak[0] in edit_times and edit_times[pak[0]][0] == float(pak[1]):
                file_list.remove(pak[0])
                info.update({pak[0]:(os.path.join(PAK_PATH, pak[0]), pak[2])})
                edit_times[pak[0]].append(pak[2])

        backlog.close()

    for file_name in file_list:
        file_path = os.path.join(PAK_PATH, file_name)
        with open(file_path, 'rb') as pakfile:
            md5 = hashlib.md5(pakfile.read()).hexdigest()

            edit_times[file_name].append(md5)
            info.update({file_name:(file_path, md5)})


    with open(BACKLOG_FILENAME, 'w') as backlog:
        for pak_name, pak_info in edit_times.items():
            line = pak_name + ' ' + str(pak_info[0]) + ' ' + pak_info[1] + '\n'
            backlog.write(line)

        backlog.close()

    CPRINT('... Done', 'green')

    return info


def find_paks(file_list):
    """returns a dictionary of name:(path, checksum) reading the current pak files"""
    CPRINT('')
    CPRINT('Checking current pak files and their checksums (this may take '
            'a while)', 'magenta')
    file_list = [x for x in os.listdir(os.path.join(HOME_PATH, PAK_PATH)) if x.endswith('.pak')]
    file_list.remove('UnrealTournament-LinuxServer.pak') # don't mess with the main pak
    info = {}

    for file_name in file_list:
        file_path = os.path.join(PAK_PATH, file_name)
        with open(file_path, 'rb') as pakfile:
            md5 = hashlib.md5(pakfile.read()).hexdigest()

        info.update({file_name:(file_path, md5)})

    CPRINT('... Done', 'green')

    return info

    
def download_new_paks(references):
    """given a list of references, cross-references with paks for matches 
        and then does the following things:
        ignore any matches
        if an item does not exist in the first list, but does in the second: download it
        for the reverse: if PURGE_OLD is set to true, delete the pak"""
    new_paks = extract_info(references)
    current_paks = find_paks()

    to_download = []
    redundant = []
    downloaded = []

    for line in new_paks:
        name, ptc, url, md5 = line
        if name in current_paks and current_paks[name][1] == md5:
            del(current_paks[name])
            continue

        else:
            action = 'downloading'
            colour = 'lightred'

            if name in current_paks:
                action = 'outdated'
                colour = 'yellow'
                os.remove(current_paks[name][0])
                del(current_paks[name])

            CPRINT('{} - {}'.format(name, action), colour)
            full_url = ptc+'://'+url
            destination = os.path.join(PAK_PATH, name)
            urllib.request.urlretrieve(full_url, destination)

            downloaded.append(name)


    CPRINT('The following has been downloaded:')
    CPRINT('\n'.join(['---' + CPRINT.wrap(x, 'lightred') for x in downloaded]))
    if current_paks and PURGE_OLD: # remove old paks
        CPRINT('')
        CPRINT('cross reference completed, deleting old paks')
        for redundant_pak_name, items in current_paks.items():
            CPRINT('---deleting {}'.format(CPRINT.wrap(redundant_pak_name, 'lightred')))
            os.remove(items[0])
            
        



def extract_info(reference_list):
    """given a list of references, extract all the information given into a more digestable form"""
    CPRINT('')
    CPRINT('Extracting reference information', 'magenta')
    return_list = []

    for reference in reference_list:
        reference_extract = re.findall(r'"([A-Za-z0-9_\./\\-]*)"', reference)
        reference_extract[0] = reference_extract[0]+'.pak'
        return_list.append(reference_extract)

    CPRINT('... Done', 'green')

    return return_list




def overwrite_game_ini(references):
    """given a list of references, overwrites the current references in game.ini"""
    CPRINT('')
    CPRINT('Rewriting game ini references', 'magenta')

    #Create temp file
    fh, abs_path = tempfile.mkstemp()
    with os.fdopen(fh,'w') as new_file:
        with open(INI_PATH) as old_file:
            for line in old_file:
                if not line.startswith("RedirectReferences=("):
                    new_file.write(line)

        for reference in references:
            new_file.write(reference)
        #Remove original file
        os.remove(INI_PATH)
        #Move new file
        shutil.move(abs_path, INI_PATH)

    CPRINT('... Done', 'green')


if __name__ == "__main__":
    update_main(sys.argv[1:])
