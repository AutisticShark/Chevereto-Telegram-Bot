# Chevereto Telegram Bot   
## Installation Guide   
> 1 . Install latest version of Python3.9 & pip   
> 2 . Clone bot file

    git clone https://github.com/M1Screw/Chevereto-Telegram-Bot.git

> 3 . Enter Chevereto-Telegram-Bot folder then install dependency

    pip3.9 install -r requirements.txt

> 4 . Copy config.ini.new to config.ini, then edit it   
> 5 . Run the bot in the background using follow command

    nohup python3.9 bot.py &

## config.ini Explanation 
[BOT]   
MODE = PULLING or WEBHOOK    
ACCESS_TOKEN = Your bot's API key, @botfather to create one if you don't have this.  
WEBHOOK_URL = Your bot's Webhook url, which you can configure it via @botfather, too.   
WEBHOOK_PORT = Due to python-telegram-bot's build-in HTTP server's limite, you can only choose one from 443, 80, 88 or 8443      
WEBHOOK_KEY = Your can create one with follow command    

    openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem    

WEBHOOK_CERT = same as WEBHOOK_KEY    
ADMIN_USER = Your Telegram's username, for example @m1scew_bot (The "@" must be inclueded!), only this user can use bot's admin command like /restart.   
[HOST]   
IMAGE_HOST = The domain name of your image host site(without "https://" part)   
IMAGE_HOST_API_KEY = You can find it on https://your-image-host/dashboard/settings/api   
IMAGE_HOST_RETURN_FORMAT = json
