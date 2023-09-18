import curses
import random
import math
import os

class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.clear()
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)

        self.level_number = 1
        self.load_level()

        self.score = 0
        self.game_over = False

        self.player_x, self.player_y = self.find_player_position()
        self.ghosts = self.generate_ghosts()
        self.player_moved = False

        # Função lambda para verificar colisão
        collision_check = lambda gx, gy, player_x, player_y: gx == player_x and gy == player_y
        self.check_collision = lambda: any(collision_check(gx, gy, self.player_x, self.player_y) for gx, gy in self.ghosts)

        # Função de continuação como uma corotina
        self.game_coroutine = self.game_loop()

    def load_level(self):
        with open(f'level{self.level_number}.txt', 'r') as file:
            self.level_data = [list(line.strip()) for line in file.readlines()]

    def find_player_position(self):
        for y, row in enumerate(self.level_data):
            for x, char in enumerate(row):
                if char == 'P':
                    return x, y

    def generate_ghosts(self):
        with open('quant.txt', 'r') as file:
            self.ghosts_count = int(file.readline().strip())

        # List comprehension para gerar as coordenadas das posições vazias no nível
        free_spaces = [(x, y) for y, row in enumerate(self.level_data) for x, char in enumerate(row) if char == '.']

        # Closure para calcular a distância entre o jogador e um fantasma
        def distance_to_player(fx, fy):
            px, py = self.player_x, self.player_y
            return math.sqrt((fx - px) ** 2 + (fy - py) ** 2)

        free_spaces.sort(key=lambda coord: distance_to_player(coord[0], coord[1]))

        ghosts = free_spaces[-self.ghosts_count:]

        # Função de alta ordem para aplicar uma função de transformação às coordenadas dos fantasmas
        def apply_to_coordinates(function, coordinates):
            return [function(coord) for coord in coordinates]

        distances_to_player = apply_to_coordinates(lambda coord: distance_to_player(coord[0], coord[1]), ghosts)

        return ghosts

    def move_player(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        if self.is_valid_move(new_x, new_y):
            if self.level_data[new_y][new_x] == '.':
                self.score += 10
            elif self.level_data[new_y][new_x] == '*':
                self.score += 50

            self.level_data[self.player_y][self.player_x] = ' '
            self.player_x, self.player_y = new_x, new_y

            if self.level_data[new_y][new_x] == '.':
                self.level_data[new_y][new_x] = 'P'
            else:
                self.level_data[new_y][new_x] = ' '

            self.player_moved = True

    def is_valid_move(self, x, y):
        if 0 <= x < len(self.level_data[0]) and 0 <= y < len(self.level_data):
            return self.level_data[y][x] != '#'
        return False

    def move_ghosts(self):
        if self.player_moved:
            for i, (gx, gy) in enumerate(self.ghosts):
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                new_x, new_y = gx + dx, gy + dy

                if self.is_valid_move(new_x, new_y):
                    self.ghosts[i] = (new_x, new_y)

            self.player_moved = False

    def check_win(self):
        if all('.' not in row for row in self.level_data):
            self.level_number += 1
            level_file = f'level{self.level_number}.txt'
            if os.path.exists(level_file) and self.level_number <= 3:
                self.load_level()
                self.ghosts = self.generate_ghosts()
                self.restart_game()
            else:
                self.game_over = True

    def game_loop(self):
        while not self.game_over:
            self.stdscr.clear()

            self.move_ghosts()
            if self.check_collision():
                self.restart_game()
                yield # Função de continuação pausa aqui quando ocorre uma colisão

            self.check_win()

            self.stdscr.addch(self.player_y, self.player_x, ' ')

            for y, row in enumerate(self.level_data):
                for x, char in enumerate(row):
                    self.stdscr.addch(y, x, char)

            self.stdscr.addch(self.player_y, self.player_x, 'P')

            for gx, gy in self.ghosts:
                self.stdscr.addch(gy, gx, 'G')

            level_info = f'Level: {self.level_number}'
            score_info = f'Score: {self.score}'
            self.stdscr.addstr(len(self.level_data), 0, level_info)
            self.stdscr.addstr(len(self.level_data), len(level_info) + 1, score_info)
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key == ord('q'):
                break
            elif key == curses.KEY_RIGHT:
                self.move_player(1, 0)
            elif key == curses.KEY_LEFT:
                self.move_player(-1, 0)
            elif key == curses.KEY_DOWN:
                self.move_player(0, 1)
            elif key == curses.KEY_UP:
                self.move_player(0, -1)

            yield # Função de continuação pausa aqui no final de cada iteração do loop

    def restart_game(self):
        self.score = 0
        self.game_over = False
        self.load_level()
        self.player_x, self.player_y = self.find_player_position()
        self.ghosts = self.generate_ghosts()
        self.player_moved = False

def main(stdscr):
    game = Game(stdscr)
    for _ in game.game_coroutine:
        pass  # Continua a execução da função de continuação

if __name__ == "__main__":
    curses.wrapper(main)
