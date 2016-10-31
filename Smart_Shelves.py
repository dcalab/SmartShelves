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

    #TODO update this statement, maybe use join for mutliple locations
    #TODO need name from items table and LED id from locaitons table
    cur.execute("SELECT name, led FROM Locations WHERE LocationID IN (SELECT locationID FROM Items WHERE name=%s)", (item))
    if cur.fetchall() == 0: 
        #no available spots
    else: 
        #list spots available in speech
    result= cur.fetchone()
    location = result[0]
    led = result[1]
    url = PI_ENDPOINT + str(led);
    print (url)
    print (location)
    print (item)
    print (led)
    urllib2.urlopen(PI_ENDPOINT + str(led))
    speech_text = render_template('get_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item, location):
    card_title = render_template('card_title')
    #cur.execute("UPDATE Items SET location=%s WHERE name=%s", (location, item))
    #db.commit()
    #first ensure item location exists in db
    if cur.execute("SELECT LocationID FROM Locations WHERE name=%s", (location)):
        #location is in DB
        #use cur.fetch
        selectId = cur.fetchone()
        cur.execute("UPDATE Items SET location=%s WHERE name=%s", (selectId, item))

    else:
        cur.execute("INSERT INTO Locations (name, Led) OUTPUT INSERTED.LocationID VALUES (%s, 0)", (item))
        cur.execute("UPDATE Items SET LocastionID = LAST_INSERT_ID() WHERE name=%s", (item))
    speech_text = render_template('move_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('GetOpenLocations', mapping={'item': 'Item'})
def get_item(item):
    card_title = render_template('card_title')
    cur.execute("SELECT name FROM Locations WHERE locationID NOT IN (SELECT locationID FROM Items)")
    db.commit()
    if cur.fetchall() == 0: 
        #no available spots
    else: 
        #list spots available in speech
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
