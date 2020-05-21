from PyQt5 import QtWidgets
import sys


def get_screen_dimensions():
    """
    Grabs the user's screen dimensions and calculates draw space for app window
    :return: x and y coordinates to draw window in middle of screen
    """
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_width, screen_height = screen.size().width(), screen.size().height()

    return screen_width / 2, screen_height / 2
