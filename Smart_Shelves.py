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
    cur.execute("SELECT name, led FROM Locations WHERE LocationID IN (SELECT locationID FROM Items WHERE name=%s) ORDER BY LocationId DESC", (item))
    data = cur.fetchall()
    location = ""
    led = ""
    speech_text = ""
    if data: 
        for row in data:
            #list spots available in speech
            #TODO THIS NEEDS TO CHANGE
            #does not currently handle multiple locations on pi, need a "batch signal"
            if row[0] == "unknown":
                break
            print("success")
            location += row[0]
            location += ", "
            led = row[1]
            #urllib2.urlopen(PI_ENDPOINT + str(led))

    if location == "":
        speech_text = render_template('not_found', item=item)
    else:
        speech_text = render_template('get_response', item=item, location=location)

    return statement(speech_text).simple_card(card_title, speech_text)


@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location'})
def get_item(item, location):
    card_title = render_template('card_title')
    #cur.execute("UPDATE Items SET location=%s WHERE name=%s", (location, item))
    #db.commit()
    #first ensure item location exists in db
    if cur.execute("SELECT LocationID FROM Locations WHERE name=%s", (location)):
        #TODO ensure that item moved is the one we want if duplicate in database
        selectId = cur.fetchone()
        print (selectId)
        cur.execute("UPDATE Items SET locationID=%s WHERE name=%s", (selectId, item))

    else:
        cur.execute("INSERT INTO Locations (name, Led) OUTPUT INSERTED.LocationID VALUES (%s, 0)", (item))
        cur.execute("UPDATE Items SET LocastionID = LAST_INSERT_ID() WHERE name=%s", (item))
    db.commit()
    speech_text = render_template('move_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('GetOpenLocations', mapping={'item': 'Item'})
def get_item(item):
    card_title = render_template('card_title')
    cur.execute("SELECT name, led FROM Locations WHERE locationID NOT IN (SELECT locationID FROM Items) ORDER BY LocationID DESC")
    data = cur.fetchall()
    speech_text = ""
    location = ""
    if data: 
        #no available spots
        print("open locations")
        for row in data:
            if row[0] == "unkown":
                break
            location += row[0]
            location += ", "
            led = row[1]
    if location == "":
        speech_text = render_template('no_open_locations')
    else:
        speech_text = render_template('open_locations', location=location)
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
