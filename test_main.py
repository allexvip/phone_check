import unittest
from main import check_phone_number

class mainTest(unittest.TestCase):

    async def test(self):
        self.assertEqual(
            await check_phone_number('7911133345566'),False
        )
