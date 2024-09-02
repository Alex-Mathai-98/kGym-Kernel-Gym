# setup.py
from setuptools import setup, find_namespace_packages

setup(name='kbdr-kcomposer',
      version='0.3.4',
      description='KBDr KComposer',
      packages=find_namespace_packages(where='./', include=['KBDr.kcomposer']),
      install_requires=[
          'requests',
          'aiohttp'
      ],
      zip_safe=False)
