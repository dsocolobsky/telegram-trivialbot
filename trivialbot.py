#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import requests
from difflib import SequenceMatcher as seqmatch
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

def sanitize(s) :
    ss = s.upper().replace(" ", "")
    ss = ss.replace("<I>", "").replace("</I>", "")
    ss = ss.replace("-", "").replace(".", "").replace("\'", "")
    return ss

def get_question():
    global current_question
    r = requests.get('http://jservice.io/api/random')
    if r.status_code != 200:
        sys.exit('Error querying the API')

    current_question = r.json()[0]
    qst = current_question['question']
    answer = current_question['answer']
    sanswer = sanitize(answer)
    cat = current_question['category']['title']
    print(f'Category: {cat}\nQuestion: {qst}\nAnswer: {answer} | {sanswer}\n========')

def handle_msg(update, context):
    txt = update.message.text
    if (txt == 'dame'):
        get_question()
    elif current_question:
        ratio = seqmatch(a=sanitize(current_question['answer']), b=sanitize(txt)).ratio()
        print(f'Recibi {txt} y el ratio es {ratio}')
        if (ratio > 0.95):
            print("Correcto!")
            get_question()
            print(current_question['question'])

def main():
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_msg))
    
    print('Bot initialized')
    
    updater.start_polling()
    updater.idle()
    

if __name__ == '__main__':
    main()

