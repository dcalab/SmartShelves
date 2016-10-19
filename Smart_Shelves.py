import logging

from flask import Flask
from flask_ask import Ask, request, session, question, statement
import MySQLdb

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

#JINJA keys
ITEM_KEY = "ITEM"
LOCATION_KEY = "LOCATION"

#connect to sql
db = MySQLdb.connect(host="localhost",
                     user="root",
                     passwd="",
                     db="SmartShelves")

cur = db.cursor

@ask.launch
def launch():
    card_title = render_template('card_title')
    speech_text = render_template('launch')
    return question(speech_text).reprompt(speech_text).simple_card(card_title, speech_text)


@ask.intent('SetItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def set_item(item, location):
    card_title = render_template('card_title')
    #write to database with new item location
    speech_text = render_template('set_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('GetItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item):
    card_title = render_template('card_title')
    #query database for item, store item in variable called location
    #location = 
    speech_text = render_template('get_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item, location):
    card_title = render_template('card_title')
    #write to database with new item location
    speech_text = render_template('move_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'You can say hello to me!'
    return question(speech_text).reprompt(speech_text).simple_card('SmartShelves', speech_text)

@ask.intent('AMAZON.StopIntent')
def stop():
    speech_text = 'Thanks for using SmartShelves!'
    return question(speech_text).reprompt(speech_text).simple_card('SmartShelves', speech_text)

@ask.session_ended
def session_ended():
    return "", 200


if __name__ == '__main__':
    app.run(debug=True)