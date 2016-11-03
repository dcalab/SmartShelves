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


@ask.intent('SetItemLocation', mapping={'item': 'Item', 'location':'Location_one'})
def set_item(item, location):
    
    print(location)
    card_title = render_template('card_title')
    cur.execute("SELECT * FROM Items WHERE name=%s", (item,))
    if (cur.fetchone() > 0):
        cur.execute("UPDATE Items SET location=%s WHERE name=%s", (location, item))
    else :
        cur.execute("INSERT INTO Items (name,location) Values(%s, %s)", (item, location)) 
    speech_text = render_template('set_response', item=item, location=location)
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('GetItemLocation', mapping={'item':'Item'})
def get_item(item):
    card_title = render_template('card_title')
    #query database for item, store item in variable called location
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


@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location_one', 'location2': 'Location_two'})
def get_item(item, location, location2):
    card_title = render_template('card_title')
    start = location
    end  = location2
    speech_text = ""
    if end != None:
        selectedItemId = checkAndInsertItem(item, start)
        startId = checkAndInsertLocation(start)
        cur.execute("SELECT itemId FROM Items WHERE name=%s and locationId=%s", (item, startId))
        endId = checkAndInsertLocation(end)
        cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, selectedItemId))
        speech_text = render_template('move_response', item=item, location=location2)
    else:
        selectedItemId = checkAndInsertItem(item, "");
        endId = checkAndInsertLocation(end)
        cur.execute("UPDATE Items SET locationId = %s WHERE itemId=%s", (endId, selectItemId))
        speech_text = render_template('move_response', item=item, location=location)
    db.commit()
    return statement(speech_text).simple_card(card_title, speech_text)

def checkAndInsertItem(item, location):
    if location != "":
        locationId = checkAndInsertLocation(location)
        cur.execute("SELECT itemID FROM Items WHERE locationID =%s AND name= %s", (locationId, item));
        results = cur.fetchall()
        if len(result):
            return results[0]
        else: 
            cur.execute("INSERT INTO Items (name, locationId) VALUES (%s, %s)", (item, locationId))
            cur.execute("SELECT ItemId FROM Items WHERE name=%s and locationid=%s", (item, locationId))
            return cur.fetchone()[0]
    else:
        if cur.execute("SELECT itemID FROM Items WHERE name= %s", (item)):
            #check number of existing, if many start conversation
            results = cur.fetchall()
            if len(results) > 1:
                #TODO have conversation if more than one exists to decide which paper towel to move
                print ("which item should we move?")
                return results[0]
        else:
            cur.execute("INSERT INTO Items (locationID, name) VALUES (1, %s)", (item))
            cur.execute("SELECT ItemId FROM Items WHERE name=%s and locationid=1", (item))
            return cur.fetchone()[0]

def checkAndInsertLocation(location):
    if cur.execute("SELECT LocationId FROM Locations WHERE name = %s", (location)):
        return cur.fetchone()[0]
    else:
        cur.execute("INSERT INTO Locations (name, Led) VALUES (%s, 0)", (location))
        #this line might cause a problem, need to get last id
        return cur.lastrowid()

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
