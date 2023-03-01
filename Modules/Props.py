from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSystemTrayIcon, QMenu
from PySide6.QtCore import QRunnable, Signal, QObject, Slot, QSize, Qt
from datetime import datetime
from PySide6.QtGui import QGuiApplication
from PySide6 import QtGui
import configparser
import os

app_version = '1.2.4.2'


def read_config():
    config = configparser.ConfigParser()
    config.optionxform = str

    if not os.path.exists('config.ini'):
        config['Settings'] = {'Adhan Sound': 0,
                              'Calculation Method': 4,
                              'Add To Startup': 0}

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    config.read('config.ini')
    return config


def update_config(c):

    with open('config.ini', 'w') as f:
        c.write(f)


def clear_layout(layout):

    while layout.count():
        child = layout.takeAt(0)

        if child.widget():
            child.widget().deleteLater()


class Worker(QObject, QRunnable):
    start = Signal(int)
    progress = Signal(int)
    operation = Signal(str)
    result = Signal(object)
    finished = Signal()
    close = Signal()

    def __init__(self, func=None, *args, **kwargs):
        QObject.__init__(self)
        QRunnable.__init__(self)

        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        self.func(*self.args, **self.kwargs)

    def set_func(self, func):
        self.func = func


class CustomWindowFrame(QWidget):

    def __init__(self, title, closable=True, maximizable=True, minimizable=True, movable=True):
        super().__init__()
        self.setFixedHeight(30)

        self.movable = movable

        self.mouse_offset = None
        self.grabbed = False

        # Structure
        self.title_body = QGridLayout()
        self.title_body.setContentsMargins(6, 0, 6, 0)

        self.title_container = QWidget()
        self.title_container.setFixedHeight(15)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 6, 0, 2)

        # Components
        self.title = QLabel(title)
        self.title.setStyleSheet('font-size: 12px')

        self.minimize_btn = QPushButton('–')
        self.minimize_btn.setFixedWidth(12)
        self.minimize_btn.setFlat(True)

        self.maximize_btn = QPushButton('❒')
        self.maximize_btn.setFixedWidth(12)
        self.maximize_btn.setFlat(True)

        self.exit_btn = QPushButton('X')
        self.exit_btn.setFixedWidth(12)
        self.exit_btn.setFlat(True)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Functionality
        self.minimize_btn.clicked.connect(self.minimize)
        self.maximize_btn.clicked.connect(self.maximize)
        self.exit_btn.clicked.connect(self.exit)

        # Assembly
        self.title_body.addWidget(self.title, 0, 0, alignment=Qt.AlignLeft)

        if minimizable:
            self.title_body.addWidget(self.minimize_btn, 0, 2, alignment=Qt.AlignRight)

        if maximizable:
            self.title_body.addWidget(self.maximize_btn, 0, 3, alignment=Qt.AlignRight)

        if closable:
            self.title_body.addWidget(self.exit_btn, 0, 4, alignment=Qt.AlignRight)

        self.title_body.setColumnStretch(1, 1)
        self.title_container.setLayout(self.title_body)

        self.body.addWidget(self.title_container)
        self.body.addWidget(self.separator)

        self.setLayout(self.body)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if not self.movable:
            return

        self.mouse_offset = event.pos()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(event)

        if not self.movable:
            return

        self.grabbed = False

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if not self.movable:
            return

        if not self.grabbed and event.y() < self.height() and self.mouse_offset.y() < self.height():
            self.grabbed = True

        if self.grabbed:
            x, y = event.globalX(), event.globalY()
            self.parent().move(x - self.mouse_offset.x(), y - self.mouse_offset.y())

    def minimize(self):
        self.parent().hide()

    def maximize(self):
        mw, mh = QGuiApplication.screens()[0].size().toTuple()

        if self.parent().size() == QSize(mw - 1, mh - 1):
            self.parent().resize(QSize(420, 510))
            self.parent().move(QGuiApplication.screens()[0].geometry().center() - self.parent().frameGeometry().center())

        else:
            self.parent().resize(QSize(mw - 1, mh - 1))
            self.parent().move(0, 0)

    def exit(self):
        self.parent().close()


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        menu = QMenu(parent)

        menu.addAction("Exit")
        menu.triggered.connect(parent.close)

        self.setContextMenu(menu)
        self.activated.connect(self.activate)

    def activate(self, reason):

        if reason != QSystemTrayIcon.ActivationReason.Trigger:

            if self.parent().isHidden():
                self.parent().show()

            else:
                self.parent().hide()


class PrayerTimesMonth:

    def __init__(self, data):
        self.data = data['data']
        self.month = datetime.now().month

    def get_prayer_times(self, day):
        prayer_times = self.data[day - 1]['timings']
        prayer_times = [prayer_times['Fajr'].split(' ')[0],
                        prayer_times['Dhuhr'].split(' ')[0],
                        prayer_times['Asr'].split(' ')[0],
                        prayer_times['Maghrib'].split(' ')[0],
                        prayer_times['Isha'].split(' ')[0]]

        for i, pt in enumerate(prayer_times):
            dt = datetime.strptime(pt, '%H:%M')
            prayer_times[i] = dt.strftime("%I:%M %p")

        return prayer_times