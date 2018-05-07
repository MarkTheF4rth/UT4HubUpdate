#!/usr/bin/env python3


"""A simple script to update UT4 hubs
Options:
(no options) : if PORT is not taken (hub isn't running) do all updates
-f           : run all updates, even if the hub is up
-r           : only update rulesets
-i           : only update ini's
-p           : only update paks

you may use any of these in combination with each other to produce the desired result"""

import os
import sys
import time 
import hashlib                  # md5sum
import re                       # parse references
import urllib.request           # download
import tempfile                 # ini rewriting
import shutil
import socket                   # check if server is running


__author__ = "MII#0255"
__credits__ = ["MII#0255", "skandalouz#1109", "Scoob#7073"]
__license__ = "MIT"
__version__ = "1.0.2"
__maintainer__ = "MII#0255"


#TODO THESE MUST BE CHANGED TO THE SUITABLE VALUES
PRIVCODE = "abcdefg"
SERVER_TOKEN = "abcdefg"
ALLOWED_RULES = "1,2,3,4"
HIDE_DEFAULTS = True
REFERENCE_FILENAME = 'references.txt'
PORT = 7777

PURGE_OLD = True # WARNING: set to false if you do not want unlisted paks deleted

HOME_PATH = os.path.split(os.path.realpath(__file__))[0]
PAK_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Content/Paks/")
INI_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/LinuxServer/Game.ini")
RULESET_PATH = os.path.join(HOME_PATH, "LinuxServer/UnrealTournament/Saved/Config/Rulesets/rulesets.json")

class colprint:
    def __init__(self):
        self.header = '\033[95m'
        self.okblue = '\033[94m'
        self.green = '\033[92m'
        self.lightred = '\033[93m'
        self.fail = '\033[91m'
        self.endc = '\033[0m'
        self.bold = '\033[1m'
        self.underline = '\033[4m'
        self.cyan = '\033[36m'
        self.yellow = '\033[33m'
        self.magenta = '\033[35m'

    def wrap(self, string, colour):
        return (getattr(self, colour) + string + self.endc)

    def __call__(self, string, colour):
        print(self.wrap(string, colour))

CPRINT = colprint()


def main(args):
    """runs the update, based on validation and user input"""

    output = validate()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1',PORT))

    if result == 0 and '-f' not in args:
        CPRINT('server appears to be running, use the'
                'argument -f if you would like to ignore this', 'lightred')
        return

    if not args or args == ['-f']: # update everything if theres no arguments or only -f
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
    pak_check = os.path.exists(PAK_PATH)
    ini_check = os.path.isfile(INI_PATH)
    rules_check = os.path.isfile(RULESET_PATH)

    return pak_check, ini_check, rules_check




def update_rulesets():
    """ a new ruleset file based on the info given above"""
    print('')
    CPRINT('Downloading rulesets', 'magenta')
    if HIDE_DEFAULTS:
        url_string = "http://utcc.unrealpugs.com/rulesets/download?privateCode={}&hideDefaults&rulesets={}"
    else:
        url_string = "http://utcc.unrealpugs.com/rulesets/download?privateCode={}&rulesets={}"
    urllib.request.urlretrieve(url_string.format(PRIVCODE, ALLOWED_RULES), RULESET_PATH)
    print('Ruleset downloaded to', CPRINT.wrap(RULESET_PATH, 'cyan'))



def download_references():
    """downloads the latest ini configuration to "list.txt" and extracts its contents
        NOTE: this will download to cwd"""
    print('')
    CPRINT('Downloading references', 'magenta')
    path = os.path.join(HOME_PATH, REFERENCE_FILENAME)
    url_string = "https://utcc.unrealpugs.com/hub/{}/supersecretreferencesurl"
    urllib.request.urlretrieve(url_string.format(SERVER_TOKEN), path)

    with open('references.txt', 'r') as reference_file:
        print('References saved to ' + CPRINT.wrap(path, 'cyan'))
        return reference_file.readlines()
    

def find_paks():
    """returns a dictionary of name:(path, checksum) reading the current pak files"""
    print('')
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


    print('The following has been downloaded:')
    print('\n'.join(['---' + CPRINT.wrap(x, 'lightred') for x in downloaded]))
    if current_paks and PURGE_OLD: # remove old paks
        print('')
        print('cross reference completed, deleting old paks')
        for redundant_pak_name, items in current_paks.items():
            print('---deleting {}'.format(CPRINT.wrap(
                redundant_pak_name, 'lightred')))
            os.remove(items[0])
            
        



def extract_info(reference_list):
    """given a list of references, extract all the information given into a more digestable form"""
    print('')
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
    print('')
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


main(sys.argv[1:])
