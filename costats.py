import requests
import json
import os
import logging
import time
import random

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError

updater = Updater(os.environ.get("TELEGRAM_TOKEN"))
dispatcher = updater.dispatcher
logging.basicConfig(level=logging.DEBUG)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
TIME = time.time()

# For handling rate limiting, updating the contents at 30 minutes interval
ISS = ""
PR = ""

# CommandHandlers
# ---------------

def start(bot, update):
    logging.debug("start invoked...")
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Hi! I am a bot that provides some misc. information about coala.")

def stop(bot, update):
    logging.debug("stop invoked...")
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Bye! Hope to see you soon.")

def stats(bot, update, args):
    logging.debug("stats invoked...")
    try:
        if len(args) > 1:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Incorrect Usage.\nUsage is as: /stats <username>")
        username = args[0].strip()
    finally:
        logging.debug("args passed: " + str(args))
        rq = requests.get("http://webservices.coala.io/contrib")
        stats = rq.json()
        found = False
        for i in stats:
            try:
                if i["login"] == username:
                    logging.debug(str(i))
                    found = True
                    msg = ("*Reviews*: " + str(i["reviews"]) +
                          "\n*Commits*: " + str(i["contributions"]) +
                          "\n*Issues opened*:" + str(i["issues"]))
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=msg,
                                    parse_mode=telegram.ParseMode.MARKDOWN)
            except err:
                bot.sendMessage(chat_id=update.message.chat_id, text="An unknown error occured...\n Please report  at github.com/meetmangukiya/costats")
                bot.sendMessage(chat_id=update.message.chat_id, text=err)
        if not found:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Information about the user {} *not* found.".format(username) +
                                 "\nPlease check the username.")

def rand(bot, update, args):
    logging.debug("rand invoked...")
    end = "https://api.github.com/"

    try:
        if len(args) > 1:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Incorrect Usage.\nUsage is as: /rand [issue, is, pr, pull]")
        cmp = args[0].strip() # cmp - Component
    finally:
        logging.debug("args passed: " + str(args))
        typ = "issue" if cmp.lower() in ["issue", "is"] else 'pr label:"process/pending review"' if cmp.lower() in ["pr", "pull"] else ""
        if typ:
            params = {
                "q": "type:{} user:coala is:open".format(typ)
            }

            global TIME, ISS, PR
            if time.time() - TIME > 1800 or not (ISS if typ is "issue" else PR):
                TIME = time.time()
                rq = requests.get(end + "search/issues", params=params, headers = {"Authorization": "token {}".format(GITHUB_TOKEN)})
                logging.debug("Sent request..\n Status Code: {}".format(rq.status_code))
                issues = rq.json()
                if typ == "issue":
                    ISS = issues
                else:
                    PR = issues
            else:
                issues = PR if "pr" in typ else ISS
            logging.debug("issues: " + str(issues))
            iss = issues["items"][random.randint(0, len(issues) - 1) ]
            logging.debug("iss: " + str(iss))

            msg = iss["html_url"] + "\n" + iss["title"] + "\n" + (iss["body"] if typ is "issue" else "")
            logging.debug("msg: " + str(msg))
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=msg)
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Incorrect Usage.\nUsage is as: /rand [issue, is, pr, pull]")


# Registering the handlers
# ------------------------

start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)
stats_handler = CommandHandler('stats', stats, pass_args=True)
rand_handler = CommandHandler('rand', rand, pass_args=True)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(stop_handler)
dispatcher.add_handler(stats_handler)
dispatcher.add_handler(rand_handler)

updater.start_polling()
