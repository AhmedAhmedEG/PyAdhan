from copy import deepcopy
import configparser
import sys
import os
import io
from pathlib import Path


class Config:
    singleton_instance = None

    def __init__(self):
        # self.APP_VERSION = next(open('./Changelog.txt', 'r', encoding='utf-8')).split(' ')[-1][1:-3]
        self.APP_VERSION = '2.8.10.5'
        self.ADHAN_CALLERS = ['Random'] + list(map(lambda a: Path(a).stem, os.listdir('Resources/Adhan Callers')))
        self.CALC_METHODS = ['Auto',
                             'University of Islamic Sciences, Karachi',
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
                             'Spiritual Administration of Muslims of Russia']

        self.window = None
        self.tray_icon = None

        self.settings = configparser.ConfigParser()
        self.settings.optionxform = str

        if getattr(sys, "frozen", False):
            os.chdir(os.path.dirname(sys.executable))
            #     sys.stderr = io.StringIO()
            #     sys.stdout = io.StringIO()

        if not os.path.exists('Settings.ini'):
            self.create_settings()
        else:
            self.read_settings()

    def create_settings(self):
        self.settings['General'] = {'Adhan Caller': '0',
                                    'Calculation Method': '0',
                                    'Adhan Reminder': '0',
                                    'Always On Top': '1'}

        with open('Settings.ini', 'w', encoding='utf-8') as f:
            self.settings.write(f)

    def read_settings(self):

        with open('Settings.ini', 'r', encoding='utf-8') as f:
            self.settings.read_file(f)

    def save_settings(self):

        with open('Settings.ini', 'w', encoding='utf-8') as c:
            deepcopy(self.settings).write(c)

    def update_settings(self, section, key, value):
        self.settings.set(section, key, str(value))
        self.save_settings()

    def __new__(cls, *args, **kwargs):

        if cls.singleton_instance is None:
            cls.singleton_instance = super().__new__(cls, *args, **kwargs)

        return cls.singleton_instance
