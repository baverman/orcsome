class TestWM(object):
    def on_key(self, key):
        assert isinstance(key, basestring), 'First argument to on_key must be string'
        return lambda func: func

    def on_create(self, *args, **matchers):
        assert matchers or args

        if args:
            assert len(args) == 1
            return args[0]

        if matchers:
            possible_args = set(('cls', 'role', 'name', 'desktop'))
            assert possible_args.union(matchers) == possible_args, \
                'Invalid matcher, must be one of %s' % possible_args

        return lambda func: func

    def on_property_change(self, *args):
        assert all(isinstance(r, basestring) for r in args)
        return lambda func: func

    def on_destroy(self, window):
        return lambda func: func

    def on_init(self, func):
        return func

    def on_deinit(self, func):
        return func
