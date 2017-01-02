#!/usr/bin/python
"""

 Copyright 2011 Paul Willworth <ioscode@gmail.com>

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
#
form = cgi.FieldStorage()

resCategory = form.getfirst('resCategory', '')
outType = form.getfirst('outType', '')
# escape input to prevent sql injection
resCategory = dbShared.dbInsertSafe(resCategory)
outType = dbShared.dbInsertSafe(outType)

print 'Content-type: text/html\n'
if outType == 'links':
	print '<ul class="plain">'
else:
	print '<option value="none" title="p00000000000">None</option>'

if len(resCategory) > 0:
	joinStr = ' INNER JOIN (SELECT resourceGroup FROM tResourceGroupCategory WHERE resourceCategory = "' + resCategory + '") rgc ON tResourceGroup.resourceGroup = rgc.resourceGroup'
else:
	joinStr = ''

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	cursor.execute('SELECT tResourceGroup.resourceGroup, groupName, CONCAT("p", CASE WHEN Max(CRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(CDmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(DRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(FLmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(HRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(MAmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(PEmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(OQmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(SRmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(UTmax)>0 THEN "1" ELSE "0" END, CASE WHEN Max(ERmax)>0 THEN "1" ELSE "0" END) AS statMask FROM tResourceGroup' + joinStr + ' LEFT JOIN tResourceTypeGroup ON tResourceGroup.resourceGroup = tResourceTypeGroup.resourceGroup LEFT JOIN tResourceType ON tResourceTypeGroup.resourceType = tResourceType.resourceType WHERE enterable>0 GROUP BY tResourceGroup.resourceGroup ORDER BY groupName;')
	row = cursor.fetchone()
	while (row != None):
		if outType == 'links':
			print '<li><a href="/resourceType.py/' + row[0] + '">' + row[1] + '</a></li>'
		else:
			print '<option value="'+str(row[0])+'" title="'+row[2]+'">'+row[1]+'</option>'
		row = cursor.fetchone()

if outType == 'links':
	print '</ul>'

