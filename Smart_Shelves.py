import logging

from flask import Flask
from flask_ask import Ask, request, session, question, statement


app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)


@ask.launch
def launch():
    speech_text = 'Welcome to Smart Shelves, you can ask where an item is or you can set or move an item'
    return question(speech_text).reprompt(speech_text).simple_card('SmartShelves', speech_text)


@ask.intent('SetItemLocation')
def set_item():
    #speech_text = 'Alright, you have placed {{item}} on {{location}}'
    speech_text = 'Alright, you have placed the paper towel on the top shelf'
    return statement(speech_text).simple_card('SmartShelves', speech_text)

@ask.intent('GetItemLocation')
def get_item():
    speech_text = 'The paper towel is on the top shelf'
    return statement(speech_text).simple_card('SmartShelves', speech_text)

@ask.intent('MoveItemLocation')
def get_item():
    speech_text = 'You have moved the paper towel to the bottom shelf'
    return statement(speech_text).simple_card('SmartShelves', speech_text)

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
