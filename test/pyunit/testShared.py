import unittest
from datetime import timedelta, datetime
import sys
sys.path.append("../../config")
sys.path.append("../../html")
import ghShared

class testShared(unittest.TestCase):
	def setUp(self):
		# nothin yet
		self.test = "rad"
	
	def test_timeAgoMinutes(self):
		minutesago = datetime.now() - timedelta(0, 2760)
		result = ghShared.timeAgo(minutesago)
		self.assertEqual(result, "46 minutes")

	def test_timeAgoDays(self):
		daysago = datetime.now() - timedelta(4)
		result = ghShared.timeAgo(daysago)
		self.assertEqual(result, "4 days")

if __name__ == '__main__':
	unittest.main()

