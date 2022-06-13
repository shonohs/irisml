import setuptools


setuptools.setup(name='irisml',
                 author='irisdev',
                 version='0.0.0',
                 packages=setuptools.find_packages(exclude=['test', 'test.*']),
                 entry_points={
                     'console_scripts': [
                         'irisml_run=irisml.core.commands.run:main',
                         'irisml_run_task=irisml.core.commands.run_task:main',
                         'irisml_show=irisml.core.commands.show:main',
                     ]})
