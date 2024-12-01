from tatsu.ast import AST

from ._operation import operations_from_event
from .errors import ShakespeareRuntimeError


class Play:
    def __init__(self, ast: AST):
        self.operations = []
        self.act_indices: dict[int, int] = {}
        self.scene_indices: dict[int, dict[int, int]] = {}
        self._preprocess(ast)

    def _preprocess(self, ast: AST):
        for act in ast.acts:  # type: ignore
            act_number = act.number.value
            if act_number in self.scene_indices:
                raise ShakespeareRuntimeError(
                    f"Act numeral {act_number} is not unique",
                    parseinfo=act.number.parseinfo,
                )
            self.act_indices[act_number] = len(self.operations)
            self.scene_indices[act_number] = {}
            for scene in act.scenes:
                scene_number = scene.number.value
                if scene_number in self.scene_indices[act_number]:
                    raise ShakespeareRuntimeError(
                        f"Scene numeral {scene_number} is not unique in {act_number}",
                        parseinfo=scene.number.parseinfo,
                    )
                self.scene_indices[act_number][scene_number] = len(self.operations)
                for event in scene.events:
                    self.operations += operations_from_event(event)

    def get_act(self, position: int) -> int:
        last_act = None
        for act, pos in self.act_indices.items():
            if last_act is None:
                last_act = act
                continue
            if pos > position:
                return last_act
            last_act = act

        else:
            return list(self.act_indices.keys())[-1]
