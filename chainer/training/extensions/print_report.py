import os
import sys

from chainer.training import extension
from chainer.training.extensions import log_report as log_report_module
from chainer.training.extensions import util


class PrintReport(extension.Extension):

    """Trainer extension to print the accumulated results.

    This extension uses the log accumulated by a :class:`LogReport` extension
    to print specified entries of the log in a human-readable format.

    Args:
        entries (list of str): List of keys of observations to print.
        log_report (str or LogReport): Log report to accumulate the
            observations. This is either the name of a LogReport extensions
            registered to the trainer, or a LogReport instance to use
            internally.
        out: Stream to print the bar. Standard output is used by default.

    """

    def __init__(self, entries=None, log_report='LogReport', out=sys.stdout):
        self._entries = entries
        self._log_report = log_report
        self._out = out

        self._log_len = 0  # number of observations already printed

    def __call__(self, trainer):
        out = self._out

        # delete the printed contents from the current cursor
        out.write('\033[J')

        log_report = self._log_report
        if isinstance(log_report, str):
            log_report = trainer.get_extension(log_report)
        elif isinstance(log_report, log_report_module.LogReport):
            log_report(trainer)  # update the log report
        else:
            raise TypeError('log report has a wrong type %s' %
                            type(log_report))

        log = log_report.log
        log_len = self._log_len

        if log_len == 0:

            if self._entries is None:
                def key(heading):
                    if heading[:4] == 'dev/':
                        return heading[4:] + '*'
                    return heading
                entries = sorted(list(log[0].keys()), key=key)
            else:
                entries = self._entries

            # format information
            entry_widths = [max(10, len(s)) for s in entries]

            out.write('  '.join(('{:%d}' % w for w in entry_widths)).format(
                *entries) + '\n')

            templates = []
            for entry, w in zip(entries, entry_widths):
                templates.append((entry, '{:<%dg}  ' % w, ' ' * (w + 2)))
            self._templates = templates

        while len(log) > log_len:
            # delete the printed contents from the current cursor
            if os.name == 'nt':
                util.erase_console(0, 0)
            else:
                out.write('\033[J')
            self._print(log[log_len])
            log_len += 1
        self._log_len = log_len

    def serialize(self, serializer):
        log_report = self._log_report
        if isinstance(log_report, log_report_module.LogReport):
            log_report.serialize(serializer['_log_report'])

    def _print(self, observation):
        out = self._out
        for entry, template, empty in self._templates:
            if entry in observation:
                out.write(template.format(observation[entry]))
            else:
                out.write(empty)
        out.write('\n')
