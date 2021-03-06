import logging

from flask import Flask, json, render_template, request, redirect, url_for
from flask_ask import Ask, session, question, statement
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
#PI_ENDPOINT = "https://smartshelves.localtunnel.me/api/locate/"
PI_ENDPOINT = "https://b5bedaea.ngrok.io/api/locate/"
@app.route("/about")
def about():
    return "about us"

@app.route("/view")
def view():
    objectDict = {}
    locationDict = {}

    cur.execute("SELECT locationId, name FROM Locations")
    results = cur.fetchall()
    if results:
        for row in results:
            locationDict[row[0]] = row[1]
            objectDict[row[0]] = []

    cur.execute("SELECT name, locationId FROM Items")
    results = cur.fetchall()
    if results:
        for row in results:
            objectDict[row[1]].append(row[0])
    print ("objectDict = "+str(objectDict))
    return render_template('smartshelves-me.html', objectDict = objectDict, locationDict= locationDict)

@app.route("/add", methods=['POST'])
def website_add_item():
    item = request.form['item']
    location = standardize_shelf_location(request.form['new_location'])
    if item != "" and location != "":
        print("got to insert item")
        checkAndInsertItem(item, location)
    print("pre redirect")
    return redirect(url_for('view'))

@app.route("/move", methods=['POST'])
def website_move_item():
    item = request.form['item']
    start = request.form['old_location']
    end = request.form['new_location']
    print(item)
    print ("got request")
    print(start)
    if item != None and start != None and end != None:
        start = standardize_shelf_location(start)
        end  = standardize_shelf_location(end)
        print("in move item intent, end != none")
        print ("end = "+str(end))
        selectedItemId = checkAndInsertItem(item, start)
        print ("item id = " + str(selectedItemId))
        startId = checkAndInsertLocation(start)
        endId = checkAndInsertLocation(end)
        if selectedItemId == "conversation_needed":
            return redirect(url_for('view'))
        print("startId = " + str(startId) + " endId = " + str(endId))
        cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, selectedItemId))
        db.commit()
    return redirect(url_for('view'))

@app.route("/remove", methods=['POST'])
def website_remove_item():
    item = request.form['item']
    location = request.form['old_location']
    print(" item = "+item)
    print("location = "+location)
    if item != None and location != None:
        location = standardize_shelf_location(location)
        locationId = checkAndInsertLocation(location)
        print("locationId = " + str(locationId))

        # cur.execute("SELECT itemID FROM Items WHERE name=%s AND locationID=%s", (item, locationId))
        # if len(cur.fetchall()) == 0:
        #     #no objects of that name at that location error:
        #     return redirect(url_for('view'))
        print("before delete statement")
        cur.execute("DELETE FROM Items WHERE name=%s AND locationID=%s", (item, locationId))
        print("after delete statement")
        db.commit()
        return redirect(url_for('view'))
    #TODO: print error item or location wasn't filled in
    print("if did not have correct values")
    return redirect(url_for('view'))


@ask.launch
def launch():
    card_title = render_template('card_title')
    speech_text = render_template('launch')
    return question(speech_text).reprompt(speech_text).simple_card(card_title, speech_text)


@ask.intent('PrevItemLocationIntent', mapping={'location':'Location_one'})
def set_item(location):
    print ('in PrevItemLocationIntent')
    item_name = ""
    location_name = ""
    card_title = render_template('card_title')
    try:
        req_type = session.attributes['type']
        item_name = session.attributes['item_name']
        locationId = checkAndInsertLocation(location)
        print ("req_type = " +req_type)
        if req_type == "move":
            endId = session.attributes['dest']
            print (endId)
            print (locationId)
            for key in session.attributes['items']:
               value = session.attributes['items'][key]
               print(str(key)+" "+str(value))
               if str(locationId) == str(key):
                    print ("found key")
                    cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, value))
                    db.commit()
                    cur.execute("SELECT name FROM Locations WHERE LocationID=%s",(endId))
                    location_name = cur.fetchone()[0]
            if location_name is "":
                speech_text = render_template('move_conversation', item=item_name)
                return question(speech_text).simple_card(card_title, speech_text)
        elif req_type == "remove":
            print("in remove prev")
            cur.execute("DELETE FROM Items WHERE name=%s and locationID=%s", (item_name, locationId))
            db.commit()
            speech_text = render_template('remove_response', item=item_name, location=location)    
            return statement(speech_text).simple_card(card_title, speech_text)
    except:
        speech_text = render_template('bad_session')
        return statement(speech_text).simple_card(card_title, speech_text)

    speech_text = render_template('move_response', item=session.attributes['item_name'], location=location_name)    
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
            if row[0] == "unkown":
                led += str(row[1])
                break
            location += row[0]
            location += ", "
            led += row[1]

    if location == "":
        led = "0"
        speech_text = render_template('not_found', item=item)
    else:
        grammar_checks = check_grammar(item, location)
        if grammar_checks[0] == False and grammar_checks[1] == False:
            speech_text = render_template('get_response_in', item=item, location=location)
        elif grammar_checks[0] == True and grammar_checks[1] == False:
            speech_text = render_template('get_response_in_plural', item=item, location=location)
        elif grammar_checks[0] == False and grammar_checks[1] == True:
            speech_text = render_template('get_response_on', item=item, location=location)
        else:
            speech_text = render_template('get_response_on_plural', item=item, location=location)
    try:
        urllib2.urlopen(PI_ENDPOINT + led)
    except:
        print ("could not reach shelf enpoint")
    print (PI_ENDPOINT + str(led))
    return statement(speech_text).simple_card(card_title, speech_text)


