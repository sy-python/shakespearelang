from collections import deque
import sys
from typing import TextIO

from .errors import ShakespeareRuntimeError


class BasicInputManager:
    def __init__(self):
        self._input_buffer = deque()

    def consume_numeric_input(self) -> int:
        try:
            self._ensure_input_buffer()
        except EOFError:
            return 0

        sign = self._consume_sign_if_present()
        number = self._consume_digits()

        if number is None:
            if sign:
                self._input_buffer.appendleft(sign)
            return 0

        return -number if sign == "-" else number

    def _consume_sign_if_present(self) -> str:
        if self._input_buffer and (sign := self._input_buffer[0]) in ["+", "-"]:
            self._input_buffer.popleft()
            return sign

        return ""

    def _consume_digits(self) -> int | None:
        number_input = []
        while self._input_buffer and self._input_buffer[0].isdigit():
            number_input.append(self._input_buffer.popleft())

        if len(number_input) == 0:
            return None

        return int("".join(number_input))

    def consume_character_input(self) -> int:
        try:
            self._ensure_input_buffer()
        except EOFError:
            return -1

        value = ord(self._input_buffer.popleft())
        return value

    def _ensure_input_buffer(self) -> None:
        if not self._input_buffer:
            # We want all output that has already happened to appear before we
            # ask the user for input
            sys.stdout.flush()
            self._input_buffer.extend(sys.stdin.readline())
            if not self._input_buffer:
                raise EOFError()


class InteractiveInputManager:
    def consume_numeric_input(self) -> int:
        try:
            value = int(input("Taking input number: "))
        except ValueError:
            raise ShakespeareRuntimeError("No numeric input was given.")

        return value

    def consume_character_input(self) -> int:
        value = input("Taking input character: ")
        if value == "EOF":
            return -1
        elif value == "":
            return ord("\n")
        else:
            return ord(value[0])


class ReaderInputManager:
    def __init__(self, reader: TextIO) -> None:
        self._reader = reader
        self._buffer: deque[str] = deque()

    def consume_numeric_input(self) -> int:
        char = self._get_character()
        if char in ["+", "-"]:
            sign = char
            number = []
        elif char.isdigit():
            sign = ""
            number = [char]
        else:
            self._buffer.appendleft(char)
            return 0

        while (char := self._get_character()).isdigit():
            number.append(char)

        self._buffer.appendleft(char)

        return int(sign + "".join(number))

    def consume_character_input(self) -> int:
        value = self._get_character()
        if value == "":
            return -1
        else:
            return ord(value)

    def _get_character(self) -> str:
        if self._buffer:
            return self._buffer.popleft()

        return self._reader.read(1)
