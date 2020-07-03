#!/usr/bin/python
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
import cgi
import Cookie
import dbSession
import MySQLdb
import ghShared
import ghLists
import dbShared
import time
from datetime import timedelta, datetime
import urllib
from jinja2 import Environment, FileSystemLoader


class userAbility:
	def __init__(self, key="", description="", unlocked=False):
		self.key = key
		self.description = description
		self.unlocked = unlocked
		self.minReputation = -99

def main():
	# Get current url
	try:
		url = os.environ['REQUEST_URI']
	except KeyError:
		url = ''
	uiTheme = ''
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
		try:
			uiTheme = cookies['uiTheme'].value
		except KeyError:
			uiTheme = ''
		try:
			avatarResult = cookies['avatarAttempt'].value
		except KeyError:
			avatarResult = ''
		try:
			galaxy = cookies['galaxy'].value
		except KeyError:
			galaxy = ghShared.DEFAULT_GALAXY
	else:
		currentUser = ''
		loginResult = form.getfirst('loginAttempt', '')
		avatarResult = form.getfirst('avatarAttempt', '')
		sid = form.getfirst('gh_sid', '')
		galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)

	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)

	# Get a session
	logged_state = 0
	linkappend = ''
	disableStr = ''
	created = datetime.fromtimestamp(time.time())
	inGameInfo = ''
	pictureName = ''
	userPictureName = ''
	friendCountStr = ''
	donateTotal = ''
	userTitle = ''
	donorBadge = ''
	email = ''
	defaultAlertTypes = 0
	sharedInventory = 0
	sharedRecipes = 0
	siteAlertCheckStr = ''
	emailAlertCheckStr = ''
	mobileAlertCheckStr = ''
	reputation = 0
	resScore = 0
	mapScore = 0
	repColor = 'grey'
	resColor = 'grey'
	mapColor = 'grey'
	abilities = []

	if loginResult == None:
		loginResult = 'success'

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess
		if (useCookies == 0):
			linkappend = 'gh_sid=' + sid
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		cursor.execute('SELECT userID, emailAddress, themeName FROM tUsers WHERE userID="' + currentUser + '"')
		row = cursor.fetchone()
		if (row != None):
			email = row[1]
			uiTheme = row[2]
		cursor.close()
		conn.close()
	else:
		disableStr = ' disabled="disabled"'
		if (uiTheme == ''):
			uiTheme = 'crafter'

	path = []
	uid = ''
	template = 'user.html'
	userPage = 'root'
	if os.environ.has_key('PATH_INFO'):
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']

	# get user attributes
	if len(path) > 0:
		uid = dbShared.dbInsertSafe(path[0])
		if len(path) > 1:
			userPage = path[1]
		if userPage == 'inventory':
			template = 'inventory.html'
		else:
			created = dbShared.getUserAttr(uid, 'created')
			inGameInfo = dbShared.getUserAttr(uid, 'inGameInfo')
			userPictureName = dbShared.getUserAttr(uid, 'pictureName')
			defaultAlerts = dbShared.getUserAttr(uid, 'defaultAlertTypes')
			if defaultAlerts > 0:
				if defaultAlerts % 2 == 1:
					siteAlertCheckStr = ' checked="checked"'
				if defaultAlerts >= 4:
					mobileAlertCheckStr = ' checked="checked"'
				if defaultAlerts != 1 and defaultAlerts != 4 and defaultAlerts != 5:
					emailAlertCheckStr = ' checked="checked"'
			sharedInventory = dbShared.getUserAttr(uid, 'sharedInventory')
			sharedRecipes = dbShared.getUserAttr(uid, 'sharedRecipes')

			donateTotal = dbShared.getUserDonated(uid)
			userTitle = dbShared.getUserTitle(uid)
			userStats = dbShared.getUserStats(uid, galaxy).split(',')
			resScore = int(userStats[0])
			mapScore = int(userStats[1])
			reputation = int(userStats[2])
			if resScore != None:
				if resScore > 2000:
					resColor = '#ffcc00'
				elif resScore > 500:
					resColor = '#3366ff'
				elif resScore > 25:
					resColor = '#009933'

			if mapScore != None:
				if mapScore > 400:
					mapColor = '#ffcc00'
				elif mapScore > 100:
					mapColor = '#3366ff'
				elif mapScore > 5:
					mapColor = '#009933'

			if reputation != None:
				if reputation > 100:
					repColor = '#ffcc00'
				elif reputation > 50:
					repColor = '#3366ff'
				elif reputation > 10:
					repColor = '#009933'
				elif reputation < 0:
					repColor = '#800000'

			if userPictureName == '':
				userPictureName = 'default.jpg'
			if donateTotal != '':
				donorBadge = '<img src="/images/coinIcon.png" width="16" title="This user has donated to the site" alt="coin" />'
			# get friend count
			conn = dbShared.ghConn()
			cursor = conn.cursor()
			cursor.execute('SELECT Count(uf1.added) FROM tUserFriends uf1 INNER JOIN tUserFriends uf2 ON uf1.friendID=uf2.userID AND uf1.userID=uf2.friendID WHERE uf1.userID="' + uid + '"')
			row = cursor.fetchone()
			if (row != None):
				friendCountStr = '(' + str(row[0]) + ')'
			cursor.close()
			conn.close()

		# Load list of unlocked abilities
		for k, v in ghShared.ABILITY_DESCR.iteritems():
			if reputation >= ghShared.MIN_REP_VALS[k] and ghShared.MIN_REP_VALS[k] != -99:
				a = userAbility(k, v, True)
				a.minReputation = ghShared.MIN_REP_VALS[k]
				abilities.append(a)

	convertGI = ghShared.convertText(inGameInfo, "js")
	tmpStat = dbShared.friendStatus(uid, currentUser)
	joinedStr = 'Joined ' + ghShared.timeAgo(created) + ' ago'
	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')

	print 'Content-type: text/html\n'
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template(template)
	if userPage == 'inventory':
		print template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), professionList=ghLists.getProfessionList(galaxy), resourceGroupList=ghLists.getResourceGroupList(), resourceTypeList=ghLists.getResourceTypeList(galaxy), uid=uid, editable=(uid == currentUser and logged_state==1), enableCAPTCHA=ghShared.RECAPTCHA_ENABLED, siteidCAPTCHA=ghShared.RECAPTCHA_SITEID)
	else:
		print template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), themeList=ghLists.getThemeList(), uid=uid, convertGI=convertGI, sid=sid, avatarResult=avatarResult, email=email, donorBadge=donorBadge, joinedStr=joinedStr, userPictureName=userPictureName, tmpStat=tmpStat, userTitle=userTitle, friendCountStr=friendCountStr,
		userAbilities=abilities, resScore=resScore, mapScore=mapScore, reputation=reputation, resColor=resColor, mapColor=mapColor, repColor=repColor, siteAlertCheckStr=siteAlertCheckStr, emailAlertCheckStr=emailAlertCheckStr, mobileAlertCheckStr=mobileAlertCheckStr, sharedInventory=sharedInventory, sharedRecipes=sharedRecipes, inGameInfo=ghShared.convertText(inGameInfo, 'html'), enableCAPTCHA=ghShared.RECAPTCHA_ENABLED, siteidCAPTCHA=ghShared.RECAPTCHA_SITEID)

if __name__ == "__main__":
	main()