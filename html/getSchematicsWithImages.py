#!/usr/bin/python
"""

 Copyright 2010 Paul Willworth <ioscode@gmail.com>

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

import MySQLdb
import dbShared
import ghLists
import cgi
# return option list of schematics with images uploaded
form = cgi.FieldStorage()
schematicID = form.getfirst('schematicID', '')
# escape input to prevent sql injection
schematicID = dbShared.dbInsertSafe(schematicID)

if schematicID == '':
	whereStr = ' WHERE imageType=1'
else:
	# only include schematics of same object type as schematic passed
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	# get old image file name
	cursor.execute('SELECT objectType FROM tSchematic WHERE schematicID="' + schematicID + '";')
	row = cursor.fetchone()
	if row != None:
		result = row[0]
	else:
		result = 0
	whereStr = ' WHERE imageType=1 AND objectType=' + str(result) + ' AND tSchematic.schematicID != "' + schematicID + '"'

print 'Content-type: text/html\n'
print '<option value="">-Select-</option>' + ghLists.getOptionList('SELECT tSchematic.schematicID, schematicName FROM tSchematic INNER JOIN tSchematicImages ON tSchematic.schematicID = tSchematicImages.schematicID' + whereStr + ';')
