import sys
import os
import cv2

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QDialog,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QPropertyAnimation,
    QEasingCurve, QTimer, QSequentialAnimationGroup
)
from PyQt6.QtGui import QImage, QPixmap

from core.pipeline import GesturePipeline, LDPlayerNotFoundError, CameraNotFoundError
from PyQt6.QtGui import QIcon
from config import resource_path
from ui.pip_window import PiPWindow


# ─── Paths ────────────────────────────────────────────────────────────────────

ASSETS_DIR = resource_path(os.path.join("assets", "gestures"))


# ─── Gesture data ─────────────────────────────────────────────────────────────

GESTURES = [
    {"name": "Left fist drag",   "action": "Movement",       "key": "WASD",      "img": "fist_left.png",  "tag": "MOVE",   "color": "#6d28d9"},
    {"name": "Right pinch tap",  "action": "Instant attack", "key": "E",         "img": "pinch.png",      "tag": "ATTACK", "color": "#0891b2"},
    {"name": "Right pinch drag", "action": "Aimed attack",   "key": "X + mouse", "img": "pinch_drag.png", "tag": "AIM",    "color": "#0891b2"},
    {"name": "Right fist tap",   "action": "Instant super",  "key": "F",         "img": "fist_right.png", "tag": "SUPER",  "color": "#b45309"},
    {"name": "Right fist drag",  "action": "Aimed super",    "key": "C + mouse", "img": "fist_drag.png",  "tag": "AIM",    "color": "#b45309"},
    {"name": "Right peace sign", "action": "Hypercharge",    "key": "R",         "img": "peace.png",      "tag": "HYPER",  "color": "#065f46"},
    {"name": "Right L-shape",    "action": "Gadget",         "key": "Q",         "img": "lshape.png",     "tag": "GADGET", "color": "#9f1239"},
]


# ─── Frame bridge ─────────────────────────────────────────────────────────────

class FrameBridge(QObject):
    frame_ready = pyqtSignal(QImage)

    def push(self, frame):
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg     = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.frame_ready.emit(qimg.copy())


# ─── Dot indicator ────────────────────────────────────────────────────────────

class DotIndicator(QWidget):
    dot_clicked = pyqtSignal(int)

    def __init__(self, count, parent=None):
        super().__init__(parent)
        self._current = 0
        self._buttons = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addStretch()
        for i in range(count):
            btn = QPushButton()
            btn.setFixedSize(8, 8)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=i: self.dot_clicked.emit(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)
        layout.addStretch()
        self._refresh()

    def set_current(self, index):
        self._current = index
        self._refresh()

    def _refresh(self):
        for i, btn in enumerate(self._buttons):
            if i == self._current:
                btn.setFixedWidth(20)
                btn.setStyleSheet("background: #fff; border-radius: 4px; border: none;")
            else:
                btn.setFixedWidth(8)
                btn.setStyleSheet("background: rgba(255,255,255,0.2); border-radius: 4px; border: none;")


# ─── Gesture card ─────────────────────────────────────────────────────────────

class GestureCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # nav bar
        nav = QWidget()
        nav.setFixedHeight(48)
        nav.setStyleSheet("background: #0d0d18; border-bottom: 1px solid rgba(255,255,255,0.06);")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(16, 0, 12, 0)

        self._tag = QLabel()
        self._tag.setFixedHeight(22)
        self._tag.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._counter = QLabel()
        self._counter.setStyleSheet("color: rgba(255,255,255,0.3); font-size: 12px; background: transparent;")

        self._prev = QPushButton("‹")
        self._next = QPushButton("›")
        for btn in (self._prev, self._next):
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.06);
                    color: rgba(255,255,255,0.5);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 7px; font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.12);
                    color: #fff;
                }
                QPushButton:pressed { background: rgba(255,255,255,0.03); }
            """)
        self._prev.clicked.connect(lambda: self._navigate(-1))
        self._next.clicked.connect(lambda: self._navigate(1))

        nav_layout.addWidget(self._tag)
        nav_layout.addStretch()
        nav_layout.addWidget(self._counter)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self._prev)
        nav_layout.addSpacing(4)
        nav_layout.addWidget(self._next)
        root.addWidget(nav)

        # image
        self._img = QLabel()
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setStyleSheet("background: #0a0a14;")
        self._img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self._img, stretch=1)

        # info
        info = QWidget()
        info.setFixedHeight(120)
        info.setStyleSheet("background: #0d0d18; border-top: 1px solid rgba(255,255,255,0.06);")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 14, 16, 12)
        info_layout.setSpacing(4)

        self._gesture_name = QLabel()
        self._gesture_name.setStyleSheet("color: rgba(255,255,255,0.35); font-size: 10px; letter-spacing: 1.5px; background: transparent;")

        self._action = QLabel()
        self._action.setStyleSheet("color: #fff; font-size: 18px; font-weight: 600; background: transparent;")

        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        key_row.setContentsMargins(0, 0, 0, 0)

        key_lbl = QLabel("KEY")
        key_lbl.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 10px; letter-spacing: 1px; background: transparent;")

        self._key = QLabel()
        self._key.setFixedHeight(22)
        self._key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._key.setStyleSheet("""
            background: rgba(255,255,255,0.07);
            color: rgba(255,255,255,0.8);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 5px;
            font-size: 11px;
            font-family: 'Consolas', monospace;
            padding: 0 10px;
            letter-spacing: 1px;
        """)

        key_row.addWidget(key_lbl)
        key_row.addWidget(self._key)
        key_row.addStretch()

        info_layout.addWidget(self._gesture_name)
        info_layout.addWidget(self._action)
        info_layout.addSpacing(6)
        info_layout.addLayout(key_row)
        root.addWidget(info)

        # dots
        dots_wrap = QWidget()
        dots_wrap.setFixedHeight(30)
        dots_wrap.setStyleSheet("background: #0d0d18;")
        dots_layout = QHBoxLayout(dots_wrap)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        self._dots = DotIndicator(len(GESTURES))
        self._dots.dot_clicked.connect(self._go_to)
        dots_layout.addWidget(self._dots)
        root.addWidget(dots_wrap)

        self._refresh()

    def _navigate(self, direction):
        self._current = (self._current + direction) % len(GESTURES)
        self._animate_transition()

    def _go_to(self, index):
        self._current = index
        self._animate_transition()

    def _animate_transition(self):
        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_out.setDuration(80)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        fade_in.setDuration(180)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._seq = QSequentialAnimationGroup()
        self._seq.addAnimation(fade_out)
        self._seq.addAnimation(fade_in)
        self._seq.finished.connect(lambda: None)
        self._seq.stateChanged.connect(
            lambda state, _: self._refresh() if state == QSequentialAnimationGroup.State.Running and
            self._seq.currentAnimation() == fade_in else None
        )
        # refresh at midpoint
        QTimer.singleShot(80, self._refresh)
        self._seq.start()

    def _refresh(self):
        g = GESTURES[self._current]
        c = g["color"]

        self._tag.setText(g["tag"])
        self._tag.setStyleSheet(f"""
            background: {c};
            color: rgba(255,255,255,0.9);
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            padding: 0 10px;
            letter-spacing: 1.5px;
        """)

        self._counter.setText(f"{self._current + 1} / {len(GESTURES)}")
        self._gesture_name.setText(g["name"].upper())
        self._action.setText(g["action"])
        self._key.setText(g["key"])

        img_path = os.path.join(ASSETS_DIR, g["img"])
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img.setPixmap(pixmap)
        else:
            self._img.clear()
            self._img.setText("No image")
            self._img.setStyleSheet("background: #0a0a14; color: rgba(255,255,255,0.2); font-size: 12px;")

        self._dots.set_current(self._current)



# ─── Feed widget ──────────────────────────────────────────────────────────────

class FeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel()
        self._label.setObjectName("cameraFeed")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._label.setText("TAP START TO BEGIN")
        layout.addWidget(self._label)

    def update_frame(self, qimg):
        pixmap = QPixmap.fromImage(qimg).scaled(
            self._label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(pixmap)

    def reset(self):
        self._label.setPixmap(QPixmap())
        self._label.setText("TAP START TO BEGIN")


# ─── Error dialog ─────────────────────────────────────────────────────────────

class ErrorDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        layout.setSpacing(0)

        icon = QLabel("⚠")
        icon.setStyleSheet("font-size: 28px; color: #ef4444; background: transparent;")
        layout.addWidget(icon)
        layout.addSpacing(12)

        title = QLabel("Something went wrong")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #fff; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(8)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.45); background: transparent;")
        layout.addWidget(msg)
        layout.addSpacing(24)

        ok = QPushButton("Got it")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self.accept)
        ok.setStyleSheet("""
            QPushButton {
                background: #ef4444; color: #fff;
                border: none; border-radius: 8px;
                padding: 10px; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover   { background: #dc2626; }
            QPushButton:pressed { background: #b91c1c; }
        """)
        layout.addWidget(ok)

        self.setStyleSheet("""
            QDialog {
                background: #16161e;
                border: 1px solid rgba(239,68,68,0.25);
                border-radius: 14px;
            }
        """)

    def showEvent(self, event):
        if self.parent():
            pr = self.parent().geometry()
            self.move(
                pr.x() + (pr.width()  - self.width())  // 2,
                pr.y() + (pr.height() - self.height()) // 2,
            )
        super().showEvent(event)


# ─── Main window ──────────────────────────────────────────────────────────────

class GestureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path('icon.png')))
        self.setWindowTitle("Gesture Controller")
        self.setMinimumSize(960, 640)

        self._pipeline         = None
        self._accepting_frames = False
        self._guide_open       = False
        self._pip = None

        self._bridge = FrameBridge()
        self._bridge.frame_ready.connect(self._update_frame)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # title bar
        tb = QWidget()
        tb.setFixedHeight(46)
        tb.setObjectName("titlebar")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(18, 0, 18, 0)

        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #10b981; font-size: 9px; background: transparent;")
        self._dot_visible = True
        self._dot_timer = QTimer()
        self._dot_timer.setInterval(1000)
        self._dot_timer.timeout.connect(self._blink_dot)
        self._dot_timer.start()

        brand = QLabel("Gesture Controller")
        brand.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 500; background: transparent;")

        tbl.addWidget(self._dot)
        tbl.addSpacing(8)
        tbl.addWidget(brand)
        tbl.addStretch()
        rl.addWidget(tb)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.05);")
        rl.addWidget(sep)

        # content
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cl = QHBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        self._feed = FeedWidget()
        cl.addWidget(self._feed, stretch=1)

        self._guide = GestureCard()
        self._guide.setFixedWidth(0)
        self._guide.setObjectName("guideCard")
        cl.addWidget(self._guide)

        rl.addWidget(content, stretch=1)

        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background: rgba(255,255,255,0.05);")
        rl.addWidget(sep2)

        # bottom bar
        bot = QWidget()
        bot.setFixedHeight(62)
        bot.setObjectName("bottomBar")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(14, 0, 14, 0)
        bl.setSpacing(10)

        self._btn_start = QPushButton("▶  Start")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._toggle_pipeline)

        self._btn_guide = QPushButton("Guide")
        self._btn_guide.setObjectName("btnGuide")
        self._btn_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_guide.clicked.connect(self._toggle_guide)

        bl.addWidget(self._btn_start, stretch=1)
        bl.addWidget(self._btn_guide)
        rl.addWidget(bot)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #0e0e18;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
            }
            QWidget#titlebar  { background: #09090f; }
            QWidget#bottomBar { background: #09090f; }
            QWidget#guideCard { background: #0d0d18; border-left: 1px solid rgba(255,255,255,0.05); }
            QLabel#cameraFeed {
                background: #09090f;
                color: rgba(255,255,255,0.12);
                font-size: 11px;
                letter-spacing: 4px;
                font-weight: 500;
            }
            QPushButton#btnStart {
                background: #6d28d9;
                color: #fff;
                border: none;
                border-radius: 9px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#btnStart:hover   { background: #7c3aed; }
            QPushButton#btnStart:pressed { background: #5b21b6; }
            QPushButton#btnGuide {
                background: rgba(255,255,255,0.04);
                color: rgba(255,255,255,0.45);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 9px;
                padding: 12px 20px;
                font-size: 14px;
            }
            QPushButton#btnGuide:hover {
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.75);
                border-color: rgba(255,255,255,0.12);
            }
        """)

    def _show_pip(self):
        self._pip = PiPWindow()
        self._pip.expand_clicked.connect(self._hide_pip)
        self._bridge.frame_ready.disconnect()
        self._bridge.frame_ready.connect(self._pip.update_frame)
        self._pip.show()

    def _hide_pip(self):
        self._bridge.frame_ready.disconnect()
        self._bridge.frame_ready.connect(self._update_frame)
        self._pip.close()
        self._pip = None
        self.showNormal()

    def _blink_dot(self):
        self._dot_visible = not self._dot_visible
        self._dot.setStyleSheet(
            f"color: {'#10b981' if self._dot_visible else 'transparent'}; font-size: 9px; background: transparent;"
        )

    def _toggle_guide(self):
        self._guide_open = not self._guide_open
        target = 320 if self._guide_open else 0

        self._a1 = QPropertyAnimation(self._guide, b"minimumWidth")
        self._a1.setDuration(350)
        self._a1.setStartValue(self._guide.width())
        self._a1.setEndValue(target)
        self._a1.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._a2 = QPropertyAnimation(self._guide, b"maximumWidth")
        self._a2.setDuration(350)
        self._a2.setStartValue(self._guide.width())
        self._a2.setEndValue(target)
        self._a2.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._a1.start()
        self._a2.start()

        if self._guide_open:
            self._btn_guide.setStyleSheet("""
                QPushButton#btnGuide {
                    background: rgba(109,40,217,0.15);
                    color: #a78bfa;
                    border: 1px solid rgba(109,40,217,0.35);
                    border-radius: 9px;
                    padding: 12px 20px;
                    font-size: 14px;
                }
                QPushButton#btnGuide:hover { background: rgba(109,40,217,0.25); }
            """)
        else:
            self._btn_guide.setStyleSheet("")
            self._apply_styles()

    def _toggle_pipeline(self):
        if self._pipeline is None:
            self._feed._label.setText("STARTING...")
            self._btn_start.setEnabled(False)
            QApplication.processEvents()

            try:
                self._pipeline = GesturePipeline()
                self._pipeline.on_frame = self._bridge.push
                self._pipeline.start()
                self._accepting_frames = True

                self._btn_start.setEnabled(True)
                self._btn_start.setText("■  Stop")
                self._btn_start.setStyleSheet("""
                    QPushButton#btnStart {
                        background: rgba(239,68,68,0.12);
                        color: #f87171;
                        border: 1px solid rgba(239,68,68,0.3);
                        border-radius: 9px;
                        padding: 12px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                    QPushButton#btnStart:hover {
                        background: #ef4444;
                        color: #fff;
                        border-color: #ef4444;
                    }
                    QPushButton#btnStart:pressed { background: #dc2626; color: #fff; }
                """)

            except (LDPlayerNotFoundError, CameraNotFoundError) as e:
                self._pipeline = None
                self._feed.reset()
                self._btn_start.setEnabled(True)
                self._apply_styles()
                ErrorDialog(str(e), parent=self).exec()

        else:
            self._accepting_frames = False
            self._pipeline.stop()
            self._pipeline = None
            self._feed.reset()
            self._btn_start.setText("▶  Start")
            self._apply_styles()

    def _update_frame(self, qimg):
        if not self._accepting_frames:
            return
        self._feed.update_frame(qimg)

    def closeEvent(self, event):
        if self._pipeline:
            self._accepting_frames = False
            self._pipeline.stop()
        event.accept()

    def changeEvent(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self._pipeline is not None:
                event.ignore()
                self.hide()
                self._show_pip()
        super().changeEvent(event)


# ─── Entry ────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gesture Controller")
    window = GestureApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()