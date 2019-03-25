Version: 3.4.0

This project deals with updating a UT4 hub connected to UTCC, note that it is unusable without a utcc account set up

there are 2 scripts in this project, "automation" and "updatescript"
- updatescript : this is the main script for updating the hub
- automation : this script is meant for linux automation processes concerning this script
                 it may not run smoothly on windows systems

### Update Script For Dummies
#### Running The Script

| Operand  | Output |
|----------|--------|
| -p | update paks|
| -i | update ini's |
| -r | update rulesets |
| -f | force the hub to shut down and update|
###
If you want to start the server, run the automation script

The update script has 4 separate flags

Example:

python3 automation.py -p -i

#### Configuration

| Problem                                                            | Solution                                                                                                                                 |
|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| add local paks | append the redirect reference to Data/game_ini.txt|
| remove utcc paks | add a key identifier of what you want to remove to game_ini_omit, e.g "CTF,AS" will remove CTF and assault maps|
| specify rulesets | add the number identifiers to "allowed_rulesets", e.g "64,23" |
| specify a lobby password | input your password to lobby_pw |
###
A list of things you may want to do, and how to achieve them
