from flask import Flask, render_template
from flask_ask import Ask, statement

app = Flask(__name__)
ask = Ask(app, '/')

@ask.intent('GetItemIntent')
def getItem(item):
    text = render_template('getItem', item=item)
    return statement(text).simple_card('getItem', text)

if __name__ == '__main__':
    app.run(debug=True)