import unittest
from unittest import mock
from player_mod import * 
from game_mod import indent



#On instancie deux objets et on verifie qu'ils sont bien le meme id (comme on le ferait pour un pointeur d'adr)
class TestProvost_movement(unittest.TestCase):
    @mock.patch('builtins.input')
    def test_provost_bad_interval(self,patched_input):
        patched_input.return_value = "F"
        color_player = ColorPlayer("blue")
        player = HumanPlayer(color_player)
        self.assertTrue(player.choose_n_provost_movement(0,0))
           
    
if __name__ == '__main__':
    unittest.main()


    # def choose_n_provost_movement(self, n_min_provost_movements_player: int,
    #                               n_max_provost_movements_player: int) -> int:
    #     response = input(indent(3) + 'How long do you want to move the Provost? [' +
    #                      str(n_min_provost_movements_player) + '..' + str(n_max_provost_movements_player) +
    #                      '] ')  # type: str
    #     return self.check_response_in_interval(response, n_min_provost_movements_player, n_max_provost_movements_player,
    #                                            4)