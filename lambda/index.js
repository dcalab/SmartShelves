
'use strict';

/**
 * This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
 * The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well as
 * testing instructions are located at http://amzn.to/1LzFrj6
 *
 * For additional samples, visit the Alexa Skills Kit Getting Started guide at
 * http://amzn.to/1LGWsLG
 */

var https = require('https');
var firebase = require("firebase");


var config = {
    apiKey: "AIzaSyBDyLmrfxWslhiHkSikyjUCs6XMGOLmzPE",
    authDomain: "smartshelves-5ab7e.firebaseapp.com",
    databaseURL: "https://smartshelves-5ab7e.firebaseio.com",
    storageBucket: "smartshelves-5ab7e.appspot.com",
};
firebase.initializeApp(config);

var database = firebase.database();

// --------------- Helpers that build all of the responses -----------------------
function makeFirebaseGetReq(item) {
    item = "paper towel";
    var database = firebase.database();
    database.ref().endAt(item).once('value').then(function(snapshot) {
      // The Promise was "fulfilled" (it succeeded).
      console.log("found it ");
      console.log(snapshot.val());
      database.goOffline();
      return snapshot.val();
    }, function(error) {
      // The Promise was rejected.
      console.log("error");
      console.error(error);
      database.goOffline();
      return -1;
    });

}


function buildSpeechletResponse(title, output, repromptText, shouldEndSession) {
    return {
        outputSpeech: {
            type: 'PlainText',
            text: output,
        },
        card: {
            type: 'Simple',
            title: `SessionSpeechlet - ${title}`,
            content: `SessionSpeechlet - ${output}`,
        },
        reprompt: {
            outputSpeech: {
                type: 'PlainText',
                text: repromptText,
            },
        },
        shouldEndSession,
    };
}

function buildResponse(sessionAttributes, speechletResponse) {
    return {
        version: '1.0',
        sessionAttributes,
        response: speechletResponse,
    };
}


// --------------- Functions that control the skill's behavior -----------------------

function getWelcomeResponse(callback) {
    // If we wanted to initialize the session to have some attributes we could add those here.
    const sessionAttributes = {};
    const cardTitle = 'Welcome';
    const speechOutput = 'Welcome to Smart Shelves. ' +
        'I can help you remember where items are. You can ask, where is an item or you can move and set an items location';
    // If the user either does not reply to the welcome message or says something that is not
    // understood, they will be prompted again with this text.
    const repromptText = 'Please ask where something is by asking, ' +
        'where is the paper towel';
    const shouldEndSession = false;

    callback(sessionAttributes,
        buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession));
}

function handleSessionEndRequest(callback) {
    const cardTitle = 'Session Ended';
    const speechOutput = 'Thank you for using Smart Shelves. Have a nice day!';
    // Setting this to true ends the session and exits the skill.
    const shouldEndSession = true;

    callback({}, buildSpeechletResponse(cardTitle, speechOutput, null, shouldEndSession));
}

function createFavoriteColorAttributes(favoriteColor) {
    return {
        favoriteColor,
    };
}

/**
 * Sets the color in the session and prepares the speech to reply to the user.
 */
function getItemLocation(intent, session, callback) {
    const cardTitle = intent.name;
    const requestedItemSlot = intent.slots.Item;
    let repromptText = '';
    let sessionAttributes = {};
    const shouldEndSession = false;
    let speechOutput = '';
    if (requestedItemSlot) {
        const item = requestedItemSlot.value;
        var firebase_data = new Promise(function(resolve, reject) {
            database.goOnline();

            database.ref("/"+item).once('value').then(function(snapshot) {
              // The Promise was "fulfilled" (it succeeded).
              console.log("item request: "+ item);
              console.log("db found: "+ snapshot.val());
              database.goOffline();
              resolve(snapshot.val());
            }, function(error) {
              // The Promise was rejected.
              console.log("error");
              console.error(error);
              database.goOffline();
              reject(-1);
            });
        });
        firebase_data.then(function(result) {
            if (result["is_there"] == 1) {
                speechOutput = "The " + item + " is on the " + result["item_location"] + ".";
                repromptText = "The " + item + " is on the " + result["item_location"] + ".";
            } else {
                speechOutput = "I couldn't find " + item + ".";
                repromptText = "Try again.";
            }
            callback(sessionAttributes,
                buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession));
        });
    } else {
        speechOutput = "I'm not sure what item you asked for. Please try again.";
        repromptText = "I'm not sure what item you asked. You can ask me where an item is " +
            'by asking, where is the paper towel';
        callback(sessionAttributes,
            buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession));
    }


}

/**
 * Sets the color in the session and prepares the speech to reply to the user.
 */
