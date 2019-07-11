import unittest
from game_mod.utils import ordinal_number

class TestOrdinal_number(unittest.TestCase):
    def test_number_under_scope(self):
        with self.assertRaises(Exception):
           ordinal_number(0)
           
    def test_first_digit(self):
        self.assertEqual(ordinal_number(1),"1st")

    def test_second_digit(self):
        self.assertEqual(ordinal_number(2),"2nd")

    def test_third_digit(self):
        self.assertEqual(ordinal_number(3),"3rd")

    def test_other_digit(self):
        for n in range(4,10) :
            self.assertEqual(ordinal_number(n),str(n)+"th")
    
       

if __name__ == '__main__':
    unittest.main()