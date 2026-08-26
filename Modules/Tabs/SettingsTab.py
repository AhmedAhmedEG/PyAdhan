from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QGroupBox,
    QCheckBox,
    QSpinBox
)

from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtCore import Qt, Signal

from Modules.Config import Config

from pathlib import Path
import getpass
import sys
import os

import win32com.client
import win32com


class SettingsTab(QWidget):
    method_changed = Signal()

    def __init__(self):
        super().__init__()
        self.config = Config()

        # Structure
        self.preferences_body = QFormLayout()
        self.preferences_body.setHorizontalSpacing(40)

        self.preferences_container = QGroupBox()
        self.preferences_container.setTitle("Preferences")

        self.settings_body = QFormLayout()
        self.settings_body.setHorizontalSpacing(40)

        self.settings_container = QGroupBox()
        self.settings_container.setTitle("Options")

        self.body = QVBoxLayout()

        # Components
        self.audio_output_cbb = QComboBox()
        self.check_audio_devices()

        self.media_devices = QMediaDevices(self)
        self.media_devices.audioOutputsChanged.connect(self.check_audio_devices)

        self.adhan_caller_cbb = QComboBox()
        self.adhan_caller_cbb.addItems(self.config.ADHAN_CALLERS)
        self.adhan_caller_cbb.setCurrentIndex(
            int(self.config.settings["General"]["Adhan Caller"])
        )

        self.adhan_reminder_sb = QSpinBox()
        self.adhan_reminder_sb.setMaximum(60)
        self.adhan_reminder_sb.setValue(
            int(self.config.settings["General"]["Adhan Reminder"])
        )

        self.method_cbb = QComboBox()
        self.method_cbb.addItems(self.config.CALC_METHODS)
        self.method_cbb.setCurrentIndex(
            int(self.config.settings["General"]["Calculation Method"])
        )

        self.startup_cb = QCheckBox()
        self.startup_cb.setChecked(self.check_startup())
        self.startup_cb.setMinimumSize(25, 25)

        self.always_on_top_cb = QCheckBox()
        self.always_on_top_cb.setChecked(
            int(self.config.settings["General"]["Always On Top"])
        )
        self.always_on_top_cb.setMinimumSize(25, 25)

        # Assembly
        self.preferences_body.addRow("Audio Output", self.audio_output_cbb)
        self.preferences_body.addRow("Adhan Caller", self.adhan_caller_cbb)
        self.preferences_body.addRow("Adhan Reminder (Minutes)", self.adhan_reminder_sb)

        self.preferences_container.setLayout(self.preferences_body)
        self.body.addWidget(self.preferences_container)

        self.settings_body.addRow("Calculation Method", self.method_cbb)
        self.settings_body.addRow("Add To Startup", self.startup_cb)
        self.settings_body.addRow("Always On Top", self.always_on_top_cb)

        self.settings_container.setLayout(self.settings_body)
        self.body.addWidget(self.settings_container)

        self.setLayout(self.body)

        # Functionality
        self.audio_output_cbb.currentTextChanged.connect(self.on_audio_output_changed)
        self.adhan_caller_cbb.currentIndexChanged.connect(
            lambda i: self.config.update_settings("General", "Adhan Caller", i)
        )

        self.method_cbb.currentIndexChanged.connect(
            lambda i: self.config.update_settings("General", "Calculation Method", i)
        )
        self.method_cbb.currentIndexChanged.connect(self.method_changed)

        self.adhan_reminder_sb.valueChanged.connect(
            lambda i: self.config.update_settings("General", "Adhan Reminder", i)
        )

        self.startup_cb.stateChanged.connect(lambda: self.switch_startup())
        self.always_on_top_cb.stateChanged.connect(lambda: self.switch_always_on_top())

    def on_audio_output_changed(self, text):
        if getattr(self, '_updating_audio_ui', False) or not text:
            return
        self.config.update_settings("General", "Audio Output", text)

    @staticmethod
    def check_startup():
        return Path(
            f"C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/PyAdhan.lnk"
        ).is_file()

    def check_audio_devices(self):
        self._updating_audio_ui = True
        self.audio_output_cbb.blockSignals(True)
        self.audio_output_cbb.clear()

        audio_devices = [ad.description() for ad in QMediaDevices.audioOutputs()]
        if not audio_devices:
            self.audio_output_cbb.blockSignals(False)
            self._updating_audio_ui = False
            return

        self.audio_output_cbb.addItems(audio_devices)

        configured = self.config.settings["General"].get("Audio Output", "")
        if configured in audio_devices:
            self.audio_output_cbb.setCurrentText(configured)
        elif configured:
            default_dev = QMediaDevices.defaultAudioOutput()
            if not default_dev.isNull() and default_dev.description() in audio_devices:
                self.audio_output_cbb.setCurrentText(default_dev.description())
            else:
                self.audio_output_cbb.setCurrentIndex(0)
        else:
            default_dev = QMediaDevices.defaultAudioOutput()
            dev_name = default_dev.description() if not default_dev.isNull() else audio_devices[0]
            self.audio_output_cbb.setCurrentText(dev_name)
            self.config.update_settings("General", "Audio Output", dev_name)

        self.audio_output_cbb.blockSignals(False)
        self._updating_audio_ui = False

    def switch_startup(self):
        self.config.update_settings(
            "General", "Add To Startup", int(self.startup_cb.isChecked())
        )

        if not getattr(sys, "frozen", False):
            return

        path = f"C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/PyAdhan.lnk"

        if self.startup_cb.isChecked():
            shell = win32com.client.Dispatch("WScript.Shell")

            shortcut = shell.CreateShortCut(path)
            shortcut.IconLocation = os.getcwd() + "/Resources/Icon.ico"
            shortcut.Targetpath = os.getcwd() + "/PyAdhan.exe"

            shortcut.save()

        else:
            os.remove(path)

    def switch_always_on_top(self):
        self.config.update_settings(
            "General", "Always On Top", int(self.always_on_top_cb.isChecked())
        )
        self.config.window.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self.always_on_top_cb.isChecked()
        )
        self.config.window.show()
