# This file reads the human move.

import sys

from backgammon_mcts.constants import HUMAN
from backgammon_mcts.display import display_board, show_legal_actions
from backgammon_mcts.rules import legal_sequences, sequence_to_str


def parse_move_token(token):
    # Read one move like 13/8.
    token = token.strip().lower().replace("*", "")
    if "/" not in token:
        raise ValueError("move must contain '/'")
    src_s, dst_s = token.split("/", 1)

    if src_s == "bar":
        # None means the bar.
        src = None
    else:
        src_point = int(src_s)
        if not 1 <= src_point <= 24:
            raise ValueError("source point must be 1..24")
        src = src_point - 1

    if dst_s == "off":
        # None means off the board.
        return src, None, True

    dst_point = int(dst_s)
    if not 1 <= dst_point <= 24:
        raise ValueError("destination point must be 1..24")
    return src, dst_point - 1, False


def parse_sequence_pattern(text):
    # Split a full turn into moves.
    tokens = []
    raw_tokens = text.replace(",", " ").split()
    for tok in raw_tokens:
        if tok:
            tokens.append(tok)

    if not tokens:
        raise ValueError("empty move")

    moves = []
    for tok in tokens:
        moves.append(parse_move_token(tok))
    return tuple(moves)


def match_typed_sequence(text, actions):
    # Match typed text with a legal move.
    pattern = parse_sequence_pattern(text)
    matches = []
    for action in actions:
        pattern_parts = []
        for move in action:
            pattern_parts.append(move.pattern_key())
        action_pattern = tuple(pattern_parts)

        if action_pattern == pattern:
            matches.append(action)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print("That notation is ambiguous for this roll. Please choose the move number instead.")
        return None
    print("That move is not legal for this roll. Type 'legal' to see legal moves.")
    return None


def human_choose_action(state, roll, ai_for_hint):
    # Get legal moves for the player.
    actions = legal_sequences(state, HUMAN, roll)
    if not actions or (len(actions) == 1 and not actions[0]):
        print("You have no legal moves.")
        return tuple()

    # Show moves so the player can pick a number.
    print("Legal moves:")
    show_legal_actions(actions, limit=40)
    print("Type a move number, a move like '13/8 6/5', 'hint', 'board', 'legal', or 'quit'.")

    while True:
        # Ask until the player gives a valid move.
        choice = input("Your move> ").strip()
        if not choice:
            continue
        low = choice.lower()
        if low in {"q", "quit", "exit"}:
            print("Game ended by player.")
            sys.exit(0)
        if low in {"b", "board"}:
            # Show board again.
            display_board(state)
            continue
        if low in {"l", "legal", "moves"}:
            # Show all moves.
            show_legal_actions(actions, limit=None)
            continue
        if low in {"h", "hint"}:
            # Ask the AI for a hint.
            hint = ai_for_hint.choose_move(state, HUMAN, roll)
            print(f"Hint: {sequence_to_str(hint)}")
            continue
        if choice.isdigit():
            # Pick a move by number.
            idx = int(choice) - 1
            if 0 <= idx < len(actions):
                return actions[idx]
            print(f"Enter a number from 1 to {len(actions)}.")
            continue
        try:
            matched = match_typed_sequence(choice, actions)
            if matched is not None:
                return matched
        except ValueError as exc:
            print(f"Could not parse move: {exc}")
