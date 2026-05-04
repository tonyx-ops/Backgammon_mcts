import random

from backgammon_mcts.ai_mcts import MCTSAI
from backgammon_mcts.constants import COMPUTER, HUMAN, PLAYER_NAME
from backgammon_mcts.display import display_board
from backgammon_mcts.models import create_initial_state
from backgammon_mcts.parser_io import human_choose_action
from backgammon_mcts.rules import endgame_label, legal_sequences, opponent, roll_dice, sequence_to_str


# AI level used for this project.
# The idea of using Monte Carlo rollouts comes from Backgammon AI papers,
# but the exact number here is my project tuning choice.
# Tesauro and Galperin used about 10,000+ trials per candidate move.
# Van Lishout, Chaslot, and Uiterwijk used 200,000 random games
# for Backgammon opening move tests.
# Those numbers are too slow for this terminal game on my Apple MacBook Pro M3,
# so I use level 6: 300 simulations and rollout depth 6.
AI_LEVEL = 6


def make_ai(level):
    # Make the computer player.
    simulations = level * 50
    depth = level
    return MCTSAI(simulations=simulations, rollout_depth=depth)


def opening_roll():
    # Roll dice to choose who starts.
    while True:
        human_die = random.randint(1, 6)
        computer_die = random.randint(1, 6)
        print(f"Opening roll: Human/X {human_die}, Computer/O {computer_die}")
        if human_die > computer_die:
            print("Human/X goes first using the opening dice.")
            return HUMAN, (human_die, computer_die)
        if computer_die > human_die:
            print("Computer/O goes first using the opening dice.")
            return COMPUTER, (human_die, computer_die)
        print("Tie on opening roll; rolling again.")


def play_game():
    # Make the board and AI.
    state = create_initial_state()
    ai = make_ai(AI_LEVEL)

    # Print game intro.
    print("Text Backgammon: Human/X vs Computer/O")
    print("Human/X moves 24 -> 1. Computer/O moves 1 -> 24.")
    print("A '*' after a move means a hit. Example: 13/7*")
    print(f"Computer AI level: {AI_LEVEL}")
    print("Type 'board' during your turn to redraw the X/O board.")

    current_player, current_roll = opening_roll()

    # Main game loop.
    while True:
        # Check the board before each turn.
        state.assert_valid()
        display_board(state)

        # Stop if someone wins.
        winner = state.winner()
        if winner is not None:
            print(f"{PLAYER_NAME[winner]} wins by {endgame_label(state, winner)}!")
            return

        # Use opening roll first, then normal dice.
        if current_roll is not None:
            roll = current_roll
        else:
            roll = roll_dice()
        current_roll = None

        if current_player == HUMAN:
            # Human turn.
            print(f"Your roll: {roll[0]}-{roll[1]}")
            action = human_choose_action(state, roll, ai)
            if action:
                print(f"You play: {sequence_to_str(action)}")
                state.apply_sequence(HUMAN, action)
            else:
                print("You pass.")
        else:
            # Computer turn.
            print(f"Computer roll: {roll[0]}-{roll[1]}")
            actions = legal_sequences(state, COMPUTER, roll)
            if not actions or (len(actions) == 1 and not actions[0]):
                print("Computer has no legal moves and passes.")
            else:
                action = ai.choose_move(state, COMPUTER, roll)
                print(f"Computer plays: {sequence_to_str(action)}")
                state.apply_sequence(COMPUTER, action)

        # Change turns.
        current_player = opponent(current_player)


def main():
    # Start the game.
    try:
        play_game()
    except KeyboardInterrupt:
        print("\nGame interrupted.")
