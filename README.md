# Chevereto-Telegram-Bot   
## Installation guide   
> 1 . Install latest version of Python3(3.7 or newer) & pip   
> 2 . Clone bot file

    git clone https://github.com/SuicidalCat/Chevereto-Telegram-Bot.git

> 3 . Enter Chevereto-Telegram-Bot folder then install dependency

    pip3 install -r requirements.txt

> 4 . Copy config.ini.new to config.ini, then edit it   
> 5 . Run bot.py   
## config.ini explanation   
[BOT]   
MODE = PULLING or WEBHOOK(gugugu)   
ACCESS_TOKEN = Your bot's API key, if you don't have it, @botfather to create one!   
WEBHOOK_URL = Your bot's Webhook url, which you can configure it via @botfather   
[HOST]   
IMAGE_HOST = The domain name of your image host site(without "https://" part)   
IMAGE_HOST_API_KEY = You can find it in https://your-image-host/dashboard/settings/api   
IMAGE_HOST_RETURN_FORMAT = json