import argparse
import json
import os
import pathlib
from irisml.core.job_runner import JobRunner
from irisml.core.commands.common import configure_logger


def main():
    class KeyValuePairAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            k, v = values.split('=', 1)
            d = getattr(namespace, self.dest)
            d[k] = v

    parser = argparse.ArgumentParser(description="Run a job")
    parser.add_argument('job_filepath', type=pathlib.Path)
    parser.add_argument('--env', '-e', default={}, action=KeyValuePairAction)
    parser.add_argument('--dry_run', '-n', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--very_verbose', '-vv', action='store_true')
    parser.add_argument('--no-cache', dest='no_cache', action='store_true')

    args = parser.parse_args()

    configure_logger(2 if args.very_verbose else (1 if args.verbose else 0))

    cache_storage_url = (not args.no_cache) and os.getenv('IRISML_CACHE_URL')
    job_description = json.loads(args.job_filepath.read_text())
    job_runner = JobRunner(job_description, args.env, cache_storage_url=cache_storage_url)
    job_runner.run(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
