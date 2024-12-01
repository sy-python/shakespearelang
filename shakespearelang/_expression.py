from abc import ABC, abstractmethod
import math
from typing import Any, Callable

from tatsu.ast import AST

from ._state import State
from ._utils import normalize_name
from .errors import ShakespeareRuntimeError, ShakespeareParseError


class Expression(ABC):
    def __init__(self, ast_node: AST, character: str) -> None:
        self.ast_node: AST = ast_node
        self.character: str = normalize_name(character)
        self.cacheable: bool = False
        self.cached_value: int | None = None
        self._setup()

    @abstractmethod
    def _setup(self) -> None:
        pass

    def evaluate(self, state: State) -> int:
        state.assert_character_on_stage(self.character)
        try:
            return self._evaluate_logic_cached(state)
        except ShakespeareRuntimeError as exc:
            if not exc.parseinfo:
                exc.parseinfo = self.ast_node.parseinfo
            raise exc

    def _evaluate_logic_cached(self, state: State) -> int:
        if self.cacheable and self.cached_value is not None:
            return self.cached_value
        result = self._evaluate_logic(state)
        if self.cacheable:
            self.cached_value = result
        return result

    @abstractmethod
    def _evaluate_logic(self, state: State) -> int:
        pass


class FirstPersonValue(Expression):
    def _setup(self) -> None:
        pass

    def _evaluate_logic(self, state: State) -> int:
        return state.character_by_name(self.character).value


class SecondPersonValue(Expression):
    def _setup(self) -> None:
        pass

    def _evaluate_logic(self, state: State) -> int:
        character_opposite = state.character_opposite(self.character)
        return state.character_by_name(character_opposite).value


class CharacterName(Expression):
    def _setup(self) -> None:
        self.name: str = normalize_name(self.ast_node.name)

    def _evaluate_logic(self, state: State) -> int:
        return state.character_by_name(self.name).value


class NegativeNounPhrase(Expression):
    def _setup(self) -> None:
        self.cacheable = True

    def _evaluate_logic(self, state: State) -> int:
        return -pow(2, len(self.ast_node.adjectives))  # type: ignore


class PositiveNounPhrase(Expression):
    def _setup(self) -> None:
        self.cacheable = True

    def _evaluate_logic(self, state: State) -> int:
        return pow(2, len(self.ast_node.adjectives))  # type: ignore


class Nothing(Expression):
    def _setup(self) -> None:
        self.cacheable = True

    def _evaluate_logic(self, state: State) -> int:
        return 0


def _evaluate_factorial(operand: int) -> int:
    if operand < 0:
        raise ShakespeareRuntimeError(
            f"Cannot take the factorial of a negative number: {operand}"
        )
    return math.factorial(operand)


def _evaluate_square_root(operand: int) -> int:
    if operand < 0:
        raise ShakespeareRuntimeError(
            f"Cannot take the square root of a negative number: {operand}"
        )

    return int(math.sqrt(operand))


class UnaryOperation(Expression):
    _UNARY_OPERATION_HANDLERS: dict[Any, Callable[[int], int]] = {
        ("the", "cube", "of"): lambda x: pow(x, 3),
        ("the", "factorial", "of"): _evaluate_factorial,
        ("the", "square", "of"): lambda x: pow(x, 2),
        ("the", "square", "root", "of"): _evaluate_square_root,
        "twice": lambda x: x * 2,
    }

    def _setup(self) -> None:
        self.operand: Expression = expression_from_ast(self.ast_node.value, self.character)  # type: ignore
        self.cacheable: bool = self.operand.cacheable
        self.operation = self._UNARY_OPERATION_HANDLERS[self.ast_node.operation]  # type: ignore

    def _evaluate_logic(self, state: State) -> int:
        return self.operation(self.operand.evaluate(state))


def _evaluate_quotient(first_operand: int, second_operand: int) -> int:
    if second_operand == 0:
        raise ShakespeareRuntimeError("Cannot divide by zero")
    return int(first_operand / second_operand)


def _evaluate_remainder(first_operand: int, second_operand: int) -> int:
    if second_operand == 0:
        raise ShakespeareRuntimeError("Cannot divide by zero")
    return int(math.fmod(first_operand, second_operand))


class BinaryOperation(Expression):
    _BINARY_OPERATION_HANDLERS: dict[Any, Callable[[int, int], int]] = {
        ("the", "difference", "between"): lambda a, b: a - b,
        ("the", "product", "of"): lambda a, b: a * b,
        ("the", "quotient", "between"): _evaluate_quotient,
        ("the", "remainder", "of", "the", "quotient", "between"): _evaluate_remainder,
        ("the", "sum", "of"): lambda a, b: a + b,
    }

    def _setup(self) -> None:
        self.first_operand: Expression = expression_from_ast(
            self.ast_node.first_value, self.character  # type: ignore
        )
        self.second_operand: Expression = expression_from_ast(
            self.ast_node.second_value, self.character  # type: ignore
        )
        self.cacheable: bool = (
            self.first_operand.cacheable and self.second_operand.cacheable
        )
        self.operation = self._BINARY_OPERATION_HANDLERS[self.ast_node.operation]  # type: ignore

    def _evaluate_logic(self, state: State) -> int:
        return self.operation(
            self.first_operand.evaluate(state), self.second_operand.evaluate(state)
        )


_EXPRESSION_CONSTRUCTORS: dict[str, type[Expression]] = {
    "first_person_value": FirstPersonValue,
    "second_person_value": SecondPersonValue,
    "character_name": CharacterName,
    "negative_noun_phrase": NegativeNounPhrase,
    "positive_noun_phrase": PositiveNounPhrase,
    "nothing": Nothing,
    "unary_expression": UnaryOperation,
    "binary_expression": BinaryOperation,
}


def expression_from_ast(ast_node: AST, character: str) -> Expression:
    return _EXPRESSION_CONSTRUCTORS[ast_node.parseinfo.rule](ast_node, character)  # type: ignore
