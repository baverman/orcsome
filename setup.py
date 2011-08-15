from setuptools import setup, find_packages
from orcsome import VERSION

setup(
    name     = 'orcsome',
    version  = VERSION,
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Scripting extension for NETWM compliant window managers',
    long_description = open('README.rst').read(),
    zip_safe   = False,
    packages = find_packages(exclude=('tests', )),
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'orcsome = orcsome.run:run',
        ]
    },
    url = 'http://github.com/baverman/orcsome',
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications",
        "Topic :: Desktop Environment :: Window Managers",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
    ],
)
