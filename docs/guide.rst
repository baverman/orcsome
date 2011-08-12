Guide
=====

This guide will explain orcsome configure concepts.


Configuration script
--------------------

Orcsome is only tiny wrapper around xlib. You should provide needed
functionality by configuration script ``$HOME/.config/orcsome/rc.py``

The basic template is::

   from orcsome import get_wm
   from orcsome.actions import *

   wm = get_wm()

   # Your commands here

As you see it is a simple python file without any implicit magic.

For example (reference) you can look at my
`config <https://github.com/baverman/backup/blob/master/.config/orcsome/rc.py>`_.


Signal decorators
-----------------

The whole orcsome idea is built around signal decorators. What is it?
Signal decorators represent X events which will be handled by your wrapped
functions.

Some examples::

   # Define global hotkey
   @wm.on_key('Alt+Return')
   def start_terminal():
       print 'run terminal'

   # Handle window creation
   @wm.on_create
   def window_created():
       print 'window created', wm.event_window.get_wm_class()

   # Decorators can be nested to handle specific windows events
   @wm.on_key('Alt+1')
   def bind_additional_keys():

       @wm.on_key(wm.event_window, 'Alt+2')
       def custom_key():
           print 'This is a special Alt-tered window'
