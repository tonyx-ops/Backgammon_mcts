# Monte Carlo Tree Search / UCT computer player.

import math
import random

from backgammon_mcts.rules import (
    blot_count,
    home_checker_count,
    legal_sequences,
    made_point_count,
    opponent,
    pip_count,
    roll_dice,
)


def heuristic_score(state, player):
    """Positive means good for `player`; negative means good for the opponent."""
    winner = state.winner()
    if winner == player:
        return 1_000_000.0
    if winner == opponent(player):
        return -1_000_000.0

    # Count how far both players still need to move.
    opp = opponent(player)
    my_pips = pip_count(state, player)
    opp_pips = pip_count(state, opp)

    # Citation: Berliner (1977) and Tesauro (1995) both use board features to
    # evaluate backgammon positions.
    #
    # Berliner, "BKG, a Program That Plays Backgammon", 1977.
    # Tesauro, "Temporal Difference Learning and TD-Gammon", 1995.
    # These feature ideas are common in backgammon evaluators.
    # The exact weights here are not from a paper.
    # I roughly chose them after a few small local tests.
    pip_delta = opp_pips - my_pips
    off_delta = state.off[player] - state.off[opp]
    bar_delta = state.bar[opp] - state.bar[player]
    made_delta = made_point_count(state, player) - made_point_count(state, opp)
    blot_delta = blot_count(state, opp) - blot_count(state, player)
    home_delta = home_checker_count(state, player) - home_checker_count(state, opp)

    return (
        1.6 * pip_delta + 14.0 * off_delta + 22.0 * bar_delta + 2.4 * made_delta
        + 2.0 * blot_delta + 0.5 * home_delta
    )


def terminal_or_heuristic_reward(state, root_player):
    # Return 1 for a win and 0 for a loss.
    winner = state.winner()
    if winner is not None:
        if winner == root_player:
            return 1.0
        return 0.0
    # If the game is not done, use the board score.
    score = heuristic_score(state, root_player)
    # Citation: Motif Backgammon uses (tanh(x) + 1) / 2 to turn a score into 0..1.
    # Tom Keith, "How Motif Backgammon Works", 1996/2004.
    return 0.5 + 0.5 * math.tanh(score / 80.0)


