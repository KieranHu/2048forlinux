import curses
from random import randrange, choice
from collections import defaultdict

letterCode = [ord(ch) for ch in 'WASDRQwasdrq']
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
actionsLst = dict(zip(letterCode, actions * 2))


def getUserAction(keyboard):
    char = 'N'
    while char not in actionsLst:
        char = keyboard.getch()

    return actionsLst[char]


def transpose(field):
    return [list(row) for row in zip(*field)]


def invert(field):
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win = win
        self.score = 0
        self.highScore = 0
        self.reset()

    def reset(self):
        if self.score > self.highScore:
            self.highScore = self.score
        self.score = 0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        self.spawn()
        self.spawn()

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):  # tighten items
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]

                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])

                assert len(new_row) == len(row)
                return new_row

            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.moveIsPossible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True

            else:
                return False

    def isWin(self):
        return any(any(i >= self.win for i in row) for row in self.field)

    def isGameover(self):
        return not any(self.moveIsPossible(move) for move in actions)

    def moveIsPossible(self, direction):
        def rowIsLeftMoavable(row):
            def change(i):
                if row[i] == 0 and row[i + 1] != 0:
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:
                    return True
                return False
            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left'] = lambda field: any(rowIsLeftMoavable(row) for row in field)
        check['Right'] = lambda field: check['Left'](invert(field))
        check['Up'] = lambda field: check['Left'](transpose(field))
        check['Down'] = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)

        else:
            return False

    def spawn(self):  # Generate new numbers
        new_element = 4 if randrange(100) > 89 else 2
        lst = []
        # for i in range(self.width):
        #     for j in range(self.height):
        #         if self.field[i, j] == 0:
        #             lst.append([i,j])
        #lst.append([i, j] for i in range(self.width) for j in range(self.height) if self.field[i, j] == 0)
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][i] = new_element

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'

        def cast(string):
            screen.addstr(string + '\n')

        def draw_hor_separator():
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()

        cast('SCORE: ' + str(self.score))
        if 0 != self.highScore:
            cast('HGHSCORE: ' + str(self.highScore))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.isWin():
            cast(win_string)
        else:
            if self.isGameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


def main(stdcsr):
    def init():
        gamefield.reset()
        return 'Game'

    def notGame(state):
        gamefield.draw(stdcsr)
        action = getUserAction(stdcsr)
        responses = defaultdict(lambda: state)
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]

    def game():
        gamefield.draw(stdcsr)
        action = getUserAction(stdcsr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if gamefield.move(action):
            if gamefield.isWin():
                return 'Win'
            if gamefield.isGameover():
                return 'Gameover'
        return 'Game'

    stateActions = {
        'Init': init,
        'Win' : lambda: notGame('Win'),
        'Gameover' : lambda: notGame('Gameover'),
        'Game' : game
    }

    curses.use_default_colors()
    gamefield = GameField(win=32)

    state = 'Init'
    while state != 'Exit':
        state = stateActions[state]()

curses.wrapper(main)
