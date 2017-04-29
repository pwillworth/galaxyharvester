#!/usr/bin/python
"""

 Copyright 2017 Paul Willworth <ioscode@gmail.com>

 This file is part of Galaxy Harvester.

 Galaxy Harvester is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Galaxy Harvester is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Galaxy Harvester.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys
import os
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared
import re
from xml.dom import minidom

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
	try:
		currentUser = cookies['userID'].value
	except KeyError:
		currentUser = ''
	try:
		loginResult = cookies['loginAttempt'].value
	except KeyError:
		loginResult = 'success'
	try:
		sid = cookies['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	loginResult = 'success'
	sid = form.getfirst('gh_sid', '')

itemID = form.getfirst("itemID", "0")
voteValue = form.getfirst("voteValue")
suggestion = form.getfirst("suggestion", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
suggestion = dbShared.dbInsertSafe(suggestion)
# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	linkappend = 'gh_sid=' + sid

#  Check for errors
errstr=''
if (itemID.isdigit() == False or (itemID == "0" and suggestion == "")):
	errstr = errstr + "That is not a valid feeback item. \r\n"
if (itemID != "0" and suggestion == ""):
	try:
		int(voteValue)
	except ValueError:
		errstr = errstr + "That is not a valid vote value. \r\n"
	except TypeError:
		errstr = errstr + "That is not a valid vote value. \r\n"

if (logged_state == 0):
	errstr = errstr + "You must be logged in to add or update feedback. \r\n"

if re.search("[><&]", suggestion):
	errstr = errstr + "There are illegal characters in your suggestion.  No HTML allowed."


if (len(errstr) < 5):
	cconn = dbShared.ghConn()
	if (suggestion == ""):
		cursor = cconn.cursor()
		cursor.execute("SELECT vote FROM tFeedbackVotes WHERE feedbackID=" + str(itemID) + " AND userID='" + currentUser + "';")
		row = cursor.fetchone()
		ccursor = cconn.cursor()
		if row != None:
			if (str(row[0]) != voteValue):
				ccursor.execute("UPDATE tFeedbackVotes SET vote=" + str(voteValue) + ", entered=NOW() WHERE feedbackID=" + str(itemID) + " AND userID='" + currentUser + "';")
				resultRows = ccursor.rowcount
			else:
				ccursor.execute("UPDATE tFeedbackVotes SET vote=0, entered=NOW() WHERE feedbackID=" + str(itemID) + " AND userID='" + currentUser + "';")
				resultRows = ccursor.rowcount
		else:
			ccursor.execute("INSERT INTO tFeedbackVotes (feedbackID, entered, userID, vote) VALUES (" + str(itemID) + ",NOW(),'" + currentUser + "'," + str(voteValue) + ");")
			itemID = cursor.lastrowid
			resultRows = ccursor.rowcount

		ccursor.close()
		if resultRows > 0:
			result = "Vote recorded"
		else:
			result = "Error: Vote not recorded.  Same as existing vote."
	else:
		addType = "Suggestion"
		cursor = cconn.cursor()
		cursor.execute("SELECT entered FROM tFeedback WHERE feedbackID=" + str(itemID) + ";")
		row = cursor.fetchone()
		ccursor = cconn.cursor()
		if row != None:
			addType = "Comment"
			ccursor.execute("INSERT INTO tFeedbackComments (feedbackID, entered, userID, comment) VALUES (" + str(itemID) + ",NOW(),'" + currentUser + "','" + suggestion + "');")
			itemID = cursor.lastrowid
			resultRows = ccursor.rowcount
		else:
			ccursor.execute("INSERT INTO tFeedback (entered, userID, feedback, feedbackState) VALUES (NOW(),'" + currentUser + "','" + suggestion + "',1);")
			itemID = cursor.lastrowid
			resultRows = ccursor.rowcount

		ccursor.close()
		if resultRows > 0:
			result = addType + " recorded"
		else:
			result = "Error: " + addType + " not recorded.  Invalid ID."

	cconn.close()

else:
	sys.stderr.write("-" + errstr + "-")
	result = "Error: Feedback could not be updated because of the following errors:\r\n" + errstr

print 'Content-type: text/xml\n'
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eName = doc.createElement("feedbackID")
tName = doc.createTextNode(str(itemID))
eName.appendChild(tName)
eRoot.appendChild(eName)
eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print doc.toxml()

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
