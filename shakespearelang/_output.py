from .errors import ShakespeareRuntimeError


class BasicOutputManager:
    def output_number(self, number: int) -> None:
        print(number, end="")

    def output_character(self, character_code: int) -> None:
        print(_code_to_character(character_code), end="")


class VerboseOutputManager:
    def output_number(self, number: int) -> None:
        print(f"Outputting number: {str(number)}")

    def output_character(self, character_code: int) -> None:
        char = _code_to_character(character_code)
        print(f"Outputting character: {repr(char)}")


def _code_to_character(character_code: int) -> str:
    try:
        return chr(character_code)
    except ValueError:
        raise ShakespeareRuntimeError("Invalid character code: " + str(character_code))
