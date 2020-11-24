#!/usr/bin/env python3

import pymysql
import os
import sys

SCHEM_DIR = "~/workspaces/SWGEmu/Core3/MMOCoreORB/bin/scripts/object/draft_schematic"
OBJECT_DIR = "~/workspaces/SWGEmu/Core3/MMOCoreORB/bin/scripts/"
conn = None
cursor = None

def findObjectInFile(f, objPath):
	tmpTemplates = ""
	tmpTangible = ""
	tmpType = "0"
	if (objPath[objPath.rfind("/")+1:objPath.rfind("/")+8] != "shared_"):
		objPath = objPath[:objPath.rfind("/")+1] + "shared_" + objPath[objPath.rfind("/")+1:]
	for line in f:
		line.strip()
		eqPos = line.find(":new {")
		if (eqPos != -1):
			# reset at beginning of object
			tmpTemplates = ""
			tmpTangible = ""
			tmpType = "0"
		else:
			# see if line has property value
			eqPos = line.find("=")
			if (eqPos != -1):
				# store if either of the ones we're looking for
				sName = line[:eqPos].strip()
				sVal = line[eqPos+1:line.rfind(",")].strip()
				if sName == "gameObjectType":
					tmpType = sVal
				if sName == "derivedFromTemplates":
					tmpTemplates = line[eqPos+1:].strip().strip('{').strip('}')
			else:
				# check if we found the CRC and return or reset variables
				eqPos = line.find("addClientTemplate")
				if eqPos != -1:
					tmpTangible = line[line.rfind(",")+1:].strip().strip(")").strip("\"")
					#print tmpTangible + " - " + objPath
					if (tmpTangible == objPath):
						#print "Match - " + tmpType
						return tmpType + ", " + tmpTemplates
					else:
						tmpTemplates = ""
						tmpTangible = ""
						tmpType = "0"

	return tmpType + ", " + tmpTemplates

def getObjectType(objPath):
	objectType = "0, "
	eqPos = objPath.find("/")
	if eqPos != -1:
		subPath = objPath.rpartition("/")[0]
	else:
		subPath = "object/tangible"

	tangiblePath = OBJECT_DIR + subPath
	print "Getting Object Type from " + tangiblePath
	#loop dir and get files
	for f in os.listdir(tangiblePath):
		if os.path.isdir(tangiblePath+"/"+f) and f != '.' and f != '..':
			# object type directory
			#print "  Dipping into: " + f
			for f2 in os.listdir(tangiblePath+"/"+f):
				if os.path.isdir(tangiblePath+"/"+f+"/"+f2) and f2 != '.' and f2 != '..':
					# object sub type directory
					#print "    Dipping into: " + f2
					for f3 in os.listdir(tangiblePath+"/"+f+"/"+f2):
						if os.path.isdir(tangiblePath+"/"+f+"/"+f2+"/"+f3) and f3 != '.' and f3 != '..':
							# object sub - sub type dir
							#print "      Dipping into: " + f3
							for f4 in os.listdir(tangiblePath+"/"+f+"/"+f2+"/"+f3):
								if f4 == 'objects.lua':
									tmpFile = open(tangiblePath+"/"+f+"/"+f2+"/"+f3+"/"+f4, 'r')
									objectType = findObjectInFile(tmpFile, objPath)
									tmpFile.close()
									if objectType != "0, ": break
						else:
							if f3 == 'objects.lua':
								tmpFile = open(tangiblePath+"/"+f+"/"+f2+"/"+f3, 'r')
								objectType = findObjectInFile(tmpFile, objPath)
								tmpFile.close()
								if objectType != "0, ": break
						if objectType != "0, ": break
				else:
					if f2 == 'objects.lua':
						# process schematic file in main object type directory
						tmpFile = open(tangiblePath+"/"+f+"/"+f2, 'r')
						objectType = findObjectInFile(tmpFile, objPath)
						tmpFile.close()
						if objectType != "0, ": break
				if objectType != "0, ": break
		else:
			if f == 'objects.lua':
				# process schematic file in main object type directory
				print "Looking in " + tangiblePath+"/"+f
				tmpFile = open(tangiblePath+"/"+f, 'r')
				objectType = findObjectInFile(tmpFile, objPath)
				tmpFile.close()
				if objectType != "0, ": break

		if objectType != "0, ": break

	return objectType

