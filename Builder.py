from Modules.Props import app_version
from cx_Freeze import setup, Executable
import os


file_excludes = ['Qt6WebEngineCore.dll', 'lupdate.exe', 'Qt6Designer.dll', 'Qt6Quick.dll', 'Qt6DesignerComponents.dll',
                 'Qt6Network.dll', 'qtwebengine_devtools_resources.pak', 'qtwebengine_resources.pak', 'Qt6Qml.dll',
                 'Qt6QuickTemplates2.dll', 'Qt6Quick3DRuntimeRender.dll']

module_excludes = ['tkinter', 'PySide6.qml', 'PySide6.translations.qtwebengine_locales',
                   'PySide6.QtBluetooth', 'PySide6.QtNetwork', 'PySide6.QtNfc', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine',
                   'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebKit', 'PySide6.QtWebKitWidgets',
                   'PySide6.QtWebSockets', 'PySide6.QtSql', 'PySide6.QtNetwork', 'PySide6.QtScript']

setup(name=f'PyAdhanGUI',
      version=app_version,
      options={'build_exe': {'include_files': [('Resources', 'Resources'),
                                               ('ChangeLog.txt', 'ChangeLog.txt')],
                             'excludes': module_excludes}},

      executables=[Executable(script='PyAdhanGUI.py', icon='Resources/Icon.ico', base='Win32GUI')])

for root, dirs, files in os.walk('build'):

    for filename in files:

        if filename in file_excludes:
            os.remove(os.path.join(root, filename))
