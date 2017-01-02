#!/usr/bin/python
"""

 Copyright 2012 Paul Willworth <ioscode@gmail.com>

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

import cgi
import MySQLdb
import dbShared
import ghShared
#
form = cgi.FieldStorage()

resGroup = form.getfirst('resGroup', '')
outType = form.getfirst('outType', '')
# escape input to prevent sql injection
resGroup = dbShared.dbInsertSafe(resGroup)
outType = dbShared.dbInsertSafe(outType)

print 'Content-type: text/html\n'
if outType == 'links':
	print '<ul class="plain">'
else:
	print '<option value="none" title="p00000000000">None</option>'

if len(resGroup) > 0:
	criteriaStr = ' AND (resourceGroup = "' + resGroup + '" OR resourceCategory = "' + resGroup + '")'
else:
	criteriaStr = ''

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	cursor.execute('SELECT resourceType, resourceTypeName, CONCAT("p", CASE WHEN CRmax>0 THEN "1" ELSE "0" END, CASE WHEN CDmax>0 THEN "1" ELSE "0" END, CASE WHEN DRmax>0 THEN "1" ELSE "0" END, CASE WHEN FLmax>0 THEN "1" ELSE "0" END, CASE WHEN HRmax>0 THEN "1" ELSE "0" END, CASE WHEN MAmax>0 THEN "1" ELSE "0" END, CASE WHEN PEmax>0 THEN "1" ELSE "0" END, CASE WHEN OQmax>0 THEN "1" ELSE "0" END, CASE WHEN SRmax>0 THEN "1" ELSE "0" END, CASE WHEN UTmax>0 THEN "1" ELSE "0" END, CASE WHEN ERmax>0 THEN "1" ELSE "0" END) AS statMask FROM tResourceType WHERE enterable>0' + criteriaStr + ' ORDER BY resourceTypeName;')
	row = cursor.fetchone()
	if row == None and len(resGroup) > 0:
		cursor.execute('select rgc.resourceGroup, rg.groupName, "p11111111111" AS statMask  FROM tResourceGroupCategory rgc INNER JOIN tResourceGroup rg ON rgc.resourceGroup = rg.resourceGroup WHERE rgc.resourceCategory="' + resGroup + '";')
		row = cursor.fetchone()

	while (row != None):
		if outType == 'links':
			print '<li><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[0] + '">' + row[1] + '</a></li>'
		else:
			print '<option value="'+str(row[0])+'" title="'+row[2]+'">'+row[1]+'</option>'
		row = cursor.fetchone()

if outType == 'links':
	print '</ul>'