@ask.intent('MoveItemLocation', mapping={'item': 'Item', 'location': 'Location_one', 'location2': 'Location_two'})
def get_item(item, location, location2):
    card_title = render_template('card_title')
    start = standardize_shelf_location(location)
    end  = standardize_shelf_location(location2)
    speech_text = ""
    if end != None:
        print("in move item intent, end != none")
        print ("end = "+str(end))

        selectedItemId = checkAndInsertItem(item, start)
        print ("item id = " + str(selectedItemId))
        startId = checkAndInsertLocation(start)
        endId = checkAndInsertLocation(end)
        session.attributes['dest'] = endId
        session.atrributes['item_name'] = item

        if selectedItemId == "conversation_needed":
            speech_text = render_template('move_conversation', item=item)
            return question(speech_text).simple_card(card_title, speech_text)
        
        print("startId = " + str(startId) + " endId = " + str(endId))
        cur.execute("UPDATE Items SET locationID=%s WHERE ItemID=%s", (endId, selectedItemId))
        speech_text = render_template('move_response', item=item, location=end)
    else:
        print("in move item intent, end == None")
        selectedItemId = checkAndInsertItem(item, "");
        endId = checkAndInsertLocation(start)
        session.attributes['dest'] = endId
        session.attributes['item_name'] = item
        if selectedItemId == "conversation_needed":
            speech_text = render_template('move_conversation', item=item)
            return question(speech_text).simple_card(card_title, speech_text)
        print (endId)
        print (selectedItemId)
        cur.execute("UPDATE Items SET locationId = %s WHERE itemId=%s", (endId, selectedItemId))
        speech_text = render_template('move_response', item=item, location=start)
    db.commit()
    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('RemoveItemIntent', mapping={'item':'Item', 'location':'Location'})
def remove_item(item, location):
    card_title = render_template('card_title')
    if location != None:
        print('AAAAAAAAAAAAAAAAA')
        location = standardize_shelf_location(location)
        locationId = checkAndInsertLocation(location)
        location_name = ""
        print (locationId)
        cur.execute("SELECT locationID FROM Items WHERE name=%s", (item))
        data = cur.fetchall()
        for i in data:
           if str(locationId) == str(i):
                print ("found key")
                cur.execute("DELETE FROM Items WHERE name=%s and locationID=%s", (item, i))
                db.commit()
                cur.execute("SELECT name FROM Locations WHERE LocationID=%s",(i))
                location_name = cur.fetchone()[0]
        if location_name is "":
            speech_text = render_template('remove_not_found', item=item, location=location)
        else:
            speech_text = render_template('remove_response', item=item)    
        return statement(speech_text).simple_card(card_title, speech_text)
    else:
        cur.execute("SELECT locationID FROM Items WHERE name=%s", (item))
        data = cur.fetchall()
        if cur.rowcount == 1:
            cur.execute("DELETE FROM Items WHERE name=%s", (item))
            db.commit()
            speech_text = render_template('remove_response', item=item) 
            return statement(speech_text).simple_card(card_title, speech_text)   
        else:

            session.attributes['item_name'] = item
            session.attributes['type'] = "remove"
            speech_text = render_template('remove_conversation', item=item)
            return question(speech_text).simple_card(card_title, speech_text)


