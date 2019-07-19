#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import requests
from difflib import SequenceMatcher as seqmatch
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import redis

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

def sanitize(s) :
    ss = s.upper().replace(" ", "")
    ss = ss.replace("<I>", "").replace("</I>", "")
    ss = ss.replace("-", "").replace(".", "").replace("\'", "")
    ss = ss.replace("(", "").replace(")", "")
    ss = ss.replace(",", "").replace("&", "")
    return ss

def get_question(update, context):
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
    
    context.bot.send_message(chat_id=update.message.chat_id, text=f'{cat}\n================\n{qst}')
    
def print_ranking(update, context):
    msg = 'Ranking Actual\n===========\n'
    ranking = db.zrevrange('ranking', 0, -1, withscores=True)
    for rank in ranking:
        name = db.get(rank[0]).decode('utf-8')
        score = int(rank[1])
        msg = msg + f'{name}: {score}\n'
        
    context.bot.send_message(chat_id=update.message.chat_id, text=msg)

def handle_msg(update, context):
    global db
    txt = update.message.text
    if (txt == '!ranking'):
        print_ranking(update, context)
    elif (txt == '!dame' and update.message.from_user.id == 470689485):
        get_question(update, context)
    elif current_question:
        answer = current_question['answer']
        ratio = seqmatch(a=sanitize(answer), b=sanitize(txt)).ratio()
        print(f'Recibi {txt} y el ratio es {ratio}')
        if (ratio > 0.95):
            usr = update.message.from_user
            usrid = str(usr.id)
            n = db.zadd('ranking', {usrid: '1'}, incr=True)
            # Nuestro usuario no existia en la DB
            if n == 1.0:
                if usr.last_name != None:
                    name = usr.first_name + usr.last_name
                else:
                    name = usr.first_name
                db.set(usrid, name)
            else:
                name = db.get(usrid).decode('utf-8')
                
            msg = f'Correcto {name}! La respuesta era {answer}'
            context.bot.send_message(chat_id=update.message.chat_id, text=msg)
            print_ranking(update, context)
            get_question(update, context)
            print(current_question['question'])
        elif ratio > 0.90:
            print("Alguien esta muy cerca!")

def main():
    global db
    db = redis.StrictRedis(host="localhost", port=6379, db=0, socket_keepalive=True, socket_timeout=300)
    print(f'db: {db}')
    
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text, handle_msg))
    
    print('Bot initialized')
    
    updater.start_polling()
    updater.idle()
    

if __name__ == '__main__':
    main()

