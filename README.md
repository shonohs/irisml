# Irisml

A simple framework to create a ML pipeline.


# Features
- Run a ML training with a single JSON configuration.
- Tasks are implemented as a small python module. No explicit dependency between tasks.
- Code versioning

# Getting started
## Install
Prerequisite: python 3.8+

```
# Install the core framework
pip install irisml irisml-tasks irisml-task-training # TODO: Not published yet
```

## Run an example pipeline
```
# Install additional packages that are required for the example
pip install irisml-model-timm

# Run on local machine
irisml_run docs/examples/simple_training.json
```

## Available commands
```
# Quickly verify the json file.
irisml_check <pipeline_json>

# Run the specified pipeline.
irisml_run [-e <ENV_NAME>=<env_value>] <pipeline_json>

# Show information about the specified task. If <task_name> is not provided, shows a list of available tasks.
irisml_show [<task_name>]
```

# Available packages

To show the detailed help for each task, run the following command after installing the package.
```
irisml_show <task_name>
```

## irisml-tasks (Installed by default)
- cache
- run_parallel
- run_sequence

## irisml-task-training
This package contains tasks related to pytorch training
- evaluate
- load_dataset
- load_state_dict
- save_onnx
- save_state_dict
- train

## irisml-model-timm
Adapter for models in timm library
- create_timm_model