# @ask.intent('RemoveItemConversationIntent', mapping={'location':'Location_one'})
# def remove_item_conversation(location):
#     print ('in RemoveItemLocationIntent')
#     item_name = ""
#     location_name = ""
#     card_title = render_template('card_title')
#     try:
#         item_name = session.attributes['item_name']
#         locationId = checkAndInsertLocation(location)
#         print (locationId)
#         cur.execute("SELECT locationID FROM Items WHERE name=%s", (item))
#         data = cur.fetchall()
#         for i in data:
#            if str(locationId) == str(i):
#                 print ("found key")
#                 cur.execute("DELETE FROM Items WHERE name=%s and locationID=%s", (item, i))
#                 db.commit()
#                 cur.execute("SELECT name FROM Locations WHERE LocationID=%s",(i))
#                 location_name = cur.fetchone()[0]
#         if location_name is "":
#             speech_text = render_template('remove_conversation', item=item_name)
#             return question(speech_text).simple_card(card_title, speech_text)
#     except:
#         speech_text = render_template('bad_session')
#         return statement(speech_text).simple_card(card_title, speech_text)

#     speech_text = render_template('remove_response', item=session.attributes['item_name'], location=location_name)    
#     return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('WhatsOnShelf', mapping={'location':'Location'})
def whatsOnShelf(location):
    card_title = render_template('card_title')
    speech_text = ""
    items = []
    if location == "top shelf":
        cur.execute("SELECT name FROM Items WHERE locationID=2 or locationID=5 or locationID=6 or locationID=7")
        items = cur.fetchall()
    elif location == "middle shelf" or location == "center shelf":
        cur.execute("SELECT name FROM Items WHERE locationID=3 or locationID=8 or locationID=9 or locationID=10")
        items = cur.fetchall()
    elif location == "bottom shelf":
        cur.execute("SELECT name FROM Items WHERE locationID=4 or locationID=11 or locationID=12 or locationID=13")
        items = cur.fetchall()
    else:
        location = standardize_shelf_location(location)
        cur.execute("SELECT name FROM Items WHERE locationID=(SELECT locationID FROM Locations WHERE name=%s)", (location))
        items = cur.fetchall()
        
    if len(items) > 0:
        speech_text = render_template('whats_at_location_response', location=location, items=items)
    else:
        speech_text = render_template('no_items_response')
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
        if cur.execute("SELECT itemID, locationId FROM Items WHERE name= %s", (item)):
            print("in check and insert item, found item")
            #check number of existing, if many start conversation
            results = cur.fetchall()
            if len(results) > 1:
                session.attributes['items'] = {}
                for row in results:
                    #put items in dictionary
                    #locationId -> itemId
                    #session.attributes['items']
                    session.attributes['items'][row[1]] = row[0]
                session.attributes["type"] = "move"
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
    if location == None:
        return location
    print("string given to standardize = " + location)
    if ('left' in location and 'top' in location):
        return 'left side of the top shelf'
    if ('right' in location and 'top' in location):
        return 'right side of the top shelf'
    if ((('middle' in location) or 'center' in location) and 'top' in location):
        return 'center of the top shelf'
    if ('left' in location and 'bottom' in location):
        return 'left side of the bottom shelf'
    if ('right' in location and 'bottom' in location):
        return 'right side of the bottom shelf'
    if ((('middle' in location) or 'center' in location) and 'bottom' in location):
        return 'center of the bottom shelf'
    if ('left' in location and (('middle' in location) or 'center' in location)):
        return 'left side of the middle shelf'
    if ('right' in location and (('middle' in location) or 'center' in location)):
        return 'right side of the middle shelf'
    if ((('middle' in location) or 'center' in location)):
        return 'center of the middle shelf'
    return location

def check_grammar(item, location):
    plural = False
    on_or_in = True
    if item.endswith('s'):
        plural = True
    if 'shelf' not in location:
        on_or_in = False
    return [plural, on_or_in]
    
@ask.intent('GetOpenLocations', mapping={'item': 'Item'})
def get_item(item):
    card_title = render_template('card_title')
    cur.execute("SELECT name, led FROM Locations WHERE locationID NOT IN (SELECT locationID FROM Items) AND locationID < 14 AND locationID > 4 ORDER BY LocationID DESC")
    data = cur.fetchall()
    speech_text = ""
    location = ""
    led = ""
    if data: 
        #no available spots
        print("open locations")
        for row in data:
            if row[0] in ["bottom shelf", "middle shelf", "top shelf", "unknown"]:
                while len(data) > len(led):
                    led += "0"
                break
            location += row[0]
            location += ", "
            led += row[1]
    if location == "":
        led = "0"
        speech_text = render_template('no_open_locations')
    else:
        speech_text = render_template('open_locations', location=location)

    try:
        urllib2.urlopen(PI_ENDPOINT + led)
    except:
        print ("could not reach shelf enpoint")
    print (PI_ENDPOINT + str(led))

    return statement(speech_text).simple_card(card_title, speech_text)

@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = render_template('help')
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
