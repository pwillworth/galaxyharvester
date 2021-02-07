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
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
#

def deleteSchematic(conn, schematicID):
	# Remove Qualities data
	delCursor = conn.cursor()
	qualCursor = conn.cursor()
	qualCursor.execute('SELECT expQualityID FROM tSchematicQualities WHERE schematicID=%s;', (schematicID))
	qualRow = qualCursor.fetchone()
	while qualRow != None:
		delCursor.execute('DELETE FROM tSchematicResWeights WHERE expQualityID=%s;', (qualRow[0]))
		qualRow = qualCursor.fetchone()
	qualCursor.close()
	delCursor.execute('DELETE FROM tSchematicQualities WHERE schematicID=%s;', (schematicID))
	# Remove ingredients and main schematic record.
	delCursor.execute('DELETE FROM tSchematicIngredients WHERE schematicID=%s;', (schematicID))
	delCursor.execute('DELETE FROM tSchematic WHERE schematicID=%s;', (schematicID))
	schemDeleted = cursor.rowcount
	delCursor.close()

	if schemDeleted > 0:
		return 'Schematic deleted.'
	else:
		return 'Error: No records to delete were found, could not find schematic.'

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
	sid = form.getfirst('gh_sid', '')

schematicID = form.getfirst('schematicID', '')
userGalaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
schematicID = dbShared.dbInsertSafe(schematicID)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program
owner = ''
galaxy = 0
schematicName = ''
print('Content-type: text/html\n')
if (logged_state > 0):
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		# check owner
		cursor.execute('SELECT enteredBy, galaxy, schematicName FROM tSchematic WHERE schematicID=%s;', (schematicID))
		row = cursor.fetchone()
		cursor.close()
		if (row != None):
			owner = row[0]
			galaxy = row[1]
			schematicName = row[2]

		# Lookup reputation to validate abilities
		if galaxy != 0:
			repGalaxy = galaxy
		else:
			repGalaxy = userGalaxy
		stats = dbShared.getUserStats(currentUser, repGalaxy).split(",")
		userReputation = int(stats[2])
		admin = dbShared.getUserAdmin(conn, currentUser, repGalaxy)
		# remove it
		if owner == currentUser:
			result = deleteSchematic(conn, schematicID)
		else:
			if galaxy != 0:
				if admin or userReputation >= ghShared.MIN_REP_VALS['EDIT_OTHER_SCHEMATIC']:
					result = deleteSchematic(conn, schematicID)
				else:
					result = 'Error: You do not have enough reputation to edit other users schematics.'
			else:
				if admin or userReputation >= ghShared.MIN_REP_VALS['EDIT_OTHER_SCHEMATIC']:
					cursor = conn.cursor()
					cursor.execute('INSERT INTO tSchematicOverrides (schematicID, galaxyID) VALUES (%s, %s);', [schematicID, userGalaxy])
					result = str(cursor.rowcount)
					if result != "1":
						result = 'Error: Failed to delete schematic for this galaxy with override method, please contact Administrator.'
					else:
						result = 'Schematic deleted.'
				else:
					result = 'Error: You do not have enough reputation to edit other users schematics.'

		if result.find("Error:") < 0:
			dbShared.logSchematicEvent(0, galaxy, schematicID, currentUser, 'd', 'Deleted custom schematic {0}.'.format(schematicName), 'history')
	else:
		result = "Error: No data connection"
	conn.close()
else:
	result = "Error: You must be logged in delete schematics."

print(result)

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
