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

import cgi
import pymysql
import dbShared
import ghShared
#
form = cgi.FieldStorage()

resGroup = form.getfirst('resGroup', '')
outType = form.getfirst('outType', '')
galaxy = form.getfirst('galaxy', '-1')
planetID = form.getfirst('planetID', '')
# escape input to prevent sql injection
resGroup = dbShared.dbInsertSafe(resGroup)
outType = dbShared.dbInsertSafe(outType)
galaxy = dbShared.dbInsertSafe(galaxy)

print('Content-type: text/html\n')
if outType == 'links':
	print('<ul class="plain">')
elif outType == 'graphic':
	print('')
else:
	print('<option value="none" title="p00000000000">None</option>')

if len(resGroup) > 0:
	criteriaStr = 'AND (resourceGroup = "{0}" OR resourceCategory = "{0}")'.format(resGroup)
else:
	criteriaStr = ''

if planetID.isdigit() and int(planetID) > 0:
	criteriaStr = criteriaStr + ' AND (specificPlanet = 0 OR specificPlanet = {0})'.format(planetID)
else:
	if galaxy.isdigit() and int(galaxy) > 0:
		criteriaStr = criteriaStr + ' AND (specificPlanet = 0 OR specificPlanet IN (SELECT DISTINCT tPlanet.planetID FROM tPlanet, tGalaxyPlanet WHERE (tPlanet.planetID < 11) OR (tPlanet.planetID = tGalaxyPlanet.planetID AND tGalaxyPlanet.galaxyID = {0})))'.format(galaxy)

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	sqlString = """
		SELECT
			tResourceType.resourceType,
			resourceTypeName,
			CONCAT(
				"p",
				CASE WHEN CRmax>0 THEN "1" ELSE "0" END,
				CASE WHEN CDmax>0 THEN "1" ELSE "0" END,
				CASE WHEN DRmax>0 THEN "1" ELSE "0" END,
				CASE WHEN FLmax>0 THEN "1" ELSE "0" END,
				CASE WHEN HRmax>0 THEN "1" ELSE "0" END,
				CASE WHEN MAmax>0 THEN "1" ELSE "0" END,
				CASE WHEN PEmax>0 THEN "1" ELSE "0" END,
				CASE WHEN OQmax>0 THEN "1" ELSE "0" END,
				CASE WHEN SRmax>0 THEN "1" ELSE "0" END,
				CASE WHEN UTmax>0 THEN "1" ELSE "0" END,
				CASE WHEN ERmax>0 THEN "1" ELSE "0" END
			) AS statMask,
			containerType
		FROM
			tResourceType
			LEFT JOIN tGalaxyResourceType tgrt ON tgrt.resourceType = tResourceType.resourceType AND tgrt.galaxyID = {0}
		WHERE enterable>0 {1} AND (elective = 0 OR tgrt.resourceType IS NOT NULL)
		ORDER BY resourceTypeName;
	""".format(galaxy, criteriaStr)

	cursor.execute(sqlString)
	row = cursor.fetchone()
	if row == None and len(resGroup) > 0:
		cursor.execute('select rgc.resourceGroup, rg.groupName, "p11111111111" AS statMask, containerType FROM tResourceGroupCategory rgc INNER JOIN tResourceGroup rg ON rgc.resourceGroup = rg.resourceGroup WHERE rgc.resourceCategory="' + resGroup + '";')
		row = cursor.fetchone()

	while (row != None):
		if outType == 'links':
			print('<li><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[0] + '">' + row[1] + '</a></li>')
		elif outType == 'graphic':
			print("<div id='resInventory{0}' class='inventoryItem inlineBlock' style='background-image:url(/images/resources/{2}.png);background-size:64px 64px;' tag='{1}'>".format(row[0], row[2], row[3]))
			print("<div style='position: absolute;bottom:0;width:100%'>{0}</div>".format(row[1]))
			print("</div>")
		else:
			print('<option value="'+str(row[0])+'" title="'+row[2]+'">'+row[1]+'</option>')
		row = cursor.fetchone()

	cursor.close()
conn.close()

if outType == 'links':
	print('</ul>')
