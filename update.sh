#!/bin/bash

source bot-env/bin/activate

# Ask if they would like to update python3 before running the bot
read -t 5 -p "Would you like to update python3 before running the bot? (y/n): " update_python
if [[ "$update_python" != "y" && "$update_python" != "n" ]]; then
    echo "Invalid input. Please enter 'y' or 'n'."
    exit 1
fi
if [ "$update_python" == "y" ]; then
    echo "Updating python3..."
else
    echo "Skipping python3 update."
fi
if [ "$update_python" == "y" ]; then
    sudo apt update
    sudo apt upgrade -y python3
fi


## Check to see if there are any new changes to main repo (ScottN13/spawncamped)
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ $LOCAL != $REMOTE ]; then
    echo "New update found. Updating code..."
    git pull origin main
else
    echo "No updates found. Continuing to start the bot."
fi

echo ""
echo "--------------------------------"
echo ""

nohup python3 main.py