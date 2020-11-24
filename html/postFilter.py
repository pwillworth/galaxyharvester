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
galaxy = form.getfirst("galaxy", "")
rowOrder = form.getfirst("rowOrder", "-1")
fltType = form.getfirst("fltType", "")
fltValue = form.getfirst("fltValue", "")
CRmin = form.getfirst("CRmin", "")
CDmin = form.getfirst("CDmin", "")
DRmin = form.getfirst("DRmin", "")
FLmin = form.getfirst("FLmin", "")
HRmin = form.getfirst("HRmin", "")
MAmin = form.getfirst("MAmin", "")
PEmin = form.getfirst("PEmin", "")
OQmin = form.getfirst("OQmin", "")
SRmin = form.getfirst("SRmin", "")
UTmin = form.getfirst("UTmin", "")
ERmin = form.getfirst("ERmin", "")
alertType = form.getfirst("alertType", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
rowOrder = dbShared.dbInsertSafe(rowOrder)
fltType = dbShared.dbInsertSafe(fltType)
fltValue = dbShared.dbInsertSafe(fltValue)
CRmin = dbShared.dbInsertSafe(CRmin)
CDmin = dbShared.dbInsertSafe(CDmin)
DRmin = dbShared.dbInsertSafe(DRmin)
FLmin = dbShared.dbInsertSafe(FLmin)
HRmin = dbShared.dbInsertSafe(HRmin)
MAmin = dbShared.dbInsertSafe(MAmin)
PEmin = dbShared.dbInsertSafe(PEmin)
OQmin = dbShared.dbInsertSafe(OQmin)
SRmin = dbShared.dbInsertSafe(SRmin)
UTmin = dbShared.dbInsertSafe(UTmin)
ERmin = dbShared.dbInsertSafe(ERmin)
alertType = dbShared.dbInsertSafe(alertType)

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


#  Check for errors
errstr = ""
if (galaxy == ""):
	errstr = errstr + "Error: no galaxy selected. \r\n"

if (fltType.isdigit() != True):
	errstr = errstr + "Error: Type was not valid. \r\n"
if (alertType.isdigit() != True and alertType != "-1"):
	errstr = errstr + "Error: Alert options was not valid. \r\n"
if (CRmin.isdigit() != True):
	CRmin = 0
if (CDmin.isdigit() != True):
	CDmin = 0
if (DRmin.isdigit() != True):
	DRmin = 0
if (FLmin.isdigit() != True):
	FLmin = 0
if (HRmin.isdigit() != True):
	HRmin = 0
if (MAmin.isdigit() != True):
	MAmin = 0
if (PEmin.isdigit() != True):
	PEmin = 0
if (OQmin.isdigit() != True):
	OQmin = 0
if (SRmin.isdigit() != True):
	SRmin = 0
if (UTmin.isdigit() != True):
	UTmin = 0
if (ERmin.isdigit() != True):
	ERmin = 0


# Only process if no errors
if (errstr == ""):
	result = ""
	if (logged_state > 0):
		conn = dbShared.ghConn()
		# open list of users existing filters
		cursor = conn.cursor()
		cursor.execute("SELECT alertTypes FROM tFilters WHERE galaxy=" + str(galaxy) + " AND userID='" + currentUser + "' AND rowOrder=" + str(rowOrder) + " AND fltType=" + str(fltType) + " AND fltValue='" + fltValue + "';")
		row = cursor.fetchone()
		if str(alertType) == "-1":
			# alert type -1 is code for delete it
			if row != None:
				cursor2 = conn.cursor()
				tempSQL = "DELETE FROM tFilters WHERE userID='" + currentUser + "' AND galaxy=" + str(galaxy) + " AND rowOrder=" + str(rowOrder) + " AND fltType=" + str(fltType) + " AND fltValue='" + fltValue + "';"
				cursor2.execute(tempSQL)
				result = "alert deleted."

				cursor2.close()
			else:
				result = "Error: could not find filter to remove."
		else:
			if row != None:
				cursor2 = conn.cursor()
				tempSQL = "UPDATE tFilters SET alertTypes=" + str(alertType) + ", CRmin=" + str(CRmin) + ", CDmin=" + str(CDmin) + ", DRmin=" + str(DRmin) + ", FLmin=" + str(FLmin) + ", HRmin=" + str(HRmin) + ", MAmin=" + str(MAmin) + ", PEmin=" + str(PEmin) + ", OQmin=" + str(OQmin) + ", SRmin=" + str(SRmin) + ", UTmin=" + str(UTmin) + ", ERmin=" + str(ERmin) + " WHERE userID='" + currentUser + "' AND galaxy=" + str(galaxy) + " AND rowOrder=" + str(rowOrder) + " AND fltType=" + str(fltType) + " AND fltValue='" + fltValue + "';"
				cursor2.execute(tempSQL)
				result = "alert updated."

				cursor2.close()
			else:
				cursor.execute("SELECT Max(rowOrder) FROM tFilters WHERE galaxy=" + str(galaxy) + " AND userID='" + currentUser + "';")
				row = cursor.fetchone()
				if row[0] != None:
					rowOrder = row[0] + 1
				else:
					rowOrder = 1
				cursor2 = conn.cursor()
				tempSQL = "INSERT INTO tFilters (userID, galaxy, rowOrder, fltType, fltValue, alertTypes, CRmin, CDmin, DRmin, FLmin, HRmin, MAmin, PEmin, OQmin, SRmin, UTmin, ERmin) VALUES ('" + currentUser + "', " + str(galaxy) + ", " + str(rowOrder) + ", " + str(fltType) + ", '" + fltValue + "', " + str(alertType) + ", " + str(CRmin) + ", " + str(CDmin) + ", " + str(DRmin) + ", " + str(FLmin) + ", " + str(HRmin) + ", " + str(MAmin) + ", " + str(PEmin) + ", " + str(OQmin) + ", " + str(SRmin) + ", " + str(UTmin) + ", " + str(ERmin) + ");"
				cursor2.execute(tempSQL)
				result = "alert added."

				cursor2.close()

		cursor.close()

		conn.close()
	else:
		result = "Error: must be logged in to update alerts"
else:
	result = errstr

print('Content-type: text/xml\n')
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print(doc.toxml())

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
