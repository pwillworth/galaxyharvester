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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
import ghLists
#
form = cgi.FieldStorage()

listType = form.getfirst('listType', '')
galaxy = form.getfirst('galaxy', '-1')
# escape input to prevent sql injection
listType = dbShared.dbInsertSafe(listType)
galaxy = dbShared.dbInsertSafe(galaxy)

def getArrayList(listType, sqlStr):
	vResult = '<' + listType + '_values>'
	nResult = '<' + listType + '_names>'
	pResult = '<' + listType + '_prop1>'
	thisGroup = ''
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			if len(row)>1:
				nResult = nResult + '<item>' + str(row[1]) + '</item>'
				if len(row)>2:
					pResult = pResult + '<item>' + str(row[2]) + '</item>'
			vResult = vResult + '<item>' + str(row[0]) + '</item>'
			row = cursor.fetchone()
		cursor.close()
	conn.close()
	vResult = vResult + '</' + listType + '_values>'
	nResult = nResult + '</' + listType + '_names>'
	pResult = pResult + '</' + listType + '_prop1>'

	return '<list_data>' + vResult + nResult + pResult + '</list_data>'

# Main program
print 'Content-type: text/xml\n'
listResult = ''

if listType == 'resource_type':
	listResult = getArrayList(listType, 'SELECT resourceType, resourceTypeName, CONCAT("p", CASE WHEN CRmax>0 THEN "1" ELSE "0" END, CASE WHEN CDmax>0 THEN "1" ELSE "0" END, CASE WHEN DRmax>0 THEN "1" ELSE "0" END, CASE WHEN FLmax>0 THEN "1" ELSE "0" END, CASE WHEN HRmax>0 THEN "1" ELSE "0" END, CASE WHEN MAmax>0 THEN "1" ELSE "0" END, CASE WHEN PEmax>0 THEN "1" ELSE "0" END, CASE WHEN OQmax>0 THEN "1" ELSE "0" END, CASE WHEN SRmax>0 THEN "1" ELSE "0" END, CASE WHEN UTmax>0 THEN "1" ELSE "0" END, CASE WHEN ERmax>0 THEN "1" ELSE "0" END) AS statMask FROM tResourceType WHERE enterable>0 ORDER BY resourceTypeName;')

if listType == 'resource_type_sp':
	listResult = getArrayList(listType, 'SELECT resourceType, resourceTypeName, specificPlanet FROM tResourceType WHERE enterable>0 ORDER BY resourceTypeName;')

if listType == 'resource_group':
	listResult = getArrayList(listType, 'SELECT tResourceGroup.resourceGroup, groupName, CONCAT("p", CASE WHEN Max(CRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(CDmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(DRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(FLmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(HRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(MAmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(PEmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(OQmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(SRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(UTmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(ERmax)>0 THEN "1" ELSE "0" END) AS statMask FROM tResourceGroup LEFT JOIN tResourceTypeGroup ON tResourceGroup.resourceGroup = tResourceTypeGroup.resourceGroup LEFT JOIN tResourceType ON tResourceTypeGroup.resourceType = tResourceType.resourceType WHERE enterable>0 GROUP BY tResourceGroup.resourceGroup ORDER BY groupName;')

if listType == 'resource_type_group':
	listResult = getArrayList(listType, 'SELECT resourceType, resourceGroup FROM tResourceTypeGroup;')

if listType == 'galaxy':
    listResult = getArrayList(listType, 'SELECT galaxyID, galaxyName, CASE WHEN galaxyState=1 THEN "Active" ELSE "Inactive" END FROM tGalaxy WHERE galaxyState < 3 ORDER BY galaxyState, galaxyName;')

if listType == 'planet':
    listResult = getArrayList(listType, 'SELECT DISTINCT tPlanet.planetID, planetName FROM tPlanet, tGalaxyPlanet WHERE (tPlanet.planetID < 11) OR (tPlanet.planetID = tGalaxyPlanet.planetID AND tGalaxyPlanet.galaxyID = {0}) ORDER BY planetName;'.format(galaxy));

print listResult

if (listResult.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
