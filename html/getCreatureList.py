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
import os
import sys
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
#
form = cgi.FieldStorage()

resType = form.getfirst('resType', '')
# escape input to prevent sql injection
resType = dbShared.dbInsertSafe(resType)

# Main program
print 'Content-type: text/html\n'
clist = '<table class="userData" width="100%">'
conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	clist += '<thead><tr class="tableHead"><th>Creature</th><th>Yield</th></thead>'
	sqlStr = 'SELECT speciesName, maxAmount FROM tResourceTypeCreature WHERE resourceType="' + resType + '" ORDER BY maxAmount DESC, speciesName'
	cursor.execute(sqlStr)
	row = cursor.fetchone()

	while (row != None):
		clist += '  <tr class="statRow"><td>' + str(row[0]).replace('_',' ') + '</td><td>' + str(row[1]) + '</td>'
		clist += '  </tr>'
		row = cursor.fetchone()
        
	cursor.close()
conn.close()
clist += '  </table>'
print clist
