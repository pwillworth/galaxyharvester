#!/usr/bin/python
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
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared
import ghShared
import ghNames

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

spawnID = form.getfirst("spawnID", '')
newSpawnName = form.getfirst("newSpawnName", '')
newGalaxyId = form.getfirst("newGalaxyId", '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
newSpawnName = dbShared.dbInsertSafe(newSpawnName)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid

#  Check for errors
errstr = ''
result = ''
if (spawnID.isdigit() == False):
	errstr = errstr + "No Spawn ID provided. \r\n"
if (logged_state == 0):
	errstr = errstr + "You must be logged in to do that. \r\n"
else:
	# Make sure user has enough rep to do this
	stats = dbShared.getUserStats(currentUser, 0).split(",")
	if int(stats[2]) < 50:
		errstr = errstr + "You do not have high enough reputation to do that. \r\n"

if (newSpawnName == '' and newGalaxyId.isdigit() == False):
    errstr = errstr + "You did not provide any valid update info."

if (errstr != ''):
	result = "Error: Resource admin operation failed because of the following errors:\r\n" + errstr
else:

	conn = dbShared.ghConn()
	checkCursor = conn.cursor()
	checkCursor.execute("SELECT spawnName, galaxy, galaxyName FROM tResources INNER JOIN tGalaxy ON tResources.galaxy = tGalaxy.galaxyID WHERE spawnID=%s", (spawnID))
	checkRow = checkCursor.fetchone()
	updated = "nothing"
	newLink = ""
	if checkRow != None:
		finalGalaxy = checkRow[1]
		finalName = checkRow[0]
		fixCursor = conn.cursor()
		# Update whichever item has changed
		if finalName != newSpawnName:
			# First make sure the new name does not already exist
			checkCursor2 = conn.cursor()
			checkCursor2.execute("SELECT spawnID FROM tResources WHERE spawnName=%s AND galaxy=%s", (newSpawnName, finalGalaxy))
			checkRow2 = checkCursor2.fetchone()
			if checkRow2 == None:
				fixCursor.execute("UPDATE tResources SET spawnName=%s WHERE spawnID=%s;", (newSpawnName, spawnID))
				if fixCursor.rowcount > 0:
					updated = "resource name"
					finalName = newSpawnName
					dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, eventDetail) VALUES (" + str(finalGalaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'n', '" + checkRow[0] + " to " + newSpawnName + "');", 'n', currentUser, finalGalaxy, spawnID)
			else:
				result = "Error: The name you are updating to already has been entered for this galaxy."
			checkCursor2.close()
		elif finalGalaxy != newGalaxyId:
			# First make sure the name does not already exist in new galaxy
			checkCursor2 = conn.cursor()
			checkCursor2.execute("SELECT spawnID FROM tResources WHERE spawnName=%s AND galaxy=%s", (finalName, newGalaxyId))
			checkRow2 = checkCursor2.fetchone()
			if checkRow2 == None:
				fixCursor.execute("UPDATE tResources SET galaxy=%s WHERE spawnID=%s;", (newGalaxyId, spawnID))
				if fixCursor.rowcount > 0:
					updated = "galaxy"
					dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, eventDetail) VALUES (" + str(finalGalaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'g','" + checkRow[2] + " to " + ghNames.getGalaxyName(newGalaxyId) + "');", 'g', currentUser, finalGalaxy, spawnID)
					finalGalaxy = newGalaxyId
			else:
				result = "Error: The galaxy you are updating to already has a spawn with that name entered."
			checkCursor2.close()
		else:
			updated = "nothing"

		fixCursor.close()

		if updated != "nothing":
			newLink = ": <a href='{0}resource.py/{1}/{2}'>Go to Updated Resource</a>".format(ghShared.BASE_SCRIPT_URL, finalGalaxy, finalName)
	else:
		result = "Error: SpawnID not found"
		updated = "nothing"

	checkCursor.close()
	conn.close()
	result = "{0} Updated{1} {2}".format(updated, newLink, result)

print "Content-Type: text/html\n"
print result
