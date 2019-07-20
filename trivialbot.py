#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, re, random
import requests
from difflib import SequenceMatcher as seqmatch
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import redis

API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

def replace_str_index(text,index,replacement):
    return '%s%s%s'%(text[:index],replacement,text[index+1:])

def sanitize_mild(s):
    ss = s.replace("<i>", "").replace("</i>", "")
    ss = ss.replace("&", "and").replace("\'", "")
    ss = re.sub("[^ a-zA-Z]","", ss)
    print(f'Sanitized: {ss}')
    #ss = ss.replace(",", "").replace(".", "")
    #ss = ss.replace("(", "").replace(")", "")
    #ss = ss.replace("-", "")
    return ss

def sanitize_full(s):
    ss = s.upper().replace(" ", "")
    return ss

class Question():
    def __init__(self, q):
        self.text = q['question']
        self.answer = q['answer']
        self.mild_answer = sanitize_mild(self.answer)
        self.san_answer = sanitize_full(self.mild_answer)
        self.category = q['category']['title']
        self.length = len(self.mild_answer)
        self.masked = re.sub("[^ ]", "*", self.mild_answer)
        self.pista_idx = self.length

    def pista(self):
        if self.pista_idx >= 0:
            ri = random.randint(0, self.length-1)
            i = 0
            while self.masked[ri] != '*':
                ri = random.randint(0, self.length-1)
                i += 1
                if i > self.length:
                    break

            print(f'ri: {ri}')
            if self.masked[ri] != '*':
                print('Nope')
                return None
            else:
                self.masked = replace_str_index(self.masked, ri, self.mild_answer[ri])
                self.pista_idx -= 1
                print('New Masked: {self.masked}')
                return self.masked
        return None

    def check(self, answ):
        return seqmatch(a=sanitize_full(answ), b=self.san_answer).ratio()

    def debug(self):
        return f'Answer: {self.answer} | {self.mild_answer} | {self.san_answer}'

    def __str__(self):
        return f'{self.category} ({self.length} caracteres)\n==========================\n{self.text}'


def get_question(update, context):
    global current_question
    r = requests.get('http://jservice.io/api/random')
    if r.status_code != 200:
        sys.exit('Error querying the API')

    current_question = Question(r.json()[0])
    print(current_question.debug())
    context.bot.send_message(chat_id=update.message.chat_id, text=str(current_question))
    
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
    elif (txt == '!pista' and current_question):
        pista = current_question.pista()
        if pista != None:
            context.bot.send_message(chat_id=update.message.chat_id, text=pista)
    elif current_question:
        ratio = current_question.check(txt)
        print(f'El ratio es {ratio}')
        if (ratio > 0.85):
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
                
            answ = current_question.mild_answer
            msg = f'Correcto {name}! La respuesta era {answ}'
            context.bot.send_message(chat_id=update.message.chat_id, text=msg)

            print_ranking(update, context)
            get_question(update, context)
        elif ratio > 0.75:
            context.bot.send_message(chat_id=update.message.chat_id, text="Alguien esta muy cerca!")

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

