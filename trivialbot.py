#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

def handle_msg(update, context):
    print(update.message.text)

def main():
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_msg))
    
    updater.start_polling()
    updater.idle()
    

if __name__ == '__main__':
    main()

