#!/usr/bin/env python3
"""

 Copyright 2025 Paul Willworth <ioscode@gmail.com>

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

import dbShared
import cgi
import pymysql
import json

form = cgi.FieldStorage()

# Get form info
galaxy = form.getfirst("galaxy", "")
# escape input to prevent sql injection
galaxy = dbShared.dbInsertSafe(galaxy)

if galaxy.isdigit():
  galaxy = int(galaxy)
  overrides = []

  overridesSql = """
    SELECT
      rto.resourceType,
      rto.specificPlanet
    FROM
      tResourceTypeOverrides rto
      INNER JOIN tResourceType rt1 ON rt1.resourceType = rto.resourceType
    WHERE
      rto.galaxyID = %(galaxyID)s;
  """

  conn = dbShared.ghConn()
  cursor = conn.cursor(pymysql.cursors.DictCursor)
  cursor.execute(overridesSql, {'galaxyID': galaxy})
  row = cursor.fetchone()

  while row != None:
    overrides.append(row)
    row = cursor.fetchone()

  cursor.close()
  conn.close()

  result = {'overrides': overrides}
  status = 200

else:
  result = {'message': 'Galaxy ID must be an integer'}
  status = 400

print(f'Status: {status}')
print('Content-Type: application/json\n')
print(json.dumps(result))
