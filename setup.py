from setuptools import setup, find_packages

import orcsome
import orcsome.xlib

setup(
    name     = 'orcsome',
    version  = orcsome.VERSION,
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Scripting extension for NETWM compliant window managers',
    long_description = open('README.rst').read(),
    zip_safe   = False,
    packages = find_packages(exclude=('tests', )),
    ext_modules=[orcsome.xlib.ffi.verifier.get_extension()],
    download_url = 'https://github.com/baverman/orcsome/archive/{}.zip'.format(orcsome.VERSION),
    install_requires = ['cffi'],
    include_package_data = True,
    scripts = ['bin/orcsome'],
    url = 'http://github.com/baverman/orcsome',
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications",
        "Topic :: Desktop Environment :: Window Managers",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
    ],
)
