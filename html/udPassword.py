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
import sys
import cgi
import Cookie
import hashlib
import MySQLdb
import dbSession
import dbShared
sys.path.append("../")
import dbInfo


# Get current url
try:
    url = os.environ['SCRIPT_NAME']
except KeyError:
    url = ''

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
cookies = Cookie.SimpleCookie()
try:
    cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
    errorstr = 'no cookies\n'

if errorstr == '':
    try:
        currentUser = cookies['userID'].value
    except KeyError:
        currentUser = ''
    try:
        loginResult = cookies['loginAttempt'].value
    except KeyError:
        loginResult = 'success'
    try:
        sid = cookies['gh_sid'].value
    except KeyError:
        sid = form.getfirst('gh_sid', '')
else:
    currentUser = ''
    loginResult = 'success'
    sid = form.getfirst('gh_sid', '')
userpass = form.getfirst("userpass")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
userpass = dbShared.dbInsertSafe(userpass)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
    logged_state = 1
    currentUser = sess
    linkappend = 'gh_sid=' + sid

#  Check for errors
errstr='';
if (len(userpass) < 6):
    errstr = errstr + "Your password must be at least 6 characters. \r\n"
if (logged_state == 0):
    errstr = errstr + "You must be logged in to update your password. \r\n"
if (errstr != ''):
    result = "Your Password could not be updated because of the following errors:\r\n" + errstr
else:
    crypt_pass = hashlib.sha1(dbInfo.DB_KEY3 + userpass).hexdigest()

    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute("UPDATE tUsers SET userPassword='" + crypt_pass + "', lastReset=NOW() WHERE userID='" + currentUser + "';")

    cursor.close()
    conn.close()
    result = "Password Updated"


print "Content-Type: text/html\n"
print result
