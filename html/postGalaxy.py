#!/usr/bin/python
"""

 Copyright 2018 Paul Willworth <ioscode@gmail.com>

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
from xml.dom import minidom
import ghNames
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
galaxy = form.getfirst("galaxyID", "")
galaxyName = form.getfirst("galaxyName", "")
galaxyState = form.getfirst("galaxyState", "")
galaxyNGE = form.getfirst("galaxyNGE", "")
galaxyPlanets = form.getfirst("galaxyPlanets", "")
galaxyAdmins = form.getfirst("galaxyAdmins", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
galaxyName = dbShared.dbInsertSafe(galaxyName)
galaxyState = dbShared.dbInsertSafe(galaxyState)
galaxyNGE = dbShared.dbInsertSafe(galaxyNGE)
galaxyPlanets = dbShared.dbInsertSafe(galaxyPlanets)
galaxyAdmins = dbShared.dbInsertSafe(galaxyAdmins)

galaxyPlanets = galaxyPlanets.split(",")
galaxyAdmins = galaxyAdmins.split(",")

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


def addGalaxy(galaxyName, galaxyNGE, galaxyPlanets, userID, galaxyAdmins):
	# Add new draft galaxy
	returnStr = "Galaxy submit failed."
	result = 0
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	
	tempSQL = "INSERT INTO tGalaxy (galaxyName, galaxyState, galaxyNGE, submittedBy) VALUES (%s, %s, %s, %s);"
	try:
		cursor.execute(tempSQL, (galaxyName, 0, galaxyNGE, userID))
		result = cursor.rowcount
	except Exception, e:
		returnStr = 'Error: Add Failed. {0}'.format(e)

	for planet in galaxyPlanets:
		if planet.isdigit():
			cursor.execute("INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (LAST_INSERT_ID(), %s)", [planet])
			result = result + cursor.rowcount
	for user in galaxyAdmins:
		if len(user) > 0:
			cursor.execute("INSERT INTO tGalaxyUser (galaxyID, userID, roleType) VALUES (LAST_INSERT_ID(), %s, %s);", [user, "a"])
			result = result + cursor.rowcount

	if returnStr.find("Error:") == -1 and result > 0:
		returnStr = "Galaxy submitted for review."
	cursor.close()
	conn.close()
	return returnStr

def updateGalaxy(galaxyID, galaxyName, galaxyState, galaxyNGE, galaxyPlanets, galaxyAdmins):
	# Update galaxy information
	returnStr = ""
	result = 0
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	
	tempSQL = "UPDATE tGalaxy SET galaxyName=%s, galaxyState=%s, galaxyNGE=%s WHERE galaxyID=%s;"
	cursor.execute(tempSQL, (galaxyName, galaxyState, galaxyNGE, galaxyID))
	result = cursor.rowcount

	cursor.execute("DELETE FROM tGalaxyPlanet WHERE galaxyID=%s;", [galaxyID])
	for planet in galaxyPlanets:
		if planet.isdigit():
			cursor.execute("INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (%s, %s)", [galaxyID, planet])
			result = result + cursor.rowcount
	cursor.execute("DELETE FROM tGalaxyUser WHERE galaxyID=%s AND roleType='a';", [galaxyID])
	for user in galaxyAdmins:
		if len(user) > 0:
			cursor.execute("INSERT INTO tGalaxyUser (galaxyID, userID, roleType) VALUES (%s, %s, %s);", [galaxyID, user, "a"])
			result = result + cursor.rowcount
	if (result < 1):
		returnStr = "Error: galaxy data not updated."
	else:
		returnStr = " galaxy data updated."

	cursor.close()
	conn.close()
	return returnStr


#  Check for errors
errstr = ""

if (galaxyName == ""):
	errstr = errstr + "Error: You must include the Galaxy name. \r\n"

if (len(galaxy) > 0 and galaxy != 'new' and galaxy.isdigit() != True):
	errstr = errstr + "Error: Galaxy ID was not a valid number.\n"
if len(galaxy) > 0 and galaxy != 'new' and galaxyState.isdigit() != True:
	errstr = errstr + "Error: Galaxy State was not a valid number.\n"
if (len(galaxyState) > 0 and galaxyState.isdigit() != True):
	errstr = errstr + "Error: Galaxy State was not a valid number.\n"

if galaxyNGE == '1' or galaxyNGE == 'checked':
	galaxyNGE = 1
else:
	galaxyNGE = 0

# Only process if no errors or just verifying
if (errstr == ""):
	result = ""
	if (logged_state > 0):
		# Edit existing galaxy info or submit new draft
		if len(galaxy) > 0 and galaxy != 'new':
			# check owner
			try:
				conn = dbShared.ghConn()
				cursor = conn.cursor()
			except Exception:
				result = "Error: could not connect to database"

			if (cursor):
				# Forbid approval by normal users
				cursor.execute('SELECT galaxyState FROM tGalaxy WHERE galaxyID=%s', [galaxy])
				row = cursor.fetchone()
				cursor.close()
				if row[0] == 0 and galaxyState != '0' and currentUser != 'ioscode':
					result = "Error: You may not change the status of this galaxy until it has been approved by the site administrator."
				else:
					# Get user galaxy admin status
					adminList = dbShared.getGalaxyAdminList(conn, currentUser)
					if '<option value="{0}">'.format(galaxy) in adminList:
						result = updateGalaxy(galaxy, galaxyName, galaxyState, galaxyNGE, galaxyPlanets, galaxyAdmins)
					else:
						result = "Error: You are not listed as an administrator of that galaxy."
			else:
				result = "Error: No database connection"
			conn.close()

		else:
			if 0 == 0:
				result = addGalaxy(galaxyName, galaxyNGE, galaxyPlanets, currentUser, galaxyAdmins)
			else:
				result = "Error: You don't have permission to add creature data yet."
	else:
		result = "Error: must be logged in to add galaxy data"
else:
	result = errstr

print 'Content-type: text/xml\n'
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print doc.toxml()

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
