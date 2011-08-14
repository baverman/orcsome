from Xlib.protocol import rq

EXTENSION = 'MIT-SCREEN-SAVER'

class QueryInfo(rq.ReplyRequest):
    _request = rq.Struct(
        rq.Card8('opcode'),
        rq.Opcode(1),
        rq.RequestLength(),
        rq.Window('window'),
        )
    _reply = rq.Struct(
        rq.Card8('state'),
        rq.Pad(1),
        rq.Card16('sequence_number'),
        rq.Pad(4),
        rq.Window('window'),
        rq.Card32('til_or_since'),
        rq.Card32('idle'),
        rq.Card32('event_mask'),
        rq.Card8('kind'),
        rq.Pad(7)
        )


def init(display):
    info = display.query_extension(EXTENSION)
    if info.present:
        MAJOR_OPCODE = info.major_opcode

        display.extension_add_method('window', 'get_screen_saver_info',
            lambda self: QueryInfo(display=self.display, opcode=MAJOR_OPCODE, window=self.id))

        return True

    return False