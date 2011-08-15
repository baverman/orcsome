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

For example (reference) you can look at my
`config <https://github.com/baverman/backup/blob/master/.config/orcsome/rc.py>`_.

As you see it is a simple python file without any implicit magic.


Signal decorators
-----------------

The whole orcsome idea is built around signal decorators. What it is?
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

Here is the list of available signal decorators:

* :meth:`~orcsome.core.WM.on_create`
* :meth:`~orcsome.core.WM.on_destroy`
* :meth:`~orcsome.core.WM.on_key`
* :meth:`~orcsome.core.WM.on_property_change`

Signal handlers removing
************************

Sometimes you may need to remove signal handler. Just call ``remove()`` on
wrapped function::

   @wm.on_create
   def switch_to_desktop():
       # We are interested in freshly created windows only
       if not wm.startup:
           if wm.activate_window_desktop(wm.event_window) is None:

               # Subscribe to _NET_WM_DESKTOP property change
               @wm.on_property_change(wm.event_window, '_NET_WM_DESKTOP')
               def property_was_set():
                   wm.activate_window_desktop(wm.event_window)

                   # Ok. Handler was called and can be removed
                   property_was_set.remove()


Actions
-------

Actions are signal handler generators which provide shorthand way to do some
tasks::

   # Start xterm
   wm.on_key('Mod+Return')(
       spawn('xterm'))

Is equivalent to::

   @wm.on_key('Mod+Return'):
   def start_xterm():
       # Take note: Parentheses after ``spawn`` call is
       # important. Action will not be executed without it.
       spawn('xterm')()

:doc:`Here <actions>` is the list of builtin actions.