import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from Window.main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon.fromTheme("media-playback-start"))
    win = MainWindow()
    if win.config:
        win.show()
    sys.exit(app.exec())
