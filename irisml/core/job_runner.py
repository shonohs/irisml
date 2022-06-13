import logging
import random
from irisml.core import JobDescription
from irisml.core.context import Context
from irisml.core.job import Job

logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, job_dict, env_vars: dict):
        job_description = JobDescription.from_dict(job_dict)
        self._job = Job(job_description)
        self._env_vars = env_vars

    def run(self, dry_run=False):
        logger.info("Loading task modules.")
        self._job.load_modules()

        logger.info("Running a job.")

        context = Context(self._env_vars)

        # Initialize the random seed so that we can get deterministic results.
        # PyTorch random generator should be taken care by each task.
        random.seed(42)

        for task in self._job.tasks:
            logger.debug(f"Running a task: {task}")
            try:
                task.execute(context, dry_run)
            except Exception as e:
                logger.exception(f"Failed to run a task {task}: {e}")
                raise

        logger.info("Completed.")
