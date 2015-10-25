from . utils import cached_property, match_string
from . import xlib as X


class Window(int):
    @cached_property
    def desktop(self):
        """Return window desktop.

        Result is:

        * number from 0 to desktop_count - 1
        * -1 if window placed on all desktops
        * None if window does not have desktop property

        """
        d = self.get_property('_NET_WM_DESKTOP')
        if d:
            d = d[0]
            if d == 0xffffffff:
                return -1
            else:
                return d

    @cached_property
    def role(self):
        """Return WM_WINDOW_ROLE property"""
        return self.get_property('WM_WINDOW_ROLE', 'STRING')

    def get_name_and_class(self):
        """Return WM_CLASS property"""
        result = self.get_property('WM_CLASS', 'STRING', split=True)
        if not result:
            return None, None

        return result

    @cached_property
    def cls(self):
        """Return second part from WM_CLASS property"""
        self.name, cls = self.get_name_and_class()
        return cls

    @cached_property
    def name(self):
        """Return first part from WM_CLASS property"""
        name, self.cls = self.get_name_and_class()
        return name

    @cached_property
    def title(self):
        """Return _NET_WM_NAME property"""
        return self.get_property('_NET_WM_NAME', 'UTF8_STRING')

    def matches(self, name=None, cls=None, role=None, desktop=None, title=None):
        """Check if window suits given matchers.

        Matchers keyword arguments are used in :meth:`on_create`,
        :func:`~orcsome.actions.spawn_or_raise`. :meth:`find_clients` and
        :meth:`find_client`.

        name
          window name (also referenced as `instance`).
          The first part of ``WM_CLASS`` property.

        cls
          window class. The second part of ``WM_CLASS`` property.

        role
          window role. Value of ``WM_WINDOW_ROLE`` property.

        desktop
          matches windows placed on specific desktop. Must be int.

        title
          window title.

        `name`, `cls`, `title` and `role` can be regular expressions.

        """
        if name and not match_string(name, self.name): return False
        if cls and not match_string(cls, self.cls): return False
        if role and not match_string(role, self.role): return False
        if title and not match_string(title, self.title): return False
        if desktop is not None and desktop != self.desktop: return False

        return True

    @cached_property
    def state(self):
        """Return _NET_WM_STATE"""
        return self.get_property('_NET_WM_STATE', 'ATOM') or []

    def get_property(self, property, type=None, **kwargs):
        atom = self.wm.atom
        return X.get_window_property(self.wm.dpy, self, atom[property],
            atom[type] if type else 0, **kwargs)

    @cached_property
    def maximized_vert(self):
        return self.wm.atom['_NET_WM_STATE_MAXIMIZED_VERT'] in self.state

    @cached_property
    def maximized_horz(self):
        return self.wm.atom['_NET_WM_STATE_MAXIMIZED_HORZ'] in self.state

    @cached_property
    def decorated(self):
        return self.wm.atom[self.wm.undecorated_atom_name] not in self.state

    @cached_property
    def urgent(self):
        return self.wm.atom['_NET_WM_STATE_DEMANDS_ATTENTION'] in self.state

    @cached_property
    def fullscreen(self):
        return self.wm.atom['_NET_WM_STATE_FULLSCREEN'] in self.state
