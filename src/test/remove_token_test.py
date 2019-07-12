import unittest
from game_mod.game import Game
from game_mod.game import GameElement
from  moneyres_mod.moneyres import Castle



class MockedCastle():
    def __init__(self, n_castle_tokens, n_prestige_pts):
        self.n_prestige_pts = n_prestige_pts
        self.n_castle_tokens = n_castle_tokens
        self.current_n_castle_tokens = 4

class MockedGameElement():
    def __init__(self,castle):
        self.castle = castle     

        

class TestRemove_token(unittest.TestCase):
    def test_remove_0_points(self):
        castle = []
        for i in range(0,10):
            c = MockedCastle(2,15)
            castle.append(c)        

        game_element = MockedGameElement(castle)  
        game = Game(game_element,None,None)
        
        self.assertEqual(game.remove_tokens_castle(0),0)
        

class TestRemove_token(unittest.TestCase):
    def test_remove_all_points(self):
        castle = []
        for i in range(0,10):
            c = MockedCastle(2,15)
            castle.append(c)        

        game_element = MockedGameElement(castle)  
        game = Game(game_element,None,None)
        
        self.assertEqual(game.remove_tokens_castle(600),600)


class TestRemove_token(unittest.TestCase):
    def test_excede_points_capacity(self):
        castle = []
        for i in range(0,10):
            c = MockedCastle(2,15)
            castle.append(c)        

        game_element = MockedGameElement(castle)  
        game = Game(game_element,None,None)
        
        self.assertEqual(game.remove_tokens_castle(1000),600)

class TestRemove_token(unittest.TestCase):
    def test_remove_negative(self):
        castle = []
        for i in range(0,10):
            c = MockedCastle(2,15)
            castle.append(c)        

        game_element = MockedGameElement(castle)  
        game = Game(game_element,None,None)
        
        self.assertEqual(game.remove_tokens_castle(-150),0)


        
            
       

if __name__ == '__main__':
    unittest.main()

