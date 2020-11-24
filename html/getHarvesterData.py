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
import ghShared
#

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
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

# Get a session
logged_state = 0
linkappend = ''
galaxy = form.getfirst('galaxy', '')
uid = form.getfirst('uid', '')
period = form.getfirst('period', '')
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)
uid = dbShared.dbInsertSafe(uid)
sid = dbShared.dbInsertSafe(sid)
period = dbShared.dbInsertSafe(period)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program
errstr = ""
if (galaxy.isdigit() == False and uid == ''):
	errstr = errstr + "Error: no galaxy selected. \r\n"

tmpGalaxy = ''
tableStart = '<table class="userData" width="100%">'
print('Content-type: text/html\n')
if errstr == "":
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		if uid != '':
			tableStart += '<thead><tr class="tableHead"><td>Action</td><td>Updates</td></th></thead>'
			sqlStr = 'SELECT added, planet, edited, removed, verified, waypoint, galaxyName FROM tUserStats INNER JOIN tGalaxy ON tUserStats.galaxy = tGalaxy.galaxyID WHERE userID="' + uid + '" ORDER BY tGalaxy.galaxyID DESC;'
		else:
			tableStart += '<thead><tr class="tableHead"><td>Member</td><td>Action</td><td>Updates</td></th></thead>'
			if period == 'current':
				sqlStr = 'SELECT eventData.userID, action, numActions, pictureName FROM ('
				sqlStr = sqlStr + '(SELECT userID, \'Adds\' AS action, Count(*) AS numActions FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID WHERE tResourceEvents.galaxy=' + galaxy + ' AND unavailable IS NULL AND eventType=\'a\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ' UNION (SELECT userID, \'Planet Add\', Count(*) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID WHERE tResourceEvents.galaxy=' + galaxy + ' AND unavailable IS NULL AND eventType=\'p\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ' UNION (SELECT userID, \'Verified\', Count(*) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID WHERE tResourceEvents.galaxy=' + galaxy + ' AND unavailable IS NULL AND eventType=\'v\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ' UNION (SELECT userID, \'Waypoints\', Count(*) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID WHERE tResourceEvents.galaxy=' + galaxy + ' AND unavailable IS NULL AND eventType=\'w\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ') eventData INNER JOIN tUsers ON eventData.userID = tUsers.userID;'
			elif period == 'category':
				sqlStr = 'SELECT eventData.userID, action, numActions, pictureName FROM ('
				sqlStr = sqlStr + '(SELECT userID, \'Creature\' AS action, Count(*) AS numActions FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID INNER JOIN tResourceTypeGroup ON tResources.resourceType = tResourceTypeGroup.resourceType WHERE tResourceEvents.galaxy=' + galaxy + ' AND resourceGroup = \'creature_resources\' AND unavailable IS NULL AND eventType=\'a\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ' UNION (SELECT userID, \'Flora\', Count(*) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID INNER JOIN tResourceTypeGroup ON tResources.resourceType = tResourceTypeGroup.resourceType WHERE tResourceEvents.galaxy=' + galaxy + ' AND resourceGroup = \'flora_resources\' AND unavailable IS NULL AND eventType=\'a\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ' UNION (SELECT userID, \'Inorganic\', Count(*) FROM tResourceEvents INNER JOIN tResources ON tResourceEvents.spawnID = tResources.spawnID INNER JOIN tResourceTypeGroup ON tResources.resourceType = tResourceTypeGroup.resourceType WHERE tResourceEvents.galaxy=' + galaxy + ' AND resourceGroup = \'inorganic\' AND unavailable IS NULL AND eventType=\'a\' GROUP BY userID ORDER BY Count(*) DESC LIMIT 1)'
				sqlStr = sqlStr + ') eventData INNER JOIN tUsers ON eventData.userID = tUsers.userID;'
			else:
				sqlStr = 'SELECT tUserStats.userID, \'Adds\' AS action, added, pictureName FROM tUserStats INNER JOIN tUsers ON tUserStats.userID = tUsers.userID WHERE galaxy=' + galaxy + ' AND added != 0 AND added=(SELECT Max(added) FROM tUserStats WHERE galaxy=' + galaxy + ')'
				sqlStr = sqlStr + ' UNION SELECT tUserStats.userID, \'Planet Add\', planet, pictureName FROM tUserStats INNER JOIN tUsers ON tUserStats.userID = tUsers.userID WHERE galaxy=' + galaxy + ' AND planet != 0 AND planet=(SELECT Max(planet) FROM tUserStats WHERE galaxy=' + galaxy + ')'
				sqlStr = sqlStr + ' UNION SELECT tUserStats.userID, \'Cleanup\', removed, pictureName FROM tUserStats INNER JOIN tUsers ON tUserStats.userID = tUsers.userID WHERE galaxy=' + galaxy + ' AND removed != 0 AND removed=(SELECT Max(removed) FROM tUserStats WHERE galaxy=' + galaxy + ')'
				sqlStr = sqlStr + ' UNION SELECT tUserStats.userID, \'Verified\', verified, pictureName FROM tUserStats INNER JOIN tUsers ON tUserStats.userID = tUsers.userID WHERE galaxy=' + galaxy + ' AND verified != 0 AND verified=(SELECT Max(verified) FROM tUserStats WHERE galaxy=' + galaxy + ')'
				sqlStr = sqlStr + ' UNION SELECT tUserStats.userID, \'Waypoints\', waypoint, pictureName FROM tUserStats INNER JOIN tUsers ON tUserStats.userID = tUsers.userID WHERE galaxy=' + galaxy + ' AND waypoint != 0 AND waypoint=(SELECT Max(waypoint) FROM tUserStats WHERE galaxy=' + galaxy + ');'
		cursor.execute(sqlStr)
		row = cursor.fetchone()

		if uid == '':
			print(tableStart)
			while (row != None):
				print('  <tr class="statRow"><td><a href="' + ghShared.BASE_SCRIPT_URL + 'user.py/' + row[0] + '" class="nameLink"><img src="/images/users/'+ row[3] + '" class="tinyAvatar" /><span style="vertical-align:4px;">'+ row[0] + '</span></a></td><td>', row[1], '</td><td>', str(row[2]), '</td>')
				print('  </tr>')
				row = cursor.fetchone()
		else:
			if (row == None):
				print(tableStart)
			while (row != None):
				if row[6] != tmpGalaxy:
					if tmpGalaxy != '':
						print('</table>')
					tmpGalaxy = row[6]
					print('  <h3>Galaxy: ' + tmpGalaxy + '</h3>')
					print(tableStart)
				print('  <tr class="statRow"><td>Adds</td><td>'+ str(row[0]) + '</td></tr>')
				print('  <tr class="statRow"><td>Planet Add</td><td>'+ str(row[1]) + '</td></tr>')
				print('  <tr class="statRow"><td>Edits</td><td>'+ str(row[2]) + '</td></tr>')
				print('  <tr class="statRow"><td>Cleanup</td><td>'+ str(row[3]) + '</td></tr>')
				print('  <tr class="statRow"><td>Verified</td><td>'+ str(row[4]) + '</td></tr>')
				print('  <tr class="statRow"><td>Waypoints</td><td>'+ str(row[5]) + '</td></tr>')
				row = cursor.fetchone()

		print('  </table>')
		cursor.close()
	conn.close()
else:
	print(errstr)
if (errstr.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
