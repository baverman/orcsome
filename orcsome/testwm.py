from .utils import ActionCaller, Mixable

idfunc = lambda func: func


class TestWM(Mixable):
    def on_key(self, key):
        assert isinstance(key, basestring), 'First argument to on_key must be string'
        return ActionCaller(self, idfunc)

    def on_timer(self, period, start=True):
        return ActionCaller(self, idfunc)

    def on_create(self, *args, **matchers):
        assert matchers or args

        if args:
            assert len(args) == 1
            return args[0]

        if matchers:
            possible_args = set(('cls', 'role', 'name', 'title', 'desktop'))
            assert possible_args.union(matchers) == possible_args, \
                'Invalid matcher, must be one of %s' % possible_args

        return ActionCaller(self, idfunc)

    def on_manage(self, *args, **matchers):
        assert matchers or args

        if args:
            assert len(args) == 1
            return args[0]

        if matchers:
            possible_args = set(('cls', 'role', 'name', 'title', 'desktop'))
            assert possible_args.union(matchers) == possible_args, \
                'Invalid matcher, must be one of %s' % possible_args

        return ActionCaller(self, idfunc)

    def on_property_change(self, *args):
        assert all(isinstance(r, basestring) for r in args)
        return ActionCaller(self, idfunc)

    def on_destroy(self, window):
        return ActionCaller(self, idfunc)

    def on_init(self, func):
        return func

    def on_deinit(self, func):
        return func

    def close_window(self, window=None):
        pass
