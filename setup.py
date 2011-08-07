from setuptools import setup, find_packages

setup(
    name     = 'orcsome',
    version  = '0.2.2',
    author   = 'Anton Bobrov',
    author_email = 'bobrov@vl.ru',
    description = 'NETWM compliant wm scripting extension',
    #long_description = open('README.rst').read(),
    zip_safe   = False,
    packages = find_packages(exclude=('tests', )),
    include_package_data = True,
    entry_points = {
        'gui_scripts': [
            'orcsome = orcsome.run:run',
        ]
    },
    url = 'http://github.com/baverman/orcsome',
    classifiers = [
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
    ],
)
