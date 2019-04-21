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
import re
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
from xml.dom import minidom

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
galaxy = form.getfirst("galaxy", "")
updateList = form.getfirst("updateList", "")
operation = form.getfirst("operation", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
updateList = dbShared.dbInsertSafe(updateList)
updateList = updateList.split(",")

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

#  Check for errors
errstr = ""
fc = len(updateList)
if (galaxy == ""):
	errstr = errstr + "Error: no galaxy selected. \r\n"
if fc > 0:
	for x in range(fc):
		if updateList[x] != "":
			thisUpdate = updateList[x].split(":")
			if len(thisUpdate) != 2:
				errstr = errstr + "Error: Malformed data in inventory adjustment."
				sys.stderr.write(str(thisUpdate))
			else:
				resName = thisUpdate[0]
				qtyAdjust = thisUpdate[1]
			if qtyAdjust.isdigit() != True:
				errstr = errstr + "Error: Quantity for {0} ({1}) was not valid. \n".format(resName, qtyAdjust)
else:
	errstr = errstr + "Error: No update data provided.\r\n"

if operation not in ['-','+']:
	errstr = errstr + "Error: Invalid operation ({0}).  - or + are allowed.".format(operation)

udCount = 0
# Only process if no errors
if (errstr == ""):
	result = ""
	if (logged_state > 0):
		# Alter inventory
		conn = dbShared.ghConn()
		# Open each item
		for x in range(fc):
			if updateList[x] != "":
				thisUpdate = updateList[x].split(":")
				resName = thisUpdate[0]
				resID = dbShared.getSpawnID(resName, galaxy)
				qtyAdjust = thisUpdate[1]
				cursor = conn.cursor()
				cursor.execute("SELECT units FROM tFavorites WHERE galaxy=%s AND userID=%s and favType=1 AND itemID=%s;", [galaxy, currentUser, resID])
				row = cursor.fetchone()
				if row != None:
					if row[0] == None:
						currentAmount = 0
					else:
						currentAmount = row[0]
					adjustedAmount = eval("{0} {1} {2}".format(str(currentAmount), operation, qtyAdjust))
					if adjustedAmount < -2147483647 or adjustedAmount > 2147483647:
						result = result + "I can't handle numbers that big for (" + resName + ")\n "
						break
					if adjustedAmount <= 0:
						result = result + " Warning: adjustment for " + resName + " resulted in depletion of inventory (" + str(adjustedAmount) + " units."
						adjustedAmount = 0
					cursor.execute("UPDATE tFavorites SET units=%s WHERE galaxy=%s AND userID=%s AND favType=1 AND itemID=%s;", [adjustedAmount, galaxy, currentUser, resID])
					udCount += 1
				else:
					result = result + "Warning: Did not find any (" + resName + ") in your favorites list.\n "
				cursor.close()

		conn.close()
		result = result + "Inventory update complete: " + str(udCount) + " updated."
	else:
		result = result + "Error: must be logged in to update inventory"
else:
	result = errstr

print 'Content-type: text/xml\n'
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eName = doc.createElement("udCount")
tName = doc.createTextNode(str(udCount))
eName.appendChild(tName)
eRoot.appendChild(eName)
eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print doc.toxml()

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
