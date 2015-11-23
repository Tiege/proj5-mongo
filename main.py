"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - In the session object, date or datetimes are represented as
   ISO format strings in UTC.  Unless otherwise specified, this
   is the format passed around internally. Note that ordering
   of ISO format strings is consistent with date/time order
   - User input/output is in local (to the server) time
   - Database representation is as MongoDB 'Date' objects
   Note that this means the database may store a date before or after
   the date specified and viewed by the user, because 'today' in
   Greenwich may not be 'today' here. 
"""

import flask
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we may still need time
from dateutil import tz  # For interpreting local times

# Mongo database
from pymongo import MongoClient

from bson import ObjectId
###
# Globals
###
import CONFIG

app = flask.Flask(__name__)

#Establish our mongo database connection
try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

import uuid
app.secret_key = str(uuid.uuid4())

###
# Pages
###

#the main page which displays any memo currently held in our database
@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  flask.session['memos'] = get_memos()
  for memo in flask.session['memos']:
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')


# Our interface to create memos
@app.route("/create")
def create():
     app.logger.debug("Create")
     return flask.render_template('create.html')

#Function to add memo to database
#Receives date and msg from user input and sends to put function
@app.route("/_addMemo")
def addMemo():
     app.logger.debug("addMemo")
     date = request.args.get('Date', 0, type=str)
     
     #Check for valid date entry
     validDate = format_arrow_date(date)
     if(validDate == "(bad date)"):
         print(date)
         flask.flash("Invalid date format! Use: MM-DD-YYYY")
         return flask.redirect(flask.url_for("create"))

     msg = request.args.get('Memo', 0, type=str)
     put_memo(validDate, msg)
     
     return flask.redirect(flask.url_for("index"))

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################
 
@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
     #check if date format is valid: only accepts MM-DD-YYYY
     try:
         normal = arrow.get(datetime.datetime.strptime(date, '%m-%d-%Y')).to('local')
         return normal 
     except:
         return "(bad date)"

@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """   
    try:
        then = arrow.get(date).to('local')
        now = arrow.utcnow().to('local')
        if then.date() == now.date():
            human = "Today"
        else: 
            human = then.humanize(now)
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    for record in collection.find( { "type": "dated_memo" } ):
        record['date'] = arrow.get(record['date']).isoformat()
        record['_id'] = str(record['_id'])
        records.append(record)
    return records 


def put_memo(dt, mem):
     """
     Place memo into database
     Args:
        dt: Datetime (arrow) object
        mem: Text of memo
     """
     record = { "type": "dated_memo", 
                "date": dt.to('utc').naive,
                "text": mem
             }
     collection.insert(record)
     return

@app.route('/delMemo', methods=['GET', 'POST'])
def delMemo():
     """
     Delete memo from database
     -Gets _id for memo from index page to remove said memo
     """
     if request.method == 'POST':
         for key in request.form:
            if key.startswith('delete.'):#_id form: "delete.(ObjectId)"
                _id = key.partition('.')[-1]
     
     #Removes any document from db with matching _id
     collection.remove( {"_id" : ObjectId(_id)} )
     
     return flask.redirect(flask.url_for("index"))

if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")

    
