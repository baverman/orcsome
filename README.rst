Orcsome is a scripting extension for NETWM compliant window managers. It can
help a lot to customize your work environment.


Motivation
----------

I'm old `awesome`_ user with two year experience. I like it not for tiling but
for lua and ability to tune its behavior. But for a very long time some problems
stay unsolved:

* Grey swing windows. I was hoping it will be fixed in java7 but no luck.
* Input focus for swing windows. Awesome treats such windows as inputless.
* Random focus problems. For example sometimes evince or opera save dialog are
  not take focus.

Simply put, awesome sucks as window manager.

I need a robust wm with long devel history, small, fast, candy and
**scriptable** on normal language (hello fvwm). But there are a plenty of
robust, small, fast and candy only wm's. There is no any scriptable.

So I decide to write tiny wm helper application which will be compatible with
many window managers and allow to configure flexible workflows.

.. _awesome: http://awesome.naquadah.org/

Features
--------

* Written on python. It means very hackable.

* Optimization, cpu and memory efficiency are top goals (cffi is used for xlib
  bindings).

* Extensive use of python syntax to provide easy and expressive eDSL in
  configuration script.

* Supports NETWM standards.

* Very thin wrapper around X. You can use existing xlib background.


Installation
------------

From PyPI
'''''''''

I'm regularly upload packages of new versions. So you can install orcsome with
``easy_install``::

   sudo easy_install orcsome

or `pip`_::

   sudo pip install orcsome


From source
'''''''''''

::

   git clone --depth=1 git://github.com/baverman/orcsome.git
   cd orcsome
   python setup.py build
   sudo python setup.py install

If you often pull changes from master brunch I recommend you following recipe:

* First install orcsome in develop mode (remove any orcsome dirs in site-packages
  before that)::

     sudo python setup.py develop

* Then, if you want use latest version from master branch simply do::

     cd cloned/orcsome/dir
     git pull


ArchLinux
'''''''''

There is orcsome package in AUR.

.. _pip: http://pip.openplans.org/


`Documentation <http://pythonhosted.org/orcsome/>`_
---------------------------------------------------

Quick start
'''''''''''

The most common functionality needed is to bind hot keys to spawn or raise
applications.

Edit ``~/.config/orcsome/rc.py``::

   from orcsome import get_wm
   from orcsome.actions import *

   wm = get_wm()

   wm.on_key('Shift+Mod+r')(
       restart)

   wm.on_key('Ctrl+Alt+p')(
       spawn_or_raise('urxvtc -name ncmpcpp -e ncmpcpp', name='ncmpcpp'))

   wm.on_key('Mod+n')(
       spawn_or_raise('urxvtc -name mutt -e mutt', name='mutt'))

   wm.on_key('Mod+k')(
       spawn_or_raise('urxvtc -name rtorrent -e rtorrent-screen', name='rtorrent'))

And start orcsome. That's all.


TODO
----

* Tests
* Python3 port
* API to configure window geometry
* Layouts (tiling)
* Multiple screens


Contacts
--------

You can create issues on `github <https://github.com/baverman/orcsome/issues>`_.

Or mail directly to bobrov at vl dot ru.
