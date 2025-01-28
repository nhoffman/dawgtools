import os
import setuptools

package_data = ['data/*']

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dawgtools",
    version='0.1',
    author="Noah Hoffman",
    author_email="ngh2@uw.edu",
    description="Utilities for the am-dawg-tool environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nhoffman/dawgtools",
    project_urls={
        "Bug Tracker": "https://github.com/nhoffman/dawgtools/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={'': 'src'},
    package_data={'dawgtools': package_data},
    packages=setuptools.find_packages(where="src"),
    entry_points={
        'console_scripts': ['dawgtools = dawgtools.main:main']
    },
    python_requires=">=3.9",
    install_requires=[
        'openai'
    ],
)
