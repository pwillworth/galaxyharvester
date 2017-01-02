import unittest
from datetime import timedelta, datetime
import sys
sys.path.append("../../config")
sys.path.append("../../html")
import ghObjects
import ghObjectRecipe

class TestObjects(unittest.TestCase):
	def setUp(self):
		# nothin yet
		self.test = "rad"
	
	def test_spawnHTML(self):
		# arrange
		spawnName = "testspawn"
		s = ghObjects.resourceSpawn()
		s.spawnID = 42
		s.spawnName = spawnName
		s.spawnGalaxy = 1
		s.resourceType = "wood_deciduous_yavin4"
		s.resourceTypeName = "Yavinian Deciduous Wood"
		s.containerType = "flora_structural"
		s.stats.CR = 0
		s.stats.CD = 0
		s.stats.DR = 780
		s.stats.FL = 0
		s.stats.HR = 0
		s.stats.MA = 560
		s.stats.PE = 0
		s.stats.OQ = 656
		s.stats.SR = 450
		s.stats.UT = 800
		s.stats.ER = 0
		
		s.percentStats.CR = None
		s.percentStats.CD = None
		s.percentStats.DR = 780.0/800
		s.percentStats.FL = None
		s.percentStats.HR = None
		s.percentStats.MA = 160.0/400
		s.percentStats.PE = None
		s.percentStats.OQ = 656.0/1000
		s.percentStats.SR = 150.0/400
		s.percentStats.UT = 800.0/800
		s.percentStats.ER = None
		s.entered = daysago = datetime.now() - timedelta(4)
		s.enteredBy = "ioscode"
		s.verified = daysago = datetime.now() - timedelta(3)
		s.verifiedBy = "tester"
		s.unavailable = None
		s.unavailableBy = None
		s.maxWaypointConc = None

		# act		
		mobileHTML = s.getMobileHTML(0)
		normalHTML = s.getHTML(0, 0, "")
		rowHTML = s.getRow(0)
		invHTML = s.getInventoryObject()

		#assert
		self.assertIn("ioscode", mobileHTML, "Username not in mobile HTML.")
		self.assertIn("ioscode", normalHTML, "Username not in normal HTML.")
		self.assertIn(spawnName, rowHTML, "No spawn name in row HTML.")
		self.assertIn(spawnName, invHTML, "No spawn name in inventory HTML.")

	def test_recipeRender(self):
		# arrage
		r = ghObjectRecipe.schematicRecipe()
		r.recipeID = 1
		r.schematicID = "armor_segment_composite_advanced"
		r.recipeName = "Test Recipe"

		i1 = ghObjectRecipe.recipeIngredient("steel_kiirium", "17895", "armor_layer_weld_tabs", 8, "0", "Kiirium Steel", 455, "stuff steel")
		i2 = ghObjectRecipe.recipeIngredient("copper_polysteel", "13455", "segment_mounting_tabs", 5, "0", "Polysteel Copper", 877, "This is great")

		r.recipeIngredients.append(i1)
		r.recipeIngredients.append(i2)

		# act
		slotHTML = r.getIngredientSlots()
		rowHTML = r.getRow()

		# assert
		self.assertIn("steel_kiirium", slotHTML, "Resource id not in slot html.")
		self.assertIn("Test Recipe", rowHTML, "Title not in row html.")
		self.assertIn("yellow", slotHTML, "Expected quality color not present in slot HTML.")

if __name__ == '__main__':
	unittest.main()

