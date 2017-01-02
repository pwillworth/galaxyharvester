#!/usr/bin/python
"""

 Copyright 2016 Paul Willworth <ioscode@gmail.com>

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
fltTypes = form.getfirst("fltTypes", "")
alertTypes = form.getfirst("alertTypes", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
fltTypes = dbShared.dbInsertSafe(fltTypes)
alertTypes = dbShared.dbInsertSafe(alertTypes)

fltTypes = fltTypes.split(",")
alertTypes = alertTypes.split(",")

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

def n2n(inVal):
	if (inVal == '' or inVal == None or inVal == 'undefined' or inVal == 'None'):
		return 'NULL'
	else:
		return str(inVal)

fltCount = 0
#  Check for errors
errstr = ""

if (galaxy == ""):
	errstr = errstr + "Error: no galaxy selected. \r\n"

doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

# Only process if no errors
if (errstr == ""):
	result = ""
	if (logged_state > 0):
		conn = dbShared.ghConn()
		# open list of users existing filters
		cursor = conn.cursor()
		cursor.execute("SELECT rowOrder, fltType, fltValue, alertTypes, CRmin, CDmin, DRmin, FLmin, HRmin, MAmin, PEmin, OQmin, SRmin, UTmin, ERmin, groupName FROM tFilters LEFT JOIN (SELECT resourceGroup, groupName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) typegroup ON tFilters.fltValue = typegroup.resourceGroup WHERE galaxy=" + str(galaxy) + " AND userID='" + currentUser + "' ORDER BY rowOrder;")
		row = cursor.fetchone()
		while row != None:
			fltType = row[1]
			fltValue = row[2]
			eFilter = doc.createElement("filter")
			eRoot.appendChild(eFilter)

			eOrder = doc.createElement("fltOrder")
			tOrder = doc.createTextNode(str(row[0]))
			eOrder.appendChild(tOrder)
			eFilter.appendChild(eOrder)

			eType = doc.createElement("fltType")
			tType = doc.createTextNode(str(fltType))
			eType.appendChild(tType)
			eFilter.appendChild(eType)

			eValue = doc.createElement("fltValue")
			tValue = doc.createTextNode(str(fltValue))
			eValue.appendChild(tValue)
			eFilter.appendChild(eValue)

			eAlerts = doc.createElement("alertTypes")
			tAlerts = doc.createTextNode(str(row[3]))
			eAlerts.appendChild(tAlerts)
			eFilter.appendChild(eAlerts)

			eCR = doc.createElement("CRmin")
			tCR = doc.createTextNode(str(row[4]))
			eCR.appendChild(tCR)
			eFilter.appendChild(eCR)
			eCD = doc.createElement("CDmin")
			tCD = doc.createTextNode(str(row[5]))
			eCD.appendChild(tCD)
			eFilter.appendChild(eCD)
			eDR = doc.createElement("DRmin")
			tDR = doc.createTextNode(str(row[6]))
			eDR.appendChild(tDR)
			eFilter.appendChild(eDR)
			eFL = doc.createElement("FLmin")
			tFL = doc.createTextNode(str(row[7]))
			eFL.appendChild(tFL)
			eFilter.appendChild(eFL)
			eHR = doc.createElement("HRmin")
			tHR = doc.createTextNode(str(row[8]))
			eHR.appendChild(tHR)
			eFilter.appendChild(eHR)
			eMA = doc.createElement("MAmin")
			tMA = doc.createTextNode(str(row[9]))
			eMA.appendChild(tMA)
			eFilter.appendChild(eMA)
			ePE = doc.createElement("PEmin")
			tPE = doc.createTextNode(str(row[10]))
			ePE.appendChild(tPE)
			eFilter.appendChild(ePE)
			eOQ = doc.createElement("OQmin")
			tOQ = doc.createTextNode(str(row[11]))
			eOQ.appendChild(tOQ)
			eFilter.appendChild(eOQ)
			eSR = doc.createElement("SRmin")
			tSR = doc.createTextNode(str(row[12]))
			eSR.appendChild(tSR)
			eFilter.appendChild(eSR)
			eUT = doc.createElement("UTmin")
			tUT = doc.createTextNode(str(row[13]))
			eUT.appendChild(tUT)
			eFilter.appendChild(eUT)
			eER = doc.createElement("ERmin")
			tER = doc.createTextNode(str(row[14]))
			eER.appendChild(tER)
			eFilter.appendChild(eER)
			eName = doc.createElement("valueName")
			tName = doc.createTextNode(str(row[15]))
			eName.appendChild(tName)
			eFilter.appendChild(eName)
			fltCount = fltCount + 1
			row = cursor.fetchone()

		cursor.close()
		conn.close()
		result = "Fetched " + str(fltCount) + " filters."
	else:
		result = "Error: must be logged in to update alerts"
else:
	result = errstr

print 'Content-type: text/xml\n'


eName = doc.createElement("fltCount")
tName = doc.createTextNode(str(fltCount))
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
