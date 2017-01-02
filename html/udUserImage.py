#!/usr/bin/python
"""

 Copyright 2010 Paul Willworth <ioscode@gmail.com>

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

import sys
import os
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared
import Image
import urllib
import time

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
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

errstr=''
if not form.has_key("avatar"):
	errstr = "No avatar sent."
else:
	img_data = form["avatar"]
	if not img_data.file: errstr = "avatar is not a file."

src_url = form.getfirst('src_url', '/user.py?uid='+currentUser)
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid

#  Check for errors
if errstr == '':
	imgName = img_data.filename
if (logged_state == 0):
	errstr = errstr + "You must be logged in to update your avatar. \r\n"
try:
	im = Image.open(img_data.file)
except:
	errstr = errstr + "I don't recognize the file you uploaded as an image (" + imgName + ").  Please make sure it is a jpg, gif, or png.  \r\n"

if (errstr != ''):
	result = "Your Avatar could not be updated because of the following errors:\r\n" + errstr
else:
	result = ''
	
	#resize if too big
	xsize, ysize = im.size
	newwidth = xsize
	newheight = ysize
	if (xsize > 320 or ysize > 320):
		if xsize >= ysize:
			newheight = ysize * (320.0/xsize)
			newwidth = 320
		elif ysize > xsize:
			newwidth = xsize * (320.0/ysize)
			newheight = 320
	try:
		im.thumbnail((newwidth,newheight))
	except IOError:
		result = "I can't handle that type of image file, please try a different one."

	if result == '':
		# write image file
		imageName = currentUser + str(time.time()) + ".jpg"
		im.save("images/users/"+imageName, "JPEG")

		# update user record to point to file
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		# get old image file name
		cursor.execute("SELECT pictureName FROM tUsers WHERE userID='" + currentUser + "';")
		row = cursor.fetchone()
		if row != None:
			result = row[0]
		# update to new file name
		cursor.execute("UPDATE tUsers SET pictureName='" + imageName + "' WHERE userID='" + currentUser + "';")

		cursor.close()
		conn.close()
		# remove old file
		if (result != None and result != 'default.jpg'):
			os.remove("images/users/"+result)

		result = "Avatar Updated"


if useCookies:
	cookies['avatarAttempt'] = result
	cookies['avatarAttempt']['max-age'] = 60
	print cookies
else:
	linkappend = linkappend + '&avatarAttempt=' + urllib.quote(result)

print "Content-Type: text/html\n"
if src_url != None:
	print '<html><head><script type=text/javascript>document.location.href="' + src_url + '?uid=' + currentUser + '&' + linkappend + '"</script></head><body></body></html>'
else:
	print result

