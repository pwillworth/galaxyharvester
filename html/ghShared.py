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

import time
from datetime import timedelta, datetime
import random
import os
import sys
import math

BASE_SCRIPT_URL = '/'
BASE_WEB_DOMAIN = 'https://www.galaxyharvester.net' # Update to the root domain name for your site. Used for email verification link do not include trailing /
DEFAULT_THEME = 'crafter'
DEFAULT_GALAXY = '118'
imgNum = random.randint(1,17)
automatedUsers = ["etas", "c0pp3r", "RogueOne", "SRAlderaan", "EiFScript", "RelicsAdmin", "SRUpdater", "SwgAwakening", "Europa", "swginfinity", "Xela_TheCreation", "Reckoning", "TarkinSWG"]
RECAPTCHA_ENABLED = True
RECAPTCHA_SITEID = "6LdKFa0ZAAAAAFqbK_-0VBPWtPmFAxjZuunGLqHo"
RECAPTCHA_URL = "https://www.google.com/recaptcha/api/siteverify"

# Minimum reputation needed to perform actions
MIN_REP_VALS = {'VERIFY_RESOURCE': -99,
                'ADD_WAYPOINT': -99,
                'VERIFY_WAYPOINT': -99,
                'ADD_RES_PLANET': -99,
                'ADD_RESOURCE': -99,
                'REMOVE_RESOURCE': 1,
                'EDIT_RESOURCE_STATS_TYPE': 5,
                'EDIT_RESOURCE_GALAXY_NAME': 50,
                'UPDATE_SCHEMATIC_IMAGE': 15,
                'ADD_SCHEMATIC': 15,
                'EDIT_OTHER_SCHEMATIC': 75,
                'ADD_CREATURE': 10,
                'EDIT_OTHER_CREATURE': 30}

# Descriptions about abilities users can unlock
ABILITY_DESCR = {'VERIFY_RESOURCE': 'verify resources',
                'ADD_WAYPOINT': 'add waypoints',
                'VERIFY_WAYPOINT': 'verify waypoints',
                'ADD_RES_PLANET': 'add resources to planets',
                'ADD_RESOURCE': 'add new resources',
                'REMOVE_RESOURCE': 'mark resources unavailable',
                'EDIT_RESOURCE_STATS_TYPE': 'edit resource stats and type',
                'EDIT_RESOURCE_GALAXY_NAME': 'move resources to different galaxy or change their name',
                'UPDATE_SCHEMATIC_IMAGE': 'update images on schematics',
                'ADD_SCHEMATIC': 'add new schematics',
                'EDIT_OTHER_SCHEMATIC': 'edit other users schematic entries',
                'ADD_CREATURE': 'add new creature resource type data',
                'EDIT_OTHER_CREATURE': 'edit other users creature data entries'}


def timeAgo(theTime):
	try:
		timeSinceEntered = datetime.fromtimestamp(time.time()) - theTime
		tmpDays = timeSinceEntered.days
		tmpStr = ''
		if (tmpDays > 0):
			if (tmpDays > 365):
				tmpStr = str(math.floor(tmpDays / 365)) + " years, "
				tmpDays = tmpDays % 365
			return tmpStr + str(tmpDays)+" days"
		elif (timeSinceEntered.seconds/3600 >= 1):
			return str(math.floor(timeSinceEntered.seconds/3600))+" hours"
		elif (timeSinceEntered.seconds/60 >= 1):
			return str(math.floor(timeSinceEntered.seconds/60))+" minutes"
		else:
			return "less than a minute"
	except:
		return "no time"

def getNumberAbbr(theNumber):
	if theNumber >= 1000000:
		return "%0.1f" % (theNumber / 1000000.0) + "m"
	elif theNumber >= 1000:
		return str(theNumber / 1000) + "k"
	else:
		return str(theNumber)

def percOfRangeColor(percValue):
	if (float(percValue) < 80):
		return "statNormal"
	elif (float(percValue) < 99):
		return "statHigh"
	else:
		return "statMax"

def getActionName(action):
	if action == 'a':
		return 'Add'
	if action == 'p':
		return 'Planet Add'
	if action == 'e':
		return 'Edit'
	if action == 'r':
		return 'Cleanup'
	if action == 'v':
		return 'Verified'
	if action == 'w':
		return 'Waypoint'
	if action == 'n':
		return 'Name Change'
	if action == 'g':
		return 'Galaxy Change'
	return 'Unknown'

def convertText(text, fmt):
	newStr = ""
	if (text != None):
		for i in range(len(text)):
			if (text[i] == "\n"):
				if fmt == "html":
					newStr = newStr + "<br />"
				else:
					newStr = newStr + "\\n"
			else:
				newStr = newStr + text[i]
	return newStr

def getMobilePlatform(agentString):
	# Get mobile platform
	mobilePlatform = ''
	if 'Android' in agentString:
		mobilePlatform = 'android'
	if 'iPhone' in agentString or 'iPad' in agentString or 'iPod' in agentString:
		mobilePlatform = 'ios'
	if 'Windows Phone' in agentString:
		mobilePlatform = 'microsoft'
	if 'BlackBerry' in agentString or 'BB' in agentString:
		mobilePlatform = 'amazon'

	return mobilePlatform

def tryInt(v):
	try:
		return int(v)
	except:
		return v

# Translation of schematic event types to names
SCHEMATIC_EVENT_NAMES = {'a': 'Added',
                'e': 'Edited',
                'd': 'Deleted',
                'i': 'Updated Image'}
