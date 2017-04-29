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

import os
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared

cookies = Cookie.SimpleCookie()
errorstr = ""
try:
    cookies.load(os.environ["HTTP_COOKIE"])
except KeyError:
    errorstr = "no cookies\n"

form = cgi.FieldStorage()

logged_state = 0
try:
    currentUser = cookies['userID'].value
except KeyError:
    currentUser = ""

try:
    sid = cookies['gh_sid'].value
except KeyError:
    sid = form.getfirst('gh_sid', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

sess = dbSession.getSession(sid)
if (sess != ''):
    logged_state = 1
    currentUser = sess

src_url = form.getfirst("src_url")

if logged_state > 0:
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    updatestr = 'DELETE FROM tSessions WHERE userID="' + currentUser + '" AND sid="' + sid + '";'
    cursor.execute(updatestr)
    cursor.close()
    conn.close()


if src_url != None:
    # go back where they came from
    print 'Status: 303 See Other'
    print 'Location: ' + src_url
    print ''
else:
    print 'Content-Type: text/html\n'
    print 'logout complete'
