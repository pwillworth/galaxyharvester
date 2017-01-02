#!/usr/bin/python
"""

 Copyright 2015 Paul Willworth <ioscode@gmail.com>

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
email = form.getfirst("email")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
email = dbShared.dbInsertSafe(email)
# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
    logged_state = 1
    currentUser = sess
    linkappend = 'gh_sid=' + sid

#  Check for errors
errstr=''
if (len(email) < 6):
    errstr = errstr + "That is not a valid email address. \r\n"
if (logged_state == 0):
    errstr = errstr + "You must be logged in to update your email address. \r\n"

if (errstr != ''):
    result = "Your E-mail Address could not be updated because of the following errors:\r\n" + errstr
else:
    conn = dbShared.ghConn()
    # Do not allow duplicate email
    ecursor = conn.cursor()
    ecursor.execute("SELECT userID FROM tUsers WHERE emailAddress='" + email + "' AND userState > 0;")
    erow = ecursor.fetchone()
    if erow != None:
        result = "That e-mail is already in use by another user."
    else:
        cursor = conn.cursor()
        cursor.execute("UPDATE tUsers SET emailAddress='" + email + "' WHERE userID='" + currentUser + "';")
        result = "E-Mail Address Updated"
        cursor.close()

    conn.close()


print "Content-Type: text/html\n"
print result
