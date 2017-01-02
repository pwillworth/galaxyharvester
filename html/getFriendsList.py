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
import os
import dbShared
import cgi
import Cookie
import MySQLdb
import ghShared
import dbShared
import dbSession
#
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
		sid = cookies['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

uid = form.getfirst('uid', '')
lastUser = form.getfirst('lastUser', '')
direction = form.getfirst('direction', '')
# escape input to prevent sql injection
uid = dbShared.dbInsertSafe(uid)
lastUser = dbShared.dbInsertSafe(lastUser)
direction = dbShared.dbInsertSafe(direction)
userCriteria = ""
pageSize = 10
headStr = ""
tmpStr = ""
rowStr = ""

# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

# Main program
if uid == '':
	tmpStr = 'Error: no user id'

if (len(lastUser) > 2 and len(direction) > 0):
	if direction == 'back':
		userCriteria = " AND uf1.friendID < '" + lastUser + "' ORDER BY uf1.friendID DESC"
	else:
		userCriteria = " AND uf1.friendID > '" + lastUser + "' ORDER BY uf1.friendID"

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor and tmpStr == ''):
	headStr = '<table class="userData" width="200">'
	if (logged_state == 1 and currentUser == uid):
		headStr += '<thead><tr class="tableHead"><td width="150">User</td><td width="50">Status</td><td><img src="/images/xRed16.png" title="Remove friend column" /></td></th></thead>'
		sqlStr = 'SELECT uf1.friendID, uf2.added, pictureName FROM tUserFriends uf1 INNER JOIN tUsers tu ON uf1.friendID = tu.userID LEFT JOIN tUserFriends uf2 ON uf1.friendID=uf2.userID AND uf1.userID=uf2.friendID WHERE uf1.userID="' + uid + '"' + userCriteria + ' LIMIT ' + str(pageSize) + ';'
	else:
		headStr += '<thead><tr class="tableHead"><td width="200">User</td></th></thead>'
		sqlStr = 'SELECT uf1.friendID, uf2.added, pictureName FROM tUserFriends uf1 INNER JOIN tUsers tu ON uf1.friendID = tu.userID INNER JOIN tUserFriends uf2 ON uf1.friendID=uf2.userID AND uf1.userID=uf2.friendID WHERE uf1.userID="' + uid + '"' + userCriteria + ' LIMIT ' + str(pageSize) + ';'

	cursor.execute(sqlStr)
	row = cursor.fetchone()

	lastFriend = ''
	if row != None:
		firstFriend = row[0]
		if direction == 'back':
			lastFriend = row[0]
	else:
		firstFriend = ''
		tmpStr = 'Error: No Data'

	while (row != None):
		rowStr = '  <tr class="statRow" id="frow_' + row[0] + '"><td><a href="user.py?uid=' + row[0] + '" class="nameLink"><img src="/images/users/'+str(row[2])+'" class="tinyAvatar" /><span style="vertical-align:4px;">'+ row[0] + '</span></a></td>'
		if (logged_state == 1 and currentUser == uid):
			if row[1] == None:
				rowStr += '<td><img src="/images/eStar16.png" title="' + row[0] + ' has not added you to their friends list yet." /></td>'
			else:
				rowStr += '<td><img src="/images/rStar16.png" title="You are on ' + row[0] + '\'s friends list." /></td>'
			rowStr += '<td><img src="/images/xGrey16.png" title="Click to remove from friends list." style="cursor: pointer;" onclick="removeFriend(\'' + row[0] + '\')" /></td>'
		rowStr += '  </tr>'
		# Append or pre-pend row depending on sort
		if direction == 'back':
			firstFriend = row[0]
			tmpStr = rowStr + tmpStr
		else:
			lastFriend = row[0]
			tmpStr = tmpStr + rowStr

		row = cursor.fetchone()
        
	if tmpStr != 'Error: No Data':
		tmpStr = headStr + tmpStr + '  </table>'
		# Print paging controls
		tmpStr += '<div style="text-align:center;">'
		if lastUser != '':
			tmpStr += '<button id="prevFriendsButton" class="ghButton" style="margin:10px;" onclick="moreFriends(\''+ firstFriend + '\', \'back\');">Back</button>'
		if cursor.rowcount == pageSize:
			tmpStr += '<button id="nextFriendsButton" class="ghButton" style="margin:10px;" onclick="moreFriends(\''+ lastFriend + '\', \'next\');">Next</button>'
		tmpStr += '</div>'

	cursor.close()
conn.close()

print 'Content-type: text/html\n'
print tmpStr


