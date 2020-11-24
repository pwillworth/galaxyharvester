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
import re
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
from xml.dom import minidom
import ghNames
#
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
	loginResult = 'success'
	sid = form.getfirst('gh_sid', '')

# Get form info
wpID = form.getfirst("wpID", "")
galaxy = form.getfirst("galaxy", "")
planet = form.getfirst("planet", "")
spawnID = form.getfirst("resID", "")
spawnName = form.getfirst("resName", "")
price = form.getfirst("price", "0")
concentration = form.getfirst("concentration", "")
location = form.getfirst("location", "")
wpName = form.getfirst("wpName", "")
shareLevel = form.getfirst("shareLevel", "")
forceOp = form.getfirst("forceOp", "")
waypointID = form.getfirst("waypointID", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
wpID = dbShared.dbInsertSafe(wpID)
galaxy = dbShared.dbInsertSafe(galaxy)
planet = dbShared.dbInsertSafe(planet)
spawnID = dbShared.dbInsertSafe(spawnID)
spawnName = dbShared.dbInsertSafe(spawnName)
price = dbShared.dbInsertSafe(price)
concentration = dbShared.dbInsertSafe(concentration)
location = dbShared.dbInsertSafe(location)
wpName = dbShared.dbInsertSafe(wpName)
shareLevel = dbShared.dbInsertSafe(shareLevel)
forceOp = dbShared.dbInsertSafe(forceOp)
waypointID = dbShared.dbInsertSafe(waypointID)

lattitude = ""
longitude = ""
result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

def n2n(inVal):
	if (inVal == '' or inVal == None or inVal == 'undefined' or inVal == 'None'):
		return 'NULL'
	else:
		return str(inVal)


def addWaypoint(spawnID, planetID, price, concentration, lattitude, longitude, wpName, shareLevel):
	# Add new waypoint
	returnStr = ""
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	tempSQL = "INSERT INTO tWaypoint (spawnID, planetID, owner, price, concentration, lattitude, longitude, waypointType, waypointName, shareLevel, entered) VALUES (" + str(spawnID) + "," + str(planetID) + ",'" + currentUser + "'," + price + "," + str(concentration) + "," + str(lattitude) + "," + str(longitude) + ",'u','" + wpName + "'," + str(shareLevel) + ",NOW());"
	try:
		cursor.execute(tempSQL)
		returnStr = "Waypoint added."
		waypointID = cursor.lastrowid
	except:
		returnStr = 'Error: Add Failed.'

	if str(waypointID).isdigit():
		dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(galaxy) + "," + str(spawnID) + ",'" + currentUser + "',NOW(),'w'," + str(planetID) + ");","w",currentUser, galaxy, str(spawnID))

	cursor.close()
	conn.close()
	return returnStr

def updateWaypoint(waypointID, spawnID, planetID, price, concentration, lattitude, longitude, wpName, shareLevel):
	# Update waypoint information
	returnStr = ""
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	tempSQL = "UPDATE tWaypoint SET spawnID=" + str(spawnID) + ", planetID=" + str(planetID) + ", price=" + price + ", concentration=" + str(concentration) + ", lattitude=" + str(lattitude) + ", longitude=" + str(longitude) + ", waypointName='" + wpName + "', shareLevel=" + str(shareLevel) + " WHERE waypointID=" + str(waypointID) + ";"
	cursor.execute(tempSQL)
	result = cursor.rowcount
	if (result < 1):
		returnStr = "Error: waypoint not updated."
	else:
		returnStr = " waypoint updated."

	cursor.close()
	conn.close()
	return returnStr

def getSpawnID(resName, galaxy):
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	cursor.execute("SELECT spawnID FROM tResources WHERE galaxy=" + galaxy + " AND spawnName='" + resName + "';")
	row = cursor.fetchone()
	if row == None:
		newid = -1
	else:
		newid = row[0]

	cursor.close()
	conn.close()
	return newid

#  Check for errors
errstr = ""
if (shareLevel.isdigit() != True):
	errstr = errstr + "Error: Invalid share level. \r\n"
else:
	if (int(shareLevel) != 256):
		errstr = errstr + "Error: You can only post public waypoints. \r\n"
if (len(spawnName) < 1 and spawnID == ""):
	errstr = errstr + "Error: no resource name. \r\n"
if (spawnID == "" and galaxy == ""):
	errstr = errstr + "Error: no galaxy selected. \r\n"
