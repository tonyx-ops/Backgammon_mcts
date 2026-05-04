# This file stores the move and board.

from backgammon_mcts.constants import COMPUTER, HUMAN, PLAYER_NAME, PLAYERS


class Move:
    def __init__(self, src, dst, die, hit=False, bear_off=False):
        # Where the checker starts.
        self.src = src
        # Where the checker lands.
        self.dst = dst
        # The die used for this move.
        self.die = die
        # True if this move hits the other player.
        self.hit = hit
        # True if this checker leaves the board.
        self.bear_off = bear_off

    def key(self):
        # Make a small ID for this move.
        return (self.src, self.dst, self.die, self.hit, self.bear_off)

    def pattern_key(self):
        # Used when the player types a move.
        return (self.src, self.dst, self.bear_off)


class GameState:
    # Related code reference, not copied:
    # dellalibera/gym-backgammon also stores a Backgammon board,
    # bar checkers, and off checkers as the main game state.
    # https://github.com/dellalibera/gym-backgammon
    def __init__(self, board=None, bar=None, off=None):
        # Board has 24 points.
        if board is not None:
            self.board = board[:]
        else:
            self.board = [0] * 24
        # Bar holds hit checkers.
        if bar is not None:
            self.bar = dict(bar)
        else:
            self.bar = {HUMAN: 0, COMPUTER: 0}
        # Off holds finished checkers.
        if off is not None:
            self.off = dict(off)
        else:
            self.off = {HUMAN: 0, COMPUTER: 0}

    def copy(self):
        # Make a copy before trying a move.
        return GameState(self.board, self.bar, self.off)

    def add_checkers(self, player, point, count):
        # Put checkers on the board.
        if not 1 <= point <= 24:
            raise ValueError(f"point must be 1..24, got {point}")
        self.board[point - 1] += player * count

    def count_on_point(self, player, idx):
        # Count this player's checkers on one point.
        val = self.board[idx] * player
        if val > 0:
            return val
        return 0

    def opponent_count_on_point(self, player, idx):
        # Count enemy checkers on one point.
        val = self.board[idx] * player
        if val < 0:
            return -val
        return 0

    def total_checkers(self, player):
        # Each player should always have 15 checkers.
        on_board = 0
        for i in range(24):
            count = self.board[i] * player
            if count > 0:
                on_board += count
        return on_board + self.bar[player] + self.off[player]

    def assert_valid(self):
        # Stop if the board is broken.
        for player in PLAYERS:
            total = self.total_checkers(player)
            if total != 15:
                raise AssertionError(f"{PLAYER_NAME[player]} has {total} checkers, expected 15")
        for i, val in enumerate(self.board):
            if abs(val) > 15:
                raise AssertionError(f"impossible checker count on point {i + 1}: {val}")

    def winner(self):
        # First player with 15 off wins.
        if self.off[HUMAN] >= 15:
            return HUMAN
        if self.off[COMPUTER] >= 15:
            return COMPUTER
        return None

    def apply_move(self, player, move):
        # Remove the checker from the start.
        if move.src is None:
            if self.bar[player] <= 0:
                raise ValueError("cannot move from bar: no checker on bar")
            self.bar[player] -= 1
        else:
            if self.board[move.src] * player <= 0:
                raise ValueError(f"no {PLAYER_NAME[player]} checker on point {move.src + 1}")
            self.board[move.src] -= player

        if move.bear_off:
            self.off[player] += 1
            return

        if move.dst is None:
            raise ValueError("non-bearing move requires a destination point")

        # Hit sends one enemy checker to the bar.
        if move.hit:
            if self.board[move.dst] != -player:
                raise ValueError("hit flag set, but destination is not an opponent blot")
            self.board[move.dst] = 0
            self.bar[-player] += 1

        if self.board[move.dst] * player <= -2:
            raise ValueError("cannot move onto a blocked point")
        self.board[move.dst] += player

    def apply_sequence(self, player, sequence):
        # Apply all moves in one turn.
        for move in sequence:
            self.apply_move(player, move)


def create_initial_state():
    # Make the starting board.
    # Rule source: U.S. Backgammon Federation,
    # "Backgammon Basics: How To Play".
    # It gives the standard starting checker setup.
    state = GameState()
    # X starting checkers.
    state.add_checkers(HUMAN, 24, 2)
    state.add_checkers(HUMAN, 13, 5)
    state.add_checkers(HUMAN, 8, 3)
    state.add_checkers(HUMAN, 6, 5)
    # O starting checkers.
    state.add_checkers(COMPUTER, 1, 2)
    state.add_checkers(COMPUTER, 12, 5)
    state.add_checkers(COMPUTER, 17, 3)
    state.add_checkers(COMPUTER, 19, 5)
    return state
