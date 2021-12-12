#! /usr/bin/env python

"""
Shakespeare -- An interpreter for the Shakespeare Programming Language
"""

from ._parser import shakespeareParser
from tatsu.exceptions import FailedParse
from .errors import ShakespeareRuntimeError, ShakespeareParseError
from ._input import BasicInputManager, InteractiveInputManager
from ._output import BasicOutputManager, VerboseOutputManager
from ._utils import parseinfo_context, normalize_name
from ._character import Character
from ._state import State
import math
from functools import wraps


class Shakespeare:
    """
    Interpreter for the Shakespeare Programming Language.
    """

    def _add_interpreter_context_to_errors(func):
        @wraps(func)
        def inner_function(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ShakespeareRuntimeError as exc:
                if not exc.interpreter:
                    exc.interpreter = self
                raise exc

        return inner_function

    def _parse_first_argument(rule_name):
        def decorator(func):
            @wraps(func)
            def inner_function(self, first_arg, *args, **kwargs):
                parsed = self._parse_if_necessary(first_arg, rule_name)

                try:
                    return func(self, parsed, *args, **kwargs)
                except ShakespeareRuntimeError as exc:
                    if not exc.parseinfo:
                        exc.parseinfo = parsed.parseinfo
                    raise exc

            return inner_function

        return decorator

    def __init__(self, play, input_style="basic", output_style="basic"):
        self.set_input_style(input_style)
        self.set_output_style(output_style)
        self.parser = shakespeareParser()
        self.ast = self._parse_if_necessary(play, "play")
        self.state = State(self.ast.dramatis_personae)

        self.current_position = {"act": 0, "scene": 0, "event": 0}
        self._make_position_consistent()

    # PUBLIC METHODS

    @_add_interpreter_context_to_errors
    def run(self, breakpoint_callback=lambda: None):
        """
        Run the SPL play.

        Arguments:
        breakpoint_callback -- An optional callback, to be called if a debug
                               breakpoint is hit
        """
        while not self.play_over():
            if self._next_event().parseinfo.rule == "breakpoint":
                self._advance_position()
                breakpoint_callback()
            else:
                self.step_forward()

    @_add_interpreter_context_to_errors
    def play_over(self):
        """Return whether the play has finished."""
        return self.current_position["act"] >= len(self.ast.acts)

    @_add_interpreter_context_to_errors
    def step_forward(self):
        """Run the next event in the play."""
        event_to_run = self._next_event()
        if event_to_run.parseinfo.rule == "breakpoint":
            self._advance_position()
            return
        self._debug_output(
            lambda: f"----------\nat line {event_to_run.parseinfo.line}\n-----\n"
            + parseinfo_context(event_to_run.parseinfo)
            + "-----\n"
            + str(self.state)
            + "\n----------"
        )
        has_goto = self.run_event(event_to_run)

        if self.current_position and not has_goto:
            self._advance_position()

    @_add_interpreter_context_to_errors
    def next_event_text(self):
        """Return the contents of the next event in the play."""
        current_event = self._next_event()
        return parseinfo_context(current_event.parseinfo)

    _EVENT_TYPE_HANDLERS = {
        "line": lambda self, e: self._run_line(e),
        "entrance": lambda self, e: self._run_entrance(e),
        "exeunt": lambda self, e: self._run_exeunt(e),
        "exit": lambda self, e: self._run_exit(e),
    }

    @_add_interpreter_context_to_errors
    @_parse_first_argument("event")
    def run_event(self, event):
        """
        Run an event in the current executing context.

        Arguments:
        event -- A string or AST representation of an event (line, entrance,
                 exit, etc.)
        """
        if event.parseinfo.rule not in self._EVENT_TYPE_HANDLERS:
            raise ShakespeareRuntimeError("Unknown event type: " + event.parseinfo.rule)
        return self._EVENT_TYPE_HANDLERS[event.parseinfo.rule](self, event)

    _SENTENCE_TYPE_HANDLERS = {
        "assignment": lambda self, s, c: self._run_assignment(s, c),
        "question": lambda self, s, c: self._run_question(s, c),
        "output": lambda self, s, c: self._run_output(s, c),
        "input": lambda self, s, c: self._run_input(s, c),
        "push": lambda self, s, c: self._run_push(s, c),
        "pop": lambda self, s, c: self._run_pop(s, c),
        "goto": lambda self, s, c: self._run_goto(s),
    }

    @_add_interpreter_context_to_errors
    @_parse_first_argument("sentence")
    def run_sentence(self, sentence, character):
        """
        Run a sentence in the current execution context.

        Arguments:
        sentence -- A string or AST representation of a sentence
        character -- A name or shakespearelang.Character representation of the
                     character speaking the sentence.
        """
        character = self.state.character_by_name_if_necessary(character)
        self.state.assert_character_on_stage(character)

        if sentence.parseinfo.rule not in self._SENTENCE_TYPE_HANDLERS:
            raise ShakespeareRuntimeError(
                "Unknown sentence type: " + sentence.parseinfo.rule
            )
        return self._SENTENCE_TYPE_HANDLERS[sentence.parseinfo.rule](
            self, sentence, character
        )

    _COMPARATIVE_TYPE_HANDLERS = {
        "positive_comparative": lambda a, b: a > b,
        "negative_comparative": lambda a, b: a < b,
        "neutral_comparative": lambda a, b: a == b,
    }

    @_add_interpreter_context_to_errors
    @_parse_first_argument("question")
    def evaluate_question(self, question, character):
        """
        Evaluate a question in the current execution context.

        Arguments:
        question -- A string or AST representation of a question
        character -- A name or shakespearelang.Character representation of the
                     character asking the question.
        """
        character = self.state.character_by_name_if_necessary(character)
        self.state.assert_character_on_stage(character)

        rule = question.comparative.parseinfo.rule
        if rule not in self._COMPARATIVE_TYPE_HANDLERS:
            raise ShakespeareRuntimeError("Unknown comparative type: " + rule)
        return self._COMPARATIVE_TYPE_HANDLERS[rule](
            self.evaluate_expression(question.first_value, character),
            self.evaluate_expression(question.second_value, character),
        )

    _EXPRESSION_TYPE_HANDLERS = {
        "first_person_value": lambda self, v, c: c.value,
        "second_person_value": lambda self, v, c: self.state.character_opposite(
            c
        ).value,
        "negative_noun_phrase": lambda self, v, c: -pow(2, len(v.adjectives)),
        "positive_noun_phrase": lambda self, v, c: pow(2, len(v.adjectives)),
        "character_name": lambda self, v, c: self.state.character_by_name(v.name).value,
        "nothing": lambda self, v, c: 0,
        "unary_expression": lambda self, v, c: self._evaluate_unary_operation(v, c),
        "binary_expression": lambda self, v, c: self._evaluate_binary_operation(v, c),
    }

    @_add_interpreter_context_to_errors
    @_parse_first_argument("value")
    def evaluate_expression(self, value, character):
        """
        Evaluate an expression in the current execution context.

        Arguments:
        expression -- A string or AST representation of an expression
        character -- A name or shakespearelang.Character representation of the
                     character speaking the expression.
        """
        character = self.state.character_by_name_if_necessary(character)

        if value.parseinfo.rule not in self._EXPRESSION_TYPE_HANDLERS:
            raise ShakespeareRuntimeError(
                "Unknown expression type: " + value.parseinfo.rule
            )
        return self._EXPRESSION_TYPE_HANDLERS[value.parseinfo.rule](
            self, value, character
        )

    _INPUT_MANAGERS = {
        "basic": BasicInputManager,
        "interactive": InteractiveInputManager,
    }

    def set_input_style(self, input_style):
        if input_style not in self._INPUT_MANAGERS:
            raise ValueError("Unknown input style")

        self._input_manager = self._INPUT_MANAGERS[input_style]()
        self._input_style = input_style

    def get_input_style(self):
        return self._input_style

    _OUTPUT_MANAGERS = {
        "basic": BasicOutputManager,
        "verbose": VerboseOutputManager,
        "debug": VerboseOutputManager,
    }

    def set_output_style(self, output_style):
        if output_style not in self._OUTPUT_MANAGERS:
            raise ValueError("Unknown output style")

        self._output_manager = self._OUTPUT_MANAGERS[output_style]()
        self._output_style = output_style

    def get_output_style(self):
        return self._output_style

    def parse(self, item, rule_name):
        try:
            return self.parser.parse(item, rule_name=rule_name)
        except FailedParse as parseException:
            raise ShakespeareParseError(parseException) from None

    # HELPERS

    def _parse_if_necessary(self, item, rule_name):
        if not isinstance(item, str):
            return item
        return self.parse(item, rule_name)

    def _scene_number_from_roman_numeral(self, roman_numeral):
        for index, scene in enumerate(self.current_act.scenes):
            if scene.number == roman_numeral:
                return index
        raise ShakespeareRuntimeError("Scene " + roman_numeral + " does not exist.")

    def _next_event(self):
        act_head = self.ast.acts[self.current_position["act"]]
        scene_head = act_head.scenes[self.current_position["scene"]]
        return scene_head.events[self.current_position["event"]]

    def _make_position_consistent(self):
        # This is very ugly, but leaving it like this because it will disappear with
        # play flattening.
        if self.play_over():
            return

        self.current_act = self.ast.acts[self.current_position["act"]]
        current_scene = dict(enumerate(self.current_act.scenes)).get(
            self.current_position["scene"]
        )

        while self.current_position["scene"] >= len(
            self.current_act.scenes
        ) or self.current_position["event"] >= len(current_scene.events):
            if self.play_over():
                break

            if current_scene is not None and self.current_position["event"] >= len(
                current_scene.events
            ):
                self.current_position["event"] = 0
                self.current_position["scene"] += 1
            if self.current_position["scene"] >= len(self.current_act.scenes):
                self.current_position["scene"] = 0
                self.current_position["act"] += 1

            if self.play_over():
                break

            self.current_act = self.ast.acts[self.current_position["act"]]
            current_scene = dict(enumerate(self.current_act.scenes)).get(
                self.current_position["scene"]
            )

    def _goto_scene(self, numeral):
        scene_number = self._scene_number_from_roman_numeral(numeral)
        self.current_position["scene"] = scene_number
        self.current_position["event"] = 0

        self._make_position_consistent()

    def _advance_position(self):
        self.current_position["event"] += 1
        self._make_position_consistent()

    def _verbose_output(self, out):
        self._output_by_style(out, ["verbose", "debug"])

    def _debug_output(self, out):
        self._output_by_style(out, ["debug"])

    def _output_by_style(self, out, style_list):
        if self._output_style in style_list:
            if callable(out):
                out = out()
            print(out)

    # EXPRESSION TYPES

    def _evaluate_factorial(operand):
        if operand < 0:
            raise ShakespeareRuntimeError(
                "Cannot take the factorial of a negative number: " + str(operand)
            )
        return math.factorial(operand)

    def _evaluate_square_root(operand):
        if operand < 0:
            raise ShakespeareRuntimeError(
                "Cannot take the square root of a negative number: " + str(operand)
            )
        # Truncates (does not round) result -- this is equivalent to C
        # implementation's cast.
        return int(math.sqrt(operand))

    _UNARY_OPERATION_HANDLERS = {
        ("the", "cube", "of"): lambda x: pow(x, 3),
        ("the", "factorial", "of"): _evaluate_factorial,
        ("the", "square", "of"): lambda x: pow(x, 2),
        ("the", "square", "root", "of"): _evaluate_square_root,
        "twice": lambda x: x * 2,
    }

    def _evaluate_unary_operation(self, op, character):
        if op.operation not in self._UNARY_OPERATION_HANDLERS:
            raise ShakespeareRuntimeError("Unknown operation!")

        operand = self.evaluate_expression(op.value, character)
        return self._UNARY_OPERATION_HANDLERS[op.operation](operand)

    def _evaluate_quotient(first_operand, second_operand):
        if second_operand == 0:
            raise ShakespeareRuntimeError("Cannot divide by zero")
        # Python's built-in integer division operator does not behave the
        # same as C for negative numbers, using floor instead of truncated
        # division
        return int(first_operand / second_operand)

    def _evaluate_remainder(first_operand, second_operand):
        if second_operand == 0:
            raise ShakespeareRuntimeError("Cannot divide by zero")
        # See note above. math.fmod replicates C behavior.
        return int(math.fmod(first_operand, second_operand))

    _BINARY_OPERATION_HANDLERS = {
        ("the", "difference", "between"): lambda a, b: a - b,
        ("the", "product", "of"): lambda a, b: a * b,
        ("the", "quotient", "between"): _evaluate_quotient,
        ("the", "remainder", "of", "the", "quotient", "between"): _evaluate_remainder,
        ("the", "sum", "of"): lambda a, b: a + b,
    }

    def _evaluate_binary_operation(self, op, character):
        if op.operation not in self._BINARY_OPERATION_HANDLERS:
            raise ShakespeareRuntimeError("Unknown operation!")

        first_operand = self.evaluate_expression(op.first_value, character)
        second_operand = self.evaluate_expression(op.second_value, character)

        return self._BINARY_OPERATION_HANDLERS[op.operation](
            first_operand, second_operand
        )

    # SENTENCE TYPES

    def _run_assignment(self, sentence, character):
        character_opposite = self.state.character_opposite(character)
        character_opposite.value = self.evaluate_expression(sentence.value, character)

        self._verbose_output(
            f"{character_opposite.name} set to {character_opposite.value}"
        )

    def _run_question(self, question, character):
        self.state.global_boolean = self.evaluate_question(question, character)

        self._verbose_output(f"Setting global boolean to {self.state.global_boolean}")

    def _run_goto(self, goto):
        condition = goto.condition
        condition_type = condition and condition.parseinfo.rule == "positive_if"
        if (not condition) or (condition_type == self.state.global_boolean):
            self._goto_scene(goto.destination)
            self._verbose_output(f"Jumping to Scene {goto.destination}")
            return True
        else:
            self._verbose_output(
                f"Not jumping to Scene {goto.destination} because global boolean is {self.state.global_boolean}"
            )

    def _run_output(self, output, speaking_character):
        character_to_output = self.state.character_opposite(speaking_character)
        self._verbose_output(f"Outputting {character_to_output.name}")
        value = character_to_output.value
        if output.output_number:
            self._output_manager.output_number(value)
        elif output.output_char:
            self._output_manager.output_character(value)
        else:
            raise ShakespeareRuntimeError("Unknown output type!")

    def _run_input(self, input_op, speaking_character):
        character_to_set = self.state.character_opposite(speaking_character)
        if input_op.input_number:
            value = self._input_manager.consume_numeric_input()
        elif input_op.input_char:
            value = self._input_manager.consume_character_input()
        else:
            raise ShakespeareRuntimeError("Unknown input type!")

        self._verbose_output(
            f"Setting {character_to_set.name} to input value {repr(value)}"
        )
        character_to_set.value = value

    def _run_push(self, push, speaking_character):
        pushing_character = self.state.character_opposite(speaking_character)
        value = self.evaluate_expression(push.value, speaking_character)
        self._verbose_output(f"{pushing_character.name} pushed {value}")
        pushing_character.push(value)

    def _run_pop(self, pop, speaking_character):
        popping_character = self.state.character_opposite(speaking_character)
        self._verbose_output(f"Popping stack of {popping_character.name}")
        popping_character.pop()

    # EVENT TYPES

    def _run_line(self, line):
        character = self.state.character_by_name(line.character)
        self.state.assert_character_on_stage(character)
        for sentence in line.contents:
            # Returns whether this sentence caused a goto
            has_goto = self.run_sentence(sentence, character)
            if has_goto:
                return True

    def _run_entrance(self, entrance):
        self._verbose_output(
            lambda: f"Enter {', '.join([normalize_name(c) for c in entrance.characters])}"
        )
        self.state.enter_characters(entrance.characters)

    def _run_exeunt(self, exeunt):
        if exeunt.characters:
            self._verbose_output(
                lambda: f"Exeunt {', '.join([normalize_name(c) for c in exeunt.characters])}"
            )
            self.state.exeunt_characters(exeunt.characters)
        else:
            self._verbose_output(f"Exeunt all")
            self.state.exeunt_all()

    def _run_exit(self, exit):
        self._verbose_output(lambda: f"Exit {normalize_name(exit.character)}")
        self.state.exit_character(exit.character)
