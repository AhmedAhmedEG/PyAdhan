import sys

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QSystemTrayIcon, QMenu, QHBoxLayout,
                               QMainWindow, QProgressBar, QApplication, QTabWidget, QGraphicsOpacityEffect)
from PySide6.QtCore import (QRunnable, Signal, QObject, Slot, QSize, Qt, QRect, QEvent, QPoint, QPropertyAnimation,
                            QEasingCurve, QParallelAnimationGroup)
from PySide6.QtGui import QGuiApplication, QPainter, QBrush, QColor, QIcon, QPixmap, QFont, QPalette, QPen
from PySide6 import QtGui

from datetime import datetime


def clear_layout(layout):

    while layout.count():
        child = layout.takeAt(0)

        if child.widget():
            child.widget().deleteLater()


def get_palette():
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor('#cbcbcb'))
    palette.setColor(QPalette.WindowText, QColor('#000000'))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor('#808080'))

    palette.setColor(QPalette.Button, QColor('#cfcfcf'))  # Changes the background color of QPushButton, QTabBar and QTabWidget.
    palette.setColor(QPalette.ButtonText, QColor('#000000'))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor('#808080'))

    palette.setColor(QPalette.Base, QColor('#dddddd'))  # Changes background color of text input widgets.

    palette.setColor(QPalette.Highlight, QColor('#2a82da'))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor('#808080'))

    palette.setColor(QPalette.HighlightedText, QColor('#dddddd'))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor('#808080'))

    palette.setColor(QPalette.Text, QColor('#000000'))  # Changes GroupBox, LineEdit and QDocument text color. Also Changes Checkbox check mark color.
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor('#808080'))

    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)

    return palette


class PrayerTimesMonth:

    def __init__(self, data):
        self.data = data['data']
        self.year = datetime.now().year
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
            dt = dt.replace(year=self.year, month=self.month, day=day)

            prayer_times[i] = dt

        return prayer_times


