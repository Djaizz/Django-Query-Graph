import os
from ruamel import yaml
from setuptools import find_packages, setup


_PACKAGE_NAMESPACE_NAME = 'django_model_query_graphs'

_METADATA_FILE_NAME = 'metadata.yml'

_REQUIREMENTS_FILE_NAME = 'requirements.txt'


_metadata = \
    yaml.safe_load(
        stream=open(os.path.join(
                os.path.dirname(__file__),
                _PACKAGE_NAMESPACE_NAME,
                _METADATA_FILE_NAME)))


setup(
    name=_metadata['PACKAGE'],
    author=_metadata['AUTHOR'],
    author_email=_metadata['AUTHOR_EMAIL'],
    url=_metadata['URL'],
    version=_metadata['VERSION'],
    description=_metadata['DESCRIPTION'],
    long_description=_metadata['DESCRIPTION'],
    keywords=_metadata['DESCRIPTION'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=
        [s for s in open(_REQUIREMENTS_FILE_NAME).readlines()
           if not s.startswith('#')])
