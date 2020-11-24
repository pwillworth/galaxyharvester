#!/usr/bin/env python3
"""

 Copyright 2020 Paul Willworth <ioscode@gmail.com>

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

import os
import sys
import re
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
import time
from datetime import timedelta, datetime
import ghShared


PAGE_SIZE = 10

def getOutputJSON(cursor):
	output = '{\n'
	alertData = ''
	row = cursor.fetchone()

	while row != None:
		alertData = alertData + '      {\n        "id" : ' + str(row[0]) + ',\n        "alert_time" : "' + str(row[2]) + '",\n        "message" : "' + row[3] + '",\n        "link" : "' + row[4] + '",\n        "status" : ' + str(row[5]) + '\n      },\n'
		row = cursor.fetchone()

	if alertData == '':
		output += '"response" :\n  {\n    "result" : "no alerts",\n'
	else:
		output += '"response" :\n  {\n    "result" : "new alerts",\n    "server_time" : "' + datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + '",\n    "alerts" : [\n'
		output += alertData
		output += '    ]\n'

	if (cursor.rowcount == PAGE_SIZE):
		output += ',\n    "more_alerts" : "yes"\n'

	output += '  },\n}'
	return output

def getOutputHTML(cursor, userID):
	output = '  <ul class="alert">'
	row = cursor.fetchone()
	while row != None:
		if row[4] == "{0}user.py/{1}".format(ghShared.BASE_SCRIPT_URL, userID):
            # Ability Unlocks link to user profile and stand out
			output = output + '<li id="alert_' + str(row[0]) + '"><div class="tableHead"><a href="' + row[4] + '"><div class="inlineBlock" style="width:90%;">' + ghShared.timeAgo(row[2]) + ' ago - ' + row[3] + '</div></a><div class="inlineBlock" style="vertical-align:top;min-width:20px;"><img src="/images/xRed16.png" style="cursor:pointer;" title="Click to remove this alert" alt="Red X" onclick="updateAlertStatus(' + str(row[0]) + ', 2)" /></div></div></li>'
		else:
			output = output + '<li id="alert_' + str(row[0]) + '"><div><a href="' + row[4] + '"><div class="inlineBlock" style="width:90%;">' + ghShared.timeAgo(row[2]) + ' ago - ' + row[3] + '</div></a><div class="inlineBlock" style="vertical-align:top;min-width:20px;"><img src="/images/xRed16.png" style="cursor:pointer;" title="Click to remove this alert" alt="Red X" onclick="updateAlertStatus(' + str(row[0]) + ', 2)" /></div></div></li>'
		row = cursor.fetchone()
	if output.find("<li") > -1:
		output = output + "</ul>"
	else:
		output = "No Alerts"

	return output

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
	try:
		currentUser = C['userID'].value
	except KeyError:
		currentUser = ''
	try:
		loginResult = C['loginAttempt'].value
	except KeyError:
		loginResult = 'success'
	try:
		sid = C['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	loginResult = 'success'
	sid = form.getfirst('gh_sid', '')

# Get form info
alertTypes = form.getfirst("alertTypes", "")
formatType = form.getfirst("formatType", "")
includeAll = form.getfirst("includeAll", "")
lastTime = form.getfirst("lastTime", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
alertTypes = dbShared.dbInsertSafe(alertTypes)
lastTime = dbShared.dbInsertSafe(lastTime)


# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

fltCount = 0
result = ""
statusFilter = ""
if includeAll == "":
	statusFilter = " AND alertStatus < 2"
timeFilter = ""
if lastTime != "":
	timeFilter = " AND alertTime < '" + lastTime + "'"

#  Check for errors
errstr = ""

if (alertTypes == ""):
	errstr = errstr + "Error: no alert types given. \r\n"
if not logged_state > 0:
	errstr = errstr + "Error: must be logged in to get alerts. \r\n"

if formatType == 'json':
	print('Content-type: text/json\n')
else:
	print('Content-type: text/html\n')

# Only process if no errors
if (errstr == ""):
	conn = dbShared.ghConn()
	# select alert data
	cursor = conn.cursor()
	cursor.execute("SELECT alertID, alertType, alertTime, alertMessage, alertLink, alertStatus FROM tAlerts WHERE userID='" + currentUser + "' AND alertType IN (" + alertTypes + ")" + statusFilter + timeFilter + " ORDER BY alertTime DESC LIMIT " + str(PAGE_SIZE) + ";")
	if formatType == "json":
		result = getOutputJSON(cursor)
	else:
		result = getOutputHTML(cursor, currentUser)

	cursor.close()
	conn.close()

	print(result)
else:
	if formatType == 'json':
		print('{"response" : "' + errstr + '"}')
	else:
		print('<h2>' + errstr + '</h2>')

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
