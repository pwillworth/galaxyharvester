#!/usr/bin/env python3

import pymysql
import os
import sys

CREAT_DIR = "~/workspaces/SWGEmu/Core3/MMOCoreORB/bin/scripts/mobile"

conn = None
cursor = None

def scrapeFile(f, n, planet):
	creature = {}
	pos = 0
	badCreature = False
	for line in f:
		line.strip()
		eqPos = line.find("=")
		if (eqPos != -1):
			sName = line[:eqPos].strip()
			sVal = line[eqPos+1:line.rfind(",")].strip()
			creature[sName] = sVal.strip('"')
			pos += 1

	try:
		print "saving: " + n + ": " + creature["objectName"]
	except KeyError:
		print "bad creature" + str(creature.keys())
		badCreature = True

	if badCreature == False:
		speciesName = creature["objectName"]
		if speciesName[:20] == "@mob/creature_names:":
			speciesName = speciesName[20:]
		else:
			badCreature = True
			print speciesName[20:] + " is not a creature"

	if badCreature == False:
		# write creature information to database
		try:
			if creature["boneType"] != None and len(creature["boneType"]) > 4:
				resSQL = "INSERT INTO tResourceTypeCreature (resourceType, speciesName, maxAmount) VALUES ('" + creature["boneType"] + "_" + planet + "','" + speciesName + "'," + creature["boneAmount"] + ");"
				cursor.execute(resSQL)
			else:
				print "No bone for " + speciesName
		except KeyError:
			print "No bone data " + speciesName
		except MySQLdb.Error:
			print "Skipping duplicate bone for " + speciesName

		try:
			if creature["hideType"] != None and len(creature["hideType"]) > 4:
				resSQL = "INSERT INTO tResourceTypeCreature (resourceType, speciesName, maxAmount) VALUES ('" + creature["hideType"] + "_" + planet + "','" + speciesName + "'," + creature["hideAmount"] + ");"
				cursor.execute(resSQL)
			else:
				print "No hide for " + speciesName
		except KeyError:
			print "No hide data " + speciesName
		except MySQLdb.Error:
			print "Skipping duplicate hide for " + speciesName

		try:
			if creature["meatType"] != None and len(creature["meatType"]) > 4:
				fixedType = creature["meatType"].replace("reptilian","reptillian")
				resSQL = "INSERT INTO tResourceTypeCreature (resourceType, speciesName, maxAmount) VALUES ('" + fixedType + "_" + planet + "','" + speciesName + "'," + creature["meatAmount"] + ");"
				cursor.execute(resSQL)
			else:
				print "No meat for " + speciesName
		except KeyError:
			print "No meat data " + speciesName
		except MySQLdb.Error:
			print "Skipping duplicate meat for " + speciesName

		try:
			if creature["milk"] != None and creature["milk"].isdigit() and int(creature["milk"]) > 0:
				resSQL = "INSERT INTO tResourceTypeCreature (resourceType, speciesName, maxAmount) VALUES ('milk_wild_" + planet + "','" + speciesName + "'," + creature["milk"] + ");"
				cursor.execute(resSQL)
			else:
				print "No milk for " + speciesName
		except KeyError:
			print "No milk data " + speciesName
		except MySQLdb.Error:
			print "Skipping duplicate milk for " + speciesName

#main
conn = pymysql.connect(host = "localhost",
		db = "swgresource",
		user = "webusr",
		passwd = "")
conn.autocommit(True)

cursor = conn.cursor()
#get argument for path or use current
if len(sys.argv) > 1:
	# do just the 1 passed
	schemPath = sys.argv[1]
	tmpFile = open(schemPath, 'r')
	scrapeSchem(tmpFile)
	tmpFile.close()
else:
	#loop dir and get creatures
	for f in os.listdir(CREAT_DIR):
		if os.path.isdir(CREAT_DIR+"/"+f) and f != '.' and f != '..':
			# Planet directory
			print "  Dipping into: " + f
			for f2 in os.listdir(CREAT_DIR+"/"+f):
				if os.path.isdir(CREAT_DIR+"/"+f+"/"+f2):
					# object type directory
					print "    Dipping into: " + f2
					for f3 in os.listdir(CREAT_DIR+"/"+f+"/"+f2):
						if f3 != '.' and f3 != '..' and os.path.isdir(CREAT_DIR+"/"+f+"/"+f2+"/"+f3) == False:
							tmpFile = open(CREAT_DIR+"/"+f+"/"+f2+"/"+f3, 'r')
							scrapeFile(tmpFile, f3, f)
							tmpFile.close()
				else:
					tmpFile = open(CREAT_DIR+"/"+f+"/"+f2, 'r')
					scrapeFile(tmpFile, f2, f)
					tmpFile.close()

cursor.close()
conn.close()
