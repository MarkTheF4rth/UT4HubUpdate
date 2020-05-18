Version: 3.4.2

This project deals with updating a UT4 hub connected to UTCC, note that it is unusable without a utcc account set up

there are 2 scripts in this project, "automation" and "updatescript"
- updatescript : this is the main script for updating the hub
- automation : this script is meant for linux crontab automation processes concerning this script
                 it may not run smoothly on windows systems

### Update Script For Dummies
#### Running The Script

The update script has 4 separate flags

| Operand  | Output |
|----------|--------|
| -p | update paks|
| -i | update ini's |
| -r | update rulesets |
| -f | force the hub to shut down and update|
###

Example:
```
python3 automation.py -p -i
```

#### Configuration
To initialise your configuration file, navigate to the project head and run
```
cp Data/config_template.yaml ./config.yaml
```

| Problem                                                            | Solution                                                                                                                                 |
|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| add local paks | append the redirect reference to Data/game_ini.txt|
| remove utcc paks | add a key identifier of what you want to remove to game_ini_omit, e.g "CTF,AS" will remove CTF and assault maps|
| specify rulesets | add the number identifiers to "allowed_rulesets", e.g "64,23" |
| specify a lobby password | input your password to lobby_pw |
###
A list of things you may want to do, and how to achieve them

#### Automation
The automation script is intended to run in cron, it will scan for any running games, and if none exist, it will shut down the server, run updatescript.py, and start the server back up again

If the server is not running when automation.py is run, the server will be started up

To set up automation.py, specify the path to the server under the ```server_loc``` option in the config file
