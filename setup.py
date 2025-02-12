from setuptools import setup, find_packages

setup(
    name="autobotAI_cache",  # Use lowercase for package name on PyPI
    version="1.0.0",
    description="A flexible and efficient caching library with support for multiple backends",
    author="ShunyEka Systems Private Limited",
    author_email="hello@shunyeka.com",
    packages=find_packages(),
    install_requires=[
        "pymongo",
        "pydantic",
        "python-dotenv",
        "redis",
    ],
    classifiers=[
        "License :: Other/Proprietary License" "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.11",
)
