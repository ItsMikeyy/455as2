# CMPUT 455 Assignment 2 starter code
# Implement the specified commands to complete the assignment
# Full assignment specification here: https://webdocs.cs.ualberta.ca/~mmueller/courses/cmput455/assignments/a2.html

import sys
import random
import time

class TranspositionTable:
    def __init__(self):
        self.table = {}
    
    def store(self, hash_value, value):
        self.table[hash_value] = value
    
    def lookup(self, hash_value):
        return self.table.get(hash_value, None)

class ZobristHash:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        # Initialize random numbers for each cell and piece
        self.zobrist_table = [[[random.getrandbits(64) for _ in range(2)] for _ in range(cols)] for _ in range(rows)]
        self.current_hash = 0

    def compute_hash(self, board):
        h = 0
        for row in range(self.rows):
            for col in range(self.cols):
                piece = board[row][col]
                if piece is not None:
                    h ^= self.zobrist_table[row][col][piece]
        self.current_hash = h
        return h

    def update_hash(self, row, col, old_piece, new_piece):
        if old_piece is not None:
            self.current_hash ^= self.zobrist_table[row][col][old_piece]
        if new_piece is not None:
            self.current_hash ^= self.zobrist_table[row][col][new_piece]
        return self.current_hash

class CommandInterface:

    def __init__(self):
        # Define the string to function command mapping
        self.command_dict = {
            "help" : self.help,
            "game" : self.game,
            "show" : self.show,
            "play" : self.play,
            "legal" : self.legal,
            "genmove" : self.genmove,
            "winner" : self.winner,
            "timelimit" : self.timelimit,
            "solve" : self.solve
        }
        self.board = [[None]]
        self.player = 1
        self.time_limit = 10
    
    #===============================================================================================
    # VVVVVVVVVV START of PREDEFINED FUNCTIONS. DO NOT MODIFY. VVVVVVVVVV
    #===============================================================================================

    # Convert a raw string to a command and a list of arguments
    def process_command(self, str):
        str = str.lower().strip()
        command = str.split(" ")[0]
        args = [x for x in str.split(" ")[1:] if len(x) > 0]
        if command not in self.command_dict:
            print("? Uknown command.\nType 'help' to list known commands.", file=sys.stderr)
            print("= -1\n")
            return False
        try:
            return self.command_dict[command](args)
        except Exception as e:
            print("Command '" + str + "' failed with exception:", file=sys.stderr)
            print(e, file=sys.stderr)
            print("= -1\n")
            return False
        
    # Will continuously receive and execute commands
    # Commands should return True on success, and False on failure
    # Every command will print '= 1' or '= -1' at the end of execution to indicate success or failure respectively
    def main_loop(self):
        while True:
            str = input()
            if str.split(" ")[0] == "exit":
                print("= 1\n")
                return True
            if self.process_command(str):
                print("= 1\n")

    # Will make sure there are enough arguments, and that they are valid numbers
    # Not necessary for commands without arguments
    def arg_check(self, args, template):
        converted_args = []
        if len(args) < len(template.split(" ")):
            print("Not enough arguments.\nExpected arguments:", template, file=sys.stderr)
            print("Recieved arguments: ", end="", file=sys.stderr)
            for a in args:
                print(a, end=" ", file=sys.stderr)
            print(file=sys.stderr)
            return False
        for i, arg in enumerate(args):
            try:
                converted_args.append(int(arg))
            except ValueError:
                print("Argument '" + arg + "' cannot be interpreted as a number.\nExpected arguments:", template, file=sys.stderr)
                return False
        args = converted_args
        return True

    # List available commands
    def help(self, args):
        for command in self.command_dict:
            if command != "help":
                print(command)
        print("exit")
        return True

    #===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ END OF PREDEFINED FUNCTIONS. ɅɅɅɅɅɅɅɅɅɅ
    #===============================================================================================

    #===============================================================================================
    # VVVVVVVVVV START OF ASSIGNMENT 2 FUNCTIONS. ADD/REMOVE/MODIFY AS NEEDED. VVVVVVVV
    #===============================================================================================

    def game(self, args):
        if not self.arg_check(args, "n m"):
            return False
        n, m = [int(arg) for arg in args]
        if n < 0 or m < 0:
            print("Invalid board size:", n, m, file=sys.stderr)
            return False

        self.board = [[None] * n for _ in range(m)]
        self.player = 1
        # Initialize Zobrist hashing
        self.zobrist_hash = ZobristHash(m, n)
        self.current_hash = self.zobrist_hash.compute_hash(self.board)
        return True

    def show(self, args):
        for row in self.board:
            for x in row:
                if x is None:
                    print(".", end="")
                else:
                    print(x, end="")
            print()
        return True

    def is_legal_reason(self, x, y, num):
        if self.board[y][x] is not None:
            return False, "occupied"

        # Check row
        row = self.board[y][:]
        row[x] = num
        if not self.is_valid_line(row):
            return False, "invalid row"

        # Check column
        column = [self.board[i][x] for i in range(len(self.board))]
        column[y] = num
        if not self.is_valid_line(column):
            return False, "invalid column"

        return True, ""

    def is_valid_line(self, line):
        count_zero = count_one = 0
        consecutive = 1
        for i in range(len(line)):
            if line[i] is not None:
                if i > 0 and line[i] == line[i - 1]:
                    consecutive += 1
                    if consecutive >= 3:
                        return False
                else:
                    consecutive = 1
                if line[i] == 0:
                    count_zero += 1
                else:
                    count_one += 1
            else:
                consecutive = 1
        if count_zero > len(line) // 2 or count_one > len(line) // 2:
            return False
        return True

    def is_legal(self, x, y, num):
        legal, _ = self.is_legal_reason(x, y, num)
        return legal

    def valid_move(self, x, y, num):
        return (0 <= x < len(self.board[0]) and
                0 <= y < len(self.board) and
                num in (0, 1) and
                self.is_legal(x, y, num))

    def play(self, args):
        if not self.arg_check(args, "x y number"):
            return False
        x, y, num = [int(arg) for arg in args]
        if not self.valid_move(x, y, num):
            print(f"= illegal move: {x} {y} {num}", file=sys.stderr)
            return False

        old_piece = self.board[y][x]
        self.board[y][x] = num
        self.zobrist_hash.update_hash(y, x, old_piece, num)
        self.current_hash = self.zobrist_hash.current_hash
        self.player = 3 - self.player  # Switch player
        return True

    def legal(self, args):
        if not self.arg_check(args, "x y number"):
            return False
        x, y, num = args
        print("yes" if self.valid_move(x, y, num) else "no", flush=True)
        return True

    def get_legal_moves(self):
        moves = []
        for y in range(len(self.board)):
            for x in range(len(self.board[0])):
                for num in (0, 1):
                    if self.is_legal(x, y, num):
                        moves.append([x, y, num])
        return moves

    def genmove(self, args):
        moves = self.get_legal_moves()
        if not moves:
            print("resign", flush=True)
        else:
            move = random.choice(moves)
            self.play([str(move[0]), str(move[1]), str(move[2])])
            print(f"{move[0]} {move[1]} {move[2]}", flush=True)
        return True

    def winner(self, args):
        if not self.get_legal_moves():
            print(self.player, flush=True)
        else:
            print("unfinished", flush=True)
        return True

    def timelimit(self, args):
        if not self.arg_check(args, "time"):
            return False
        self.time_limit = args[0]
        return True

    def solve(self, args):
        start_time = time.time()
        time_limit = min(self.time_limit, 0.9)  # Slightly less than 1 second to prevent timeout
        self.transposition_table = TranspositionTable()
        try:
            can_win = self.minimax(self.player, start_time, time_limit)
            print(self.player if can_win else 3 - self.player)
            sys.stdout.flush()
        except TimeoutError:
            print("unknown")
            sys.stdout.flush()
        return True

    def minimax(self, player, start_time, time_limit):
        if time.time() - start_time >= time_limit:
            raise TimeoutError

        # Use Zobrist hash value and player as state
        state = (self.current_hash, player)
        lookup = self.transposition_table.lookup(state)
        if lookup is not None:
            return lookup

        moves = self.get_legal_moves()
        if not moves:
            self.transposition_table.store(state, False)
            return False  # Current player loses

        for move in moves:
            x, y, num = move
            old_piece = self.board[y][x]
            # Make move and update hash
            self.board[y][x] = num
            self.zobrist_hash.update_hash(y, x, old_piece, num)
            self.current_hash = self.zobrist_hash.current_hash
            # Recurse
            win = not self.minimax(3 - player, start_time, time_limit)
            # Undo move and hash
            self.board[y][x] = old_piece
            self.zobrist_hash.update_hash(y, x, num, old_piece)
            self.current_hash = self.zobrist_hash.current_hash
            if time.time() - start_time >= time_limit:
                raise TimeoutError
            if win:
                self.transposition_table.store(state, True)
                return True
        self.transposition_table.store(state, False)
        return False

    #===============================================================================================
    # ɅɅɅɅɅɅɅɅɅɅ END OF ASSIGNMENT 2 FUNCTIONS. ɅɅɅɅɅɅɅɅɅɅ
    #===============================================================================================
    
if __name__ == "__main__":
    interface = CommandInterface()
    interface.main_loop()