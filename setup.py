from setuptools import (
    find_packages,
    setup,
)

VERSION = "0.1.0"

with open("README.md") as f:
    long_description = f.read()

setup(
    name='remote_procedure',
    author="Imanji Beki",
    version=VERSION,
    author_email="imanjibeki@gmail.com",
    packages=find_packages(),
    url="https://github.com/Beki95/rpc",
    license="MIT",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "aio-pika==8.2.4",
        "fastapi==0.85.0",
    ],
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
