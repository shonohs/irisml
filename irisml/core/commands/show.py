import argparse
import dataclasses
import importlib
import inspect
import pkgutil
from irisml.core.commands.common import configure_logger


def _print_dataclass(data_class):
    for field in dataclasses.fields(data_class):
        print(f"    {field.name}: {field.type}")


def main():
    configure_logger()
    parser = argparse.ArgumentParser(description="Show information about a task")
    parser.add_argument('task_name', nargs='?', help="If not provided, shows all available tasks on this environment.")

    args = parser.parse_args()

    if args.task_name:
        task_module = importlib.import_module('irisml.tasks.' + args.task_name)
        task_class = task_module.Task

        task_doc = inspect.getdoc(task_class)
        if task_doc:
            print(task_doc)
        else:
            print("No description found. Please add documentation to the Task class.")

        print("\nConfiguration:")
        _print_dataclass(task_class.Config)

        print("\nInputs:")
        _print_dataclass(task_class.Inputs)

        print("\nOutputs:")
        _print_dataclass(task_class.Outputs)
    else:
        parser.print_usage()
        print("\nAvailable tasks on this environment:\n")
        import irisml.tasks
        names = [name for module_loader, name, ispkg in pkgutil.iter_modules(irisml.tasks.__path__)]
        for name in sorted(names):
            print(name)

        print(f"\nTotal {len(names)}")


if __name__ == '__main__':
    main()
