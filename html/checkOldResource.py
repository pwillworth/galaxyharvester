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

import sys
import dbShared
import cgi
import pymysql
from xml.dom import minidom
import ghShared
#

form = cgi.FieldStorage()

spawnName = form.getfirst('spawn', '')
galaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
spawnName = dbShared.dbInsertSafe(spawnName)
galaxy = dbShared.dbInsertSafe(galaxy)



# Main program

print('Content-type: text/xml\n')
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eName = doc.createElement("spawnName")
tName = doc.createTextNode(spawnName)
eName.appendChild(tName)
eRoot.appendChild(eName)

try:
	conn = dbShared.ghConn()
	cursor = conn.cursor()
except Exception:
	result = "Error: could not connect to database"

if (cursor):
	cursor.execute('SELECT spawnID, spawnName, resourceType, entered FROM tResources WHERE galaxy=' + galaxy + ' AND spawnName != \'' + spawnName + '\' AND unavailable IS NULL AND resourceType=(SELECT resourceType FROM tResources WHERE spawnName=\'' + spawnName + '\' AND galaxy=' + galaxy + ') AND resourceType IN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup IN (\'flora_resources\',\'creature_resources\') GROUP BY resourceType);')
	row = cursor.fetchone()

	if (row != None):
		spawnID = str(row[0])

		eSpawn = doc.createElement("oldSpawnID")
		tSpawn = doc.createTextNode(spawnID)
		eSpawn.appendChild(tSpawn)
		eRoot.appendChild(eSpawn)

		eOldName = doc.createElement("oldSpawnName")
		tOldName = doc.createTextNode(row[1])
		eOldName.appendChild(tOldName)
		eRoot.appendChild(eOldName)

		eType = doc.createElement("resourceType")
		tType = doc.createTextNode(row[2])
		eType.appendChild(tType)
		eRoot.appendChild(eType)

		eAge = doc.createElement("resAge")
		tAge = doc.createTextNode(ghShared.timeAgo(row[3]))
		eAge.appendChild(tAge)
		eRoot.appendChild(eAge)

		result = "found"
	else:
		result = "new"
	cursor.close()
	conn.close()
else:
	result = "Error: could not connect to database"

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)

print(doc.toxml())
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
