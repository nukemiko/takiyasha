import os

with open(os.path.join(os.path.dirname(__file__), 'VERSION'), encoding='UTF-8') as f:
    __version__: str = f.read().strip()


def version() -> str:
    return __version__