function setItemLocation(intent, session, callback) {
    const cardTitle = intent.name;
    const requestedItemSlotToBe = intent.slots.Location;
    const requestedItemSlot = intent.slots.Item;
    let repromptText = '';
    let sessionAttributes = {};
    const shouldEndSession = true;
    let speechOutput = '';
    //if item already here
    if (requestedItemSlot && requestedItemSlotToBe) {
        item = requestedItemSlot.value;
        database.goOnline();
        database.ref("/"+item+"/").set({
                                       is_there : 1,
                                       item_location: requestedItemSlotToBe.value
                                       })
        database.goOffline();
    }
    else {
        console.log("invalid request");
    }
    speechOutput = "I've place " + requestedItemSlot.value + " at " + requestedItemSlotToBe.value;
    
    callback(sessionAttributes,
             buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession));
    
    
}

function getColorFromSession(intent, session, callback) {
    let favoriteColor;
    const repromptText = null;
    const sessionAttributes = {};
    let shouldEndSession = false;
    let speechOutput = '';

    if (session.attributes) {
        favoriteColor = session.attributes.favoriteColor;
    }

    if (favoriteColor) {
        speechOutput = `Your favorite color is ${favoriteColor}. Goodbye.`;
        shouldEndSession = true;
    } else {
        speechOutput = "I'm not sure what your favorite color is, you can say, my favorite color " +
            ' is red';
    }

    // Setting repromptText to null signifies that we do not want to reprompt the user.
    // If the user does not respond or says something that is not understood, the session
    // will end.
    callback(sessionAttributes,
         buildSpeechletResponse(intent.name, speechOutput, repromptText, shouldEndSession));
}


// --------------- Events -----------------------

/**
 * Called when the session starts.
 */
function onSessionStarted(sessionStartedRequest, session) {
    console.log(`onSessionStarted requestId=${sessionStartedRequest.requestId}, sessionId=${session.sessionId}`);
}

/**
 * Called when the user launches the skill without specifying what they want.
 */
function onLaunch(launchRequest, session, callback) {
    console.log(`onLaunch requestId=${launchRequest.requestId}, sessionId=${session.sessionId}`);

    // Dispatch to your skill's launch.
    getWelcomeResponse(callback);
}

/**
 * Called when the user specifies an intent for this skill.
 */
function onIntent(intentRequest, session, callback) {
    console.log(`onIntent requestId=${intentRequest.requestId}, sessionId=${session.sessionId}`);

    const intent = intentRequest.intent;
    const intentName = intentRequest.intent.name;

    // Dispatch to your skill's intent handlers
    if (intentName === 'GetItemLocation') {
        getItemLocation(intent, session, callback);
    } else if (intentName === 'SetItemLocation') {
        getColorFromSession(intent, session, callback);
    } else if (intentName === 'MoveItemLocation') {
        getColorFromSession(intent, session, callback);
    } else if (intentName === 'AMAZON.HelpIntent') {
        getWelcomeResponse(callback);
    } else if (intentName === 'AMAZON.StopIntent' || intentName === 'AMAZON.CancelIntent') {
        handleSessionEndRequest(callback);
    } else {
        throw new Error('Invalid intent');
    }
}

/**
 * Called when the user ends the session.
 * Is not called when the skill returns shouldEndSession=true.
 */
function onSessionEnded(sessionEndedRequest, session) {
    console.log(`onSessionEnded requestId=${sessionEndedRequest.requestId}, sessionId=${session.sessionId}`);
    // Add cleanup logic here
}


// --------------- Main handler -----------------------

// Route the incoming request based on type (LaunchRequest, IntentRequest,
// etc.) The JSON body of the request is provided in the event parameter.
exports.handler = (event, context, callback) => {
    try {
        console.log(`event.session.application.applicationId=${event.session.application.applicationId}`);
        database.goOffline();
        /**
         * Uncomment this if statement and populate with your skill's application ID to
         * prevent someone else from configuring a skill that sends requests to this function.
         */
        /*
        if (event.session.application.applicationId !== 'amzn1.echo-sdk-ams.app.[unique-value-here]') {
             callback('Invalid Application ID');
        }
        */

        if (event.session.new) {
            onSessionStarted({ requestId: event.request.requestId }, event.session);
        }

        if (event.request.type === 'LaunchRequest') {
            onLaunch(event.request,
                event.session,
                (sessionAttributes, speechletResponse) => {
                    callback(null, buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === 'IntentRequest') {
            onIntent(event.request,
                event.session,
                (sessionAttributes, speechletResponse) => {
                    callback(null, buildResponse(sessionAttributes, speechletResponse));
                });
        } else if (event.request.type === 'SessionEndedRequest') {
            onSessionEnded(event.request, event.session);
            callback();
        }
    } catch (err) {
        callback(err);
    }
};