def getSkillGroup(objPath):
	# look in schematic skill list for object
	print "Finding skill group for " + objPath
	tmpFile = open('schematic_group.csv', 'r')
	for line in tmpFile:
		vals = line.split(',')
		if vals[1].strip() == objPath:
			return vals[0].strip()

	tmpFile.close()
	return ""

def scrapeSchem(f):
	print "Scraping Schematic: " + str(f)
	schem = {}
	pos = 0
	badSchem = False
	schemID = ""
	for line in f:
		line.strip()
		eqPos = line.find("=")
		if (eqPos != -1):
			if schemID == "":
				schemID = line[:eqPos].strip()
				schemID = "\"" + schemID[23:] + "\""
			sName = line[:eqPos].strip()
			sVal = line[eqPos+1:line.rfind(",")].strip()
			schem[sName] = sVal
			# get path to object file
			if sName == "targetTemplate":
				schem[sName] = sVal.strip("\"")
				objectFile = schem["targetTemplate"][:-3] + "lua"
				print "Getting other data from object file: " + OBJECT_DIR + objectFile
				tmpFile = open(OBJECT_DIR + objectFile, 'r')
				for oline in tmpFile:
					oline.strip()
					oeqPos = oline.find("=")
					if (oeqPos != -1):
						oName = oline[:oeqPos].strip()
						oVal = oline[oeqPos+1:oline.rfind(",")].strip()
						if not oName in schem.keys():
							schem[oName] = oVal
			pos += 1
		else:
			# get schematic path
			eqPos = line.find(":addTemplate")
			if (eqPos != -1):
				eqPos = line.find("\"")
				if (eqPos != -1):
					sName = "objectPath"
					sVal = line[eqPos+1:line.rfind("\"")].strip()
					schem[sName] = sVal

	#for k, v in schem.items():
	#	print k, v
	try:
		print "saving: " + schem["customObjectName"] + " - " + schem["targetTemplate"]
	except KeyError:
		print "bad schem" + str(schem.keys())
		badSchem = True

	if badSchem == False:
		# get object type
		if (schem["targetTemplate"] == ""):
			objectType = "0"
			objectGroup = ""
		else:
			objectTypes = getObjectType(schem["targetTemplate"]).split(", ")
			#print objectTypes
			objectType = objectTypes[0]
			objectGroup = objectTypes[len(objectTypes)-1].replace("shared_","")

		# get skill group
		if (schem["objectPath"] == ""):
			skillGroup = ""
		else:
			skillGroup = getSkillGroup(schem["objectPath"])

		# write schematic information to database
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup) VALUES (" + schemID + "," + schem["customObjectName"] + "," + schem["craftingToolTab"] + ",\"" + skillGroup + "\"," + objectType + "," + schem["complexity"] + "," + schem["size"] + "," + schem["xpType"] + "," + schem["xp"] + ",\"" + schem["targetTemplate"] + "\"," + objectGroup + ");"
		cursor.execute(schemSQL)
		conn.commit()
		# write ingredient information to database
		ingredients = schem["ingredientTitleNames"].strip('{').strip('}').split(",")
		ingTypes = schem["ingredientSlotType"].strip('{').strip('}').split(",")
		ingObjects = schem["resourceTypes"].strip('{').strip('}').split(",")
		resQuantities = schem["resourceQuantities"].strip('{').strip('}').split(",")
		resContribution = schem["contribution"].strip('{').strip('}').split(",")
		# Git rid of whitespace that may be present after items
		ingredients = map(str.strip, ingredients)
		ingTypes = map(str.strip, ingTypes)
		ingObjects = map(str.strip, ingObjects)
		resQuantities = map(str.strip, resQuantities)
		resContribution = map(str.strip, resContribution)
		for i in range(len(ingredients)):
			# print str(len(ingObjects)) + ": " + str(ingObjects)
			if ingObjects[i][-5:] == ".iff\"":
				ingObject = ingObjects[i].replace("shared_","")
			else:
				ingObject = ingObjects[i]
			ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) VALUES (" + schemID + "," + ingredients[i] + "," + ingTypes[i] + "," + ingObject + "," + resQuantities[i] + "," + resContribution[i] + ");"
			cursor.execute(ingSQL)
			conn.commit()
		# write experimental property/quality info to database
		expProps = None
		try:
			expProps = schem["experimentalSubGroupTitles"].strip('{').strip('}').split(",")
			expGroups = schem["experimentalGroupTitles"].strip('{').strip('}').split(",")
			expCounts = schem["numberExperimentalProperties"].strip('{').strip('}').split(",")
			# res data
			expResProps = schem["experimentalProperties"].strip('{').strip('}').split(",")
			expResWeights = schem["experimentalWeights"].strip('{').strip('}').split(",")
			# git rid of whitespace that may be present after items
			expProps = map(str.strip, expProps)
			expGroups = map(str.strip, expGroups)
			expCounts = map(str.strip, expCounts)
			expResProps = map(str.strip, expResProps)
			expResWeights = map(str.strip, expResWeights)
		except KeyError:
			print "No schematic qualities data available for: " + schemID

		if expProps != None:
			weightPos = 0
			for i in range(len(expProps)):
				# count the number of resource property weights to add to quality record
				weightTotal = 0
				for i2 in range(int(expCounts[i])):
					if (expResProps[weightPos+i2] != "\"XX\""):
						weightTotal += int(expResWeights[weightPos+i2])
				if (expProps[i] != "null"):
					qualSQL = "INSERT INTO tSchematicQualities (schematicID, expProperty, expGroup, weightTotal) VALUES (" + schemID + "," + expProps[i] + "," + expGroups[i] + "," + str(weightTotal) + ");"
					cursor.execute(qualSQL)
					conn.commit()
				# add resource properties according to count for this quality attribute
				for i2 in range(int(expCounts[i])):
					if (expResProps[weightPos+i2] != "\"XX\""):
						weightSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) VALUES (LAST_INSERT_ID()," + expResProps[weightPos+i2] + "," + expResWeights[weightPos+i2] + ");"
						cursor.execute(weightSQL)
						conn.commit()

				weightPos += int(expCounts[i])

