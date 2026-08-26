from PySide6.QtWidgets import (
    QApplication,
    QTabWidget
)

from PySide6.QtGui import QIcon

from Modules.Tabs.HomeTab import HomeTab
from Modules.Tabs.SettingsTab import SettingsTab
from Modules.Utils import (
    CustomSystemTrayIcon,
    ModernMainWindow,
    get_palette,
    ModernTabWidget
)

from Modules.Config import Config


class PyAdhan(ModernMainWindow):

    def __init__(self):
        super().__init__()
        self.window_frame.set_title('PyAdhan')
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
