from setuptools import setup, find_packages

import orcsome

setup(
    name     = 'orcsome',
    version  = orcsome.VERSION,
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'Scripting extension for NETWM compliant window managers',
    long_description = open('README.rst').read(),
    zip_safe = False,
    packages = find_packages(exclude=('tests', )),
    cffi_modules=["orcsome/ev_build.py:ffi", "orcsome/xlib_build.py:ffi"],
    setup_requires=["cffi>=1.0.0"],
    install_requires = ['cffi>=1.0.0'],
    include_package_data = True,
    scripts = ['bin/orcsome'],
    url = 'https://github.com/baverman/orcsome',
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
