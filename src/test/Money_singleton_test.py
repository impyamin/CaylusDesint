import unittest
from moneyres_mod import Money


#On instancie deux objets et on verifie qu'ils sont bien le meme id (comme on le ferait pour un pointeur d'adr)
class TestMoney_singleton(unittest.TestCase):
    def test_money_singleton(self):
        money = Money("moneyTest",14)
        money2= Money("moneyTest2",14)

        self.assertEqual(id(money),id(money2))
           

if __name__ == '__main__':
    unittest.main()