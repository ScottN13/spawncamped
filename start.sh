sudo apt update
sudo apt upgrade -y python3

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


python3 main.py