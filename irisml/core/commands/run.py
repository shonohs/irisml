import argparse
import json
import pathlib
from irisml.core.job_runner import JobRunner


def main():
    parser = argparse.ArgumentParser(description="Run a job")
    parser.add_argument('job_filepath', type=pathlib.Path)

    args = parser.parse_args()

    job_description = json.loads(args.job_filepath.read_text())
    job_runner = JobRunner(job_description)
    job_runner.run()


if __name__ == '__main__':
    main()
