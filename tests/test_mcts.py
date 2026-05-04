import random
import unittest

from backgammon_mcts.ai_mcts import MCTSAI
from backgammon_mcts.constants import COMPUTER, HUMAN
from backgammon_mcts.models import create_initial_state
from backgammon_mcts.rules import legal_sequences, opponent, pip_count, roll_dice


def make_ai(level, simulations):
    # Make one AI for the test.
    return MCTSAI(simulations=simulations, rollout_depth=level)


def play_ai_game(seed, human_ai, computer_ai):
    # Play one fixed-seed AI game.
    random.seed(seed)
    state = create_initial_state()
    current_player = HUMAN
    current_roll = (3, 1)
    turns = 0
    max_turns = 220

    while turns < max_turns:
        winner = state.winner()
        if winner is not None:
            return winner

        if current_roll is not None:
            roll = current_roll
        else:
            roll = roll_dice()
        current_roll = None

        actions = legal_sequences(state, current_player, roll)
        if actions and actions[0]:
            if current_player == HUMAN:
                action = human_ai.choose_move(state, HUMAN, roll)
            else:
                action = computer_ai.choose_move(state, COMPUTER, roll)
            state.apply_sequence(current_player, action)

        current_player = opponent(current_player)
        turns += 1

    # If the game does not finish, use pip count as a backup.
    human_pips = pip_count(state, HUMAN)
    computer_pips = pip_count(state, COMPUTER)
    if human_pips < computer_pips:
        return HUMAN
    return COMPUTER


class MCTSTest(unittest.TestCase):
    def test_level_6_beats_level_3_in_seeded_game(self):
        # Level 3 uses 120 simulations.
        # Level 6 uses the project setting of 300 simulations.
        level_6 = make_ai(6, 300)
        level_3 = make_ai(3, 120)

        winner = play_ai_game(1, level_6, level_3)

        self.assertEqual(HUMAN, winner)

    def test_level_8_beats_level_6_in_seeded_game(self):
        # Level 8 uses 400 simulations.
        # This is a small safety check.
        level_8 = make_ai(8, 400)
        level_6 = make_ai(6, 300)

        winner = play_ai_game(2, level_8, level_6)

        self.assertEqual(HUMAN, winner)

    def test_level_8_beats_level_3_in_seeded_game(self):
        # This checks a larger strength gap.
        level_8 = make_ai(8, 400)
        level_3 = make_ai(3, 120)

        winner = play_ai_game(3, level_8, level_3)

        self.assertEqual(HUMAN, winner)


if __name__ == "__main__":
    unittest.main()
