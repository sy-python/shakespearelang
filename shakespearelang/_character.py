from collections import deque
from .errors import ShakespeareRuntimeError


class Character:
    """A character in an SPL play."""

    def __init__(self):
        self.value: int = 0
        self.stack: deque[int] = deque()

    def __str__(self) -> str:
        return f'{self.value} ({" ".join([str(v) for v in self.stack][::-1])})'

    def push(self, newValue: int) -> None:
        """Push a value onto the character's stack."""
        self.stack.append(newValue)

    def pop(self) -> None:
        """Pop a value off the character's stack, and set the character to
        that value."""
        if len(self.stack) == 0:
            raise ShakespeareRuntimeError("Tried to pop from an empty stack.")
        self.value = self.stack.pop()
