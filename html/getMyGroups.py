#!/usr/bin/python
"""

 Copyright 2012 Paul Willworth <ioscode@gmail.com>

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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
import ghShared
#
# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
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

# Get form info
favType = form.getfirst("favType", "")
firstOption = form.getfirst("firstOption", "<option value=\"New_Group\">New Group</option>")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
favType = dbShared.dbInsertSafe(favType)
firstOption = dbShared.dbInsertSafe(firstOption)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

result = firstOption
#  Check for errors
errstr = ""

if (not favType.isdigit()):
	errstr = errstr + "Error: no favorite type given. \r\n"

print 'Content-type: text/html\n'

# Only process if no errors
if (errstr == ""):
	if (logged_state > 0):
		conn = dbShared.ghConn()
		# open list of users existing groups
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT favGroup FROM tFavorites WHERE userID='" + currentUser + "' AND favType=" + favType + " ORDER BY favGroup;")
		row = cursor.fetchone()
		while row != None:
			result = result + '<option value="' + row[0] + '">' + str(row[0]).replace("_"," ") + '</option>'
			row = cursor.fetchone()

		cursor.close()
		conn.close()
	else:
		result = "Error: must be logged in to get groups"
else:
	result = errstr

print result

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
