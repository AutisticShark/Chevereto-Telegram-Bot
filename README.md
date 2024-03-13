# Chevereto Telegram Bot

An easy-to-use telegram bot for your Chevereto site.    

![7253cf6c16296b27e9a6417a294c830d.png](https://i.jpg.dog/7253cf6c16296b27e9a6417a294c830d.png)
## Installation Guide   
> 1 . Install Python3.10+ & pip   
> 2 . Clone bot file   

    git clone https://github.com/M1Screw/Chevereto-Telegram-Bot.git

> 3 . Install dependency(Use venv if you want to keep your system clean)   

    pip install -r requirements.txt

> 4 . Copy config.ini.new to config.ini, then edit it   
> 5 . Run bot   

    nohup python3 bot.py &

## config.ini Example 
[BOT]   
MODE = PULLING or WEBHOOK    
ACCESS_TOKEN = Your bot's API key. Talk to @botfather to create one if you don't have it.  
WEBHOOK_URL = Your bot's Webhook URL  
WEBHOOK_SSL = True or False, if your bot is behind reverse proxy with SSL enabled, this can be set to False.
WEBHOOK_KEY = You can create one with the following command    

    openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 3650 -out cert.pem    

WEBHOOK_CERT = same as WEBHOOK_KEY    
ADMIN_USER = Your Telegram's user id, only this user can use the bot's admin command for example /cache.   
[HOST]   
IMAGE_HOST = The domain name of your image host site(without "https://" part)   
IMAGE_HOST_API_KEY = You can find it on https://your-image-host/dashboard/settings/api   
IMAGE_HOST_RETURN_FORMAT = json
