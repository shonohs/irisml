import logging
from irisml.core.context import Context
from irisml.core.job import Job

logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, job_dict, env_vars: dict):
        self._job = Job.from_dict(job_dict)
        self._env_vars = env_vars

    def run(self):
        logger.info("Loading task modules.")
        self._job.load_modules()

        logger.info("Running a job.")

        context = Context(self._env_vars)

        for task in self._job.tasks:
            logger.debug(f"Running a task: {task}")
            try:
                task.execute(context)
            except Exception as e:
                logger.exception(f"Failed to run a task {task}: {e}")
                raise

        logger.info("Completed.")
