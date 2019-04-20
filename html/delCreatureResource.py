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

galaxy = form.getfirst('galaxy', '')
resourceType = form.getfirst('resType', '')
creatureName = form.getfirst('creatureName', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
resourceType = dbShared.dbInsertSafe(resourceType)
creatureName = dbShared.dbInsertSafe(creatureName)

# Get a session
logged_state = 0
sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program
result = ""
if galaxy.isdigit() != True:
	result = "Error: Invalid galaxy ID provided."
else:
	if galaxy == 0:
		result = "Error: You cannot remove system shared creature resource data."
if logged_state != 1:
	result = "Error: You must be logged in delete creature data."

print "Content-type: text/html\n"
if result == "":
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		# Look up user reputation for later checks
		stats = dbShared.getUserStats(currentUser, galaxy).split(",")
		userReputation = int(stats[2])
		admin = dbShared.getUserAdmin(conn, currentUser, galaxy)
		# Lookup the data to remove
		cursor.execute("SELECT enteredBy FROM tResourceTypeCreature WHERE galaxy=%s AND resourceType=%s AND speciesName=%s;", (galaxy, resourceType, creatureName))
		row = cursor.fetchone()

		# Check for ownership or reputation before removing
		if row[0] == currentUser or userReputation >= ghShared.MIN_REP_VALS['EDIT_OTHER_CREATURE'] or admin:
			sqlStr = "DELETE FROM tResourceTypeCreature WHERE resourceType=%s AND speciesName=%s AND galaxy=%s;"
			cursor.execute(sqlStr, (resourceType, creatureName, galaxy))
			affRows = cursor.rowcount
			if affRows > 0:
				result = "Creature data removed."
			else:
				result = "Error: Creature data not found."

		else:
			result = "Error: You do not have permission to edit other users creature data."

		cursor.close()

	else:
		result = "Error: No data connection"
	conn.close()


print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
