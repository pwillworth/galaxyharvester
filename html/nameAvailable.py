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

import os
import sys
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
#

def findName(nameString):
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute("SELECT userID FROM tUsers WHERE userID='" + nameString + "' AND userState > 0;")
    row = cursor.fetchone()
    if row == None:
        userid = ""
    else:
        userid = row[0]

    cursor.close()
    conn.close()
    return userid


# Main program
form = cgi.FieldStorage()
uname = form.getfirst("uname", "")
uname = dbShared.dbInsertSafe(uname)

result = ""

tmpID = findName(uname)

if (tmpID == ""):
    result = ""
else:
    result = "That user name is not available."

print('Content-type: text/html\n')
print(result)
