#!/usr/bin/env python3


"""A simple script to update UT4 hubs
Options:
(no options) : if PORT is not taken (hub isn't running) do all updates
-r           : only update rulesets
-i           : only update ini's
-p           : only update paks

you may use any of these in combination with each other to produce the desired result

NOTE: if you use the automation script, you do not need to pay attention to this one
"""

__author__ = "MII#0255"
__credits__ = ["MII#0255", "skandalouz#1109", "Scoob#7073"]
__license__ = "MIT"
__version__ = "3.2.0"
__mainainer__ = "MII#0255"


import os
import sys                      # command-line args
import hashlib                  # md5sum
import re                       # parse references
import urllib.request           # download
import tempfile                 # ini rewriting
import shutil
import yaml                     # configs


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

class Update:
    def __init__(self, uprint):
        self.uprint = uprint # modified print
        file_path = os.path.dirname(os.path.realpath(__file__))
        raw_config = open(os.path.join(file_path, "config.yaml"))
        self.config = yaml.load(raw_config)
        

        #set paths
        base = self.config['server_loc']
        self.pak_dir = os.path.join(base, self.config['pak_dir_ext'])
        self.ini_path = os.path.join(base, self.config['ini_ext'])
        self.rules_path = os.path.join(base, self.config['ruleset_ext'])

        #initialise data
        self.init_data(file_path)



    def update_main(self, args):
        """runs the update, based on validation and user input"""
    
        output = self.validate()
    
        if not args: # update everything if theres no arguments
            self.uprint('No arguments specified, running full update', 'okblue')
            args = args + ['-r', '-i', '-p']
    
        references = self.download_references() # always get latest references
    
        if '-p' in args:
            if output[0]:
                self.download_new_paks(references)
    
            else:
                # invalid pak directory path error message
                self.uprint('please make sure that self.pak_dir points to a valid'
                        'directory', 'lightred')
    
        if '-i' in args:
            if output[1]:
                self.overwrite_game_ini(references)
    
            else:
                # invalid ini path error message
                self.uprint('please make sure that self.ini_path points to your game ini',
                        'lightred')
    
        if '-r' in args: # update rulesets
            if not output[2]:
                self.uprint('Saving ruleset under new file:{}'.format(self.uprint.wrap(self.rules_path, 'orange')))
    
            self.update_rulesets()

    def init_data(self, file_path):
        """Initialises data dir and creates data file paths"""

        # __default__ will make the data dir generate in the script dir
        if self.config['data_path'] == "__default__":
            self.config['data_path'] = os.path.join(file_path, "Data")
        else:
            self.config['data_path'] = os.path.join(self.config['data_path'], "Data")

        if not os.path.exists(self.config['data_path']):
            # assume data dir hasn't been generated in this case
            try:
                os.mkdir(self.config['data_path'])
            except FileNotFoundError:
                # assume user provided invalid path, critical error
                self.uprint('data path given is invalid, please make sure this points to a valid directory', 'fail')
                sys.exit()

        self.config['log_path'] = os.path.join(self.config['data_path'], self.config['log_path'])
        self.config['cache_path'] = os.path.join(self.config['data_path'], self.config['cache_path'])
        self.config['references'] = os.path.join(self.config['data_path'], self.config['references'])
        
        #initialise cache
        open(self.config['cache_path'], 'a').close()
    
    
    def validate(self):
        """checks file paths and makes sure the program is able to run"""
        # checks file locations
        pak_check = os.path.exists(self.pak_dir)
        ini_check = os.path.isfile(self.ini_path)
        rules_check = os.path.isfile(self.rules_path)
    
        # checks utcc credentials
        passres = True
        errorcode = urllib.error.HTTPError
        try:
            urllib.request.urlopen('http://utcc.unrealpugs.com/rulesets/download?privateCode={}'.format(self.config['private_code']))
        except errorcode:
            self.uprint('private_code is incorrect, please fix this before using this script again', 'fail')
            passres = False
    
        try:
            urllib.request.urlopen('https://utcc.unrealpugs.com/server/{}/supersecretreferencesurl'.format(self.config['server_token']))
        except errorcode:
            self.uprint('server_token is incorrect, please fix this before using this script again', 'fail')
            passres = False
    
        if not passres:
            sys.exit()
    
    
        return pak_check, ini_check, rules_check
    
    
    
    
    def update_rulesets(self):
        """ a new ruleset file based on the info given above"""
        self.uprint('')
        self.uprint('Downloading rulesets', 'magenta')
        url = 'http://utcc.unrealpugs.com/'
        inp = [self.config['server_token']]
        endpoint = 'server/{}/rulesets?'
    
        if self.config['allowed_rulesets']: # if there are any allowed rules, switch to individual ruleset endpoint
            inp = [self.config['private_code'], self.config['allowed_rulesets']]
            endpoint = 'rulesets/download?privateCode={}&rulesets={}&'
    
        url_string = url+endpoint
        
        if self.config['hide_defaults']:
            url_string += "hideDefaults"
    
        open(self.rules_path, 'a') # create file if it isn't already there
        urllib.request.urlretrieve(url_string.format(*inp), self.rules_path)
        self.uprint('Ruleset downloaded to: ' + self.uprint.wrap(self.rules_path, 'cyan'), 'green')
    
    
    
    def download_references(self):
        """downloads the latest ini configuration to "list.txt" and extracts its contents
            NOTE: this will download to cwd"""
        self.uprint('')
        self.uprint('Downloading references', 'magenta')
        url_string = "https://utcc.unrealpugs.com/server/{}/supersecretreferencesurl"
        urllib.request.urlretrieve(url_string.format(self.config['server_token']), self.config['references'])
    
        with open(self.config['references'], 'r') as reference_file:
            self.uprint('References saved to ' + self.uprint.wrap(self.rules_path, 'cyan'))
            return reference_file.readlines()
    
        
    def find_paks(self):
        """returns a dictionary of name:(path, checksum) reading the current pak files
        cross references against current references to see which paks don't need to be updated"""
        self.uprint('')
        self.uprint('Checking current pak files and their checksums (this may take '
                'a while)', 'magenta')
        file_list = [x for x in os.listdir(self.pak_dir) if x.endswith('.pak')]
        file_list.remove('UnrealTournament-LinuxServer.pak') # don't mess with the main pak
        info = {}
    
        edit_times = {x : [os.path.getmtime(os.path.join(self.pak_dir, x))] for x in file_list}
    
        with open(self.config['cache_path'], 'r') as backlog:
            for pak in backlog.readlines():
                pak = pak.split()
                if pak[0] in edit_times and edit_times[pak[0]][0] == float(pak[1]):
                    file_list.remove(pak[0])
                    info.update({pak[0]:(os.path.join(self.pak_dir, pak[0]), pak[2])})
                    edit_times[pak[0]].append(pak[2])
    
            backlog.close()
    
        for file_name in file_list:
            file_path = os.path.join(self.pak_dir, file_name)
            with open(file_path, 'rb') as pakfile:
                md5 = hashlib.md5(pakfile.read()).hexdigest()
    
                edit_times[file_name].append(md5)
                info.update({file_name:(file_path, md5)})
    
    
        with open(self.config['cache_path'], 'w') as backlog:
            for pak_name, pak_info in edit_times.items():
                line = pak_name + ' ' + str(pak_info[0]) + ' ' + pak_info[1] + '\n'
                backlog.write(line)
    
            backlog.close()
    
        self.uprint('... Done', 'green')
    
        return info
    
    
    def download_new_paks(self, references):
        """given a list of references, cross-references with paks for matches 
            and then does the following things:
            ignore any matches
            if an item does not exist in the first list, but does in the second: download it
            for the reverse: if self.config['delete_old'] is set to true, delete the pak"""
        new_paks = self.extract_info(references)
        current_paks = self.find_paks()
    
        to_download = []
        redundant = []
        downloaded = []
    
        for line in new_paks:
            if len(line) < 4:
                print(line)
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
    
                self.uprint('{} - {}'.format(name, action), colour)
                full_url = ptc+'://'+url
                destination = os.path.join(self.pak_dir, name)
                urllib.request.urlretrieve(full_url, destination)
    
                downloaded.append(name)
    
    
        self.uprint('The following has been downloaded:')
        self.uprint('\n'.join(['---' + self.uprint.wrap(x, 'lightred') for x in downloaded]))
        if current_paks and self.config['delete_old']: # remove old paks
            self.uprint('')
            self.uprint('cross reference completed, deleting old paks')
            for redundant_pak_name, items in current_paks.items():
                self.uprint('---deleting {}'.format(self.uprint.wrap(redundant_pak_name, 'lightred')))
                os.remove(items[0])
                
            
    
    
    
    def extract_info(self, reference_list):
        """given a list of references, extract all the information given into a more digestable form"""
        self.uprint('')
        self.uprint('Extracting reference information', 'magenta')
        return_list = []
    
        for reference in reference_list:
            reference_extract = re.findall(r'"([A-Za-z0-9_\./\\-]*)"', reference)
            if len(reference_extract) != 4:
                # failed regex
                continue
            reference_extract[0] = reference_extract[0]+'.pak'
            return_list.append(reference_extract)
    
        self.uprint('... Done', 'green')
    
        return return_list
    
    
    
    
    def overwrite_game_ini(self, references):
        """given a list of references, overwrites the current references in game.ini"""
        self.uprint('')
        self.uprint('Rewriting game ini references', 'magenta')
    
        #Create temp file
        fh, abs_path = tempfile.mkstemp()
        with os.fdopen(fh,'w') as new_file:
            with open(self.ini_path) as old_file:
                for line in old_file:
                    if not line.startswith("RedirectReferences=("):
                        new_file.write(line)
    
            for reference in references:
                new_file.write(reference)
            #Remove original file
            os.remove(self.ini_path)
            #Move new file
            shutil.move(abs_path, self.ini_path)
    
        self.uprint('... Done', 'green')
    
    
    
if __name__ == "__main__":
    cprint = colprint()
    update_script = Update(cprint)
    update_script.update_main(sys.argv[1:])
