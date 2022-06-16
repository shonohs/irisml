# IrisML

A simple framework to create a ML pipeline.


# Features
- Run a ML training/inference with a simple JSON configuration.
- Modularized interfaces for task components.
- Cache task outputs for faster experiments.

# Getting started
## Installation
Prerequisite: python 3.8+

```
# Install the core framework and standard tasks.
pip install irisml irisml-tasks irisml-task-training
```

## Run an example pipeline
```
# Install additional packages that are required for the example
pip install irisml-task-torchvision

# Run on local machine
irisml_run docs/examples/simple_training.json
```

## Available commands
```
# Run the specified pipeline.
irisml_run [-e <ENV_NAME>=<env_value>] <pipeline_json>

# Show information about the specified task. If <task_name> is not provided, shows a list of available tasks in the current environment.
irisml_show [<task_name>]
```

## Pipeline definition
```
PipelineDefinition = {"tasks": <list of TaskDefinition>}

TaskDefinition = {
    "task": <task module name>,
    "name": <optional unique name of the task>,
    "inputs": <list of input objects>,
    "config": <config for the task. Use irisml_show command to find the available configurations.>
}
```
In the TaskDefinition.inputs and TaskDefinition.config, you cna use the following two variable.
- $env.<variable_name>
  This variable will be replaced by the environment variable that was provided as arguments for irisml_run command.
- $outputs.<task_name>.<field_name>
  This variable will be replaced by the outputs of the specified previdous task.

It raises an exception on runtime if the specified variable was not found.

## Enable cache
To enable cache, you must specify the cache storage location by setting IRISML_CACHE_URL environment variable. Currently Azure Blob Storage and local filesystem is supported.

To use Azure Blob Storage, a container URL must be provided. It the URL contains a SAS token, it will be used for authentication. Otherwise, interactive authentication and Managed Identity authentication will be used.

# List of available offial tasks

To show the detailed help for each task, run the following command after installing the package.
```
irisml_show <task_name>
```

## [irisml-tasks](https://github.com/shonohs/irisml-tasks)
- assert
- download_azure_blob
- run_parallel
- run_sequential
- search_grid_sequential
- upload_azure_blob

## irisml-task-training
This package contains tasks related to pytorch training
- evaluate
- export_onnx
- load_dataset
- load_state_dict
- save_onnx
- save_state_dict
- train

## irisml-task-torchvision
- load_torchvision_dataset
- create_torchvision_model
- create_torchvision_transform

## irisml-task-timm
Adapter for models in timm library
- create_timm_model

# Development
## Create a new task
To create a Task, you must define a module container a class "Task" inheriting irisml.core.TaskBase. The following is the simplest example
```python
# irisml/tasks/my_custom_task.py
import dataclasses
import irisml.core

class Task(irisml.core.TaskBase):  # The class name must be "Task".
  VERSION = '1.0.0'
  CACHE_ENABLED = True  # (default: True) This is optional.

  @dataclasses.dataclass
  class Inputs:  # You can remove this class if the task doesn't require inputs.
    int_value: int
    float_value: float

  @dataclasses.dataclass
  class Config:  # If there is no configuration, you can remove this class. All fields must be JSON-serializable.
    another_float: float
    child_dataclass: dataclass  # If you'd like to define a nested config, you can define another dataclass.

  @dataclasses.dataclass
  class Outputs:  # Can be removed if the task doesn't have outputs.
    float_value: float = 0  # Outputs fields must have default value or default factory.

  def execute(self, inputs: Inputs) -> Outputs:
    return self.Outputs(inputs.int_value * inputs.float_value * self.config.another_float)

  def dry_run(self, inputs: Inputs) -> Outputs:  # This method is optional.
    return self.Outputs(0)  # Must return immediately without actual processing.
```

Each Task must define "execute" method. The base class has empty implementation for Inputs, Config, Outputs and dry_run(). For the detail, please see the document for TaskBase class.