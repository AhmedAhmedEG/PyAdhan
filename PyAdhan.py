from PySide6.QtWidgets import (QWidget, QApplication, QVBoxLayout, QFormLayout, QLabel, QComboBox, QGroupBox, QCheckBox,
                               QSpinBox, QTabWidget)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon

from Modules.Utils import (PrayerTimesMonth, clear_layout, CustomSystemTrayIcon, ModernMainWindow, get_palette,
                           ModernTabWidget)
from Modules.Config import Config

from datetime import datetime, timedelta
from pathlib import Path
import getpass
import random
import pickle
import sys
import os

import win32com.client
import win32com

import public_ip
import requests


class HomeTab(QWidget):

    def __init__(self):
        super().__init__()
        self.prayer_names = {0: 'Fajr', 1: 'Dhuhr', 2: 'Asr', 3: 'Maghrib', 4: 'Isha'}
        self.today_prayer_times = None

        self.audio_output = QAudioOutput()

        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        # Structure
        self.prayer_times_body = QFormLayout()
        self.prayer_times_body.setHorizontalSpacing(240)

        self.prayer_times_container = QGroupBox()
        self.prayer_times_container.setTitle('Prayer Times')

        self.body = QVBoxLayout()
        self.body.setContentsMargins(4, 4, 4, 4)

        # Components
        self.counter_lb = QLabel()
        self.counter_lb.setStyleSheet('font-size: 65px; font-weight: 600')

        self.counter_timer = QTimer()
        self.counter_timer.setInterval(1000)

        # Assembly
        self.body.addWidget(self.counter_lb, alignment=Qt.AlignmentFlag.AlignCenter)

        self.prayer_times_container.setLayout(self.prayer_times_body)
        self.body.addWidget(self.prayer_times_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.body)

        # Functionality
        self.counter_timer.timeout.connect(lambda: self.tick())

        # Initialization
        self.counter_timer.start()
        self.update_prayer_times()

    def update_prayer_times(self, reset=False):
        prayer_times_month = None
        loaded = False

        if not reset and os.path.isfile('Resources/PrayerTimesMonth.pkl'):

            with open('Resources/PrayerTimesMonth.pkl', 'rb') as f:
                prayer_times_month = pickle.load(f)

            if prayer_times_month.month == datetime.now().month:
                self.today_prayer_times = prayer_times_month.get_prayer_times(datetime.now().day)
                loaded = True

        if not loaded:

            try:
                requests.get(f'http://www.google.com')

            except Exception as e:
                print(e)
                return

            res = requests.get(f'http://ip-api.com/json/{public_ip.get()}')
            ip_geo_json = res.json()

            params = {
                'latitude': ip_geo_json['lat'],
                'longitude': ip_geo_json['lon']
            }

            if int(config.settings['General']['Calculation Method']):
                params['method'] = int(config.settings['General']['Calculation Method'])

            res = requests.get(
                f'https://api.aladhan.com/v1/calendar/{datetime.now().year}/{datetime.now().month}',
                params=params
            )

            adhan_json = res.json()

            prayer_times_month = PrayerTimesMonth(adhan_json)
            with open('Resources/PrayerTimesMonth.pkl', 'wb') as f:
                pickle.dump(prayer_times_month, f)

        self.today_prayer_times = prayer_times_month.get_prayer_times(datetime.now().day)

        clear_layout(self.prayer_times_body)

        self.prayer_times_body.addRow(self.prayer_names[0], QLabel(self.today_prayer_times[0].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[1], QLabel(self.today_prayer_times[1].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[2], QLabel(self.today_prayer_times[2].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[3], QLabel(self.today_prayer_times[3].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[4], QLabel(self.today_prayer_times[4].strftime("%I:%M %p")))

    def tick(self):

        current_time = datetime.now()
        if (current_time.hour == 24) and (current_time.minute == 60) and (current_time.second == 60):
            self.update_prayer_times()

        next_prayer = 0
        for i in range(0, 5):
            prayer_time = self.today_prayer_times[i]
            adhan_reminder = int(config.settings['General']['Adhan Reminder'])

            if adhan_reminder:
                reminder_time = prayer_time - timedelta(minutes=adhan_reminder)

                if self.equale_times(current_time, reminder_time):
                    config.tray_icon.showMessage(f'{self.prayer_names[i]} Reminder',
                                                 f'{self.prayer_names[i]} After {adhan_reminder} Minutes',
                                                 QIcon("Resources/Icon.png"))

                    audio_output = [ad for ad in QMediaDevices.audioOutputs() if
                                    ad.description() == config.settings['General']['Audio Output']][0]
                    self.audio_output.setDevice(audio_output)

                    self.player.setSource(f'file:Resources/Alarm.mp3')
                    self.player.play()

            if self.equale_times(current_time, prayer_time):

                if self.player.isPlaying():
                    return

                adhan_caller = int(config.settings['General']['Adhan Caller'])

                if adhan_caller == 0:
                    adhan_caller = random.choice(range(1, len(config.ADHAN_CALLERS)))

                adhan_sound = config.ADHAN_CALLERS[adhan_caller]
                config.tray_icon.showMessage(f'{self.prayer_names[i]} Is Calling',
                                             adhan_sound,
                                             QIcon("Resources/Icon.png"))

                audio_output = [ad for ad in QMediaDevices.audioOutputs() if
                                ad.description() == config.settings['General']['Audio Output']][0]
                self.audio_output.setDevice(audio_output)

                self.player.setSource(f'file:Resources/Adhan Callers/{adhan_sound}.mp3')
                self.player.play()

            if current_time.time() < prayer_time.time():
                next_prayer = i
                break

        prayer_time = self.today_prayer_times[next_prayer]
        if current_time < prayer_time:
            delta = prayer_time - current_time

        else:

            if current_time.hour < 24:
                delta = prayer_time - current_time + timedelta(days=1)

            else:
                delta = current_time - prayer_time

        ts = delta.seconds
        m, s = divmod(ts, 60)
        h, m = divmod(m, 60)
        self.counter_lb.setText(f'-{h:02}:{m:02}:{s:02}')

        if next_prayer:
            next_prayer *= 2

        for i in range(2 * 5):

            if (i == next_prayer) or (i == next_prayer + 1):
                self.prayer_times_body.itemAt(i).widget().setStyleSheet('font-size: 25px; font-weight: bold; color: green')

            else:
                self.prayer_times_body.itemAt(i).widget().setStyleSheet('font-size: 25px')

    @staticmethod
    def equale_times(dt1, dt2):
        return (dt1.hour, dt1.minute, dt1.second) == (dt2.hour, dt2.minute, dt2.second)


class SettingsTab(QWidget):
    method_changed = Signal()

    def __init__(self):
        super().__init__()

        # Structure
        self.preferences_body = QFormLayout()
        self.preferences_body.setHorizontalSpacing(40)

        self.preferences_container = QGroupBox()
        self.preferences_container.setTitle('Preferences')

        self.settings_body = QFormLayout()
        self.settings_body.setHorizontalSpacing(40)

        self.settings_container = QGroupBox()
        self.settings_container.setTitle('Options')

        self.body = QVBoxLayout()

        # Components
        self.audio_output_cbb = QComboBox()
        self.audio_output_cbb.addItems([ad.description() for ad in QMediaDevices.audioOutputs()])
        self.check_audio_devices()
        
        self.adhan_caller_cbb = QComboBox()
        self.adhan_caller_cbb.addItems(config.ADHAN_CALLERS)
        self.adhan_caller_cbb.setCurrentIndex(int(config.settings['General']['Adhan Caller']))

        self.adhan_reminder_sb = QSpinBox()
        self.adhan_reminder_sb.setMaximum(60)
        self.adhan_reminder_sb.setValue(int(config.settings['General']['Adhan Reminder']))

        self.method_cbb = QComboBox()
        self.method_cbb.addItems(config.CALC_METHODS)
        self.method_cbb.setCurrentIndex(int(config.settings['General']['Calculation Method']))

        self.startup_cb = QCheckBox()
        self.startup_cb.setChecked(self.check_startup())
        self.startup_cb.setMinimumSize(25, 25)

        self.always_on_top_cb = QCheckBox()
        self.always_on_top_cb.setChecked(int(config.settings['General']['Always On Top']))
        self.always_on_top_cb.setMinimumSize(25, 25)

        # Assembly
        self.preferences_body.addRow('Audio Output', self.audio_output_cbb)
        self.preferences_body.addRow('Adhan Caller', self.adhan_caller_cbb)
        self.preferences_body.addRow('Adhan Reminder (Minutes)', self.adhan_reminder_sb)

        self.preferences_container.setLayout(self.preferences_body)
        self.body.addWidget(self.preferences_container)

        self.settings_body.addRow('Calculation Method', self.method_cbb)
        self.settings_body.addRow('Add To Startup', self.startup_cb)
        self.settings_body.addRow('Always On Top', self.always_on_top_cb)

        self.settings_container.setLayout(self.settings_body)
        self.body.addWidget(self.settings_container)

        self.setLayout(self.body)

        # Functionality
        self.audio_output_cbb.currentIndexChanged.connect(lambda i: config.update_settings('General', 'Audio Output', i))
        self.adhan_caller_cbb.currentIndexChanged.connect(lambda i: config.update_settings('General', 'Adhan Caller', i))

        self.method_cbb.currentIndexChanged.connect(lambda i: config.update_settings('General', 'Calculation Method', i))
        self.method_cbb.currentIndexChanged.connect(self.method_changed)

        self.adhan_reminder_sb.valueChanged.connect(lambda i: config.update_settings('General', 'Adhan Reminder', i))

        self.startup_cb.stateChanged.connect(lambda: self.switch_startup())
        self.always_on_top_cb.stateChanged.connect(lambda: self.switch_always_on_top())

    @staticmethod
    def check_startup():
        return Path(f'C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/PyAdhan.lnk').is_file()

    def check_audio_devices(self):
        audio_devices = [ad.description() for ad in QMediaDevices.audioOutputs()]

        if not audio_devices:
            return

        if config.settings['General']['Audio Output'] in audio_devices:
            self.audio_output_cbb.setCurrentText(config.settings['General']['Audio Output'])

        else:
            config.update_settings('General', 'Audio Output', audio_devices[0])

    def switch_startup(self):
        config.update_settings('General', 'Add To Startup', int(self.startup_cb.isChecked()))

        if not getattr(sys, "frozen", False):
            return

        path = f'C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/PyAdhan.lnk'

        if self.startup_cb.isChecked():
            shell = win32com.client.Dispatch('WScript.Shell')

            shortcut = shell.CreateShortCut(path)
            shortcut.IconLocation = os.getcwd() + '/Resources/Icon.ico'
            shortcut.Targetpath = os.getcwd() + '/PyAdhan.exe'

            shortcut.save()

        else:
            os.remove(path)

    def switch_always_on_top(self):
        config.update_settings('General', 'Always On Top', int(self.always_on_top_cb.isChecked()))
        config.window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.always_on_top_cb.isChecked())
        config.window.show()


class PyAdhan(ModernMainWindow):

    def __init__(self):
        super().__init__()
        self.window_frame.set_title(f'PyAdhan')
        self.window_frame.set_icon('Resources/Icon.ico')

        # Structure
        self.container = ModernTabWidget()
        self.container.setTabPosition(QTabWidget.TabPosition.South)

        # Components
        self.home_tab = HomeTab()
        self.settings_tab = SettingsTab()

        # Assembly
        self.container.addTab(self.home_tab, 'Home')
        self.container.addTab(self.settings_tab, 'Settings')

        self.main_window.setCentralWidget(self.container)

        # Functionality
        self.settings_tab.method_changed.connect(lambda: self.home_tab.update_prayer_times(reset=True))
        self.settings_tab.method_changed.connect(lambda: self.home_tab.tick())


if '__main__' in __name__:
    app = QApplication([])
    app.setStyle('Fusion')
    app.setPalette(get_palette())
    app.setStyleSheet('''QWidget {font-weight: 600}
                         ModernTitleBar {border-style: solid; border-top-left-radius: 10px; border-top-right-radius: 10px;}
                         ModernTitleBar QWidget, QMenuBar, QMenuBar QMenu {color: #ffffff}
                         ModernTitleBar, QToolBar, QMenuBar, QMenuBar QMenu {background: #2b579a}''')

    config = Config()

    config.window = PyAdhan()
    config.window.show()

    config.tray_icon = CustomSystemTrayIcon(QIcon("Resources/Icon.png"), config.window)
    config.tray_icon.show()

    config.window.home_tab.tick()
    config.window.settings_tab.switch_always_on_top()

    app.exec()
