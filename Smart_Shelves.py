import logging

from flask import Flask, json, render_template
from flask_ask import Ask, request, session, question, statement
import MySQLdb, urllib2

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

cur = db.cursor()

PI_ENDPOINT = "http://smartshelves.ddns.net/api/locate/"

@ask.launch
def launch():
    card_title = render_template('card_title')
    speech_text = render_template('launch')
    return question(speech_text).reprompt(speech_text).simple_card(card_title, speech_text)


@ask.intent('SetItemLocation', mapping={'item': 'Item'})
def set_item(item, location):
    card_title = render_template('card_title')
    cur.execute("SELECT * FROM Items WHERE name=%s", (item,))
    if (cur.fetchone() > 0):
        cur.execute("UPDATE Items SET location=%s WHERE name=%s", (location, item))
    else :
        cur.execute("INSERT INTO Items (name,location) Values(%s, %s)", (item, location)) 
    speech_text = render_template('set_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('GetItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item):
    card_title = render_template('card_title')
    #query database for item, store item in variable called location
    cur.execute("SELECT location, led FROM Items where name=%s", (item,))
    
    result= cur.fetchone()
    location = result[0]
    led = result[1]
    url = PI_ENDPOINT + str(led);
    print (url)
    print (location)
    print (item)
    urllib2.urlopen(url)
    speech_text = render_template('get_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item, location):
    card_title = render_template('card_title')
    #write to database with new item location
    led = 20
    if location == "top shelf":
        led=80
    elif location == "middle shelf":
        led = 50
    elif location == "bottom shelf":
        led = 80
    cur.execute("UPDATE Items SET location=%s, led=%d WHERE name=%s", (location, led, item))
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
