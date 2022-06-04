import unittest
from irisml.core import JobDescription
from irisml.core.job import Job


class TestJob(unittest.TestCase):
    def test_assign_unique_name(self):
        job_description = {'tasks': [
            {'task': 'custom_task'},
            {'task': 'custom_task'},
            {'task': 'custom_task'},
            {'task': 'custom_task', 'name': 'custom_name'},
            {'task': 'custom_task', 'name': 'custom_name'},
            {'task': 'custom_task', 'name': 'custom_name'}
        ]}

        job = Job(JobDescription.from_dict(job_description))
        names = [t.name for t in job.tasks]
        self.assertEqual(names, ['custom_task', 'custom_task@2', 'custom_task@3', 'custom_name', 'custom_name@2', 'custom_name@3'])
