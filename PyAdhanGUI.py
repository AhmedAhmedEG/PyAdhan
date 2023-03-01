from Modules.Props import CustomWindowFrame, PrayerTimesMonth, clear_layout, Worker, update_config, read_config, SystemTrayIcon, app_version
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QFormLayout, QLabel, QComboBox, QGroupBox, QCheckBox
from PySide6.QtCore import QSize, Qt, QTimer, Slot, QThreadPool
from PySide6.QtGui import QPalette, QColor, QIcon
from datetime import datetime, timedelta
from win10toast import ToastNotifier
from playsound import playsound
from PySide6 import QtGui
import win32com.client
import win32com
import requests
import getpass
import random
import pickle
import sys
import os


class PyAdhan(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowIcon(QIcon('Resources/Icon.ico'))
        self.prayer_names = {0: 'Fajr', 1: 'Dhuhr', 2: 'Asr', 3: 'Maghrib', 4: 'Isha'}
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
        self.window_frame = CustomWindowFrame('PyAdhanGUI v' + app_version, maximizable=False)

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

        self.startup_cb = QCheckBox()
        self.startup_cb.setFixedSize(QSize(25, 25))
        self.startup_cb.setChecked(int(config['Settings']['Add To Startup']))

        self.counter_timer = QTimer()
        self.counter_timer.start(1000)

        self.thread_pool = QThreadPool()

        # Functionality
        self.counter_timer.timeout.connect(self.checker)
        self.adhan_cbb.currentIndexChanged.connect(lambda i: config.set('Settings', 'Adhan Sound', str(i)))
        self.adhan_cbb.currentIndexChanged.connect(lambda: update_config(config))

        self.method_cbb.currentIndexChanged.connect(lambda i: config.set('Settings', 'Calculation Method', str(i)))
        self.method_cbb.currentIndexChanged.connect(lambda: update_config(config))
        self.method_cbb.currentIndexChanged.connect(self.update_prayer_times)

        self.startup_cb.stateChanged.connect(lambda: config.set('Settings', 'Add To Startup', str(int(self.startup_cb.isChecked()))))
        self.startup_cb.stateChanged.connect(lambda: update_config(config))
        self.startup_cb.stateChanged.connect(self.switch_startup)

        # Assembly
        self.body.addWidget(self.window_frame)
        self.body.addWidget(self.counter_lb, alignment=Qt.AlignCenter)

        self.prayer_times_container.setLayout(self.prayer_times_body)
        self.body.addWidget(self.prayer_times_container, alignment=Qt.AlignCenter)

        self.settings_body.addRow('Adhan Sound', self.adhan_cbb)
        self.settings_body.addRow('Calculation Method', self.method_cbb)
        self.settings_body.addRow('Add To Startup', self.startup_cb)

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
        self.prayer_times_body.addRow(self.prayer_names[0], QLabel(self.prayer_times[0]))
        self.prayer_times_body.addRow(self.prayer_names[1], QLabel(self.prayer_times[1]))
        self.prayer_times_body.addRow(self.prayer_names[2], QLabel(self.prayer_times[2]))
        self.prayer_times_body.addRow(self.prayer_names[3], QLabel(self.prayer_times[3]))
        self.prayer_times_body.addRow(self.prayer_names[4], QLabel(self.prayer_times[4]))

    @Slot()
    def update_prayer_times(self):

        if os.path.isfile('Resources/CurrentMonthPrayerTimes.pkl'):
            os.remove('Resources/CurrentMonthPrayerTimes.pkl')

        self.get_prayer_times_month()
        self.checker()

    @Slot()
    def switch_startup(self):

        if not getattr(sys, "frozen", False):
            return

        path = f'C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/PyAdhanGUI.lnk'

        if self.startup_cb.isChecked():
            shell = win32com.client.Dispatch('WScript.Shell')

            shortcut = shell.CreateShortCut(path)
            shortcut.IconLocation = os.getcwd() + '/Resources/Icon.ico'
            shortcut.Targetpath = os.getcwd() + '/PyAdhanGUI.exe'

            shortcut.save()

        else:
            os.remove(path)

    @Slot()
    def checker(self):
        current_time = datetime.now()

        next_prayer = 0
        for i in range(0, 5):
            prayer_time = datetime.strptime(self.prayer_times[i], '%I:%M %p')
            prayer_time = prayer_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)

            if (current_time.hour, current_time.minute, current_time.second) == (prayer_time.hour, prayer_time.minute, prayer_time.second):

                if self.adhan_cbb.currentText() == 'Random':
                    adhan_ind = random.choice(range(1, self.adhan_cbb.count()))
                    adhan_sound = self.adhan_cbb.itemText(adhan_ind)

                else:
                    adhan_sound = self.adhan_cbb.currentText()

                if not self.thread_pool.activeThreadCount():
                    self.thread_pool.start(Worker(playsound, 'Resources/Adhan Sounds/' + adhan_sound + '.mp3'))
                    self.thread_pool.start(Worker(toast.show_toast, self.prayer_names[i], adhan_sound, duration=10, icon_path="Resources/Icon.ico"))

            if current_time.time() < prayer_time.time():
                next_prayer = i
                break

        prayer_time = datetime.strptime(self.prayer_times[next_prayer], '%I:%M %p')
        prayer_time = prayer_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)

        if current_time < prayer_time:
            delta = prayer_time - current_time

        else:

            if current_time.hour < 24:
                delta = prayer_time - current_time + timedelta(days=1)

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

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))

    toast = ToastNotifier()
    config = read_config()

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
    window.resize(QSize(420, 510))
    window.show()

    tray_icon = SystemTrayIcon(QtGui.QIcon("Resources/Icon.ico"), window)
    tray_icon.show()

    app.exec()
