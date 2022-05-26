class TaskBase:
    def __init__(self, config):
        self._config = config

    def __call__(self, inputs):
        return self.execute(inputs)

    def execute(self, inputs: dict):
        raise NotImplementedError
