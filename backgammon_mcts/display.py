# display.py.

from backgammon_mcts.constants import COMPUTER, HUMAN, PLAYER_SYMBOL
from backgammon_mcts.rules import pip_count, sequence_to_str

CELL_W = 5
MIN_STACK_ROWS = 5
MAX_STACK_ROWS = 8


def format_points_for_player(state, player):
    # Make the game info line.
    pieces = []
    if player == HUMAN:
        point_iter = range(24, 0, -1)
    else:
        point_iter = range(1, 25)
    for point in point_iter:
        idx = point - 1
        count = state.board[idx] * player
        if count > 0:
            symbol = PLAYER_SYMBOL[player]
            pieces.append(f"{point}:{count}{symbol}")
    if pieces:
        return " ".join(pieces)
    return "none"


def make_cell(text=""):
    # Make one box.
    return f"|{str(text):^{CELL_W}}"


def make_row(cells):
    # Make one board row.
    row = ""
    for cell in cells:
        row += make_cell(cell)
    row += "|"
    return row


def make_separator(cell_count):
    # Make a line like +---+---+.
    line = "+"
    for i in range(cell_count):
        line += "-" * CELL_W
        line += "+"
    return line


def get_symbol_and_count(state, point):
    # Get X or O for one point.
    val = state.board[point - 1]
    if val > 0:
        return PLAYER_SYMBOL[HUMAN], val
    if val < 0:
        return PLAYER_SYMBOL[COMPUTER], -val
    return "", 0


def get_stack_token(state, point, row, rows, top_half):
    # Get what to print in one board box.
    symbol, count = get_symbol_and_count(state, point)
    if count == 0:
        return ""

    display_count = min(count, rows)
    if top_half:
        if row >= display_count:
            return ""
        if count > rows and row == rows - 1:
            return f"{symbol}{count}"
        return symbol

    # Bottom half prints from the bottom.
    if row < rows - display_count:
        return ""
    if count > rows and row == 0:
        return f"{symbol}{count}"
    return symbol


def make_visual_rows_for_points(state, points, rows, top_half):
    # Make all rows for half of the board.
    rendered = []
    for row in range(rows):
        cells = []
        for item in points:
            if item == 0:  # 0 means BAR.
                if row == rows // 2:
                    cells.append("BAR")
                else:
                    cells.append("")
            else:
                cells.append(get_stack_token(state, item, row, rows, top_half=top_half))
        rendered.append(make_row(cells))
    return rendered


def display_visual_board(state):
    # Print the X/O board.
    # 0 means the BAR column.
    top_points = [13, 14, 15, 16, 17, 18, 0, 19, 20, 21, 22, 23, 24]
    bottom_points = [12, 11, 10, 9, 8, 7, 0, 6, 5, 4, 3, 2, 1]
    # Decide how many rows to print.
    max_stack = 0
    for val in state.board:
        count = abs(val)
        if count > max_stack:
            max_stack = count
    rows = max(MIN_STACK_ROWS, min(MAX_STACK_ROWS, max_stack))
    width_cells = len(top_points)
    sep = make_separator(width_cells)

    print("Visual board   X = Human/you, O = Computer")
    print("Human/X path: 24 -> 1. Computer/O path: 1 -> 24.")
    print(sep)
    top_labels = []
    for point in top_points:
        if point == 0:
            top_labels.append("BAR")
        else:
            top_labels.append(point)
    print(make_row(top_labels))
    print(sep)
    for line in make_visual_rows_for_points(state, top_points, rows, top_half=True):
        print(line)
    center_note = (
        f"BAR X:{state.bar[HUMAN]} O:{state.bar[COMPUTER]}"
        f"    OFF X:{state.off[HUMAN]} O:{state.off[COMPUTER]}"
    )
    print(center_note.center(len(sep)))
    for line in make_visual_rows_for_points(state, bottom_points, rows, top_half=False):
        print(line)
    print(sep)
    bottom_labels = []
    for point in bottom_points:
        if point == 0:
            bottom_labels.append("BAR")
        else:
            bottom_labels.append(point)
    print(make_row(bottom_labels))
    print(sep)


def display_board(state):
    # Print the full board screen.
    print("\n" + "=" * 92)
    print("Board")
    print("-" * 92)
    display_visual_board(state)
    print("Game info")
    print("-" * 92)
    print(f"Human/X    moves 24 -> 1 : {format_points_for_player(state, HUMAN)}")
    print(f"Computer/O moves 1 -> 24 : {format_points_for_player(state, COMPUTER)}")
    print(
        f"Bar  Human/X:{state.bar[HUMAN]}  Computer/O:{state.bar[COMPUTER]}    "
        f"Off  Human/X:{state.off[HUMAN]}  Computer/O:{state.off[COMPUTER]}"
    )
    print(f"Pips Human/X:{pip_count(state, HUMAN)}  Computer/O:{pip_count(state, COMPUTER)}")
    print("=" * 92)


def show_legal_actions(actions, limit=40):
    # Print legal moves.
    if not actions or (len(actions) == 1 and not actions[0]):
        print("No legal moves.")
        return

    if limit is None:
        to_show = actions
    else:
        to_show = actions[:limit]
    for i, action in enumerate(to_show, start=1):
        print(f"{i:>3}. {sequence_to_str(action)}")
    if limit is not None and len(actions) > limit:
        print(f"... {len(actions) - limit} more. Type 'legal' to show all moves.")
