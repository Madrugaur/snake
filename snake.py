import math
from pynput import keyboard
import cursor
import os
import colorama
import time
import random
import itertools
import cfonts
from display import Display, Frame

UPDATE_CADENCE: int = 4

colors = [
    colorama.Fore.GREEN,
    colorama.Fore.BLUE,
    colorama.Fore.RED,
    colorama.Fore.YELLOW,
    colorama.Fore.CYAN,
    colorama.Fore.MAGENTA,
    colorama.Fore.WHITE,
]


class Direction:
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class Cell:
    SNAKE = "█"
    EMPTY = " "
    SHADE = "▒"
    APPLE = colorama.Fore.RED + "⬤" + colorama.Fore.RESET


class SplashState:
    DISPLAY = 0
    PLAY = 1
    QUIT = 2


class HitSelfException(Exception):
    def __init__(self) -> None:
        self.reason: str = "Your snake hit itself"


class HitWallException(Exception):
    def __init__(self) -> None:
        self.reason: str = "Your snake hit the wall"


class MinSizeException(Exception):
    def __init__(self) -> None:
        columns, rows = os.get_terminal_size()
        super().__init__(
            f"Minumum size required ({MIN_COLUMNS} columns x {MIN_ROWS} rows), current size ({columns} columns x {rows} rows)"
        )


class SnakeSection:
    def __init__(self, row: int, column: int, symbol: str):
        self.row = row
        self.column = column
        self._symbol = symbol

    def __eq__(self, other):
        if isinstance(other, SnakeSection):
            return self.cell() == other.cell()
        return False

    def __hash__(self) -> int:
        return hash(self.cell())

    def cell(self) -> tuple[int, int]:
        return (self.row, self.column)

    def symbol(self) -> str:
        return self._symbol

    def set_symbol(self, symbol: str) -> None:
        self._symbol = symbol


