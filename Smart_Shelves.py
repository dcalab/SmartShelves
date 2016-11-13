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

db.autocommit(True)
cur = db.cursor()

#PI_ENDPOINT = "http://smartshelves.ddns.net/api/locate/"
PI_ENDPOINT = "http://eb3f06ba.ngrok.io/api/locate/"

@ask.launch
def launch():
    card_title = render_template('card_title')
    speech_text = render_template('launch')
    return question(speech_text).reprompt(speech_text).simple_card(card_title, speech_text)


@ask.intent('SetItemLocation', mapping={'item': 'Item', 'location':'Location_one'})
def set_item(item, location):
    print("in set item")
    print(item)
    card_title = render_template('card_title')
    itemId = checkAndInsertItem(item, "")
    endId = checkAndInsertLocation(location)
    print("endId = "+ str(endId))
    cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, itemId))
    db.commit()
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
        led += str(len(data))
        for row in data:
            #list spots available in speech
            #TODO THIS NEEDS TO CHANGE
            #does not currently handle multiple locations on pi, need a "batch signal"
            if row[0] == "unknown":
                led += str(row[1])
                break
            print("success")
            location += row[0]
            location += ", "
            led += str(row[1])

    if location == "":
        led = "0"
        speech_text = render_template('not_found', item=item)
    else:
        speech_text = render_template('get_response', item=item, location=location)
    urllib2.urlopen(PI_ENDPOINT + str(led))
    return statement(speech_text).simple_card(card_title, speech_text)


@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location_one', 'location2': 'Location_two'})
def get_item(item, location, location2):
    card_title = render_template('card_title')
    start = location
    end  = location2
    speech_text = ""
    if end != None:
        print("in move item intent, end != none")
        print ("end = "+str(end))
        selectedItemId = checkAndInsertItem(item, start)
        print ("item id = " + str(selectedItemId))
        if selectedItemId == "conversation_needed":
            speech_text = render_template('move_conversation', item=item)
            return statement(speech_text).simple_card(card_title, speech_text)
        startId = checkAndInsertLocation(start)
        endId = checkAndInsertLocation(end)
        print("startId = " + str(startId) + " endId = " + str(endId))
        cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, selectedItemId))
        speech_text = render_template('move_response', item=item, location=location2)
    else:
        print("in move item intent, end == None")
        selectedItemId = checkAndInsertItem(item, "");
        if selectedItemId == "conversation_needed":
            speech_text = render_template('move_conversation', item=item)
            return statement(speech_text).simple_card(card_title, speech_text)
        endId = checkAndInsertLocation(start)
        print (endId)
        print (selectedItemId)
        cur.execute("UPDATE Items SET locationId = %s WHERE itemId=%s", (endId, selectedItemId))
        speech_text = render_template('move_response', item=item, location=location)
    db.commit()
    return statement(speech_text).simple_card(card_title, speech_text)

def checkAndInsertItem(item, location):
    if location != "":
        locationId = checkAndInsertLocation(location)
        cur.execute("SELECT itemID FROM Items WHERE locationID =%s AND name= %s", (locationId, item));
        result = cur.fetchone()
        if result:
            return result[0]
        else: 
            cur.execute("INSERT INTO Items (name, locationId) VALUES (%s, %s)", (item, locationId))
            cur.execute("SELECT ItemId FROM Items WHERE name=%s and locationid=%s", (item, locationId))
            db.commit()
            return cur.fetchone()[0]
    else:
        print(item)
        print("item above----------")
        if cur.execute("SELECT itemID FROM Items WHERE name= %s", (item)):
            print("in check and insert item, found item, dont care about location here")
            #check number of existing, if many start conversation
            results = cur.fetchall()
            if len(results) > 1:
                return "conversation_needed"
            print ("results = ")
            print(results)
            #this has to change hard coded to grab first row
            return results[0][0]
        else:
            cur.execute("INSERT INTO Items (locationID, name) VALUES (1, %s)", (item))
            cur.execute("SELECT ItemId FROM Items WHERE name=%s and locationid=1", (item))
            db.commit()
            return cur.fetchone()[0]

def checkAndInsertLocation(location):
    location = standardize_shelf_location(location)
    print ("after standardizing, location = " + location)
    if cur.execute("SELECT LocationId FROM Locations WHERE name = %s", (location)):
        return cur.fetchone()[0]
    else:
        cur.execute("INSERT INTO Locations (name, Led) VALUES (%s, 0)", (location))
        cur.execute("SELECT LocationId FROM Locations WHERE name = %s", (location))
        db.commit()
        return cur.fetchone()[0]

def standardize_shelf_location(location):
    print("string given to standardize = " + location)
    if ('left' in location and 'top' in location):
        return 'left side of the top shelf'
    if ('right' in location and 'top' in location):
        return 'right side of the top shelf'
    if (('middle' or 'center') in location and 'top' in location):
        return 'center of the top shelf'
    if ('left' in location and 'bottom' in location):
        return 'left side of the top shelf'
    if ('right' in location and 'bottom' in location):
        return 'right side of the bottom shelf'
    if (('middle' or 'center') in location and 'bottom' in location):
        return 'center of the bottom shelf'
    if ('left' in location and ('middle' or 'center') in location):
        return 'left side of the middle shelf'
    if ('right' in location and 'middle' or 'center' in location):
        return 'right side of the bottom shelf'
    if (('middle' or 'center') in location):
        return 'center of the middle shelf'
    return location


@ask.intent('GetOpenLocations', mapping={'item': 'Item'})
def get_item(item):
    card_title = render_template('card_title')
    cur.execute("SELECT name, led FROM Locations WHERE locationID NOT IN (SELECT locationID FROM Items) ORDER BY LocationID DESC")
    data = cur.fetchall()
    speech_text = ""
    location = ""
    led = ""
    if data: 
        led += str(len(data))
        #no available spots
        print("open locations")
        for row in data:
            if row[0] == "unkown":
                led += str(row[1])
                break
            location += row[0]
            location += ", "
            led += str(row[1])
    if location == "":
        led = "0"
        speech_text = render_template('no_open_locations')
    else:
        speech_text = render_template('open_locations', location=location)
    urllib2.urlopen(PI_ENDPOINT + str(led))
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
