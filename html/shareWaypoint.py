#!/usr/bin/python
"""

 Copyright 2010 Paul Willworth <ioscode@gmail.com>

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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
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
	sid = form.getfirst('gh_sid', '')

wpID = form.getfirst('wpID', '')
userID = form.getfirst('userID', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
wpID = dbShared.dbInsertSafe(wpID)
userID = dbShared.dbInsertSafe(userID)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program

print 'Content-type: text/html\n'
if (logged_state > 0):
	if (wpID == '' or userID == '' or userID == currentUser):
		result = 'Error: Waypoint ID and User ID are both required'
	else:
		try:
			conn = dbShared.ghConn()
			cursor = conn.cursor()
		except Exception:
			result = "Error: could not connect to database"

		if (cursor):
			# check owner
			cursor.execute('SELECT owner FROM tWaypoint WHERE waypointID=' + str(wpID) + ';')
			row = cursor.fetchone()

			if (row != None):
				owner = row[0]
			# share it
			if owner == currentUser:
				sqlStr = "SELECT unlocked FROM tUserWaypoints WHERE userID='" + userID + "' AND waypointID=" + wpID + ";"
				cursor.execute(sqlStr)
				row = cursor.fetchone()
				if (row != None):
					sqlStr = "UPDATE tUserWaypoints SET unlocked=NOW() WHERE userID='" + userID + "' AND waypointID=" + wpID + ";"
				else:
					sqlStr = "INSERT INTO tUserWaypoints (userID, waypointID, unlocked) VALUES ('" + userID + "'," + str(wpID) + ",NOW());"
				cursor.execute(sqlStr)
				affRows = cursor.rowcount
				if affRows > 0:
					result = "Waypoint shared."
				else:
					result = "Error: Waypoint not found."
			else:
				result = "Error: You are not the owner of that waypoint."

			cursor.close()

		else:
			result = "Error: No data connection"
		conn.close()
else:
	result = "Error: You must be logged in share a waypoint."

print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
