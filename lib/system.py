import platform
import logging


def isWin() -> bool:
    if platform.system() == 'Windows':
        return True
    else:
        return False


def isLinux() -> bool:
    if platform.system() == 'Linux':
        return True
    else:
        return False


def isMac() -> bool:
    if platform.system() == 'Darwin':
        return True
    else:
        return False


if isWin():
    import winreg


def isWin10Dark() -> bool:
    '''
    'True' if Windows 10 is in dark theme, 'false' otherwise
    '''
    if isWin():
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize")
            theme = winreg.QueryValueEx(key, "AppsUseLightTheme")
            isDarkTheme = not bool(theme[0])
        except (FileNotFoundError, Exception) as e:
            logging.error(e)
            isDarkTheme = False
    else:
        isDarkTheme = True

    return isDarkTheme  # True if dark theme, False if light theme
