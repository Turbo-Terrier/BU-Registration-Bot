import logging
from enum import Enum


class CustomFormatter(logging.Formatter):

    def format(self, record):
        log_fmt = self.color_formatter(record)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

    def color_formatter(self, record):
        level = record.levelname
        if level == 'CRITICAL':
            return f'{LogColors.GRAY.value}[%(asctime)s] {LogColors.BOLD_RED.value}[%(levelname)s] ' \
                   f'{LogColors.BACKGROUND_RED.value}%(message)s{LogColors.RESET.value}'
        elif level == 'ERROR':
            return f'{LogColors.GRAY.value}[%(asctime)s] {LogColors.BOLD_RED.value}[%(levelname)s] ' \
                   f'{LogColors.RED.value}%(message)s{LogColors.RESET.value}'
        elif level == 'WARNING':
            return f'{LogColors.GRAY.value}[%(asctime)s] {LogColors.BOLD_YELLOW.value}[%(levelname)s] ' \
                   f'{LogColors.YELLOW.value}%(message)s{LogColors.RESET.value}'
        elif level == 'INFO':
            return f'{LogColors.GRAY.value}[%(asctime)s] {LogColors.BOLD_BRIGHT_GREEN.value}[%(levelname)s] ' \
                   f'{LogColors.BRIGHT_GREEN.value}%(message)s{LogColors.RESET.value}'
        # Debugs
        else:
            return f'{LogColors.GRAY.value}[%(asctime)s] {LogColors.BOLD_WHITE.value}[%(levelname)s] ' \
                   f'{LogColors.WHITE.value}%(message)s{LogColors.RESET.value}'


class LogColors(Enum):
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    LIGHT_RED = '\033[91m'
    GREEN = '\033[32m'
    BRIGHT_GREEN = '\033[92m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    BRIGHT_BLUE = '\033[94m'
    PURPLE = '\033[35m'
    PINK = '\033[95m'
    CYAN = '\033[36m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    LIGHT_GRAY = '\033[37m'
    BOLD_BLACK = '\033[1;30m'
    BOLD_RED = '\033[1;31m'
    BOLD_LIGHT_RED = '\033[91;1m'
    BOLD_GREEN = '\033[1;32m'
    BOLD_BRIGHT_GREEN = '\033[1;92m'
    BOLD_YELLOW = '\033[1;33m'
    BOLD_BLUE = '\033[1;34m'
    BOLD_BRIGHT_BLUE = '\033[1;94m'
    BOLD_PURPLE = '\033[1;35m'
    BOLD_PINK = '\033[1;95m'
    BOLD_CYAN = '\033[1;36m'
    BOLD_WHITE = '\033[97;1m'
    BACKGROUND_BLACK = '\033[40m'
    BACKGROUND_RED = '\033[41m'
    BACKGROUND_GREEN = '\033[42m'
    BACKGROUND_YELLOW = '\033[43m'
    BACKGROUND_BLUE = '\033[44m'
    BACKGROUND_PURPLE = '\033[45m'
    BACKGROUND_CYAN = '\033[46m'
    BACKGROUND_WHITE = '\033[47m'
