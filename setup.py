from setuptools import setup, find_packages
from orcsome import VERSION
from setuptools.command import easy_install

def install_script(self, dist, script_name, script_text, dev_path=None):
    script_text = easy_install.get_script_header(script_text) + (
        ''.join(script_text.splitlines(True)[1:]))

    self.write_script(script_name, script_text, 'b')

easy_install.easy_install.install_script = install_script

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
    scripts = ['bin/orcsome'],
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
