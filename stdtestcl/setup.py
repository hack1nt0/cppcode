from setuptools import setup
import glob

setup(
    name='stdtest',
    version='0.0.1',
    package_dir={"stdtest": "src/stdtest"},
    package_data={"sdttest": ['db/*.sql']},
    entry_points={
        'console_scripts': [
            'task=stdtest.__main__:main',
            'run=stdtest.__main__:main2',
            'stdtest=stdtest.tui.__main__:main',
        ]
    },
    install_requires=[
        "psutil",
        "aiofiles",
        "beautifulsoup4",
        "matplotlib",
        "jupyter",
        "nbconvert",
        "graphviz",
    ],
    
)