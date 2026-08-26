from threading import Thread

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QGroupBox,
    QPushButton,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from Modules.Config import Config
from Modules.Utils import PrayerTimesDay, clear_layout

from datetime import datetime, timedelta
import random
import pickle
import os

import requests


class HomeTab(QWidget):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.prayer_names = {0: 'Fajr', 1: 'Dhuhr', 2: 'Asr', 3: 'Maghrib', 4: 'Isha'}
        self.today_prayer_times = None

        self.alarm_player = QMediaPlayer()
        self.adhan_player = QMediaPlayer()

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

        self.stop_adhan_btn = QPushButton('Stop Adhan')
        self.stop_adhan_btn.setAutoFillBackground(True)
        self.stop_adhan_btn.setFlat(True)
        self.stop_adhan_btn.setEnabled(False)

        # Assembly
        self.body.addWidget(self.counter_lb, alignment=Qt.AlignmentFlag.AlignCenter)

        self.prayer_times_container.setLayout(self.prayer_times_body)
        self.body.addWidget(self.prayer_times_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.body.addWidget(self.stop_adhan_btn)
        self.setLayout(self.body)

        # Functionality
        self.counter_timer.timeout.connect(lambda: self.tick())
        self.adhan_player.playingChanged.connect(lambda b: self.stop_adhan_btn.setEnabled(b))
        self.stop_adhan_btn.clicked.connect(lambda: self.adhan_player.stop)

        # Initialization
        self.counter_timer.start()
        self.update_prayer_times()

    def update_prayer_times(self, reset=False):
        prayer_times_day = None
        fetch_succeeded = False

        try:
            geo_res = requests.get('http://ip-api.com/json/', timeout=5)
            ip_geo_json = geo_res.json()

            params = {
                'latitude': ip_geo_json['lat'],
                'longitude': ip_geo_json['lon']
            }

            calc_method = int(self.config.settings['General']['Calculation Method'])
            if calc_method:
                params['method'] = calc_method

            adhan_res = requests.get(
                'https://api.aladhan.com/v1/timings',
                params=params,
                timeout=5
            )
            adhan_json = adhan_res.json()

            if adhan_json.get('code') == 200 and 'data' in adhan_json:
                prayer_times_day = PrayerTimesDay(adhan_json)
                os.makedirs('Resources', exist_ok=True)
                with open('Resources/PrayerTimesDay.pkl', 'wb') as f:
                    pickle.dump(prayer_times_day, f)
                fetch_succeeded = True

        except Exception as e:
            print(f"Error fetching fresh prayer times: {e}")

        if not fetch_succeeded:
            if os.path.isfile('Resources/PrayerTimesDay.pkl'):
                try:
                    with open('Resources/PrayerTimesDay.pkl', 'rb') as f:
                        prayer_times_day = pickle.load(f)
                except Exception as e:
                    print(f"Error loading prayer times cache: {e}")

        if prayer_times_day is not None:
            self.today_prayer_times = prayer_times_day.get_prayer_times(datetime.now().date())
        else:
            return

        clear_layout(self.prayer_times_body)

        self.prayer_times_body.addRow(self.prayer_names[0], QLabel(self.today_prayer_times[0].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[1], QLabel(self.today_prayer_times[1].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[2], QLabel(self.today_prayer_times[2].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[3], QLabel(self.today_prayer_times[3].strftime("%I:%M %p")))
        self.prayer_times_body.addRow(self.prayer_names[4], QLabel(self.today_prayer_times[4].strftime("%I:%M %p")))

    def tick(self):
        current_time = datetime.now()

        if not self.today_prayer_times:
            self.update_prayer_times()
            if not self.today_prayer_times:
                return

        if self.today_prayer_times[0].date() != current_time.date():
            self.update_prayer_times()
            if not self.today_prayer_times:
                return

        next_prayer = 0
        for i in range(0, 5):
            prayer_time = self.today_prayer_times[i]
            adhan_reminder = int(self.config.settings['General']['Adhan Reminder'])

            if adhan_reminder:
                reminder_time = prayer_time - timedelta(minutes=adhan_reminder)

                if self.equale_times(current_time, reminder_time):

                    if self.alarm_player.isPlaying():
                        return

                    self.config.tray_icon.showMessage(f'{self.prayer_names[i]} Reminder',
                                                 f'{self.prayer_names[i]} After {adhan_reminder} Minutes',
                                                 QIcon("Resources/Icon.png"))

                    self.run_audio(self.alarm_player, 'Resources/Alarm.mp3')

            if self.equale_times(current_time, prayer_time):

                if self.adhan_player.isPlaying():
                    return

                adhan_caller = int(self.config.settings['General']['Adhan Caller'])

                if adhan_caller == 0:
                    adhan_caller = random.choice(range(1, len(self.config.ADHAN_CALLERS)))

                adhan_sound = self.config.ADHAN_CALLERS[adhan_caller]
                self.config.tray_icon.showMessage(
                    f'{self.prayer_names[i]} Is Calling',
                    adhan_sound,
                    QIcon("Resources/Icon.png")
                )

                self.run_audio(self.adhan_player, f'Resources/Adhan Callers/{adhan_sound}.mp3')

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

        next_prayer_idx = next_prayer * 2

        for i in range(2 * 5):
            item = self.prayer_times_body.itemAt(i)
            if item and item.widget():
                if (i == next_prayer_idx) or (i == next_prayer_idx + 1):
                    item.widget().setStyleSheet('font-size: 25px; font-weight: bold; color: green')
                else:
                    item.widget().setStyleSheet('font-size: 25px')

    @staticmethod
    def equale_times(dt1, dt2):
        return (dt1.hour, dt1.minute, dt1.second) == (dt2.hour, dt2.minute, dt2.second)

    def run_audio(self, player, file_path):
        audio_outputs = QMediaDevices.audioOutputs()
        if not audio_outputs:
            return

        configured_device = self.config.settings["General"].get("Audio Output", "")
        matched_devices = [ad for ad in audio_outputs if ad.description() == configured_device]

        if matched_devices:
            output_device = matched_devices[0]
        else:
            default_device = QMediaDevices.defaultAudioOutput()
            if not default_device.isNull():
                output_device = default_device
            else:
                output_device = audio_outputs[0]

        self.audio_output = QAudioOutput()
        self.audio_output.setDevice(output_device)

        player.setAudioOutput(self.audio_output)
        player.setSource(f"file:{file_path}")

        Thread(target=player.play).start()