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
import pymysql
import dbInfo
sys.path.append(".")
import dbShared

def ghConn():
	conn = pymysql.connect(host = dbInfo.DB_HOST,
		db = dbInfo.DB_NAME,
		user = dbInfo.DB_USER,
		passwd = dbInfo.DB_PASS)
	conn.autocommit(True)
	return conn
# Main program

conn = ghConn()
# Dismiss Alert records that are from over 30 days ago
galaxyCursor = conn.cursor()
if (galaxyCursor):
	galaxySQL = 'UPDATE tAlerts SET alertStatus=3, statusChanged=NOW() WHERE alertStatus < 2 AND alertTime < (NOW() - INTERVAL 30 DAY);'
	galaxyCursor.execute(galaxySQL)
	sys.stdout.write(str(galaxyCursor.rowcount) + " rows cleaned up from tAlerts.\n")
	galaxyCursor.close()

# Update summary counts of spawns and waypoints per galaxy
countsCursor = conn.cursor()
if (countsCursor):
	countsSQL = 'SELECT galaxy, Count(*) FROM tResources GROUP BY galaxy;'
	countsCursor.execute(countsSQL)
	sys.stdout.write("Updating " + str(countsCursor.rowcount) + " galaxies resource counts.\n")
	updateCursor = conn.cursor()
	row = countsCursor.fetchone()
	while row != None:
		updateSQL = 'UPDATE tGalaxy SET totalSpawns=' + str(row[1]) + ' WHERE galaxyID=' + str(row[0]) + ';'
		updateCursor.execute(updateSQL)
		row = countsCursor.fetchone()

	countsSQL = 'SELECT galaxy, Count(*) FROM tWaypoint INNER JOIN tResources ON tWaypoint.spawnID = tResources.spawnID GROUP BY galaxy;'
	countsCursor.execute(countsSQL)
	sys.stdout.write("Updating " + str(countsCursor.rowcount) + " galaxies waypoint counts.\n")
	updateCursor = conn.cursor()
	row = countsCursor.fetchone()
	while row != None:
		updateSQL = 'UPDATE tGalaxy SET totalWaypoints=' + str(row[1]) + ' WHERE galaxyID=' + str(row[0]) + ';'
		updateCursor.execute(updateSQL)
		row = countsCursor.fetchone()

	updateCursor.close()
	countsCursor.close()

# Mark Unavailable resources that have been available over maximum spawn durations
agingCursor = conn.cursor()
if (agingCursor):
	# Non JTL inorganics max spawn length 11 days
	agingSQL = "SELECT spawnID, galaxy FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType INNER JOIN tResourceTypeGroup ON tResourceType.resourceType = tResourceTypeGroup.resourceType WHERE unavailableBy IS NULL AND entered < (NOW() - INTERVAL 11 DAY) AND tResourceTypeGroup.resourceGroup = 'inorganic' AND tResourceType.resourceType NOT IN ('aluminum_perovskitic', 'copper_borocarbitic', 'ore_siliclastic_fermionic', 'radioactive_polymetric', 'steel_arveshian', 'steel_bicorbantium', 'fiberplast_gravitonic', 'gas_reactive_organometallic', 'aluminum_galvanicyn', 'copper_cagunese', 'gas_inert_rylon', 'iron_hemalite', 'ore_carbonate_calabite', 'ore_extrusive_maganite', 'ore_intrusive_galatite');"
	agingCursor.execute(agingSQL)
	sys.stdout.write("Updating " + str(agingCursor.rowcount) + " rows Non-JTL inorganics for auto mark unavailable.\n")
	cleanupCursor = conn.cursor()
	row = agingCursor.fetchone()
	while row != None:
		cleanupSQL = 'UPDATE tResources SET unavailableBy="default", unavailable=NOW() WHERE spawnID={0}'.format(row[0])
		cleanupCursor.execute(cleanupSQL)
		dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(row[1]) + "," + str(row[0]) + ",'default',NOW(),'r',0);", 'r', 'default', row[1], str(row[0]))
		row = agingCursor.fetchone()

	cleanupCursor.close()

	# Everything else max spawn length 22 days
	agingSQL = "SELECT spawnID, galaxy FROM tResources WHERE unavailableBy IS NULL AND entered < (NOW() - INTERVAL 22 DAY);"
	agingCursor.execute(agingSQL)
	sys.stdout.write("Updating " + str(agingCursor.rowcount) + " JTL/organics rows for auto mark unavailable.\n")
	cleanupCursor = conn.cursor()
	row = agingCursor.fetchone()
	while row != None:
		cleanupSQL = 'UPDATE tResources SET unavailableBy="default", unavailable=NOW() WHERE spawnID={0}'.format(row[0])
		cleanupCursor.execute(cleanupSQL)
		dbShared.logEvent("INSERT INTO tResourceEvents (galaxy, spawnID, userID, eventTime, eventType, planetID) VALUES (" + str(row[1]) + "," + str(row[0]) + ",'default',NOW(),'r',0);", 'r', 'default', row[1], str(row[0]))
		row = agingCursor.fetchone()

	cleanupCursor.close()
	agingCursor.close()

conn.close()
