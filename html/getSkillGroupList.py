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
import sys
#
form = cgi.FieldStorage()

profID = form.getfirst('prof', '')

print('Content-type: text/html\n')

if len(profID) > 0 and profID.isdigit() and int(profID) > 0:
	criteriaStr = ' WHERE profID={0}'.format(profID)
else:
	criteriaStr = ' WHERE 1=1'

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	cursor.execute('SELECT Min(skillGroup), skillGroupName FROM tSkillGroup{0} GROUP BY skillGroupName;'.format(criteriaStr))
	row = cursor.fetchone()
	while (row != None):
		print('<option value="'+str(row[0])+'">'+row[1]+'</option>')
		row = cursor.fetchone()

	cursor.close()
conn.close()

sys.exit(200)
