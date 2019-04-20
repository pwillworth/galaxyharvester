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


def removeSpawn(spawnID, planets, userID, galaxy):
	markAll = 0
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		if (planets == "all"):
			markAll = 1
			sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + userID + "' WHERE spawnID=" + str(spawnID) + ";"
		else:
			# try to look up planet by name if an ID was not provided
			if (planets.isdigit() != True):
				planets = dbShared.getPlanetID(planets)
			sqlStr = "UPDATE tResourcePlanet SET unavailable=NOW(), unavailableBy='" + userID + "' WHERE spawnID=" + str(spawnID) + " AND planetID=" + str(planets) + ";"

		# Only allow removal if user has positive reputation
		stats = dbShared.getUserStats(userID, galaxy).split(",")
		admin = dbShared.getUserAdmin(conn, userID, galaxy)
		cursor.execute("SELECT enteredBy, unavailable FROM tResources WHERE spawnID=%s;", [spawnID])
		row = cursor.fetchone()
		if int(stats[2]) < ghShared.MIN_REP_VALS['REMOVE_RESOURCE'] and row[0] != userID and not admin:
			result = "Error: You must earn a little reputation on the site before you can remove resources.  Try adding or verifying some first. \r\n"
		elif row[1] != None:
			result = "Error: You cannot remove that resource because it is already removed."
		else:
			cursor.execute(sqlStr)

			# add cleanup event
			if not planets.isdigit():
				planets = 0
			dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(galaxy) + "," + str(spawnID) + ",'" + userID + "',NOW(),'r'," + str(planets) + ");", 'r', userID, galaxy, str(spawnID))
			result = "Spawn marked unavailable."
		cursor.close()
	else:
		result = "Error: Could not connect to database"
	conn.close()
	
	return result


def main():
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

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess


	# Main program
	print 'Content-type: text/html\n'
	if (logged_state > 0):
		if (dbShared.galaxyState(galaxy) == 1):
			spawnID = dbShared.getSpawnID(spawnName, galaxy)
			result = removeSpawn(spawnID, planets, currentUser, galaxy)
		else:
			result = "Error: That Galaxy is Inactive."

	else:
		result = "Error: You must be logged in to mark a resource unavailable."

	print result
	if (result.find("Error:") > -1):
		sys.exit(500)
	else:
		sys.exit(200)

if __name__ == "__main__":
        main()
