#!/usr/bin/python
"""

 Copyright 2017 Paul Willworth <ioscode@gmail.com> & Chet Bortz <thrusterhead@gmail.com>

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
import ghShared
#
form = cgi.FieldStorage()

galaxy = form.getfirst('galaxy', '0')
resGroup = form.getfirst('resGroup', '')

# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)
resGroup = dbShared.dbInsertSafe(resGroup)

# Main program
clist = ''

conn = dbShared.ghConn()
cursor = conn.cursor()

if (cursor):
  sqlStr = """
    SELECT tResourceType.resourceType,
           tResourceType.resourceTypeName
    FROM tResourceType
      INNER JOIN tResourceTypeCreature
        ON tResourceTypeCreature.resourceType = tResourceType.resourceType
    WHERE (tResourceType.resourceCategory = %s
        OR tResourceType.containerType = %s
        OR tResourceType.resourceGroup = %s)
      AND tResourceTypeCreature.galaxy IN (0, %s)
    GROUP BY tResourceType.resourceType
    ORDER BY tResourceType.resourceTypeName
  """

  # Execute SQL and fetch first row
  cursor.execute(sqlStr, (resGroup, resGroup, resGroup, galaxy))
  row = cursor.fetchone()

  clist += '<ul class="plain">'

  while (row != None):
    clist += '<li><a href="/creatureList.py/%s">%s</a></li>' % (row[0], row[1])
    row = cursor.fetchone()

  clist += '</ul>'
  cursor.close()
conn.close()

print 'Content-type: text/html\n'
print clist
