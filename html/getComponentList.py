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

import cgi
import MySQLdb
import dbShared
import ghShared
#
form = cgi.FieldStorage()

craftingTab = form.getfirst('craftingTab', '')
outType = form.getfirst('outType', '')
# escape input to prevent sql injection
craftingTab = dbShared.dbInsertSafe(craftingTab)
outType = dbShared.dbInsertSafe(outType)

print 'Content-type: text/html\n'

if len(craftingTab) > 0:
	criteriaStr = ' AND craftingTab = {0}'.format(craftingTab)
else:
	criteriaStr = ''

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	cursor.execute('SELECT tSchematic.schematicID, schematicName, objectPath, imageName FROM tSchematic LEFT JOIN (SELECT schematicID, imageName FROM tSchematicImages WHERE imageType=1) tsi ON tSchematic.schematicID=tsi.schematicID WHERE (objectPath IN (SELECT ingredientObject FROM tSchematicIngredients WHERE ingredientType>0) OR objectGroup LIKE "%component%")' + criteriaStr + ' ORDER BY schematicName;')
	row = cursor.fetchone()

	while (row != None):
		if outType == 'graphic':
			if row[3] != None:
				imageName = row[3]
			else:
				imageName = 'none.jpg'

			print "<div id='schemComponent{1}' class='inventoryItem inlineBlock' style='background-image:url(/images/schematics/{2});background-size:64px 64px;' tag='{0}'>".format(row[0], row[2], imageName)
			print "<div style='position: absolute;bottom:0;width:100%'>{0}</div>".format(row[1])
			print "</div>"
		else:
			print '<option value="'+str(row[0])+'" title="'+row[2]+'">'+row[1]+'</option>'
		row = cursor.fetchone()

	cursor.close()
conn.close()
