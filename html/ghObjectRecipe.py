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

import ghShared

class recipeIngredient:
	def __init__(self, ingObject=None, ingResource="", ingName="", ingAmount=0, ingType="", ingObjectName="", resQuality=None, resDetails=""):
		self.ingredientObject = ingObject
		self.ingredientObjectName = ingObjectName
		self.ingredientResource = ingResource
		self.ingredientName = ingName
		self.ingredientAmount = ingAmount
		self.ingredientType = ingType
		self.resourceQuality = resQuality
		self.resourceDetails = resDetails


class schematicRecipe:
	def __init__(self):
		self.recipeID = 0
		self.schematicID = ""
		self.schematicImage = "none.jpg"
		self.recipeName = ""
		self.recipeIngredients = []

	# Return style to use for coloring on resource quality status preview
	@staticmethod
	def getResourceValueColor(resourceValue):
		if (resourceValue >= 650):
			return "green"
		elif (resourceValue >= 350):
			return "yellow"
		else:
			return "red"

	def getIngredientSlots(self):
		result = '<div id="recipeIngredients" onmousemove="slotHoverCheck(event)">'
		for ing in self.recipeIngredients:
			# Set up additional html for filled slot
			addClass = ''
			amountStr = '0'
			qualityIndicatorStyle = ''
			addProperties = ''
			qualityBarStyle = ''
			if ing.ingredientResource != None:
				addClass = ' ingredientSlotFilled'
				amountStr = str(ing.ingredientAmount)
				if ing.resourceQuality != None:
					qualityIndicatorStyle = ' style="height:' + str(70*ing.resourceQuality/1000) + 'px;background-color:' + self.getResourceValueColor(ing.resourceQuality) + ';"'
				addProperties = ' tag="filled" spawnID="' + str(ing.ingredientResource) + '" tt="' + ing.resourceDetails + '"'
			else:
				qualityBarStyle = ' style="display:none;"'
			# Add slot to result
			result += '<div class="inlineBlock recipeIngredient" tag="' + ing.ingredientObject + '" title="Requires ' + str(ing.ingredientObjectName) + '">'
			result += '<div class="ingredientHeader">' + ing.ingredientName.replace('_',' ') + '</div>'
			result += '<div class="ingredientSlot' + addClass + '" style="background-repeat:no-repeat;background-position: 10px 10px;background-image:url(/images/resources/' + str(ing.ingredientType) + '.png)"' + addProperties + '>' + amountStr + '/' + str(ing.ingredientAmount) + '</div>'
			result += '<div class="qualityBar"' + qualityBarStyle + '><div class="qualityIndicator"' + qualityIndicatorStyle + '></div></div>'
			result += '</div>'
		result += '</div>'
		return result

	def getRow(self, listType='normal', sid=''):
		result = ''
		# Get average quality of filled ingredient slots
		qualityIndicatorStyle = ''
		qualityBarInfo = ''
		qualityAvg = self.getAverageQuality()
		qualityIndicatorStyle = ' style="width:' + str(140*qualityAvg/1000.0) + 'px;background-color:' + self.getResourceValueColor(qualityAvg) + ';"'
		qualityBarInfo = str(int(qualityAvg)) + '/1000 average quality.'

		# Build row html
		result += '<tr id="recipe' + str(self.recipeID) + '" class="recipeRow">'
		if listType == 'suggest':
			result += '  <td style="width:32px;"><img src="/images/schematics/' + self.schematicImage + '" class="schematicIngredient" /></td>'
			result += '  <td title="' + qualityBarInfo + '"><div>' + self.recipeName + '</div>'
		else:
			linkTarget = ' href="' + ghShared.BASE_SCRIPT_URL + 'recipe.py/' + str(self.recipeID) + '?gh_sid=' + sid + '"'
			result += '  <td style="width:32px;"><a' + linkTarget + '><img src="/images/schematics/' + self.schematicImage + '" class="schematicIngredient" /></a></td>'
			result += '  <td title="' + qualityBarInfo + '"><div><a class="nameLink"' + linkTarget + '>' + self.recipeName + '</a></div>'

		# Quality bar
		result += '  <div class="recipeQualityBar"><div class="qualityIndicator"' + qualityIndicatorStyle + '></div></div>'

		# Slot filled summary
		result += '<div style="float:right;margin:2px;">'
		for ing in self.recipeIngredients:
			addStyle = ''
			addTitle = ''
			if ing.ingredientResource != None and ing.ingredientResource != '':
				addStyle = ' slotIndicatorFilled'
				if ing.resourceQuality != None:
					addTitle = ' (quality:%.0f' % ing.resourceQuality + ')'
				else:
					addTitle = ' (quality:N/A)'
			result += '<div class="inlineBlock slotIndicator' + addStyle + '" title="' + (ing.ingredientName + ': ' + ing.ingredientObject).replace('_',' ') + addTitle + '"></div>'
		result += '</div>'

		result += '  </td>'
		if listType == 'suggest':
			ingredientString = ''
			for ing in self.recipeIngredients:
				ingredientString += ing.ingredientName + ':' + ing.ingredientResource + ','
			result += '  <td><button type=button value="Save" class="ghButton" onclick="saveSuggestedRecipe(\'' + self.schematicID + '\',\'' + self.recipeName + ' suggested\',\'' + ingredientString + '\', $(\'#galaxySel\').val());">Save</button></td>'
		else:
			result += '  <td><a alt="Delete Recipe" style="cursor: pointer;" onclick="deleteRecipe(this, \'' + str(self.recipeID) + '\');">[X]</a></td>'

		result += '</tr>'
		return result

	def getAverageQuality(self):
		qualityTotal = 0
		qualityIngredients = 0
		for ing in self.recipeIngredients:
			if ing.ingredientResource != '' and ing.resourceQuality != None:
				qualityTotal += ing.resourceQuality
				qualityIngredients += 1

		if qualityIngredients > 0:
			qualityAvg = qualityTotal/qualityIngredients
		else:
			qualityAvg = 0

		return qualityAvg
