from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QFormLayout, QLabel, QGridLayout, QPushButton, QFrame, QComboBox, QGroupBox, QSystemTrayIcon, \
                              QMenu
from PySide6.QtCore import QSize, Qt, QTimer, Slot, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtGui import QGuiApplication, QPalette, QColor, QIcon
from playsound import playsound
from datetime import datetime
from PySide6 import QtGui
import configparser
import requests
import random
import pickle
import sys
import os


def read_config():
    config = configparser.ConfigParser()
    config.optionxform = str

    if not os.path.exists('config.ini'):
        config['Settings'] = {'Adhan Sound': 0,
                              'Calculation Method': 5}

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


config = read_config()
window_size = QSize(420, 440)


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
            self.parent().resize(window_size)
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


class PyAdhan(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon('Resources/Icon.ico'))
        self.prayer_times = None

        # Structure
        self.prayer_times_body = QFormLayout()
        self.prayer_times_body.setHorizontalSpacing(255)

        self.prayer_times_container = QGroupBox()
        self.prayer_times_container.setTitle('Prayer Times')

        self.settings_body = QFormLayout()

        self.settings_container = QGroupBox()
        self.settings_container.setTitle('Settings')

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)

        # Components
        self.window_frame = CustomWindowFrame('PyAdhan', maximizable=False)

        self.counter_lb = QLabel()
        self.counter_lb.setStyleSheet('font-size: 60px')

        self.adhan_cbb = QComboBox()
        self.adhan_cbb.addItems(['Random'] + list(map(lambda a: a.split('.')[0], os.listdir('Resources/Adhan Sounds'))))
        self.adhan_cbb.setCurrentIndex(int(config['Settings']['Adhan Sound']))

        self.method_cbb = QComboBox()
        self.method_cbb.addItems(['University of Islamic Sciences, Karachi',
                                  'Islamic Society of North America',
                                  'Muslim World League',
                                  'Umm Al-Qura University, Makkah',
                                  'Egyptian General Authority of Survey',
                                  'Institute of Geophysics, University of Tehran',
                                  'Gulf Region',
                                  'Kuwait',
                                  'Qatar',
                                  'Majlis Ugama Islam Singapura, Singapore',
                                  'Union Organization islamic de France',
                                  'Diyanet İşleri Başkanlığı, Turkey',
                                  'Spiritual Administration of Muslims of Russia'])
        self.method_cbb.setCurrentIndex(int(config['Settings']['Calculation Method']))

        self.counter_timer = QTimer()
        self.counter_timer.start(1000)

        self.thread_pool = QThreadPool()

        # Functionality
        self.counter_timer.timeout.connect(self.checker)
        self.adhan_cbb.currentIndexChanged.connect(lambda i: config.set('Settings', 'Adhan Sound', str(i)))

        self.method_cbb.currentIndexChanged.connect(lambda i: config.set('Settings', 'Calculation Method', str(i)))
        self.method_cbb.currentIndexChanged.connect(self.update_prayer_times)

        # Assembly
        self.body.addWidget(self.window_frame)
        self.body.addWidget(self.counter_lb, alignment=Qt.AlignCenter)

        self.prayer_times_container.setLayout(self.prayer_times_body)
        self.body.addWidget(self.prayer_times_container, alignment=Qt.AlignCenter)

        self.settings_body.addRow('Adhan Sound', self.adhan_cbb)
        self.settings_body.addRow('Calculation Method', self.method_cbb)

        self.settings_container.setLayout(self.settings_body)
        self.body.addWidget(self.settings_container, alignment=Qt.AlignCenter)

        self.setLayout(self.body)

        self.get_prayer_times_month()
        self.checker()

    def get_prayer_times_month(self):
        prayer_times_month = None

        if os.path.isfile('Resources/CurrentMonthPrayerTimes.pkl'):

            with open('Resources/CurrentMonthPrayerTimes.pkl', 'rb') as f:
                prayer_times_month = pickle.load(f)

            if prayer_times_month.month == datetime.now().month:
                self.prayer_times = prayer_times_month.get_prayer_times(datetime.now().day)

        if prayer_times_month is None:
            res = requests.get('http://api.aladhan.com/v1/calendar', params={'latitude': 29.897322,
                                                                             'longitude': 31.081643,
                                                                             'month': datetime.now().month,
                                                                             'year': datetime.now().year,
                                                                             'method': int(config['Settings']['Calculation Method']) + 1})

            prayer_times_month = PrayerTimesMonth(res.json())
            with open('Resources/CurrentMonthPrayerTimes.pkl', 'wb') as f:
                pickle.dump(prayer_times_month, f)

        self.prayer_times = prayer_times_month.get_prayer_times(datetime.now().day)

        clear_layout(self.prayer_times_body)
        self.prayer_times_body.addRow('Fajr', QLabel(self.prayer_times[0]))
        self.prayer_times_body.addRow('Dhuhr', QLabel(self.prayer_times[1]))
        self.prayer_times_body.addRow('Asr', QLabel(self.prayer_times[2]))
        self.prayer_times_body.addRow('Maghrib', QLabel(self.prayer_times[3]))
        self.prayer_times_body.addRow('Isha', QLabel(self.prayer_times[4]))

    def update_prayer_times(self):

        if os.path.isfile('Resources/CurrentMonthPrayerTimes.pkl'):
            os.remove('Resources/CurrentMonthPrayerTimes.pkl')

        self.get_prayer_times_month()
        self.checker()

    def checker(self):
        current_time = datetime.now()

        next_prayer = 0
        for i in range(0, 5):
            prayer_time = datetime.strptime(self.prayer_times[i], '%I:%M %p')
            prayer_time = prayer_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)

            if (current_time.hour == prayer_time.hour) and (current_time.minute == prayer_time.minute) and (current_time.second == prayer_time.second):

                if self.adhan_cbb.currentText() == 'Random':
                    adhan_ind = random.choice(range(1, self.adhan_cbb.count()))
                    adhan_sound = self.adhan_cbb.itemText(adhan_ind)

                else:
                    adhan_sound = self.adhan_cbb.currentText()

                if not self.thread_pool.activeThreadCount():
                    self.thread_pool.start(Worker(playsound, 'Resources/Adhan Sounds/' + adhan_sound + '.mp3'))

            if current_time.time() < prayer_time.time():
                next_prayer = i
                break

        prayer_time = datetime.strptime(self.prayer_times[next_prayer], '%I:%M %p')
        prayer_time = prayer_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)

        if current_time < prayer_time:
            delta = prayer_time - current_time

        else:
            delta = current_time - prayer_time

        text = str(delta).split('.')[0]
        self.counter_lb.setText('-' + text)

        if next_prayer:
            next_prayer *= 2

        for i in range(2 * 5):

            if (i == next_prayer) or (i == next_prayer + 1):
                self.prayer_times_body.itemAt(i).widget().setStyleSheet('font-size: 15px; font-weight: bold')

            else:
                self.prayer_times_body.itemAt(i).widget().setStyleSheet('font-size: 15px')

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        update_config(config)
        sys.exit(1)


if '__main__' in __name__:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#353535"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#353535"))

    app = QApplication([])
    app.setStyle('Fusion')
    app.setPalette(palette)
    app.setStyleSheet('''QWidget {color: #ffffff}
                                 QWidget:!enabled {color: #808080}''')

    window = PyAdhan()
    window.resize(window_size)
    window.show()

    tray_icon = SystemTrayIcon(QtGui.QIcon("Resources/Icon.ico"), window)
    tray_icon.show()

    app.exec()