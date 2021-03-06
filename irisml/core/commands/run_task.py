import argparse
from irisml.core.context import Context
from irisml.core.commands.common import configure_logger
from irisml.core.task import Task


def main():
    """TODO This method is WIP."""
    configure_logger()
    parser = argparse.ArgumentParser(description="Run a single task")
    parser.add_argument('task_name')
    parser.add_argument('--inputs', nargs='*')
    parser.add_argument('--config', default='')

    args = parser.parse_args()

    context = Context()
    task = Task(args.task_name, args.inputs, args.config)
    task.execute(context)