class ModernTitleBar(QFrame):
    closed = Signal()

    def __init__(self, title='', icon=None, movable=True, closable=True, maximizable=False, minimizable=True):
        super().__init__()
        self.setObjectName('ModernTitleBar')
        # self.setAutoFillBackground(True)
        self.setFixedHeight(30)

        self.movable = movable

        self.minimize_size = None
        self.window_offset = None
        self.font_size = 11

        # Structure
        self.body = QHBoxLayout()
        self.body.setSpacing(5)
        self.body.setContentsMargins(6, 2, 4, 0)

        # Components
        self.icon = QLabel()
        if icon is not None:
            self.set_icon(icon)

        else:
            self.icon.hide()

        f = QFont()
        f.setBold(True)
        f.setFamily('calibri')
        f.setPointSize(self.font_size)

        self.title = QLabel(title)
        self.title.setFont(f)

        self.minimize_btn = QPushButton('–')
        self.minimize_btn.setFixedWidth(20)
        self.minimize_btn.setFlat(True)
        self.minimize_btn.setFont(f)

        self.maximize_btn = QPushButton('❒')
        self.maximize_btn.setFixedWidth(20)
        self.maximize_btn.setFlat(True)
        self.maximize_btn.setFont(f)

        self.exit_btn = QPushButton('X')
        self.exit_btn.setFixedWidth(20)
        self.exit_btn.setFlat(True)
        self.exit_btn.setFont(f)

        # Assembly
        self.body.addWidget(self.icon, alignment=Qt.AlignLeft)
        self.body.addWidget(self.title, alignment=Qt.AlignLeft)

        self.body.addStretch(1)

        if minimizable:
            self.body.addWidget(self.minimize_btn, alignment=Qt.AlignRight | Qt.AlignmentFlag.AlignTop)

        if maximizable:
            self.body.addWidget(self.maximize_btn, alignment=Qt.AlignRight)

        if closable:
            self.body.addWidget(self.exit_btn, alignment=Qt.AlignRight)

        # self.body.addWidget(HSeparator(height=2), 1, 0, 1, 4)
        self.setLayout(self.body)

        # Functionality
        self.minimize_btn.clicked.connect(self.minimize)
        self.maximize_btn.clicked.connect(self.maximize)
        self.exit_btn.clicked.connect(self.exit)

    def set_title(self, title: str) -> None:
        self.title.setText(title)
        self.parent().setWindowTitle(title)

    def set_icon(self, icon: str):
        self.parent().setWindowIcon(QIcon(icon))

        self.icon.setPixmap(QPixmap(icon).scaled(15, 15, mode=Qt.SmoothTransformation))
        self.icon.resize(QSize(15, 15))
        self.icon.show()

    def minimize(self):
        self.parent().showMinimized()

    def maximize(self):

        if self.parent().size() == QGuiApplication.screens()[0].size():
            self.parent().resize(self.minimize_size)
            self.parent().move(
                QGuiApplication.screens()[0].geometry().center() - self.parent().frameGeometry().center())

        else:
            self.minimize_size = self.parent().size()

            self.parent().resize(QGuiApplication.screens()[0].size())
            self.parent().move(QPoint(0, 0))

    def exit(self):
        self.closed.emit()
        self.parent().hide()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(e)

        if not self.movable:
            return

        self.window_offset = e.position()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(e)

        if not self.movable:
            return

        pos = QPoint(e.globalPosition().x() - self.window_offset.x(), e.globalPosition().y() - self.window_offset.y())

        self.pos_anim = QPropertyAnimation(self.parent(), b'pos')
        self.pos_anim.setEndValue(pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        self.pos_anim.setDuration(400)

        self.pos_anim.start()


class ModernMainWindow(QFrame):
    animation_starting = Signal()
    animation_finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self.anim_duration = 400
        self.stretch_direction = None
        self.cursor_changed = False
        self.anchor = None

        # Structure
        self.body = QVBoxLayout()
        self.body.setSpacing(0)
        self.body.setContentsMargins(0, 0, 0, 0)

        # Components
        self.window_frame = ModernTitleBar()

        self.main_window = QMainWindow()
        self.main_window.setContentsMargins(4, 4, 4, 4)

        # Assembly
        self.body.addWidget(self.window_frame)
        self.body.addWidget(self.main_window, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.body)

    def eventFilter(self, watched: QObject, e: QEvent) -> bool:

        if isinstance(watched, QProgressBar):
            return False

        if e.type() == QEvent.Type.MouseMove:
            self.check_corners(self.mapFromGlobal(e.globalPosition()))

            if self.anchor:
                self.mouseMoveEvent(e)
                return True

            else:
                return False

        if e.type() == QEvent.Type.MouseButtonPress and self.stretch_direction:
            self.mousePressEvent(e)
            return False

        if e.type() == QEvent.Type.MouseButtonRelease and self.stretch_direction:
            self.mouseReleaseEvent(e)
            return False

        return False

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(e)

        if self.stretch_direction:
            self.anchor = e.globalPosition()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(e)

        if e.button() != Qt.MouseButtons.LeftButton:
            return

        self.anchor = None
        self.stretch_direction = None
        self.animation_finished.emit()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(e)
        self.check_corners(e.position())

        if self.anchor:
            self.animation_starting.emit()

            if self.stretch_direction == 'r':
                delta = e.globalPosition().x() - (self.width() + self.pos().x())

                self.size_anim = QPropertyAnimation(self, b"size")
                self.size_anim.setEndValue(QSize(self.width() + delta, self.height()))
                self.size_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                self.size_anim.setDuration(self.anim_duration)
                self.size_anim.start()

            elif self.stretch_direction == 'l':
                delta = self.pos().x() - e.globalPosition().x()

                if self.width() + delta < self.minimumWidth():
                    return

                self.animation = QParallelAnimationGroup()

                pos_anim = QPropertyAnimation(self, b'pos')
                pos_anim.setEndValue(QPoint(self.pos().x() - delta, self.pos().y()))
                pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                pos_anim.setDuration(self.anim_duration)

                size_anim = QPropertyAnimation(self, b"size")
                size_anim.setEndValue(QSize(self.width() + delta, self.height()))
                size_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                size_anim.setDuration(self.anim_duration)

                self.animation.addAnimation(pos_anim)
                self.animation.addAnimation(size_anim)

                self.animation.start()

            elif self.stretch_direction == 'u':
                delta = self.pos().y() - e.globalPosition().y()

                if self.height() + delta < self.minimumHeight():
                    return

                self.animation = QParallelAnimationGroup()

                pos_anim = QPropertyAnimation(self, b'pos')
                pos_anim.setEndValue(QPoint(self.pos().x(), self.pos().y() - delta))
                pos_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                pos_anim.setDuration(self.anim_duration)

                size_anim = QPropertyAnimation(self, b"size")
                size_anim.setEndValue(QSize(self.width(), self.height() + delta))
                size_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                size_anim.setDuration(self.anim_duration)

                self.animation.addAnimation(pos_anim)
                self.animation.addAnimation(size_anim)

                self.animation.start()

            elif self.stretch_direction == 'd':
                delta = e.globalPosition().y() - (self.height() + self.pos().y())

                self.size_anim = QPropertyAnimation(self, b"size")
                self.size_anim.setEndValue(QSize(self.width(), self.height() + delta))
                self.size_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                self.size_anim.setDuration(self.anim_duration)
                self.size_anim.start()

    def check_corners(self, pos: QPoint):
        cx = self.width() / 2
        cy = self.height() / 2

        vertical_direction = 'u' if pos.y() < cy else 'd'
        horizontal_direction = 'l' if pos.x() < cx else 'r'

        horizontal_distance = self.width() - pos.x() if horizontal_direction == 'r' else pos.x()
        vertical_distance = self.height() - pos.y() if vertical_direction == 'd' else pos.y()

        if abs(min(horizontal_distance, vertical_distance)) <= 4:

            if horizontal_distance < vertical_distance:

                if not self.cursor_changed:
                    QApplication.setOverrideCursor(Qt.CursorShape.SizeHorCursor)
                    self.cursor_changed = True

                self.stretch_direction = horizontal_direction

            else:

                if not self.cursor_changed:
                    QApplication.setOverrideCursor(Qt.CursorShape.SizeVerCursor)
                    self.cursor_changed = True

                self.main_window.setFocus()
                self.stretch_direction = vertical_direction

        else:

            if not self.anchor:

                if self.cursor_changed:
                    QApplication.restoreOverrideCursor()
                    self.cursor_changed = False

                self.stretch_direction = None

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        painter.setPen(QPen(self.palette().window().color(), 4))
        painter.setBrush(self.palette().window())

        drawing_rect = QRect(2, self.window_frame.height() - 2, self.width() - 4, self.height() - self.window_frame.height())
        painter.drawRoundedRect(drawing_rect, 4, 4)


class ModernTabWidget(QTabWidget):
    animation_starting = Signal()
    animation_finished = Signal()

    def __init__(self, animation_disabled=False):
        super().__init__()
        self.setTabShape(QTabWidget.TabShape.Rounded)
        self.setMovable(True)

        if not animation_disabled:
            self.enable_animation()

    def enable_animation(self):
        self.currentChanged.connect(self.fade_in)

    def fade_in(self):
        self.animation_starting.emit()
        widget = self.currentWidget()

        opacity = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity)

        # Defining this variable in the __init__ call will cause bugs, so I defined it here
        self.animation = QParallelAnimationGroup()

        fade_in_anim = QPropertyAnimation(opacity, b'opacity')
        fade_in_anim.setDuration(500)
        fade_in_anim.setStartValue(0)
        fade_in_anim.setEndValue(1)
        fade_in_anim.setEasingCurve(QEasingCurve.InBack)

        slide_anim = QPropertyAnimation(widget, b'pos')
        slide_anim.setDuration(500)
        slide_anim.setStartValue(QPoint(widget.x(), self.height()))
        slide_anim.setEndValue(QPoint(widget.x(), 0))
        slide_anim.setEasingCurve(QEasingCurve.OutCurve)

        self.animation.addAnimation(fade_in_anim)
        self.animation.addAnimation(slide_anim)
        self.animation.start()

        self.animation.finished.connect(lambda: widget.setGraphicsEffect(None))
        self.animation.finished.connect(self.animation_finished.emit)


class CustomSystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        menu = QMenu(parent)

        menu.addAction("Exit")
        menu.triggered.connect(lambda: sys.exit(1))

        self.setContextMenu(menu)
        self.activated.connect(lambda i: self.activated(i))

    def activated(self, reason):

        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.parent().setVisible(not self.parent().isVisible())