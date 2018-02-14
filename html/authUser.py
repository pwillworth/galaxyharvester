#!/usr/bin/python
"""

 Copyright 2018 Paul Willworth <ioscode@gmail.com>

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
import time
import MySQLdb
import dbSession
import dbShared
import urllib
import datetime
sys.path.append("../")
import dbInfo

cookies = Cookie.SimpleCookie()
useCookies = 1
result = ''
linkappend = ''
exactUser = ''
newhashDate = datetime.datetime(2016, 05, 16, 20, 30)

try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

form = cgi.FieldStorage()

src_url = form.getfirst('src_url')
sid = form.getfirst('gh_sid')
loginp = form.getfirst('loginu')
passp = form.getfirst('passu')
passc = form.getfirst('passc')
persist = form.getfirst('persist')
push_key = form.getfirst('push_key')
#sessions persist up to 90 days
duration = 7776000
#escape input to prevent sql injection
loginp = dbShared.dbInsertSafe(loginp)
sid = dbShared.dbInsertSafe(sid)
push_key = form.getfirst('push_key')

if (loginp == None or (passp == None and passc == None)):
	result = 'no login data'
else:
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT userID, userPassword, userState, created, lastReset FROM tUsers WHERE userID=%s', (loginp,))
	row = cursor.fetchone()
	if row == None:
		result = 'bad user'
	elif not row[2] > 0:
		result = 'unverified account'
	elif row[2] == 3:
		result = 'account deleted'
	else:
		exactUser = row[0]
        # New hash date is when salt that goes with password to create hash was
        # changed from loginp to DB_KEY3 since loginp did not always exactly match username
		if row[3] > newhashDate or (row[4] != None and row[4] > newhashDate):
			crypt_pass = hashlib.sha1(dbInfo.DB_KEY3 + passp).hexdigest()
		else:
			crypt_pass = hashlib.sha1(loginp + passp).hexdigest()
		if passc != None:
			# already encrypted password was sent
			crypt_pass = passc

		if row[1] == crypt_pass:
			updatestr = 'UPDATE tUsers SET lastLogin=NOW() WHERE userID=%s'
			cursor.execute(updatestr, (loginp,))
			dbSession.verifySessionDB()
			sid = hashlib.sha1(str(time.time()) + exactUser).hexdigest()
			updatestr = 'INSERT INTO tSessions (sid, userID, expires, pushKey) VALUES (%s, %s, %s, %s)'
			cursor.execute(updatestr, (sid, exactUser, time.time() + duration, push_key))
			result = 'success'
		else:
			result = 'bad password or user name'

	cursor.close()
	conn.close()

if sid == None:
	sid = ""
if useCookies:
	cookies['loginAttempt'] = result
	if result == "success":
		# session id cookie expires when browser closes unless we are told to persist
		expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
		cookies['gh_sid'] = sid
		if persist != None:
			cookies['gh_sid']['expires'] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
		# userid and theme stay for up to 7 days
		expiration = datetime.datetime.now() + datetime.timedelta(days=7)
		cookies['userID'] = exactUser
		cookies['userID']['expires'] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
		cookies['uiTheme'] = dbShared.getUserAttr(loginp, 'themeName')
		cookies['uiTheme']['expires'] = expiration.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
	print cookies
else:
	# add results to url if not using cookies
	linkappend = 'loginAttempt=' + urllib.quote(result) + '&gh_sid=' + sid

if src_url != None:
	if src_url.find('?') > -1:
		queryChar = '&'
	else:
		queryChar = '?'
	# go back where they came from
	print 'Status: 303 See Other'
	print 'Location: ' + src_url + queryChar + linkappend
	print ''
else:
	print 'Content-Type: text/html\n'
	print result + '-' + sid
