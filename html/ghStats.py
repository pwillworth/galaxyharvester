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
from xml.dom import minidom
#
form = cgi.FieldStorage()

galaxy = form.getfirst('galaxy', '')
statID = form.getfirst('statID', '')
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)

# Main program
rowCount = 0
result = ''
currentSpawnsSQL = 'SELECT Count(spawnID) FROM tResources WHERE galaxy=' + galaxy + ' AND unavailable IS NULL;'
totalSpawnsSQL = 'SELECT totalSpawns, galaxyName FROM tGalaxy WHERE galaxyID=' + galaxy + ';'
currentWaypointsSQL = 'SELECT Count(*) FROM tWaypoint INNER JOIN tResources ON tWaypoint.spawnID = tResources.spawnID WHERE galaxy=' + galaxy + ' AND tWaypoint.unavailable IS NULL AND tResources.unavailable IS NULL;'

if statID == "all":
	print('Content-type: text/xml\n')
else:
	print('Content-type: text/html\r\n\r\n')

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	if statID == 'all':
		doc = minidom.Document()
		eRoot = doc.createElement("result")
		doc.appendChild(eRoot)

		cursor.execute(totalSpawnsSQL)
		row = cursor.fetchone()
		if (row != None):
			eGalaxy = doc.createElement("galaxyName")
			tGalaxy = doc.createTextNode(row[1])
			eGalaxy.appendChild(tGalaxy)
			eRoot.appendChild(eGalaxy)

			eTotalSpawns = doc.createElement("totalSpawns")
			tTotalSpawns = doc.createTextNode(str(row[0]))
			eTotalSpawns.appendChild(tTotalSpawns)
			eRoot.appendChild(eTotalSpawns)
		else:
			result = "Error: Galaxy not found"

		cursor.execute(currentSpawnsSQL)
		row = cursor.fetchone()
		if (row != None):
			eCurrentSpawns = doc.createElement("currentSpawns")
			tCurrentSpawns = doc.createTextNode(str(row[0]))
			eCurrentSpawns.appendChild(tCurrentSpawns)
			eRoot.appendChild(eCurrentSpawns)

		cursor.execute(currentWaypointsSQL)
		row = cursor.fetchone()
		if (row != None):
			eCurrentWaypoints = doc.createElement("currentWaypoints")
			tCurrentWaypoints = doc.createTextNode(str(row[0]))
			eCurrentWaypoints.appendChild(tCurrentWaypoints)
			eRoot.appendChild(eCurrentWaypoints)

		print(doc.toxml())

	else:
		if statID == 'currentSpawns':
			sqlStr = currentSpawnsSQL
		elif statID == 'totalSpawns':
			sqlStr = totalSpawnsSQL
		elif statID == 'currentWaypoints':
			sqlStr = currentWaypointsSQL
		else:
			sqlStr = 'SELECT \'Unknown statID\';'

		cursor.execute(sqlStr)
		row = cursor.fetchone()

		if (row != None):
			print(str(row[0]))
		else:
			result = "Error: Galaxy not found."
			print(result)

	cursor.close()
else:
	result = "Error: Database unavailable"
conn.close()

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
