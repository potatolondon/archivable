import os
from setuptools import setup, find_packages


NAME = 'archivable'
PACKAGES = find_packages()
DESCRIPTION = 'Archivable class-decorator for django models which supports uniqueness'
URL = "https://github.com/potatolondon/archivable"
LONG_DESCRIPTION = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
AUTHOR = 'Potato London Ltd.'

EXTRAS = {
    "test": ["mock", "coverage==3.7.1"],
}

setup(
    name=NAME,
    version='0.1.0',
    packages=PACKAGES,

    # metadata for upload to PyPI
    author=AUTHOR,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    keywords=["django", "archivable", "uniqueness"],
    url=URL,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    include_package_data=True,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
)
