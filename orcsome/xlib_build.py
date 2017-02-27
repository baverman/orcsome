import cffi

ffi = cffi.FFI()

ffi.set_source('orcsome._xlib', """
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/extensions/scrnsaver.h>
#include <X11/extensions/dpms.h>
#include <X11/extensions/XKB.h>
#include <X11/extensions/XKBstr.h>
""", libraries=['X11', 'Xss', 'Xext'])

ffi.cdef("""
    static const long StructureNotifyMask;
    static const long SubstructureNotifyMask;
    static const long SubstructureRedirectMask;
    static const long PropertyChangeMask;
    static const long FocusChangeMask;

    static const long CurrentTime;

    static const int KeyPress;
    static const int KeyRelease;
    static const int CreateNotify;
    static const int DestroyNotify;
    static const int FocusIn;
    static const int FocusOut;
    static const int PropertyNotify;
    static const int ClientMessage;

    static const int CWX;
    static const int CWY;
    static const int CWWidth;
    static const int CWHeight;
    static const int CWBorderWidth;
    static const int CWSibling;
    static const int CWStackMode;

    static const int Above;
    static const int Below;

    static const int ShiftMask;
    static const int LockMask;
    static const int ControlMask;
    static const int Mod1Mask;
    static const int Mod2Mask;
    static const int Mod3Mask;
    static const int Mod4Mask;
    static const int Mod5Mask;
    static const int AnyKey;
    static const int AnyModifier;

    static const long NoSymbol;

    static const int GrabModeSync;
    static const int GrabModeAsync;

    static const int PropModeReplace;
    static const int PropModePrepend;
    static const int PropModeAppend;

    static const int XkbUseCoreKbd;


    typedef int Bool;
    typedef int Status;
    typedef unsigned long XID;
    typedef unsigned long Time;
    typedef unsigned long Atom;
    typedef XID Window;
    typedef XID Drawable;
    typedef XID KeySym;
    typedef XID Cursor;
    typedef unsigned char KeyCode;
    typedef ... Display;

    typedef struct {
            int type;
            unsigned long serial;	/* # of last request processed by server */
            Bool send_event;	/* true if this came from a SendEvent request */
            Display *display;/* Display the event was read from */
            Window window;	/* window on which event was requested in event mask */
    } XAnyEvent;

    typedef struct {
            int type;
            unsigned long serial;   /* # of last request processed by server */
            Bool send_event;        /* true if this came from a SendEvent request */
            Display *display;       /* Display the event was read from */
            Window window;
            Atom message_type;
            int format;
            union {
                    char b[20];
                    short s[10];
                    long l[5];
                    } data;
    } XClientMessageEvent;

    typedef struct {
            int type;               /* of event */
            unsigned long serial;   /* # of last request processed by server */
            Bool send_event;        /* true if this came from a SendEvent request */
            Display *display;       /* Display the event was read from */
            Window window;          /* "event" window it is reported relative to */
            Window root;            /* root window that the event occurred on */
            Window subwindow;       /* child window */
            Time time;              /* milliseconds */
            int x, y;               /* pointer x, y coordinates in event window */
            int x_root, y_root;     /* coordinates relative to root */
            unsigned int state;     /* key or button mask */
            unsigned int keycode;   /* detail */
            Bool same_screen;       /* same screen flag */
    } XKeyEvent;

    typedef struct {
            int type;
            unsigned long serial;	/* # of last request processed by server */
            Bool send_event;	/* true if this came from a SendEvent request */
            Display *display;	/* Display the event was read from */
            Window parent;	/* parent of the window */
            Window window;	/* window id of window created */
            int x, y;		/* window location */
            int width, height;	/* size of window */
            int border_width;	/* border width */
            Bool override_redirect;	/* creation should be overridden */
    } XCreateWindowEvent;

    typedef struct {
            int type;
            unsigned long serial;	/* # of last request processed by server */
            Bool send_event;	/* true if this came from a SendEvent request */
            Display *display;	/* Display the event was read from */
            Window event;
            Window window;
    } XDestroyWindowEvent;

    typedef struct {
            int type;		/* FocusIn or FocusOut */
            unsigned long serial;	/* # of last request processed by server */
            Bool send_event;	/* true if this came from a SendEvent request */
            Display *display;	/* Display the event was read from */
            Window window;	/* window of event */
            int mode;		/* NotifyNormal, NotifyWhileGrabbed,
                                       NotifyGrab, NotifyUngrab */
            int detail;
            /*
             * NotifyAncestor, NotifyVirtual, NotifyInferior,
             * NotifyNonlinear,NotifyNonlinearVirtual, NotifyPointer,
             * NotifyPointerRoot, NotifyDetailNone
             */
    } XFocusChangeEvent;

    typedef struct {
            int type;
            unsigned long serial;	/* # of last request processed by server */
            Bool send_event;	/* true if this came from a SendEvent request */
            Display *display;	/* Display the event was read from */
            Window window;
            Atom atom;
            Time time;
            int state;		/* NewValue, Deleted */
    } XPropertyEvent;

    typedef union {
        int type;
        XAnyEvent xany;
        XKeyEvent xkey;
        XCreateWindowEvent xcreatewindow;
        XDestroyWindowEvent xdestroywindow;
        XFocusChangeEvent xfocus;
        XPropertyEvent xproperty;
        ...;
    } XEvent;

    typedef struct {
        int x, y;
        int width, height;
        int border_width;
        Window sibling;
        int stack_mode;
    } XWindowChanges;

    typedef struct {
           Window window;
           int state;
           int kind;
           unsigned long til_or_since;
           unsigned long idle;
           unsigned long eventMask;
    } XScreenSaverInfo;

    typedef struct {
            int type;
            Display *display;	/* Display the event was read from */
            XID resourceid;		/* resource id */
            unsigned long serial;	/* serial number of failed request */
            unsigned char error_code;	/* error code of failed request */
            unsigned char request_code;	/* Major op-code of failed request */
            unsigned char minor_code;	/* Minor op-code of failed request */
    } XErrorEvent;
    typedef int (*XErrorHandler) ( Display* display, XErrorEvent* event);
    int XGetErrorText(Display *display, int code, char *buffer_return, int length);


    XErrorHandler XSetErrorHandler (XErrorHandler handler);

    Display* XOpenDisplay(char *display_name);
    int XCloseDisplay(Display *display);
    int XFree(void *data);
    Atom XInternAtom(Display *display, char *atom_name, Bool only_if_exists);

    int XPending(Display *display);
    int XNextEvent(Display *display, XEvent *event_return);
    int XSelectInput(Display *display, Window w, long event_mask);
    int XFlush(Display *display);
    int XSync(Display *display, Bool discard);
    Status XSendEvent(Display *display, Window w, Bool propagate, long event_mask, XEvent *event_send);

    KeySym XStringToKeysym(char *string);
    KeyCode XKeysymToKeycode(Display *display, KeySym keysym);

    int XGrabKey(Display *display, int keycode, unsigned int modifiers,
        Window grab_window, Bool owner_events, int pointer_mode, int keyboard_mode);
    int XUngrabKey(Display *display, int keycode, unsigned int modifiers, Window grab_window);
    int XGrabKeyboard(Display *display, Window grab_window, Bool owner_events,
        int pointer_mode, int keyboard_mode, Time time);
    int XUngrabKeyboard(Display *display, Time time);
    int XGrabPointer(Display *display, Window grab_window, Bool owner_events,
        unsigned int event_mask, int pointer_mode, int keyboard_mode,
            Window confine_to, Cursor cursor, Time time);
    int XUngrabPointer(Display *display, Time time);

    int XGetWindowProperty(Display *display, Window w, Atom property,
        long long_offset, long long_length, Bool delete, Atom req_type,
        Atom *actual_type_return, int *actual_format_return,
        unsigned long *nitems_return, unsigned long *bytes_after_return,
        unsigned char **prop_return);
    int XChangeProperty(Display *display, Window w, Atom property, Atom type,
        int format, int mode, unsigned char *data, int nelements);
    int XDeleteProperty(Display *display, Window w, Atom property);
    int XConfigureWindow(Display *display, Window w, unsigned int value_mask,
        XWindowChanges *changes);

    Status XGetGeometry(Display *display, Drawable d, Window *root_return,
        int *x_return, int *y_return, unsigned int *width_return,
        unsigned int *height_return, unsigned int *border_width_return, unsigned int *depth_return);

    Status XScreenSaverQueryInfo(Display *dpy, Drawable drawable, XScreenSaverInfo *saver_info);

    Status DPMSInfo (Display *display, unsigned short *power_level, unsigned char *state);
    Status DPMSEnable (Display *display);
    Status DPMSDisable (Display *display);

    Window DefaultRootWindow(Display *display);
    int ConnectionNumber(Display *display);

    typedef struct {
            unsigned char	group;
            unsigned char   locked_group;
            unsigned short	base_group;
            unsigned short	latched_group;
            unsigned char	mods;
            unsigned char	base_mods;
            unsigned char	latched_mods;
            unsigned char	locked_mods;
            unsigned char	compat_state;
            unsigned char	grab_mods;
            unsigned char	compat_grab_mods;
            unsigned char	lookup_mods;
            unsigned char	compat_lookup_mods;
            unsigned short	ptr_buttons;
    } XkbStateRec;

    Status XkbGetState (Display *display, unsigned int device_spec, XkbStateRec *state_return);
    Bool XkbLockGroup (Display *display, unsigned int device_spec, unsigned int group);
""")

if __name__ == "__main__":
    ffi.compile(verbose=True)
