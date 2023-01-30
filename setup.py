from setuptools import (
    find_packages,
    setup,
)

VERSION = "1.3.2"
NAME: str = 'remote_procedure'
AUTHOR: str = 'Imanji Beki'  # noqa
AUTHOR_EMAIL: str = 'imanjibeki@gmail.com'
URI: str = 'https://github.com/Beki95/rpc'

with open("README.md") as f:
    long_description = f.read()

setup(
    name=NAME,
    author=AUTHOR,
    version=VERSION,
    author_email=AUTHOR_EMAIL,
    packages=find_packages(),
    url=URI,
    license="MIT",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "aio-pika==8.2.4",
        "pika==1.3.1",
    ],
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
