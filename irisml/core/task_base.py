import dataclasses


class TaskBase:
    VERSION = '0.0.0'

    @dataclasses.dataclass(frozen=True)
    class Config:
        pass

    @dataclasses.dataclass(frozen=True)
    class Inputs:
        pass

    @dataclasses.dataclass(frozen=True)
    class Outputs:
        pass

    def __init__(self, config: Config):
        self._config = config

    def __call__(self, inputs: Inputs) -> Outputs:
        return self.execute(inputs)

    def execute(self, inputs: Inputs) -> Outputs:
        raise NotImplementedError
