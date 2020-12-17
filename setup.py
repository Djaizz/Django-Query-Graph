import json
from setuptools import find_packages, setup


_METADATA_FILE_NAME = 'metadata.json'

_REQUIREMENTS_FILE_NAME = 'requirements.txt'


_metadata = json.load(open(_METADATA_FILE_NAME))

setup(
    name=_metadata['PACKAGE'],
    url=_metadata['URL'],
    version=_metadata['VERSION'],
    author=_metadata['AUTHOR'],
    author_email=_metadata['AUTHOR-EMAIL'],
    description=_metadata['DESCRIPTION'],
    long_description=_metadata['DESCRIPTION'],
    keywords=_metadata['DESCRIPTION'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[s
                      for s in {i.strip()
                                for i in
                                open(_REQUIREMENTS_FILE_NAME).readlines()}
                      if not s.startswith('#')])
