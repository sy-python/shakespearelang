from ._input import BasicInputManager, InteractiveInputManager, ReaderInputManager
from ._output import BasicOutputManager, VerboseOutputManager


from ._input import BasicInputManager, InteractiveInputManager, ReaderInputManager
from ._output import BasicOutputManager, VerboseOutputManager


class Settings:
    """
    The settings of a Shakespeare interpreter. Controls how and when the interpreter
    does input and output.
    """

    _INPUT_MANAGERS = {
        "basic": (BasicInputManager, []),
        "interactive": (InteractiveInputManager, []),
        "reader": (ReaderInputManager, ["reader"]),
    }

    _OUTPUT_MANAGERS = {
        "basic": (BasicOutputManager, []),
        "verbose": (VerboseOutputManager, []),
        "debug": (VerboseOutputManager, []),
    }

    def __init__(self, input_style: str, output_style: str, **kwargs):
        self.input_style = input_style
        self.output_style = output_style
        self._kwargs = kwargs

    @property
    def input_style(self) -> str:
        """
        Input style of the interpreter. 'basic' is the best for piped input.
            'interactive' is nicer when getting input from a human.
            'reader' is for getting input from a file in the programming contexts.
        """
        return self._input_style

    @input_style.setter
    def input_style(self, value: str):
        if value not in self._INPUT_MANAGERS:
            raise ValueError("Unknown input style")

        input_manager_cls, input_manager_args = self._INPUT_MANAGERS[value]
        args = {}
        for arg in input_manager_args:
            if arg not in self._kwargs:
                raise ValueError(f"Missing argument {arg} for input style {value}")
            args[arg] = self._kwargs[arg]

        self.input_manager = input_manager_cls(**args)
        self._input_style = value

    @property
    def output_style(self) -> str:
        """
        Output style of the interpreter. 'basic' outputs exactly what the SPL play generated.
        'verbose' prefixes output and shows visible representations of
        whitespace characters. 'debug' is like 'verbose' but with debug output
        from the interpreter.
        """
        return self._output_style

    @output_style.setter
    def output_style(self, value: str):
        if value not in self._OUTPUT_MANAGERS:
            raise ValueError("Unknown output style")

        output_manager_cls, output_manager_args = self._OUTPUT_MANAGERS[value]
        args = {}
        for arg in output_manager_args:
            if arg not in self._kwargs:
                raise ValueError(f"Missing argument {arg} for output style {value}")
            args[arg] = self._kwargs[arg]

        self.output_manager = output_manager_cls(**args)
        self._output_style = value
