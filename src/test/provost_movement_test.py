import unittest
from unittest import mock
from player_mod import * 
from game_mod import indent



class TestProvost_movement(unittest.TestCase):
    @mock.patch('builtins.input')
    def test_provost_in_interval(self,patched_input):
        patched_input.kwargs = ['11,10']

        color_player = ColorPlayer("blue")
        player = HumanPlayer(color_player)        
        self.assertTrue(player.choose_n_provost_movement(0,10))

    
    @mock.patch('builtins.input', lambda *args : '2')
    @mock.patch('player_mod.HumanPlayer.check_response_in_interval')
    def test_proper_interval_underflow(self,response_patch):
        min_val = 0
        max_val = 10
        x = 7

        response_patch.return_value = False if x < min_val or x >  max_val else True

        color_player = ColorPlayer("blue")
        player = HumanPlayer(color_player)
        
        self.assertTrue(player.choose_n_provost_movement(3,10))


    @mock.patch('builtins.input', lambda *args : '7')
    @mock.patch('player_mod.HumanPlayer.check_response_in_interval')
    def test_proper_interval_overflow(self,response_patch):
        min_val = 0
        max_val = 10
        x = 7
        response_patch.return_value = False if x < min_val or x >  max_val else True

        color_player = ColorPlayer("blue")
        player = HumanPlayer(color_player)
        
        self.assertTrue(player.choose_n_provost_movement(0,10)) 
           
    
if __name__ == '__main__':
    unittest.main()