# This file has the game rules.
# Rule source: U.S. Backgammon Federation,
# "Backgammon Basics: How To Play".
# I used it for open points, hitting, entering from the bar,
# bearing off, doubles, and using as many dice as possible.
# Related code references, not copied:
# dellalibera/gym-backgammon has get_valid_actions for legal moves.
# https://github.com/dellalibera/gym-backgammon
# backgammon_engine has gen_poss_next_states for state transitions.

import random

from backgammon_mcts.constants import COMPUTER, HUMAN, PLAYERS
from backgammon_mcts.models import Move


def opponent(player):
    # Change X to O, or O to X.
    return -player


def movement_direction(player):
    # X moves down. O moves up.
    if player == HUMAN:
        return -1
    return 1


def home_indices(player):
    # Home board is the last 6 points.
    if player == HUMAN:
        return range(0, 6)
    return range(18, 24)


def is_open_point(state, player, idx):
    # Two enemy checkers block a point.
    return state.board[idx] * player > -2


def entry_index(player, die):
    # Find where a checker enters from the bar.
    if player == HUMAN:
        # X enters near point 24.
        return 24 - die
    # O enters near point 1.
    return die - 1


def all_checkers_home(state, player):
    # You can bear off only when all checkers are home.
    if state.bar[player] > 0:
        return False
    homes = set(home_indices(player))
    for idx, val in enumerate(state.board):
        if val * player > 0 and idx not in homes:
            return False
    return True


def can_bear_off_from(state, player, src, die):
    # First check if bearing off is allowed.
    if not all_checkers_home(state, player):
        return False

    if player == HUMAN:
        # X bears off after point 1.
        point = src + 1
        if die == point:
            return True
        if die > point:
            # Big die can only move the farthest checker.
            for i in range(src + 1, 6):
                if state.board[i] * player > 0:
                    return False
            return True
        return False

    # O bears off after point 24.
    distance = 24 - src
    if die == distance:
        return True
    if die > distance:
        # Big die can only move the farthest checker.
        for i in range(18, src):
            if state.board[i] * player > 0:
                return False
        return True
    return False


def legal_single_moves(state, player, die):
    # Make legal moves for one die.
    moves = []

    # Bar checkers must move first.
    if state.bar[player] > 0:
        dst = entry_index(player, die)
        if is_open_point(state, player, dst):
            hit = state.board[dst] == -player
            moves.append(Move(src=None, dst=dst, die=die, hit=hit, bear_off=False))
        return moves

    direction = movement_direction(player)
    # Check points in the moving direction.
    if player == HUMAN:
        point_order = range(23, -1, -1)
    else:
        point_order = range(24)

    # Try every checker.
    for src in point_order:
        if state.board[src] * player <= 0:
            continue

        # Move by the die number.
        dst = src + direction * die
        if 0 <= dst < 24:
            if is_open_point(state, player, dst):
                hit = state.board[dst] == -player
                moves.append(Move(src=src, dst=dst, die=die, hit=hit, bear_off=False))
        else:
            if can_bear_off_from(state, player, src, die):
                moves.append(Move(src=src, dst=None, die=die, hit=False, bear_off=True))

    return moves


def make_sequences_for_order(state, player, dice_order):
    # Build moves for one dice order.
    frontier = {state_key(state): (state.copy(), tuple())}
    finished = []

    # Use one die at a time.
    for die in dice_order:
        next_frontier = {}

        for current_state, path in frontier.values():
            moves = legal_single_moves(current_state, player, die)
            if not moves:
                # This path cannot use this die.
                finished.append(path)
                continue

            # Add each possible next move.
            for move in moves:
                next_state = current_state.copy()
                next_state.apply_move(player, move)
                next_path = path + (move,)
                key = state_key(next_state)

                if key not in next_frontier or sequence_to_str(next_path) < sequence_to_str(next_frontier[key][1]):
                    next_frontier[key] = (next_state, next_path)

        if not next_frontier:
            if finished:
                return finished
            return [tuple()]

        frontier = next_frontier

    for current_state, path in frontier.values():
        finished.append(path)

    if finished:
        return finished
    return [tuple()]


