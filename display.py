from io import StringIO
import os


class Frame:
    def __init__(self, key, buffer: StringIO | None= None):
        self.__key = key
        self.__buffer = StringIO(buffer.getvalue() if buffer else "")

    def copy(self, new_key: str):
        return Frame(new_key, self.__buffer)
    
    def home(self) -> None:
        self.draw("\33[H", end="")
    
    def goto(self, y, x):
        self.draw(f"\033[{y};{x}H", end="")
    
    def draw(self, *args, **kwargs):
        print(*args, **kwargs, file=self.__buffer)

    def clear(self):
        self.__buffer = StringIO()

    def value(self):
        return self.__buffer.getvalue()

    def key(self):
        return self.__key

    def rows(self):
        return self.value().count("\n")


class Display:
    def __init__(self) -> None:
        self.buffer = StringIO()
        self.__current_frame: Frame | None = None
        self.__render_history: list[str] = list()
        self.__frame_table: dict[str, Frame] = dict()
        self.__frames_rendered_count: int = 0

    def __clear_terminal(self) -> None:
        os.system("cls")

    def __move_terminal_cursor_home(self) -> None:
        print("\33[H", end="")

    def __get_frame(self) -> str:
        return self.__current_frame.value()

    def __dump_buffer(self) -> None:
        print(self.__get_frame(), end="", flush=True)

    def __switching_frames(self) -> bool:
        if len(self.__render_history) == 0:
            return True
        return self.__current_frame.key() != self.__render_history[-1]

    def __raise_no_frame(self) -> bool:
        if self.__current_frame == None:
            raise ValueError("Must call Display::new_frame before Display::render")

    def render(self) -> None:
        self.__raise_no_frame()
        if self.__current_frame.key() in self.__frame_table:
            self.__frame_table[self.__current_frame.key()] = self.__current_frame

        switching_frames = self.__switching_frames()

        if switching_frames:
            self.__clear_terminal()
        else:
            self.__move_terminal_cursor_home()

        frame: Frame = self.__current_frame
        frame_height = frame.rows()
        _, rows = os.get_terminal_size()
        unrendered_rows = rows - 1 - frame_height
        for _ in range(unrendered_rows - 1):
            frame.draw("\33[2K")
        self.__dump_buffer()

        if switching_frames:
            self.__render_history.append(self.__current_frame.key())

    def new_frame(self, frame_key: str) -> None:
        self.__current_frame = Frame(frame_key)
        return self.__current_frame

    def duplicate_frame(self, new_key: str) -> Frame:
        frame_copy = self.__current_frame.copy(new_key)
        self.__render_history.append(self.__current_frame.key())
        self.__current_frame = frame_copy
        return self.__current_frame
    
    def frame(self):
        return self.__current_frame
    
    def count_frames_rendered(self):
        return self.__frames_rendered_count