from cx_Freeze import setup, Executable
from Modules.Config import Config
import os

config = Config()

file_excludes = ['Qt6WebEngineCore.dll', 'lupdate.exe', 'Qt6Designer.dll', 'Qt6Quick.dll', 'Qt6DesignerComponents.dll',
                 'qtwebengine_devtools_resources.pak', 'qtwebengine_resources.pak', 'Qt6Qml.dll',
                 'Qt6QuickTemplates2.dll', 'Qt6Quick3DRuntimeRender.dll']

module_excludes = ['tkinter', 'PySide6.qml', 'PySide6.translations.qtwebengine_locales', 'PySide6.QtWebEngineCore',
                   'PySide6.QtNetwork', 'PySide6.QtNfc', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine', 'PySide6.QtSql',
                   'PySide6.QtBluetooth', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebKit', 'PySide6.QtScript',
                   'PySide6.QtWebKitWidgets', 'PySide6.QtWebSockets']

setup(name=f'PyAdhan',
      description='PyAdhan',
      version=config.APP_VERSION,
      options={'build_exe': {'include_files': [('Resources', 'Resources'),
                                               ('ChangeLog.txt', 'ChangeLog.txt')],
                             'excludes': module_excludes,
                             'build_exe': f'build/PyAdhan v{config.APP_VERSION}'}},

      executables=[Executable(script='PyAdhan.py', icon='Resources/Icon.ico', base='Win32GUI')])


for root, dirs, files in os.walk('build'):

    for filename in files:

        if filename in file_excludes:
            os.remove(os.path.join(root, filename))