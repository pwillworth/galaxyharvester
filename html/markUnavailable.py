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

import os
import sys
import Cookie
import dbSession
import dbShared
import ghShared
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

spawnName = form.getfirst('spawn', '')
galaxy = form.getfirst('galaxy', '')
planets = form.getfirst('planets', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
spawnName = dbShared.dbInsertSafe(spawnName)
galaxy = dbShared.dbInsertSafe(galaxy)
planets = dbShared.dbInsertSafe(planets)

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
		if (dbShared.galaxyState(galaxy) == 1):
			markAll = 0
			cursor.execute('SELECT spawnID, resourceType, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER, unavailable, enteredBy FROM tResources WHERE galaxy=' + galaxy + ' AND spawnName="' + spawnName + '";')
			row = cursor.fetchone()

			if (row != None):
				spawnID = str(row[0])

			if (planets == "all"):
				markAll = 1
				sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + currentUser + "' WHERE spawnID=" + spawnID + ";"
			else:
				# try to look up planet by name if an ID was not provided
				if (planets.isdigit() != True):
					planets = dbShared.getPlanetID(planets)
				sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + currentUser + "' WHERE spawnID=" + spawnID + " AND planetID=" + planets + ";"

			# Only allow removal if user has positive reputation
			stats = dbShared.getUserStats(currentUser, galaxy).split(",")
			if int(stats[2]) < ghShared.MIN_REP_VALS['REMOVE_RESOURCE'] and row[14] != currentUser:
				result = "Error: You must earn a little reputation on the site before you can remove resources.  Try adding or verifying some first. \r\n"
			elif row[13] != None:
				result = "Error: You cannot remove that resource because it is already removed."
			else:
				cursor.execute(sqlStr)

				# add cleanup event
				if not planets.isdigit():
					planets = 0
				dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(galaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'r'," + str(planets) + ");", 'r', currentUser, galaxy, str(spawnID))
				result = spawnName
				cursor.close()
		else:
			result = "Error: That Galaxy is Inactive."
	else:
		result = "Error: Could not connect to database"
	conn.close()
else:
	result = "Error: You must be logged in to mark a resource unavailable."

print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
