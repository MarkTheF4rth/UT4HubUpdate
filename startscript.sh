#!/bin/bash
NAME=LinuxServer
PORT=7777
STARTMAP=ut-entry
GAMEMODE=lobby
MAXPLAYERS=200
CMD="./UE4Server-Linux-Shipping UnrealTournament ${STARTMAP}?game=${GAMEMODE} maxPlayers=${MAXPLAYERS} -log"

pwd

while getopts ":p:" opt; do
  case ${opt} in
    p )
      PASSWORD="${OPTARG}"
      CMD="./UE4Server-Linux-Shipping UnrealTournament ${STARTMAP}?game=${GAMEMODE}?RequirePassword=1?ServerPassword=${PASSWORD} maxPlayers=${MAXPLAYERS} -log"
      ;;
    \? )
      ;;
  esac
echo ${cmd}
done

ps -eaf | grep $NAME | grep $PORT
if [ $? -eq 1 ]
    then
    echo $CMD
    screen -dm -S $NAME $CMD
else
    echo "$NAME is Already running on port $PORT"
fi

