#!/usr/bin/python
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
from datetime import date, datetime
import time
from time import localtime, strptime, strftime
import dbInfo

def ghConn():
	conn = pymysql.connect(host = dbInfo.DB_HOST,
		db = dbInfo.DB_NAME,
		user = dbInfo.DB_USER,
		passwd = dbInfo.DB_PASS)
	return conn

def n2z(inVal):
	if (inVal == '' or inVal == None or inVal == 'undefined' or inVal == 'None'):
		return '0'
	else:
		return str(inVal)

exportType = 'current'
siteDir= 'galaxyharvester.net/'

# check for command line argument to export all
if len(sys.argv) > 1:
	exportType = sys.argv[1]

if exportType == 'all':
	criteriaStr = '1=1'
	orderStr = ' ORDER BY spawnID'
else:
	criteriaStr = 'unavailable IS NULL'
	orderStr = ' ORDER BY rt1.resourceTypeName'

# Main program
rfc822time = '%a, %d %b %Y %H:%M:%S -0800'

sys.stdout.write(exportType)
conn = ghConn()
galaxyCursor = conn.cursor()
if (galaxyCursor):
	galaxySQL = 'SELECT galaxyID, galaxyName, lastExport, galaxyState FROM tGalaxy;'
	galaxyCursor.execute(galaxySQL)
	galaxyRow = galaxyCursor.fetchone()
	while (galaxyRow != None):
		if galaxyRow[3] == 1 and (galaxyRow[2] == None or (date(galaxyRow[2].year, galaxyRow[2].month, galaxyRow[2].day) < date.today())):
			if exportType == 'all':
				exportFile = siteDir + 'exports/all' + str(galaxyRow[0]) + '.xml'
				csvFile = siteDir + 'exports/all' + str(galaxyRow[0]) + '.csv'
			else:
				exportFile = siteDir + 'exports/current' + str(galaxyRow[0]) + '.xml'
				csvFile = siteDir + 'exports/current' + str(galaxyRow[0]) + '.csv'
			f = open(exportFile, 'w')
			fcsv = open(csvFile, 'w')
			f.write('<?xml version="1.0" encoding="iso-8859-15"?>\n')
			f.write('<resources as_of_date="' + datetime.fromtimestamp(time.time()).strftime(rfc822time) + '">\n')
			fcsv.write('"name","galaxy_id","galaxy_name","enter_date","type_id","type_name","group_id","CR","CD","DR","FL","HR","MA","PE","OQ","SR","UT","ER","unavailable_date","planets"\n')
			sqlStr1 = 'SELECT spawnID, spawnName, galaxy, entered, enteredBy, tResources.resourceType, rt1.resourceTypeName, rt1.resourceGroup,'
			sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
			sqlStr1 += ' rt1.containerType, verified, verifiedBy, unavailable, unavailableBy, rt1.resourceCategory, galaxyName FROM tResources INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType INNER JOIN tGalaxy ON tResources.galaxy = tGalaxy.galaxyID WHERE ' + criteriaStr + ' AND galaxy=' + str(galaxyRow[0])
			sqlStr1 = sqlStr1 + orderStr + ';'
			cursor = conn.cursor()
			cursor.execute(sqlStr1)
			row = cursor.fetchone()
			while (row != None):
				if row[22] != None:
					unavailStr = row[22].strftime(rfc822time)
				else:
					unavailStr = ''
				resStr = '<resource>'
				resStr += '<name>' + row[1] + '</name>'
				resStr += '<galaxy id="' + str(row[2]) + '">' + row[25] + '</galaxy>'
				resStr += '<enter_date>' + row[3].strftime(rfc822time) + '</enter_date>'
				resStr += '<resource_type id="' + row[5] + '">' + row[6] + '</resource_type>'
				resStr += '<group_id>' + row[7] + '</group_id>'
				resStr += '<stats>'
				if row[8] != None and row[8] > 0:
					resStr += '<CR>' + str(row[8]) + '</CR>'
				if row[9] != None and row[9] > 0:
					resStr += '<CD>' + str(row[9]) + '</CD>'
				if row[10] != None and row[10] > 0:
					resStr += '<DR>' + str(row[10]) + '</DR>'
				if row[11] != None and row[11] > 0:
					resStr += '<FL>' + str(row[11]) + '</FL>'
				if row[12] != None and row[12] > 0:
					resStr += '<HR>' + str(row[12]) + '</HR>'
				if row[13] != None and row[13] > 0:
					resStr += '<MA>' + str(row[13]) + '</MA>'
				if row[14] != None and row[14] > 0:
					resStr += '<PE>' + str(row[14]) + '</PE>'
				if row[15] != None and row[15] > 0:
					resStr += '<OQ>' + str(row[15]) + '</OQ>'
				if row[16] != None and row[16] > 0:
					resStr += '<SR>' + str(row[16]) + '</SR>'
				if row[17] != None and row[17] > 0:
					resStr += '<UT>' + str(row[17]) + '</UT>'
				if row[18] != None and row[18] > 0:
					resStr += '<ER>' + str(row[18]) + '</ER>'
				resStr += '</stats>'
				if row[22] != None:
					resStr += '<unavailable_date>' + unavailStr + '</unavailable_date>'
				resStr += '<planets>'
				planetSQL = 'SELECT planetName FROM tResourcePlanet INNER JOIN tPlanet ON tResourcePlanet.planetID = tPlanet.planetID WHERE spawnID=' + str(row[0]) + ' AND ' + criteriaStr
				planetCursor = conn.cursor()
				planetCursor.execute(planetSQL)
				planetRow = planetCursor.fetchone()
				planetStr = ''
				while (planetRow != None):
					resStr += '<planet>' + planetRow[0] + '</planet>'
					if planetStr == '':
						planetSeparator = ''
					else:
						planetSeparator = '|'
					planetStr += planetSeparator + planetRow[0]
					planetRow = planetCursor.fetchone()

				planetCursor.close()
				resStr += '</planets>'

				resStr += '</resource>\n'
				f.write(resStr)
				# write csv file line
				csvStr = ('"' + row[1] + '",' + str(row[2]) + ',"' + row[25] + '","' + row[3].strftime(rfc822time) + '","' + row[5] + '","' + row[6] + '","' + row[7] + '",' + n2z(row[8]) + ',' + n2z(row[9]) + ',' + n2z(row[10]) + ',' + n2z(row[11]) + ',' + n2z(row[12]) + ',' + n2z(row[13]) + ',' + n2z(row[14]) + ',' + n2z(row[15]) + ',' + n2z(row[16]) + ',' + n2z(row[17]) + ',' + n2z(row[18]) + ',' + unavailStr + ',"' + planetStr + '"\n')
				fcsv.write(csvStr)
				row = cursor.fetchone()
			f.write('</resources>')
			f.close()
			fcsv.close()
			cursor.execute('UPDATE tGalaxy SET lastExport=NOW() WHERE galaxyID=' + str(galaxyRow[0]) + ';')
			cursor.close()
		galaxyRow = galaxyCursor.fetchone()
	galaxyCursor.close()

conn.close()
