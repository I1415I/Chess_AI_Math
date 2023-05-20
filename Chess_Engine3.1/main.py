import chess
import chess.polyglot
import chess.pgn
import chess.engine
from chess import Move, Board
import tables
from functools import lru_cache
from typing import List

board = chess.Board()

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

piece_square_tables = {
    chess.PAWN: tables.pawntable,
    chess.KNIGHT: tables.knightstable,
    chess.BISHOP: tables.bishopstable,
    chess.ROOK: tables.rookstable,
    chess.QUEEN: tables.queenstable,
    chess.KING: tables.kingstable
}

# Constants for evaluation function
MATERIAL_WEIGHT = 0.6  # weight given to material value
POSITION_WEIGHT = 0.4  # weight given to piece position
PAWN_ISLAND_PENALTY = -10  # penalty for pawn islands
DOUBLED_PAWN_PENALTY = -20  # penalty for doubled pawns
BACKWARDS_PAWN_PENALTY = -8  # penalty for backwards pawns
ROOK_ON_OPEN_FILE_BONUS = 10  # bonus for rooks on open files
ROOK_ON_SEMI_OPEN_FILE_BONUS = 5  # bonus for rooks on semi-open files
BISHOP_PAIR_BONUS = 20  # bonus for having both bishops
KNIGHT_OUTPOST_BONUS = 15  # bonus for knights on outposts
KING_SAFETY_PENALTY = -20  # penalty for king safety


@lru_cache(maxsize=None)
def memoized_pieces(piece_type, color):
    return board.pieces(piece_type, color)


def evaluate_board():
    if board.is_checkmate():
        if board.turn:
            return -9999
        else:
            return 9999
    elif board.is_stalemate():
        return 0
    elif board.is_insufficient_material():
        return 0
    elif board.can_claim_threefold_repetition():
        return 0

        # Compute material value of each side
    white_material = sum(
        [len(memoized_pieces(piece_type, chess.WHITE)) * piece_values[piece_type] for piece_type in
         piece_values.keys()])
    black_material = sum(
        [len(memoized_pieces(piece_type, chess.BLACK)) * piece_values[piece_type] for piece_type in
         piece_values.keys()])

    # Compute positional value of each side
    white_position = sum([piece_square_tables[piece_type][square] for piece_type in piece_values.keys() for square in
                          memoized_pieces(piece_type, chess.WHITE)])
    black_position = sum(
        [piece_square_tables[piece_type][chess.square_mirror(square)] for piece_type in piece_values.keys() for square
         in memoized_pieces(piece_type, chess.BLACK)])

    # Combine values with weights and return evaluation
    white_value = MATERIAL_WEIGHT * white_material + POSITION_WEIGHT * white_position
    black_value = MATERIAL_WEIGHT * black_material + POSITION_WEIGHT * black_position

    wp = len(memoized_pieces(chess.PAWN, chess.WHITE))
    bp = len(memoized_pieces(chess.PAWN, chess.BLACK))
    wn = len(memoized_pieces(chess.KNIGHT, chess.WHITE))
    bn = len(memoized_pieces(chess.KNIGHT, chess.BLACK))
    wb = len(memoized_pieces(chess.BISHOP, chess.WHITE))
    bb = len(memoized_pieces(chess.BISHOP, chess.BLACK))
    wr = len(memoized_pieces(chess.ROOK, chess.WHITE))
    br = len(memoized_pieces(chess.ROOK, chess.BLACK))
    wq = len(memoized_pieces(chess.QUEEN, chess.WHITE))
    bq = len(memoized_pieces(chess.QUEEN, chess.BLACK))

    material = white_value - black_value

    pawnsq = sum([tables.pawntable[i] for i in memoized_pieces(chess.PAWN, chess.WHITE)])
    pawnsq = pawnsq + sum([-tables.pawntable[chess.square_mirror(i)] for i in memoized_pieces(chess.PAWN, chess.BLACK)])
    knightsq = sum([tables.knightstable[i] for i in memoized_pieces(chess.KNIGHT, chess.WHITE)])
    knightsq = knightsq + sum(
        [-tables.knightstable[chess.square_mirror(i)] for i in memoized_pieces(chess.KNIGHT, chess.BLACK)])
    bishopsq = sum([tables.bishopstable[i] for i in memoized_pieces(chess.BISHOP, chess.WHITE)])
    bishopsq = bishopsq + sum(
        [-tables.bishopstable[chess.square_mirror(i)] for i in memoized_pieces(chess.BISHOP, chess.BLACK)])
    rooksq = sum([tables.rookstable[i] for i in memoized_pieces(chess.ROOK, chess.WHITE)])
    rooksq = rooksq + sum(
        [-tables.rookstable[chess.square_mirror(i)] for i in memoized_pieces(chess.ROOK, chess.BLACK)])
    queensq = sum([tables.queenstable[i] for i in memoized_pieces(chess.QUEEN, chess.WHITE)])
    queensq = queensq + sum(
        [-tables.queenstable[chess.square_mirror(i)] for i in memoized_pieces(chess.QUEEN, chess.BLACK)])
    kingsq = sum([tables.kingstable[i] for i in memoized_pieces(chess.KING, chess.WHITE)])
    kingsq = kingsq + sum(
        [-tables.kingstable[chess.square_mirror(i)] for i in memoized_pieces(chess.KING, chess.BLACK)])

    eval = material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq
    if board.turn:
        return eval
    else:
        return -eval


# Searching the best move using minimax and alphabeta algorithm with negamax
def alphabeta(alpha, beta, depth_left):
    best_score = -9999
    if depth_left == 0:
        return quiesce(alpha, beta)
    for move in board.legal_moves:
        board.push(move)
        score = -alphabeta(-beta, -alpha, depth_left - 1)
        board.pop()
        if score > beta:
            return score
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
    return best_score


def quiesce(alpha, beta):
    stand_pat = evaluate_board()
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in board.legal_moves:
        if board.is_capture(move):
            board.push(move)
            score = -quiesce(-beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
    return alpha


def select_move(depth):
    try:
        move = chess.polyglot.MemoryMappedReader("C:\PythonScripts\Chess_Engine3.1\Bin\human.bin").weighted_choice(
            board).move
        move = chess.polyglot.MemoryMappedReader("C:\PythonScripts\Chess_Engine3.1\Bin\computer.bin").weighted_choice(
            board).move
        move = chess.polyglot.MemoryMappedReader("C:\PythonScripts\Chess_Engine3.1\Bin\pecg_book.bin").weighted_choice(
            board).move
        return move
    except:
        best_move = chess.Move.null()
        best_value = -99999
        alpha = -100000
        beta = 100000
        for move in board.legal_moves:
            board.push(move)
            board_value = -alphabeta(-beta, -alpha, depth - 1)
            if board_value > best_value:
                best_value = board_value
                best_move = move
            if board_value > alpha:
                alpha = board_value
            board.pop()
        return best_move


rounds = 1
while rounds <= 100:
    count = 0
    movehistory = []
    game = chess.pgn.Game()
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci("C:\PythonScripts\Chess_Engine3.1\Engines\stockfish.exe")
    while not board.is_game_over(claim_draw=True):
        if board.turn:
            count += 1
            print(f'\n{count}]\n')
            move = engine.play(board, chess.engine.Limit(time=0.1))
            movehistory.append(move.move)
            board.push(move.move)
            print(board)
            print()
        else:
            move = select_move(3)
            movehistory.append(move)
            board.push(move)
            print(board)
            print()
    game.add_line(movehistory)
    file = open("games.txt", "a")
    file.write(f"{movehistory}\n")
    file.close()
    print(game)
    rounds += 1

