from pathlib import Path

# restore the original config.php

config_string = None

def pytest_configure():
    global config_string
    with get_file_path('src/config.php').open("r") as config_file:
        config_string = config_file.read()

def pytest_unconfigure():
    with get_file_path('src/config.php').open("w") as config_file:
        config_file.write(config_string)

def get_file_path(path):
    path = Path(path) # if invoked via make in project root
    if path.exists():
        return path
    return Path(f'../{path}') # if invoked directly in the IDE