# Citation: UCT/MCTS idea from Kocsis and Szepesvari,
# "Bandit Based Monte-Carlo Planning", 2006.
class MCTSAI:
    """
    Root-level UCT/MCTS for a stochastic game.

    At the current turn, the dice are already known. Each complete legal move sequence is
    a root child. MCTS repeatedly:
        1. selects a child with UCB1,
        2. applies that move sequence,
        3. rolls out future turns by sampling dice,
        4. backs up the reward to the chosen root child.

    The rollout policy is heuristic-biased: usually choose the one-ply move with the best
    heuristic score, sometimes choose randomly for exploration.
    """
    
    def __init__(self, simulations=120, rollout_depth=6, exploration=1.4, rollout_randomness=0.18):
        # Save the AI settings.
        # The exact simulation count and rollout depth are not copied from a paper.
        # They are smaller project settings so the game is fast enough to play.
        # Related Backgammon work used much larger rollout counts:
        # Tesauro and Galperin: about 10,000+ trials per candidate move.
        # Van Lishout, Chaslot, and Uiterwijk: 200,000 random games for opening tests.
        # My Apple MacBook Pro M3 was not fast enough for those paper-level counts
        # in an interactive terminal game, so this project uses smaller numbers.
        self.simulations = max(0, simulations)
        self.rollout_depth = max(1, rollout_depth)
        # UCB1 uses: average + sqrt(2 * log(total) / tries).
        # This code writes that as average + c * sqrt(log(total) / tries).
        # So c = sqrt(2), and 1.4 is a simple approximation.
        # Citation: Auer, Cesa-Bianchi, and Fischer,
        # "Finite-time Analysis of the Multiarmed Bandit Problem", 2002.
        # Kocsis and Szepesvari also use this UCB1 idea in UCT/MCTS,
        # "Bandit Based Monte-Carlo Planning", 2006.
        self.exploration = exploration
        self.rollout_randomness = rollout_randomness

    def choose_move(self, state, player, roll):
        # Find all moves the computer can play.
        actions = legal_sequences(state, player, roll)
        playable_actions = []
        for action in actions:
            if action:
                playable_actions.append(action)

        # If there is no move, pass.
        if not playable_actions:
            return tuple()

        # If there is only one move, play it.
        if len(playable_actions) == 1:
            return playable_actions[0]

        # If simulations are off, use the simple score.
        if self.simulations <= 0:
            return self.best_by_heuristic(state, player, playable_actions)

        # Count tries and scores for each move.
        visits = []
        value_sums = []
        for action in playable_actions:
            visits.append(0)
            value_sums.append(0.0)

        # Try moves many times.
        for sim in range(self.simulations):
            idx = self.select_ucb(visits, value_sums, sim + 1)
            next_state = state.copy()
            next_state.apply_sequence(player, playable_actions[idx])
            reward = self.rollout(next_state, opponent(player), player)
            visits[idx] += 1
            value_sums[idx] += reward

        # Prefer average value; break ties by visits, then heuristic.
        best_idx = 0
        best_avg = -1.0
        best_visits = -1
        best_score = -float("inf")

        for i in range(len(playable_actions)):
            if visits[i]:
                avg = value_sums[i] / visits[i]
            else:
                avg = -1.0

            after = state.copy()
            after.apply_sequence(player, playable_actions[i])
            score = heuristic_score(after, player)

            is_better = False
            if avg > best_avg:
                is_better = True
            elif avg == best_avg and visits[i] > best_visits:
                is_better = True
            elif avg == best_avg and visits[i] == best_visits and score > best_score:
                is_better = True

            if is_better:
                best_idx = i
                best_avg = avg
                best_visits = visits[i]
                best_score = score

        return playable_actions[best_idx]

    def select_ucb(self, visits, value_sums, total):
        # Try every move at least once.
        unvisited = []
        for i in range(len(visits)):
            if visits[i] == 0:
                unvisited.append(i)
        if unvisited:
            return random.choice(unvisited)

        # After that, choose a move using the UCB1 score plus a bonus.
        log_total = math.log(max(1, total))
        best_idx = 0
        best_value = -float("inf")
        for i, v in enumerate(visits):
            mean = value_sums[i] / v
            bonus = self.exploration * math.sqrt(log_total / v)
            ucb = mean + bonus
            if ucb > best_value:
                best_value = ucb
                best_idx = i
        return best_idx

    def rollout(self, state, current_player, root_player):
        # Play a fake short game to guess what might happen.
        for turn in range(self.rollout_depth):
            winner = state.winner()
            if winner is not None:
                if winner == root_player:
                    return 1.0
                return 0.0

            # Future dice are unknown, so each rollout samples new dice.
            roll = roll_dice()
            actions = legal_sequences(state, current_player, roll)
            if actions and actions[0]:
                action = self.rollout_policy(state, current_player, actions)
                state.apply_sequence(current_player, action)
            current_player = opponent(current_player)

        return terminal_or_heuristic_reward(state, root_player)

    def rollout_policy(self, state, player, actions):
        # Sometimes choose a random move.
        if not actions:
            return tuple()
        if random.random() < self.rollout_randomness:
            return random.choice(actions)
        # Usually choose the move with the best score.
        return self.best_by_heuristic(state, player, actions)

    def best_by_heuristic(self, state, player, actions):
        # Check each move and keep the best one.
        best_action = actions[0]
        best_score = -float("inf")
        for action in actions:
            after = state.copy()
            after.apply_sequence(player, action)
            score = heuristic_score(after, player)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action