def legal_sequences(state, player, roll):
    # Make legal moves for the full roll.
    d1, d2 = roll
    if d1 == d2:
        # Doubles means four moves.
        orders = [(d1, d1, d1, d1)]
    else:
        # Normal rolls can be played in either order.
        orders = [(d1, d2), (d2, d1)]

    # Try all dice orders.
    all_sequences = []
    for order in orders:
        all_sequences.extend(make_sequences_for_order(state, player, order))

    if not all_sequences:
        return [tuple()]

    # Use as many dice as possible.
    max_len = 0
    for seq in all_sequences:
        if len(seq) > max_len:
            max_len = len(seq)

    filtered = []
    for seq in all_sequences:
        if len(seq) == max_len:
            filtered.append(seq)

    # If only one die works, use the bigger die.
    if d1 != d2 and max_len == 1:
        high = max(d1, d2)
        high_die_sequences = []
        for seq in filtered:
            if seq and seq[0].die == high:
                high_die_sequences.append(seq)
        if high_die_sequences:
            filtered = high_die_sequences

    # Remove duplicate board results.
    by_position = {}
    for seq in filtered:
        after = state.copy()
        after.apply_sequence(player, seq)
        key = state_key(after)
        if key not in by_position or sequence_to_str(seq) < sequence_to_str(by_position[key]):
            by_position[key] = seq

    unique = list(by_position.values())
    unique.sort(key=sequence_sort_key)
    if unique:
        return unique
    return [tuple()]


def sequence_sort_key(sequence):
    # Make a simple sort key for a move sequence.
    parts = []
    for move in sequence:
        parts.append(move_to_str(move))
    return tuple(parts)


def state_key(state):
    # Turn the board into a key for a dict.
    return (tuple(state.board), state.bar[HUMAN], state.bar[COMPUTER], state.off[HUMAN], state.off[COMPUTER])


def point_name(idx):
    # Show a board point name.
    if idx is None:
        return "off"
    return str(idx + 1)


def move_to_str(move):
    # Change one move to text.
    if move.src is None:
        src = "bar"
    else:
        src = str(move.src + 1)

    if move.bear_off:
        dst = "off"
    elif move.dst is not None:
        dst = str(move.dst + 1)
    else:
        dst = "?"

    if move.hit:
        suffix = "*"
    else:
        suffix = ""

    return f"{src}/{dst}{suffix}"


def sequence_to_str(sequence):
    # Change a whole turn to text.
    if not sequence:
        return "pass"

    parts = []
    for move in sequence:
        parts.append(move_to_str(move))
    return " ".join(parts)


def roll_dice():
    # Roll two dice.
    return random.randint(1, 6), random.randint(1, 6)


def pip_count(state, player):
    # Count how far the player still needs to move.
    pips = state.bar[player] * 25
    for idx, val in enumerate(state.board):
        count = val * player
        if count <= 0:
            continue
        if player == HUMAN:
            distance = idx + 1  # X moves toward point 1.
        else:
            distance = 24 - idx  # O moves toward point 24.
        pips += count * distance
    return pips


def blot_count(state, player):
    # Count single checkers.
    total = 0
    for val in state.board:
        if val * player == 1:
            total += 1
    return total


def made_point_count(state, player):
    # Count points with 2 or more checkers.
    total = 0
    for val in state.board:
        if val * player >= 2:
            total += 1
    return total


def home_checker_count(state, player):
    # Count checkers in the home board.
    total = 0
    for i in home_indices(player):
        count = state.board[i] * player
        if count > 0:
            total += count
    return total


def endgame_label(state, winner):
    # Decide what kind of win it is.
    loser = opponent(winner)
    if state.off[loser] > 0:
        return "single game"
    # Bigger win if loser has no checkers off.
    winner_home = set(home_indices(winner))
    loser_on_bar = state.bar[loser] > 0
    loser_in_winner_home = False
    for i in winner_home:
        if state.board[i] * loser > 0:
            loser_in_winner_home = True
    if loser_on_bar or loser_in_winner_home:
        return "backgammon"
    return "gammon"


# Helper for tests.
def checker_totals(state):
    totals = {}
    for player in PLAYERS:
        totals[player] = state.total_checkers(player)
    return totals
