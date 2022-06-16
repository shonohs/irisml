import logging
from irisml.core import JobDescription
from irisml.core.cache_manager import AzureBlobStorageManager, CacheManager
from irisml.core.context import Context
from irisml.core.job import Job

logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(self, job_dict, env_vars: dict, cache_storage_url: str = None):
        job_description = JobDescription.from_dict(job_dict)
        self._job = Job(job_description)
        self._env_vars = env_vars
        self._cache_storage_url = cache_storage_url

    def run(self, dry_run=False):
        logger.info("Loading task modules.")
        self._job.load_modules()

        logger.info("Running a job.")

        cache_manager = CacheManager(AzureBlobStorageManager(self._cache_storage_url)) if self._cache_storage_url else None
        if cache_manager:
            logger.info(f"Cache is enabled: {self._cache_storage_url}")

        context = Context(self._env_vars, cache_manager)

        # Note that the random seed will be reset in each Task.execute().
        for task in self._job.tasks:
            logger.debug(f"Running a task: {task}")
            try:
                task.execute(context, dry_run)
            except Exception as e:
                logger.exception(f"Failed to run a task {task}: {e}")
                raise

        logger.info("Completed.")
