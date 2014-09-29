from subprocess import Popen, PIPE

default_appname = 'orcsome'


def notify(summary, body, timeout=-1, urgency=1, appname=None):
    n = Notification(summary, body, timeout, urgency, appname or default_appname)
    n.show()
    return n


class Notification(object):
    def __init__(self, summary, body, timeout, urgency, appname):
        self.summary = summary.lstrip('-')
        self.body = body
        self.timeout = timeout
        self.urgency = urgency
        self.appname = appname
        self.replace_id = 0

    def show(self):
        timeout = int(self.timeout * 1000)
        if timeout < 0: timeout = -1

        urgency = '{}'
        if self.urgency != 1:
            urgency = "{'urgency': <byte %d>}" % self.urgency

        self.lastcmd = cmd = [
            'gdbus',
            'call',
            '--session',
            '--dest=org.freedesktop.Notifications',
            '--object-path=/org/freedesktop/Notifications',
            '--method=org.freedesktop.Notifications.Notify',
            self.appname,
            '{}'.format(self.replace_id),
            '',
            self.summary,
            self.body,
            '[]',
            urgency,
            '{}'.format(timeout),
        ]

        out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if err:
            raise Exception(err)

        self.replace_id = int(out.strip().split()[1].rstrip(',)'))

    def update(self, summary=None, body=None, timeout=None, urgency=None):
        if summary is not None:
            self.summary = summary

        if body is not None:
            self.body = body

        if timeout is not None:
            self.timeout = timeout

        if urgency is not None:
            self.urgency = urgency

        self.show()

    def close(self):
        cmd = [
            'gdbus',
            'call',
            '--session',
            '--dest=org.freedesktop.Notifications',
            '--object-path=/org/freedesktop/Notifications',
            '--method=org.freedesktop.Notifications.CloseNotification',
            '{}'.format(self.replace_id),
        ]

        _, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        if err:
            raise Exception(err)