if ((wpName == "none" or len(wpName) < 1) and spawnID == ""):
	errstr = errstr + "Error: You must enter a Name/Description of the waypoint. \r\n"
if re.search('\W', spawnName):
	errstr = errstr + "Error: spawn name contains illegal characters."
if (forceOp != "edit" and planet.isdigit() == False):
	errstr = errstr + "Error: planet must be provided to post waypoint unless editing."
if (concentration[-1:] == "%"):
	concentration = concentration[:-1]
#sys.stderr.write("conc: " + concentration)
if (concentration.isdigit() != True):
	errstr = errstr + "Error: Concentration entered was not a valid number."
else:
	if float(concentration) < 0 or float(concentration) > 100:
		errstr = errstr + "Error: Concentration should be a number between 0 and 100"

if (location.find(",") > -1):
	try:
		lattitude = int(location[:location.find(",")].rstrip())
		longitude = int(location[location.find(",")+1:].lstrip())
		if (lattitude < -8192 or lattitude > 8192 or longitude < -8192 or longitude > 8192):
			errstr = errstr + "Error: Invalid location coordinates.  Value too large.  "
	except ValueError:
		errstr = errstr + "Error: Could not identify lat/lon as numbers.  "

else:
	errstr = errstr + "Error: location is not in the right format. Separate the cooridinates with a comma."

# Only process if no errors or just verifying
if (errstr == "" or (forceOp == "verify" and wpID != None and wpID.isdigit())):
	result = ""
	if (logged_state > 0):
		if forceOp != "verify":
			if (spawnName == "" or spawnName == None):
				spawnName = ghNames.getSpawnName(spawnID)
			# First see if resource is entered at all
			if (spawnID == ""):
				spawnID = getSpawnID(spawnName, galaxy)

		if (spawnID > -1 or forceOp == "verify"):
			# waypoint already entered?
			if (wpID != None and wpID.isdigit()):
				# check owner
				try:
					conn = dbShared.ghConn()
					cursor = conn.cursor()
				except Exception:
					result = "Error: could not connect to database"

				if (cursor):
					cursor.execute('SELECT owner FROM tWaypoint WHERE waypointID=' + str(wpID) + ';')
					row = cursor.fetchone()

					if (row != None):
						owner = row[0]
					else:
						owner = ''

					cursor.close()

					if forceOp == "verify":
						if galaxy.isdigit():
							if owner != currentUser:
								dbShared.logUserEvent(currentUser, galaxy, "w", wpID, "v")
								result = "Verified!"
							else:
								result = "Error: You can not verify your own waypoint."
						else:
							result = "Error: You did not specify the galaxy."
					else:
						# edit it
						if owner == currentUser:
							result = "edit: "
							result = result + updateWaypoint(wpID, spawnID, planet, price, int(concentration), lattitude, longitude, wpName, shareLevel)
						else:
							result = "Error: You are not the owner of that waypoint."
				else:
					result = "Error: No database connection"
				conn.close()

			else:
				# check for duplicate public waypoints
				try:
					conn = dbShared.ghConn()
					cursor = conn.cursor()
				except Exception:
					result = "Error: could not connect to database"

				owner = ''
				if (cursor):
					if int(shareLevel) == 256:
						cursor.execute('SELECT owner FROM tWaypoint WHERE spawnID=' + str(spawnID) + ' AND planetID=' + str(planet) + ' AND shareLevel=256 AND lattitude BETWEEN ' + str(lattitude-50) + ' AND ' + str(lattitude + 50) + ' AND longitude BETWEEN ' + str(longitude - 50) + ' AND ' + str(longitude + 50) + ';')
						row = cursor.fetchone()

						if (row != None):
							owner = row[0]
						cursor.close()

					if owner == '':
                                                result = addWaypoint(spawnID, planet, price, int(concentration), lattitude, longitude, wpName, shareLevel)

					else:
						result = "Error: That public waypoint has already been entered by " + owner
				else:
					result = "Error: No database connection"
				conn.close()
		else:
			# spawn cannot be found
			result = "Error: I can not find the resource name you entered in this galaxy."

	else:
		result = "Error: must be logged in to add waypoints"
else:
	result = errstr

print('Content-type: text/xml\n')
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eName = doc.createElement("waypointID")
tName = doc.createTextNode(waypointID)
eName.appendChild(tName)
eRoot.appendChild(eName)
eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print(doc.toxml())

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
