#!/usr/bin/python3.7
# coding:utf-8

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functools import wraps
import os
import os.path
import glob
import telegram
import requests
import configparser
import json
import uuid
import mimetypes
import logging

#錯誤logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#加載config
config = configparser.ConfigParser()
config.read('config.ini')

def error(update, error):
    #Log Errors caused by Updates.
    logger.warning('Update "%s" caused error "%s"', update, error)

def send_typing_action(function):
    @wraps(function)
    def command_function(*args, **kwargs):
        bot, update = args
        bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        function(bot, update, **kwargs)
    return command_function

def cache_status(bot, update):
    cache_path = os.getcwd()
    cache_files_count = str(len([name for name in os.listdir(cache_path) if os.path.isfile(os.path.join(cache_path, name))]) - 1)
    cache_files_size = str(cache_files_size_count(cache_path))
    cache_status_message = 'Current cache status:\nCache files count: ' + cache_files_count + '\nCache files size: ' + cache_files_size
    bot.send_message(chat_id = update.message.chat_id, text = cache_status_message)

def cache_files_size_count(cache_path):
    size = 0
    for dirpath, dirnames, filenames in os.walk(cache_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    return size

def cache_clean(bot, update):
    cache_path = os.getcwd()
    cache_files_list = glob.glob(os.path.join(cache_path, "*.jpg"))
    for cache in cache_files_list:
        os.remove(cache) 
    bot.send_message(chat_id=update.message.chat_id, text='All upload cache are cleared')

@send_typing_action
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Send me some pictures or image file. Available format: .jpg, .png, .bmp, .gif, 20MB max file size.')

@send_typing_action
def unknow_msg(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Please send me pictures or image file only!')

@send_typing_action
def image(bot, update):
    image_id = update.message.photo[-1].file_id
    image_name = '%s.jpg' % str(uuid.uuid4())
    image = bot.getFile(image_id)
    image.download(image_name)
    update.message.reply_text('Download complete, now uploading...')
    return_data = image_upload(request_format(image_name))
    if return_data['status_code'] == 200:
        uploaded_info = 'Upload succeeded!\nHere are your links to this image:\nWeb viewer: ' + return_data['image']['url_viewer'] + '\nOrigin size: ' + return_data['image']['url']# + '\n Medium size:' + return_data['medium']['url']
        update.message.reply_text(uploaded_info)
    else:
        update.message.reply_text('Image Host error! Please try again later.')

def image_upload(images):
    image_host = config['HOST']['IMAGE_HOST']
    image_host_api_key = config['HOST']['IMAGE_HOST_API_KEY']
    image_host_return_format = config['HOST']['IMAGE_HOST_RETURN_FORMAT']
    request_url = 'https://' + image_host + '/api/1/upload/?key=' + image_host_api_key + '&format=' + image_host_return_format
    upload_response = requests.post(request_url, files = images)
    print(upload_response)
    return upload_response.json()

def request_format(image_name):
    image_upload_request = []
    image_type = mimetypes.guess_type(image_name)[0]
    image_upload_request.append(('source' , (image_name , open(image_name , 'rb') , image_type)))
    print(image_upload_request)
    return image_upload_request

def main():
    updater = Updater(config['BOT']['ACCESS_TOKEN'])#填你bot的API Key
    dp = updater.dispatcher
    #/start指令處理
    dp.add_handler(CommandHandler("start", start))
    #/cache_status指令處理
    dp.add_handler(CommandHandler("cache_status", cache_status))
    #/cache_clean指令處理
    dp.add_handler(CommandHandler("cache_clean", cache_clean))
    #處理用戶發送的圖片
    image_handler = MessageHandler(Filters.photo, image)
    dp.add_handler(image_handler)
    #處理用戶私聊發送的未知訊息
    unknow_msg_handler = MessageHandler(Filters.private, unknow_msg)
    dp.add_handler(unknow_msg_handler)
    #添加錯誤logging
    dp.add_error_handler(error)
    #啓動進程
    updater.start_polling()

if __name__ == '__main__':
    main()