class Game:
    def __init__(self, columns, rows):
        self.__columns = columns
        self.__rows = rows
        self.__board: list[list[str]] = [
            [" " for _ in range(columns)] for _ in range(rows)
        ]
        self.__snake: list[SnakeSection] = []
        self.__update_cycle = 0
        self.__update_cadence = UPDATE_CADENCE
        self.__direction: Direction = Direction.UP
        self.__queued_direction: Direction = Direction.UP
        self.__open_cells: set[tuple[int, int]] = set(
            itertools.product(range(self.__rows), range(self.__columns))
        )
        self.__running: bool = True
        self.__reason: str | None = None
        
        self.__color_iter = self.__get_color()

        self.__grow_snake()
        self.__spawn_apple()

    def snake(self):
        return self.__snake

    def cells(self):
        return self.__open_cells

    def snake_cells(self):
        return [section.cell() for section in self.snake()]

    def __grow_snake(self):
        if len(self.snake()) == 0:
            self.snake().append(
                SnakeSection(self.__rows // 2, self.__columns // 2, Cell.SNAKE)
            )
        else:
            self.snake().append(self.snake()[-1])

    def __spawn_apple(self):
        cell = random.choice(list(self.cells()))
        self.cells().remove(cell)
        row, col = cell
        self.__board[row][col] = Cell.APPLE

    def __apply_cell_to_snake(self, cell_func) -> None:
        for i, section in enumerate(self.snake()):
            row, col = section.cell()
            self.__board[row][col] = cell_func(i, section)

    def __move_snake(self, new_section: tuple):
        if new_section in self.snake_cells():
            raise HitSelfException()

        row, col = new_section

        if row < 0 or row >= self.__rows or col < 0 or col >= self.__columns:
            raise HitWallException()

        if self.__board[row][col] == Cell.APPLE:
            self.__board[row][col] = Cell.EMPTY
            self.__spawn_apple()
            if self.__update_cadence > 1:
                self.__update_cadence -= 1 / 10
        else:
            self.snake().pop()

        self.snake().insert(0, SnakeSection(row, col, Cell.SNAKE))

    def __get_color(self) -> colorama.Fore:
        for color in itertools.cycle(colors):
            yield color

    def __update_snake(self):
        self.__direction = self.__queued_direction
        self.__apply_cell_to_snake(lambda *_: Cell.EMPTY)
        row, col = self.snake()[0].cell()
        match (self.__direction):
            case Direction.UP:
                self.__move_snake((row - 1, col))
            case Direction.RIGHT:
                self.__move_snake((row, col + 1))
            case Direction.DOWN:
                self.__move_snake((row + 1, col))
            case Direction.LEFT:
                self.__move_snake((row, col - 1))

        self.__apply_cell_to_snake(
            lambda i, x: f"{next(self.__color_iter)}{x.symbol()}{colorama.Fore.RESET}"
        )

    def update_game_state(self):
        self.__update_cycle += 1
        if self.__update_cycle % int(self.__update_cadence) == 0:
            self.__update_snake()

    def render(self):
        frame: Frame = display.new_frame(f"cycle")
        frame.home()
        stats = f" Score: {len(self.snake()) - 1} Level: {int(math.floor((len(self.snake()) - 1) / 10))} "

        frame.draw("┏", f"{stats:{'━'}<{self.__columns}}", "┓", sep="")
        for row in self.__board:
            frame.draw("┃", "".join(row), "┃", sep="")
        frame.draw("┗", "━" * self.__columns, "┛", sep="")
        display.render()

    def __get_direction(self):
        return self.__direction

    def __set_next_direction(self, direction: Direction):
        self.__queued_direction = direction

    def on_press(self, key: keyboard.Key):
        if key == keyboard.Key.esc:
            self.stop()
            return False
        elif not isinstance(key, keyboard.Key):
            match (key.char):
                case "w":
                    if self.__get_direction() != Direction.DOWN:
                        self.__set_next_direction(Direction.UP)
                case "d":
                    if self.__get_direction() != Direction.LEFT:
                        self.__set_next_direction(Direction.RIGHT)

                case "s":
                    if self.__get_direction() != Direction.UP:
                        self.__set_next_direction(Direction.DOWN)
                case "a":
                    if self.__get_direction() != Direction.RIGHT:
                        self.__set_next_direction(Direction.LEFT)
                case _:
                    pass

    def stop(self):
        self.__running = False

    def running(self) -> bool:
        return self.__running

    def set_reason(self, reason: str) -> None:
        self.__reason = reason

    def reason(self) -> str:
        return self.__reason

    def rows(self) -> int:
        return self.__rows

    def columns(self) -> int:
        return self.__columns


display: Display = Display()

MIN_COLUMNS = 62
MIN_ROWS = 10

SLEEP_TIME = 1 / 60


def game_over(game: Game):
    mid_point = game.rows() // 2

    print(f"\033[{mid_point};{game.columns() // 2 - 3}H", end="")
    print("Game Over", end="")
    if game.reason():
        mid_point += 1
        print(
            f"\033[{mid_point};{game.columns() // 2 - ((len(game.reason()) + 2) // 2) + 1}H",
            end="",
        )
        print(f"({game.reason()})", end="")

    print(
        f"\033[{mid_point + 1};{game.columns() // 2 - ((len('(press enter to start / esc to quit)') + 2) // 2) + 1}H",
        end="",
    )
    print("(press enter to start / esc to quit)")
    print(f"\r\033[999B", end="")


def run(game: Game) -> str | None:
    with keyboard.Listener(on_press=game.on_press, suppress=True) as listner:
        while game.running():
            try:
                game.update_game_state()
                game.render()
                time.sleep(SLEEP_TIME)
            except (HitSelfException, HitWallException) as e:
                game.stop()
                listner.stop()
                game.set_reason(e.reason)

        listner.join()
    return game


def raise_for_min_size():
    columns, rows = os.get_terminal_size()
    if columns < MIN_COLUMNS or rows < MIN_ROWS:
        raise MinSizeException()


def ask_to_play_or_quit(render_func):
    raise_for_min_size()
    main_splash_state = SplashState.DISPLAY

    def on_press(key):
        nonlocal main_splash_state
        if key == keyboard.Key.esc:
            main_splash_state = SplashState.QUIT
            return False
        elif key == keyboard.Key.enter:
            main_splash_state = SplashState.PLAY
            return False

    with keyboard.Listener(on_press=on_press, suppress=True) as listner:
        while main_splash_state == SplashState.DISPLAY:
            render_func()

        listner.join()

    return main_splash_state


def main_menu():
    try:
        raise_for_min_size()
        splash_frame: Frame = display.new_frame("splash")
        splash_frame.draw(
            cfonts.render(
                f"Snake",
                colors=["white"],
                align="center",
                size=os.get_terminal_size(),
                background="black",
            )
        )

        columns, rows = os.get_terminal_size()

        splash_frame.draw(
            f'{f"Terminal Size: {columns} columns by {rows} rows":^{columns}}'
        )
        splash_frame.draw(f'{f"(press enter to start / esc to quit)":^{columns}}')
    except MinSizeException:
        min_size_frame: Frame = display.new_frame("min_size")

        min_size_frame.draw(
            f"Minumum size required ({MIN_COLUMNS} columns x {MIN_ROWS} rows)"
        )
    finally:
        display.render()


def main():
    splash_result = ask_to_play_or_quit(main_menu)
    if splash_result == SplashState.PLAY:
        columns, rows = os.get_terminal_size()
        game = run(Game(columns - 2, rows - 3))

        res = ask_to_play_or_quit(lambda: game_over(game))


if __name__ == "__main__":
    try:
        cursor.hide()
        colorama.init()
        main()
    except KeyboardInterrupt:
        pass
    finally:
        cursor.show()
