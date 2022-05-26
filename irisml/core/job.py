import json
import pathlib
from .task import Task


class Job:
    def __init__(self, tasks: list[Task]):
        self._tasks = tasks

    @property
    def tasks(self):
        for t in self._tasks:
            yield t

    def load_modules(self):
        for t in self.tasks:
            t.load_module()

    @classmethod
    def from_dict(cls, data: dict):
        tasks = [Task.from_dict(t) for t in data['tasks']]
        return cls(tasks)


def load_job(filepath: pathlib.Path):
    json_data = json.loads(filepath.read_text())
    return Job.from_dict(json_data)
