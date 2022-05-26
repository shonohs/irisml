"""Check a job description file."""
import argparse
import json
import pathlib
from irisml.core.job import Job


def main():
    parser = argparse.ArgumentParser(description="Check a job description")
    parser.add_argument('job_filepath', type=pathlib.Path)

    args = parser.parse_args()

    job_description = json.loads(args.job_filepath.read_text())
    job = Job.from_dict(job_description)
    print(job)
    print("Loading task modules...")
    job.load_modules()
    print("Success!")
