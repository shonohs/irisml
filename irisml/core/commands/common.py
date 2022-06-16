import logging
import sys


class ColoredStreamHandler(logging.StreamHandler):
    def __init__(self, stream=None, colorscheme=None):
        super().__init__(stream)
        self._colorscheme = colorscheme

    def emit(self, record):
        try:
            msg = self.format(record)
            msg = self._add_color(msg, record.levelno)
            self.stream.write(msg + self.terminator)
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)

    def _add_color(self, msg, levelno):
        color_code = self._colorscheme.get(levelno, '\x1b[0m')
        return color_code + msg + '\x1b[0m'


LOG_COLORS = {
    logging.CRITICAL: '\x1b[91;101m',
    logging.ERROR: '\x1b[101m',
    logging.WARNING: '\x1b[33;20m',
    logging.INFO: '',
    logging.DEBUG: '\x1b[36m'
}


def configure_logger(verbose_level=0):
    """Configure logging handlers. Show logs in color if the stdout is connected to a terminal.

       Args:
           verbose_level (int): 0: No DEBUG logs. 1: DEBUG logs only from irisml. 2: DEBUG logs from all modules.
    """
    handler = ColoredStreamHandler(colorscheme=LOG_COLORS) if sys.stdout.isatty() else logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s (%(name)s)')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose_level >= 2 else logging.INFO)
    logger.addHandler(handler)

    # Suppress noisy logs
    logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)

    if verbose_level >= 1:
        logging.getLogger('irisml').setLevel(logging.DEBUG)
