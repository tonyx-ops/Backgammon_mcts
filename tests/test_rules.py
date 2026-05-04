import unittest

from backgammon_mcts.constants import COMPUTER, HUMAN
from backgammon_mcts.models import GameState, create_initial_state
from backgammon_mcts.rules import legal_sequences, legal_single_moves, pip_count


class RulesTest(unittest.TestCase):
    def test_initial_position_is_valid(self):
        # Start board should be correct.
        state = create_initial_state()

        state.assert_valid()
        self.assertEqual(167, pip_count(state, HUMAN))
        self.assertEqual(167, pip_count(state, COMPUTER))

    def test_hit_sends_opponent_checker_to_bar(self):
        # Make a small board with one hit.
        state = GameState()
        state.add_checkers(HUMAN, 8, 1)
        state.add_checkers(COMPUTER, 5, 1)

        # X moves 8 to 5 and hits O.
        moves = legal_single_moves(state, HUMAN, 3)
        hit_moves = []
        for move in moves:
            if move.hit:
                hit_moves.append(move)

        self.assertEqual(1, len(hit_moves))
        state.apply_move(HUMAN, hit_moves[0])
        self.assertEqual(1, state.board[4])
        self.assertEqual(1, state.bar[COMPUTER])

    def test_checker_on_bar_must_enter_first(self):
        # Bar checker must move before other checkers.
        state = GameState()
        state.bar[HUMAN] = 1
        state.add_checkers(HUMAN, 6, 1)
        state.add_checkers(COMPUTER, 24, 2)
        state.add_checkers(COMPUTER, 23, 1)

        # Die 1 is blocked.
        self.assertEqual([], legal_single_moves(state, HUMAN, 1))

        # Die 2 can enter and hit.
        moves = legal_single_moves(state, HUMAN, 2)
        self.assertEqual(1, len(moves))
        self.assertIsNone(moves[0].src)
        self.assertEqual(22, moves[0].dst)
        self.assertTrue(moves[0].hit)

    def test_bear_off_with_exact_die(self):
        # Exact die can bear off.
        state = GameState()
        state.add_checkers(HUMAN, 1, 1)
        state.off[HUMAN] = 14

        moves = legal_single_moves(state, HUMAN, 1)

        self.assertEqual(1, len(moves))
        self.assertTrue(moves[0].bear_off)

    def test_initial_roll_has_legal_sequences(self):
        # Opening board should have moves.
        state = create_initial_state()
        human_actions = legal_sequences(state, HUMAN, (3, 1))
        computer_actions = legal_sequences(state, COMPUTER, (3, 1))

        self.assertEqual(16, len(human_actions))
        self.assertEqual(16, len(computer_actions))


if __name__ == "__main__":
    unittest.main()
