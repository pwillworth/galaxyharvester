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

import ghNames

class schematicIngredient:
	def __init__(self, ingredientName = "", ingredientType = 0, ingredientObject = "", ingredientQuantity = 0, resourceName = "", objectLink = "", objectImage = "", objectName = ""):
		self.ingredientName = ingredientName
		# ingredientType values
		#  0 = required resource type/group
		#  1 = required identical component
		#  2 = required similar component
		#  3 = optional identical component
		#  4 = optional similar component
		self.ingredientType = ingredientType
		self.ingredientObject = ingredientObject
		self.ingredientQuantity = ingredientQuantity
		self.resourceName = resourceName
		self.objectLink = objectLink
		self.objectImage = objectImage
		self.objectName = objectName

	def getDisplayRow(self):
		if self.ingredientType == 0:
			return '<tr><td>' + str(self.ingredientQuantity) + '</td><td style="padding-right:4px;"></td><td>' + self.objectLink + '</td></tr>'
		else:
			tempStr = '<tr><td>' + str(self.ingredientQuantity) + '</td><td style="padding-right:4px;">'
			if (self.objectImage != ""):
				# use first image for slot
				tempStr += '<img src="' + self.objectImage + '" class="schematicIngredient" />'
				tempStr += '</td><td>'
				tempStr += '<div class="schematicIngredient">'
				if self.ingredientType > 2:
					tempStr += '(Optional) '
				tempStr += self.objectLink
				tempStr += '</div>'
			else:
				tempStr = '</td><td><div>'
				if self.ingredientType > 2:
					tempStr += '(Optional) '
				tempStr += self.objectLink
				tempStr += '</div>'

			return tempStr

class schematicQualityGroup:
	def __init__(self, group = ""):
		self.group = group
		self.properties = []

	def groupName(self):
		return self.group.replace('_','')

class schematicQualityProperty:
	def __init__(self, prop = "", weightTotal = 0):
		self.prop = prop
		self.weightTotal = weightTotal
		self.statWeights = []

	def propertyName(self):
		return self.prop.replace('_','')

class schematicStatWeight:
	def __init__(self, qualityID = 0, stat = "", statWeight = 0, propWeightTotal = 0):
		self.qualityID = qualityID
		self.stat = stat
		self.statWeight = statWeight
		self.propWeightTotal = propWeightTotal

	def statName (self):
		return ghNames.getStatName(self.stat)

	def weightPercent(self):
		return '%.0f' % ((self.statWeight*1.0/self.propWeightTotal)*100)

class schematic:
	def __init__(self):
		self.schematicID = ""
		self.schematicName = ""
		self.craftingTab = 0
		self.skillGroup = ""
		self.complexity = 0
		self.xpAmount = 0
		self.schematicImage = "none.jpg"
		self.galaxy = 0
		self.enteredBy = ""
		self.ingredients = []
		self.qualityGroups = []
		self.schematicsUsedIn = []
