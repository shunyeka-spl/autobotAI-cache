from setuptools import setup, find_packages

setup(
    name="autobot_cache",
    version="0.1.0",
    description="A flexible and efficient caching library with support for multiple backends",
    author="Ritin Tiwari",
    author_email="ritintiwari417@gmail.com",
    url="https://github.com/ritin0204/autobot_cache",
    packages=find_packages(),
    install_requires=[
        "pymongo",
        "pydantic",
        "python-dotenv"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)

