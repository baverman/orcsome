import cffi

ffi = cffi.FFI()

ffi.set_source('orcsome._ev', "#include <ev.h>", libraries=['ev'])

ffi.cdef("""
#define EVBACKEND_SELECT ...
#define EV_READ ...
#define EV_WRITE ...
#define EVBREAK_ALL ...

typedef ... ev_loop;

struct ev_loop *ev_loop_new (unsigned int flags);
void ev_loop_destroy (struct ev_loop*);
void ev_break (struct ev_loop*, int);
int ev_run (struct ev_loop*, int);

typedef struct { ...; } ev_io;
typedef void (*io_cb) (struct ev_loop*, ev_io*, int);
void ev_io_init(ev_io*, io_cb, int, int);
void ev_io_start(struct ev_loop*, ev_io*);
void ev_io_stop(struct ev_loop*, ev_io*);

typedef struct { ...; } ev_signal;
typedef void (*signal_cb) (struct ev_loop*, ev_signal*, int);
void ev_signal_init(ev_signal*, signal_cb, int);
void ev_signal_start(struct ev_loop*, ev_signal*);
void ev_signal_stop(struct ev_loop*, ev_signal*);

typedef double ev_tstamp;
typedef struct { ...; } ev_timer;
typedef void (*timer_cb) (struct ev_loop*, ev_timer*, int);
void ev_timer_init(ev_timer*, timer_cb, ev_tstamp, ev_tstamp);
void ev_timer_set(ev_timer*, ev_tstamp, ev_tstamp);
void ev_timer_start(struct ev_loop*, ev_timer*);
void ev_timer_again(struct ev_loop*, ev_timer*);
void ev_timer_stop(struct ev_loop*, ev_timer*);
ev_tstamp ev_timer_remaining(struct ev_loop*, ev_timer*);
""")

if __name__ == "__main__":
    ffi.compile(verbose=True)
