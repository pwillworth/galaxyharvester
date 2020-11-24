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
import time
from datetime import timedelta, datetime
import ghShared
import dbShared

PAGE_SIZE = 42

def getHistorySQL(uid, timeCriteria, galaxy):
	if uid == '':
		return 'SELECT userID, eventTime, spawnName, eventType, planetName, tResources.resourceType, tResourceType.resourceTypeName, containerType, tResources.galaxy FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType LEFT JOIN tPlanet ON tResourceEvents.planetID = tPlanet.planetID WHERE tResourceEvents.galaxy=' + galaxy + timeCriteria + ' ORDER BY eventTime DESC LIMIT ' + str(PAGE_SIZE) + ';'
	else:
		return 'SELECT galaxyName, eventTime, spawnName, eventType, planetName, tResources.resourceType, tResourceType.resourceTypeName, containerType, tResources.galaxy FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID INNER JOIN tGalaxy ON tResourceEvents.galaxy = tGalaxy.galaxyID INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType LEFT JOIN tPlanet ON tResourceEvents.planetID = tPlanet.planetID WHERE userID="' + uid + '"' + timeCriteria + ' ORDER BY eventTime DESC LIMIT ' + str(PAGE_SIZE) + ';'


form = cgi.FieldStorage()

galaxy = form.getfirst('galaxy', '')
uid = form.getfirst('uid', '')
lastTime = form.getfirst('lastTime', '')
formatType = form.getfirst('formatType', '')
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)
uid = dbShared.dbInsertSafe(uid)
lastTime = dbShared.dbInsertSafe(lastTime)
timeCriteria = ''
errors = ''
responseData = ''

# Main program
firstCol = 'Member'
if uid != '':
	firstCol = 'Galaxy'

if formatType == 'json':
	print('Content-type: text/json\n')
else:
	print('Content-type: text/html\n')

if uid == '' and galaxy == '':
	errors = 'Error: you must specify a user id or galaxy to get history for.'

if (len(lastTime) > 5):
	timeCriteria = " AND eventTime < '" + lastTime + "'"

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor and errors == ''):
	if formatType == 'json':
		responseData = '{\n'
		responseData += ' "server_time" : "' + datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + '",\n'
		responseData += ' "events" : [\n'
	else:
		responseData = '<table class="userData" width="620">\n'
		responseData += '<thead><tr class="tableHead"><td width="100">' + firstCol + '</td><td width="140">Time</td><td width="85">Spawn</td><td width="175">Resource Type</td><td width="70">Action</td><td width="50">Planet</td></th></thead>\n'

	cursor.execute(getHistorySQL(uid, timeCriteria, galaxy))
	row = cursor.fetchone()

	while (row != None):
		if formatType == 'json':
			responseData += '  {\n'
			responseData += '    "' + firstCol + '" : "' + row[0] + '",\n'
			responseData += '    "time" : "' + str(row[1]) + '",\n'
			responseData += '    "spawn_name" : "' + row[2] + '",\n'
			responseData += '    "event_type" : "' + row[3] + '",\n'
			responseData += '    "planet_name" : "' + str(row[4]) + '",\n'
			responseData += '    "resource_type" : "' + row[5] + '",\n'
			responseData += '    "resource_type_name" : "' + row[6] + '",\n'
			responseData += '    "container_type" : "' + row[7] + '"\n'
			responseData += '  },\n'
		else:
			responseData += '  <tr class="statRow"><td>' + row[0] + '</td><td>' + str(row[1]) + '</td><td><a href="' + ghShared.BASE_SCRIPT_URL + 'resource.py/' + str(row[8]) + '/' + row[2] + '" class="nameLink">' + row[2] + '</a></td><td><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[5] + '" class="nameLink">' + row[6] + '</a></td><td>' + ghShared.getActionName(row[3]) + '</td><td>' + str(row[4]) + '</td>'
			responseData += '  </tr>'
		lastTime = row[1]
		row = cursor.fetchone()

	if formatType == 'json':
		responseData += '],\n'
	else:
		responseData += '  </table>'

	if (cursor.rowcount == PAGE_SIZE):
		if formatType == 'json':
			responseData += ' "more_events" : "yes"\n'
		else:
			responseData += '<div style="text-align:center;"><button id="moreButton" class="ghButton" onclick="moreHistory(\''+ str(lastTime) + '\');">More</button></div>'
	cursor.close()
	if formatType == 'json':
		responseData += '}'
else:
	errors = "Error: Database unavailable"
conn.close()

if errors == '':
	print(responseData)
	sys.exit(200)
else:
	if formatType == 'json':
		print('{ "response" : "' + errors + '"}')
	else:
		print(errors)
	sys.exit(500)
