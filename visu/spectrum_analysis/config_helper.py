# libraries
import pathlib

from PyQt6.QtCore import QSettings

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config.ini"


def get_config():
    '''Return the config settings'''
    settings = QSettings(
        str(CONFIG_PATH), 
        QSettings.Format.IniFormat
    )
    return settings


def get_from_config(module: str, item: str, default_value = "", type = str):
    '''Get the 'item' stored in 'module' in the config file.'''
    settings = QSettings(
        str(CONFIG_PATH), 
        QSettings.Format.IniFormat
    )
    
    val = settings.value(
        f"{module}/{item}", 
        defaultValue=default_value, 
        type=type
    )

    return val


def set_in_config(module: str, item: str, val) -> None:
    '''Set the value of 'item' stored in 'module' in the config file.'''
    settings = QSettings(
        str(CONFIG_PATH), 
        QSettings.Format.IniFormat
    )

    settings.setValue(
        f"{module}/{item}",
        val
    )