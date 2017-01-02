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
try:
	import json
except ImportError:
	import simplejson as json
#
form = cgi.FieldStorage()

q = form.getfirst('query', '')
galaxy = form.getfirst('galaxy', '')
unavailable = form.getfirst('unavailable', '')
# escape input to prevent sql injection
q = dbShared.dbInsertSafe(q)
galaxy = dbShared.dbInsertSafe(galaxy)

errstr = ''
if galaxy.isdigit() == False:
	errstr = 'Error: You must specify a galaxy.'

spawns = ['']
criteriaStr = ' WHERE galaxy = ' + str(galaxy)
if unavailable != 'on':
	criteriaStr += ' AND unavailable IS NULL'
qlen = len(q)
if qlen > 0:
	criteriaStr += ' AND SUBSTRING(spawnName, 1, ' + str(qlen) + ') = \'' + q + '\''

# Main program
print 'Content-type: text/html; charset=UTF-8\n'
if errstr == '':
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		sqlStr = 'SELECT spawnName FROM tResources' + criteriaStr + ' ORDER BY spawnName'
		#sys.stderr.write(sqlStr + '\n')
		cursor.execute(sqlStr)
		row = cursor.fetchone()

		while (row != None):
			spawns.append(row[0])
			row = cursor.fetchone()
        
		cursor.close()
	conn.close()
	print json.dumps({'query': q, 'suggestions': spawns})
else:
	print errstr


