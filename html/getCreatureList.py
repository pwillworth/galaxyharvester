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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
import ghShared
#
form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
result = ''
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
		sid = cookies['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

# Get a session
logged_state = 0

resType = form.getfirst('resType', '')
galaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
resType = dbShared.dbInsertSafe(resType)
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program
conn = dbShared.ghConn()
cursor = conn.cursor()

if (cursor):
    if logged_state == 1:
        # Get user reputation for later checking
        stats = dbShared.getUserStats(currentUser, galaxy).split(",")
        userReputation = int(stats[2])

    clist = '<table class="userData" width="100%">'
    clist += '<thead><tr class="tableHead"><th>Creature</th>'

    clist += '<th>Yield</th><th>Mission lvl</th></thead>'

    sqlStr = """
        SELECT tResourceTypeCreature.speciesName,
               tResourceTypeCreature.maxAmount,
               tResourceTypeCreature.missionLevel,
               tResourceTypeCreature.galaxy,
               tResourceTypeCreature.enteredBy,
               tResourceType.resourceTypeName,
               tResourceType.resourceType,
               tResourceType.containerType
            FROM tResourceTypeCreature
                INNER JOIN tResourceType
                    ON tResourceType.resourceType = tResourceTypeCreature.resourceType
            WHERE (tResourceType.resourceCategory = %s
                    OR tResourceType.containerType = %s
                    OR tResourceType.resourceGroup = %s
                    OR tResourceType.resourceType = %s)
                AND tResourceTypeCreature.galaxy IN (0, %s)
            ORDER BY tResourceTypeCreature.maxAmount DESC
    """

    # Execute SQL and get first row
    cursor.execute(sqlStr, (resType, resType, resType, resType, galaxy))
    row = cursor.fetchone()

    while (row != None):
        clist += '  <tr class="statRow"><td>' + str(row[0]).replace('_',' ')

        clist += '</td><td>' + str(row[1]) + '</td><td>' + str(row[2])

        # Display creature edit/dit if user has enough reputation
        if logged_state == 1 and row[3] != 0 and (row[4] == currentUser or userReputation >= ghShared.MIN_REP_VALS['EDIT_OTHER_CREATURE']):
            clist += '<div style="float:right;"><a style="cursor: pointer;" onclick="editCreatureData(\'{2}\', \'{3}\', \'{4}\')"><img src="/images/editBlue16.png" alt="Edit Info"/></a><a style="cursor: pointer;" onclick="removeCreatureResource({0}, \'{1}\', \'{2}\')"><img src="/images/xRed16.png" alt="Remove"/></a></div>'.format(str(row[3]), resType, row[0], row[1], row[2])

        clist += '</td>'
        clist += '  </tr>'

        row = cursor.fetchone()

    cursor.close()
conn.close()

clist += '  </table>'

print 'Content-type: text/html\n'
print clist
