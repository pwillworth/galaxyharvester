#!/usr/bin/python
"""

 Copyright 2019 Paul Willworth <ioscode@gmail.com>

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
import ghNames
#
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


spawnName = form.getfirst('spawn', '')
galaxy = form.getfirst('galaxy', '')
planets = form.getfirst('planets', '')
spawnID = form.getfirst('spawnID', '')
availability = form.getfirst('availability', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
spawnName = dbShared.dbInsertSafe(spawnName)
galaxy = dbShared.dbInsertSafe(galaxy)
planets = dbShared.dbInsertSafe(planets)
spawnID = dbShared.dbInsertSafe(spawnID)
availability = dbShared.dbInsertSafe(availability)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	linkappend = 'gh_sid=' + sid

# Main program

print 'Content-type: text/html\n'
if (logged_state > 0):
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		row = None
		enteredBy = ''
		# lookup spawn id if it was not passed
		if (spawnID == ''):
			if galaxy != '':
				cursor.execute('SELECT spawnID, resourceType, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER, enteredBy FROM tResources WHERE galaxy=' + galaxy + ' AND spawnName="' + spawnName + '";')
				row = cursor.fetchone()

			if (row != None):
				spawnID = str(row[0])
				enteredBy = row[13]
		# lookup galaxy if it was not passed
		if (galaxy == ''):
			cursor.execute('SELECT galaxy FROM tResources WHERE spawnID=' + spawnID + ';')
			row = cursor.fetchone()

			if (row != None):
				galaxy = str(row[0])

		# lookup spawn name if it was not passed
		if (spawnName == ''):
			cursor.execute('SELECT spawnName, enteredBy FROM tResources WHERE spawnID=' + spawnID + ';')
			row = cursor.fetchone()

			if (row != None):
				spawnName = row[0]
				enteredBy = row[1]

		sqlStr = ""
		if (spawnID != '' and galaxy != ''):
			if (dbShared.galaxyState(galaxy) == 1):
				if (availability == "0"):
					# mark unavailable on planet(s)
					if (planets == "all"):
						sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + currentUser + "' WHERE spawnID=" + spawnID + ";"
						result = "Marked unavailable on all planets."
					else:
						sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + currentUser + "' WHERE spawnID=" + spawnID + " AND planetID=" + dbShared.dbInsertSafe(planets) + ";"
						result = "Marked unavailable on " + ghNames.getPlanetName(planets)
				elif (availability == "1"):
					# mark (re)available on planet
					cursor.execute("SELECT enteredBy, unavailable FROM tResourcePlanet WHERE spawnID=" + str(spawnID) + " AND planetID=" + str(planets) + ";")
					row = cursor.fetchone()
					if row == None:
						# insert spawn planet record
						sqlStr = "INSERT INTO tResourcePlanet (spawnID, planetID, entered, enteredBy) VALUES (" + str(spawnID) + "," + str(planets) + ",NOW(),'" + currentUser + "');"
						result = "Marked available on " + ghNames.getPlanetName(planets)
					else:
						sqlStr = "UPDATE tResourcePlanet SET unavailable = NULL WHERE spawnID=" + str(spawnID) + " AND planetID=" + str(planets) + ";"
						result = "Marked re-available on " + ghNames.getPlanetName(planets)
						availability = -1

				# Only allow update if user has positive reputation
				stats = dbShared.getUserStats(currentUser, galaxy).split(",")
				admin = dbShared.getUserAdmin(conn, currentUser, galaxy)
				if (int(stats[2]) < ghShared.MIN_REP_VALS['REMOVE_RESOURCE'] and enteredBy != currentUser) and availability == "0" and not admin:
					result = "Error: You must earn a little reputation on the site before you can edit resources.  Try adding or verifying some first. \r\n"
				else:
					cursor.execute(sqlStr)

					if (availability == "0"):
						# add cleanup event
						if not planets.isdigit():
							planets = 0
						dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(galaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'r'," + str(planets) + ");", 'r', currentUser, galaxy, str(spawnID))

					elif (availability == "1"):
						# add resource planet add event
						dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(galaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'p'," + str(planets) + ");", 'p', currentUser, galaxy, str(spawnID))

					result = spawnName
			else:
				result = "Error: That galaxy is currently inactive."
		else:
			result = "Error: You must provide a spawn ID or a spawn Name and galaxy ID"
		cursor.close()
	else:
		result = "Error: No existing resource data"
	conn.close()
else:
	result = "Error: You must be logged in to change resource availability."

print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
