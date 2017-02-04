#!/usr/bin/python
"""

 Copyright 2017 Paul Willworth <ioscode@gmail.com>

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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
import ghLists
import ghObjects
#

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
	try:
		currentUser = cookies['userID'].value
	except KeyError:
		currentUser = ''
	try:
		sid = cookies['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

# Get a session
logged_state = 0
galaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

# Main program

print 'Content-type: text/html\n'
print '<table width="100%" class=resourceStats>'
if galaxy != '':
	if logged_state == 1:
		favJoin = ' LEFT JOIN (SELECT itemID, favGroup FROM tFavorites WHERE userID="' + currentUser + '" AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup'
	else:
		favJoin = ''
		favCols = ', NULL'
	galaxyState = dbShared.galaxyState(galaxy)
	conn = dbShared.ghConn()

	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])

	cursor = conn.cursor()
	if (cursor):
		sqlStr1 = 'SELECT spawnID, spawnName, galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, resourceGroup,'
		sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
		sqlStr1 += ' CASE WHEN CRmax > 0 THEN (((CASE WHEN CR IS NULL THEN 0 ELSE CR END)-CRmin) / (CRmax-CRmin))*100 ELSE NULL END AS CRperc,'
		sqlStr1 += ' CASE WHEN CDmax > 0 THEN (((CASE WHEN CD IS NULL THEN 0 ELSE CD END)-CDmin) / (CDmax-CDmin))*100 ELSE NULL END AS CDperc,'
		sqlStr1 += ' CASE WHEN DRmax > 0 THEN (((CASE WHEN DR IS NULL THEN 0 ELSE DR END)-DRmin) / (DRmax-DRmin))*100 ELSE NULL END AS DRperc,'
		sqlStr1 += ' CASE WHEN FLmax > 0 THEN (((CASE WHEN FL IS NULL THEN 0 ELSE FL END)-FLmin) / (FLmax-FLmin))*100 ELSE NULL END AS FLperc,'
		sqlStr1 += ' CASE WHEN HRmax > 0 THEN (((CASE WHEN HR IS NULL THEN 0 ELSE HR END)-HRmin) / (HRmax-HRmin))*100 ELSE NULL END AS HRperc,'
		sqlStr1 += ' CASE WHEN MAmax > 0 THEN (((CASE WHEN MA IS NULL THEN 0 ELSE MA END)-MAmin) / (MAmax-MAmin))*100 ELSE NULL END AS MAperc,'
		sqlStr1 += ' CASE WHEN PEmax > 0 THEN (((CASE WHEN PE IS NULL THEN 0 ELSE PE END)-PEmin) / (PEmax-PEmin))*100 ELSE NULL END AS PEperc,'
		sqlStr1 += ' CASE WHEN OQmax > 0 THEN (((CASE WHEN OQ IS NULL THEN 0 ELSE OQ END)-OQmin) / (CASE WHEN OQmax-OQmin < 1 THEN 1 ELSE OQmax-OQmin END))*100 ELSE NULL END AS OQperc,'
		sqlStr1 += ' CASE WHEN SRmax > 0 THEN (((CASE WHEN SR IS NULL THEN 0 ELSE SR END)-SRmin) / (SRmax-SRmin))*100 ELSE NULL END AS SRperc,'
		sqlStr1 += ' CASE WHEN UTmax > 0 THEN (((CASE WHEN UT IS NULL THEN 0 ELSE UT END)-UTmin) / (UTmax-UTmin))*100 ELSE NULL END AS UTperc,'
		sqlStr1 += ' CASE WHEN ERmax > 0 THEN (((CASE WHEN ER IS NULL THEN 0 ELSE ER END)-ERmin) / (ERmax-ERmin))*100 ELSE NULL END AS ERperc,'
		sqlStr1 += ' containerType, verified, verifiedBy, unavailable, unavailableBy' + favCols + ' FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType' + favJoin + ' WHERE galaxy=' + galaxy + ' AND unavailable IS NULL ORDER BY entered DESC LIMIT 5;'
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			s = ghObjects.resourceSpawn()
			s.spawnID = row[0]
			s.spawnName = row[1]
			s.spawnGalaxy = row[2]
			s.resourceType = row[5]
			s.resourceTypeName = row[6]
			s.containerType = row[30]
			s.stats.CR = row[8]
			s.stats.CD = row[9]
			s.stats.DR = row[10]
			s.stats.FL = row[11]
			s.stats.HR = row[12]
			s.stats.MA = row[13]
			s.stats.PE = row[14]
			s.stats.OQ = row[15]
			s.stats.SR = row[16]
			s.stats.UT = row[17]
			s.stats.ER = row[18]

			s.percentStats.CR = row[19]
			s.percentStats.CD = row[20]
			s.percentStats.DR = row[21]
			s.percentStats.FL = row[22]
			s.percentStats.HR = row[23]
			s.percentStats.MA = row[24]
			s.percentStats.PE = row[25]
			s.percentStats.OQ = row[26]
			s.percentStats.SR = row[27]
			s.percentStats.UT = row[28]
			s.percentStats.ER = row[29]

			s.entered = row[3]
			s.enteredBy = row[4]
			s.verified = row[31]
			s.verifiedBy = row[32]
			s.unavailable = row[33]
			s.unavailableBy = row[34]
			if row[35] != None:
				s.favorite = 1
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

			print '  <tr><td>'
			print s.getHTML(1, "", logged_state > 0 and galaxyState == 1, userReputation)
			print '</td></tr>'
			row = cursor.fetchone()

		cursor.close()
	conn.close()
print '  </table>'