#main
conn = pymysql.connect(host = "localhost",
		db = "swgresource",
		user = "webusr",
		passwd = "")
conn.autocommit(True)

cursor = conn.cursor()
#get argument for path or use current
if len(sys.argv) > 1:
	# do just the 1 passed schem
	schemPath = sys.argv[1]
	tmpFile = open(schemPath, 'r')
	scrapeSchem(tmpFile)
	tmpFile.close()
else:
	#loop dir and get schems
	for f in os.listdir(SCHEM_DIR):
		if os.path.isdir(SCHEM_DIR+"/"+f) and f != '.' and f != '..':
			# object type directory
			print "*  Dipping into: " + f
			for f2 in os.listdir(SCHEM_DIR+"/"+f):
				if os.path.isdir(SCHEM_DIR+"/"+f+"/"+f2) and f2 != '.' and f2 != '..':
					# schem sub type directory
					print "**    Dipping into: " + f2
					for f3 in os.listdir(SCHEM_DIR+"/"+f+"/"+f2):
						if f3 != '.' and f3 != '..' and f3 != 'objects.lua' and os.path.isdir(SCHEM_DIR+"/"+f+"/"+f2+"/"+f3) == False:
							tmpFile = open(SCHEM_DIR+"/"+f+"/"+f2+"/"+f3, 'r')
							scrapeSchem(tmpFile)
							tmpFile.close()
				else:
					if f2 != 'objects.lua':
						# process schematic file in main object type directory
						tmpFile = open(SCHEM_DIR+"/"+f+"/"+f2, 'r')
						scrapeSchem(tmpFile)
						tmpFile.close()

	# Update medical schems to put proper PE/OQ weight
	#cursor.execute("UPDATE tSchematicResWeights SET statWeight = 1 WHERE statName = \"OQ\" AND expQualityID IN (SELECT expQualityID FROM tSchematicQualities INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE tSkillGroup.profID IN (3,10) AND tSchematicQualities.expProperty=\"power\" AND tSchematicQualities.weightTotal=3);")
	#cursor.execute("UPDATE tSchematicResWeights SET statWeight = 2 WHERE statName = \"PE\" AND expQualityID IN (SELECT expQualityID FROM tSchematicQualities INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE tSkillGroup.profID IN (3,10) AND tSchematicQualities.expProperty=\"power\" AND tSchematicQualities.weightTotal=3);")

cursor.close()
conn.close()
