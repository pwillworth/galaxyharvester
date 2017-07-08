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
import cgi
import Cookie
import dbSession
import dbShared
import MySQLdb
import ghShared
import ghLists
from jinja2 import Environment, FileSystemLoader

useCookies = 1
linkappend = ''
logged_state = 0
typeID = ''
currentUser = ''
uiTheme = ''
typeName = False
showType = True
validResource = False
containerType = 'creature_resources'
breadcrumbHTML = ''
typeTitle = 'That resource type does not exist'

try:
  url = os.environ['SCRIPT_NAME']
except KeyError:
  url = ''

form = cgi.FieldStorage()

# Get Cookies
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
  try:
    uiTheme = cookies['uiTheme'].value
  except KeyError:
    uiTheme = ''
  try:
    galaxy = cookies['galaxy'].value
  except KeyError:
    galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)
else:
  loginResult = form.getfirst('loginAttempt', '')
  sid = form.getfirst('gh_sid', '')
  galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
if loginResult == None:
  loginResult = 'success'

sess = dbSession.getSession(sid)
if (sess != ''):
  logged_state = 1
  currentUser = sess
  if (uiTheme == ''):
    uiTheme = dbShared.getUserAttr(currentUser, 'themeName')
  if (useCookies == 0):
    linkappend = 'gh_sid=' + sid
else:
  if (uiTheme == ''):
    uiTheme = 'crafter'

path = ['']
if os.environ.has_key('PATH_INFO'):
  path = os.environ['PATH_INFO'].split('/')[1:]
  path = [p for p in path if p != '']

if path[0] == '':
  typeTitle = ''
else:
  typeID = dbShared.dbInsertSafe(path[0])

  try:
    conn = dbShared.ghConn()
    cursor = conn.cursor()
  except Exception:
    errorstr = "Error: could not connect to database"

  if (cursor):
    sqlStr = """
      SELECT tResourceType.containerType,
             tResourceType.resourceType,
             tResourceType.resourceCategory,
             tResourceType.resourceGroup,
             tResourceType.resourceTypeName,
             tResourceGroup.groupName
        FROM tResourceType
          INNER JOIN tResourceGroup
            ON tResourceGroup.resourceGroup = tResourceType.resourceGroup
        WHERE tResourceType.resourceCategory = %s
          OR tResourceType.containerType = %s
          OR tResourceType.resourceGroup = %s
          OR tResourceType.resourceType = %s
        LIMIT 1
    """
    cursor.execute(sqlStr, (typeID, typeID, typeID, typeID))
    row = cursor.fetchone()
    if (row != None):
      validResource = True
      containerType = row[0]
      resourceType = row[0]
      category = row[2]
      group = row[3]
      resourceTypeTitle = row[4]
      containerTypeTitle = containerType.replace('_', ' ').title()
      categoryTitle = category.replace('_', ' ').title()
      groupTitle = row[5]

      # resourceCategory > containerType > resourceGroup > resourceType
      if (typeID == category):
        typeTitle = categoryTitle
      else:
        breadcrumbHTML += '<a href="/creatureList.py/%s">%s</a>' % (category, categoryTitle)
        breadcrumbHTML += ' > '

        if (typeID == containerType):
          typeTitle = containerTypeTitle
        else:
          breadcrumbHTML += '<a href="/creatureList.py/%s">%s</a>' % (containerType, containerTypeTitle)
          breadcrumbHTML += ' > '

          if (typeID == group):
            typeTitle = groupTitle
          else:
            if (group != containerType):
              breadcrumbHTML += '<a href="/creatureList.py/%s">%s</a>' % (group, groupTitle)
              breadcrumbHTML += ' > '

            typeTitle = resourceTypeTitle
            showType = False

# Always append the type title as the last item (possibly blank)
breadcrumbHTML += typeTitle

# Set user picture
pictureName = dbShared.getUserAttr(currentUser, 'pictureName')

# Set environment
env = Environment(loader=FileSystemLoader('templates'))
env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])

template = env.get_template('creaturelist.html')

print 'Content-type: text/html\n'
print template.render(validResource=validResource, typeID=typeID, containerType=containerType, typeTitle=typeTitle, showType=showType, breadcrumbHTML=breadcrumbHTML, uiTheme=uiTheme, galaxy=galaxy, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, resourceGroupListShort=ghLists.getResourceGroupListShort(), professionList=ghLists.getProfessionList(galaxy), planetList=ghLists.getPlanetList(galaxy), resourceGroupList=ghLists.getResourceGroupList(), resourceTypeList=ghLists.getResourceTypeList(), galaxyList=ghLists.getGalaxyList())
