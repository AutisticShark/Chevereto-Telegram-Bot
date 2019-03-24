# Chevereto Telegram Bot   
## Installation guide   
> 1 . Install latest version of Python3(3.7 or newer) & pip   
> 2 . Clone bot file

    git clone https://github.com/Toxic-Cat/Chevereto-Telegram-Bot.git

> 3 . Enter Chevereto-Telegram-Bot folder then install dependency

    pip3 install -r requirements.txt

> 4 . Copy config.ini.new to config.ini, then edit it   
> 5 . Run bot.py   
## config.ini explanation   
[BOT]   
MODE = PULLING or WEBHOOK(WiP)   
ACCESS_TOKEN = Your bot's API key, @botfather to create one if you don't have this.  
WEBHOOK_URL = Your bot's Webhook url, which you can configure it via @botfather, too.   
ADMIN_USER = Your Telegram's username, for example @m1scew_bot (The "@" must be inclueded!), only this user can use bot's /restart command.   
[HOST]   
IMAGE_HOST = The domain name of your image host site(without "https://" part)   
IMAGE_HOST_API_KEY = You can find it on https://your-image-host/dashboard/settings/api   
IMAGE_HOST_RETURN_FORMAT = json
