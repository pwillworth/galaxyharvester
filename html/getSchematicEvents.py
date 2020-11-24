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
import serverBest


def refreshServerBestStatus(spawnID):
    # Calculate new current Server Best info for spawn only if it has not been calculated within last 2 hours
    result = ''
    sqlStr = 'SELECT eventTime FROM tServerBestStatus WHERE spawnID={0};'.format(spawnID)
    checkCursor = conn.cursor()
    checkCursor.execute(sqlStr)
    checkRow = checkCursor.fetchone()
    checkCursor.close()
    if checkRow != None:
        timeAgo = datetime.fromtimestamp(time.time()) - checkRow[0]
        hoursAgo = timeAgo.seconds / 3600
        if hoursAgo > 1:
            cleanCursor = conn.cursor()
            cleanCursor.execute('DELETE FROM tServerBestStatus WHERE spawnID=%s;', [spawnID])
            cleanCursor.close()
            result = serverBest.checkSpawn(spawnID, 'current')
        else:
            result = 'Current best use info was calculated for this resource {0} minutes ago, so displaying those results below.  Current best calculations cannot be run more than every 2 hours.\n'.format(str(timeAgo.seconds/60))
    else:
        result = serverBest.checkSpawn(spawnID, 'current')
    return result

form = cgi.FieldStorage()

spawnID = form.getfirst('spawnID', '')
formatType = form.getfirst('formatType', '')
schematicID = form.getfirst('schematicID', '')
serverBestMode = form.getfirst('serverBestMode', 'history')

errors = ''
responseData = ''

# Main program
if formatType == 'json':
	print('Content-type: text/json\n')
else:
	print('Content-type: text/html\n')

if spawnID.isdigit() == False and schematicID == '':
	errors = 'Error: you must provide a spawn to get schematic event history for, or a schematicID to get edit history for.'

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor and errors == ''):
	if spawnID.isdigit():
		criteriaStr = ' WHERE spawnID={0}'.format(spawnID)
	else:
		criteriaStr = ' WHERE spawnID=0 AND tSchematicEvents.schematicID="{0}"'.format(schematicID)

	if formatType == 'json':
		responseData = '{\n'
		responseData += ' "server_time" : "' + datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + '",\n'
		responseData += ' "events" : [\n'
	else:
		responseData = '<table class="userData" width="100%">\n'
		if spawnID.isdigit():
			responseData += '<thead><tr class="tableHead"><td width="100">Profession</td><td width="265">Schematic</td><td width="75">Property</td><td width="90">Rank</td></th></thead>\n'
		else:
			responseData += '<thead><tr class="tableHead"><td width="100">When</td><td width="65">Who</td><td width="65">Action</td><td width="440">Details</td></th></thead>\n'

	if spawnID.isdigit():
		if serverBestMode == 'current':
			eventTable = 'tServerBestStatus'
			result = refreshServerBestStatus(spawnID)
			if len(result) != 2:
				responseData += result
		else:
			eventTable = 'tSchematicEvents'
		cursor.execute("SELECT profName, {1}.schematicID, schematicName, expGroup, eventType FROM {1} INNER JOIN tSchematic ON {1}.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup INNER JOIN tProfession ON tSkillGroup.profID = tProfession.profID{0} ORDER BY profName, schematicName, expGroup".format(criteriaStr, eventTable))
	else:
		cursor.execute("SELECT eventTime, expGroup, eventType, eventDetail FROM tSchematicEvents{0} ORDER BY eventTime".format(criteriaStr))

	row = cursor.fetchone()

	lastTime = ''
	while (row != None):
		if formatType == 'json':
			responseData += '  {\n'
			responseData += '    "profession" : "' + row[0] + '",\n'
			responseData += '    "schematic_id" : "' + row[1] + '",\n'
			responseData += '    "schematic_name" : "' + row[2] + '",\n'
			responseData += '    "exp_group" : "' + row[3] + '",\n'
			responseData += '    "rank" : "' + row[4] + '",\n'
			responseData += '  },\n'
		else:
			if spawnID.isdigit():
				if row[4] != '1':
					if serverBestMode == 'current':
						rankStr = row[4]
					else:
						rankStr = 'Almost ({0})'.format(row[4])
				else:
					if serverBestMode == 'current':
						rankStr = 'Current Server Best'
					else:
						rankStr = 'New Server Best'
				responseData = ''.join((responseData, '  <tr class="statRow"><td>', row[0], '</td><td><a href="', ghShared.BASE_SCRIPT_URL, 'schematics.py/', row[1] + '">', row[2], '</a></td><td>', row[3].replace('exp_','').replace('exp','').replace('_', ' '), '</td><td>', rankStr, '</td>'))
				responseData += '  </tr>'
			else:
				responseData = ''.join((responseData, '  <tr class="statRow"><td>', str(row[0]), '</td><td><a href="', ghShared.BASE_SCRIPT_URL, 'user.py/', row[1] + '">', row[1], '</a></td><td>', ghShared.SCHEMATIC_EVENT_NAMES[row[2]], '</td><td>', row[3], '</td>'))
				responseData += '  </tr>'
		lastTime = row[0]
		row = cursor.fetchone()
	if len(lastTime) == 0:
		responseData += 'It seems this resource is not really good for much.'

	if formatType == 'json':
		responseData += '],\n}'
	else:
		responseData += '  </table>'

	cursor.close()

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
