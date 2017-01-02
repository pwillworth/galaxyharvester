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
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
wpID = dbShared.dbInsertSafe(wpID)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program

print 'Content-type: text/html\n'
if (logged_state > 0):
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
		# remove it
		if owner == currentUser:
			sqlStr = "UPDATE tWaypoint SET unavailable=NOW() WHERE waypointID=" + str(wpID) + ";"
			cursor.execute(sqlStr)
			affRows = cursor.rowcount
			if affRows > 0:
				result = "Waypoint removed."
			else:
				result = "Error: Waypoint not found."
			cursor.execute("INSERT INTO tUserEvents (userID, targetType, targetID, eventType, eventTime) VALUES ('" + currentUser + "','w'," + str(wpID) + ",'r',NOW());")
		else:
			sqlStr = "UPDATE tUserWaypoints SET unlocked=NULL WHERE userID='" + currentUser + "' AND waypointID=" + str(wpID) + ";"
			cursor.execute(sqlStr)
			affRows = cursor.rowcount
			if affRows > 0:
				result = "The waypoint has been removed for you.  If you want to add it back in later, you will have to ask the owner to share it with you again."
			else:
				# Check to see if waypoint is public
				cursor.execute("SELECT shareLevel FROM tWaypoint WHERE waypointID=" + str(wpID) + ";")
				row = cursor.fetchone()
				if row == None:
					shareLevel = 0
				else:
					shareLevel = int(row[0])

				#sys.stderr.write("sharelevel" + str(wpID) + ": " + str(shareLevel))
				# Add removal event is it is public
				if shareLevel == 256:
					cursor.execute("SELECT eventTime FROM tUserEvents WHERE userID='" + currentUser + "' AND targetType='w' AND targetID=" + str(wpID) + " AND eventType='r';")
					row = cursor.fetchone()
					if row == None:
						cursor.execute("INSERT INTO tUserEvents (userID, targetType, targetID, eventType, eventTime) VALUES ('" + currentUser + "','w'," + str(wpID) + ",'r',NOW());")
						result = "Your request for removal has been entered.  It may take confirmation from other members before it is actually removed."
						# See if there is enough rep on removal to mark unavailable
						cursor.execute("SELECT Sum(repGood)-Sum(repBad) FROM tUserStats WHERE userID IN (SELECT ue.userID FROM tUserEvents ue WHERE targetType='w' AND targetID=" + str(wpID) + " AND eventType='r');")
						row = cursor.fetchone()
						if row != None and row[0] != None:
							if row[0] > 2:
								sqlStr = "UPDATE tWaypoint SET unavailable=NOW() WHERE waypointID=" + str(wpID) + ";"
								cursor.execute(sqlStr)
					else:
						result = "Error: Your request for removal of this waypoint has already been entered."
				else:
					result = "Error: You are not the owner of that waypoint."

		cursor.close()

	else:
		result = "Error: No data connection"
	conn.close()
else:
	result = "Error: You must be logged in delete a waypoint."

print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
