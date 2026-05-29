import sys
import os
import cv2

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QDialog,
    QGraphicsOpacityEffect, QStackedLayout
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QPropertyAnimation,
    QEasingCurve, QTimer, QSequentialAnimationGroup
)
from PyQt6.QtGui import QImage, QPixmap, QIcon

from core.pipeline import GesturePipeline, LDPlayerNotFoundError, CameraNotFoundError
from config import resource_path
from ui.pip_window import PiPWindow
from PyQt6.QtCore import QThread


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

# ─── Pipeline worker ──────────────────────────────────────────────────────────
 
class PipelineStartWorker(QObject):
    success = pyqtSignal()
    error   = pyqtSignal(str)
 
    def __init__(self, pipeline):
        super().__init__()
        self._pipeline = pipeline
 
    def run(self):
        try:
            self._pipeline.start()
            self.success.emit()
        except Exception as e:
            self.error.emit(str(e))


# ─── Frame bridge ─────────────────────────────────────────────────────────────

class FrameBridge(QObject):
    frame_ready = pyqtSignal(QImage)

    def push(self, frame):
        rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch  = rgb.shape
        qimg      = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
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
                btn.setStyleSheet("background: #FFE600; border-radius: 4px; border: none;")
            else:
                btn.setFixedWidth(8)
                btn.setStyleSheet("background: rgba(255,255,255,0.15); border-radius: 4px; border: none;")


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

        nav = QWidget()
        nav.setFixedHeight(48)
        nav.setStyleSheet("background: #141414; border-bottom: 1px solid rgba(255,230,0,0.08);")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(16, 0, 12, 0)

        self._tag = QLabel()
        self._tag.setFixedHeight(22)
        self._tag.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._counter = QLabel()
        self._counter.setStyleSheet(
            "color: #888888; font-size: 11px; background: transparent; font-family: 'JetBrains Mono';"
        )

        self._prev = QPushButton("‹")
        self._next = QPushButton("›")
        for btn in (self._prev, self._next):
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.04);
                    color: #888888;
                    border: 1px solid rgba(255,230,0,0.12);
                    border-radius: 7px; font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(255,230,0,0.08);
                    color: #FFE600;
                    border-color: rgba(255,230,0,0.3);
                }
                QPushButton:pressed { background: rgba(255,230,0,0.04); }
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

        self._img = QLabel()
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setStyleSheet("background: #0A0A0A;")
        self._img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self._img, stretch=1)

        info = QWidget()
        info.setFixedHeight(120)
        info.setStyleSheet("background: #141414; border-top: 1px solid rgba(255,230,0,0.08);")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 14, 16, 12)
        info_layout.setSpacing(4)

        self._gesture_name = QLabel()
        self._gesture_name.setStyleSheet(
            "color: #888888; font-size: 10px; letter-spacing: 1.5px; background: transparent;"
        )

        self._action = QLabel()
        self._action.setStyleSheet(
            "color: #F5F5F5; font-size: 17px; font-weight: 600; background: transparent;"
        )

        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        key_row.setContentsMargins(0, 0, 0, 0)

        key_lbl = QLabel("KEY")
        key_lbl.setStyleSheet(
            "color: #888888; font-size: 10px; letter-spacing: 1px; background: transparent;"
        )

        self._key = QLabel()
        self._key.setFixedHeight(22)
        self._key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._key.setStyleSheet("""
            background: rgba(255,230,0,0.08);
            color: #FFE600;
            border: 1px solid rgba(255,230,0,0.25);
            border-radius: 5px;
            font-size: 11px;
            font-family: 'JetBrains Mono';
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

        dots_wrap = QWidget()
        dots_wrap.setFixedHeight(30)
        dots_wrap.setStyleSheet("background: #141414;")
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
        self._seq.stateChanged.connect(
            lambda state, _: self._refresh() if state == QSequentialAnimationGroup.State.Running and
            self._seq.currentAnimation() == fade_in else None
        )
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
            self._img.setStyleSheet("background: #0A0A0A; color: #333333; font-size: 12px;")

        self._dots.set_current(self._current)


# ─── Feed widget ──────────────────────────────────────────────────────────────

# ─── Feed widget ──────────────────────────────────────────────────────────────

class FeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0A0A0A;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # ── idle state widget
        self._idle = QWidget()
        self._idle.setStyleSheet("background-color: #0A0A0A;")
        idle_layout = QVBoxLayout(self._idle)
        idle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_layout.setSpacing(16)
        icon_lbl = QLabel()
        icon_pix = QPixmap(resource_path("icon.png"))
        if not icon_pix.isNull():
            effect = QGraphicsOpacityEffect()
            effect.setOpacity(0.25)
            icon_lbl.setGraphicsEffect(effect)
            icon_lbl.setPixmap(
                icon_pix.scaled(
                    56, 56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")

        self._idle_text = QLabel("TAP START TO BEGIN")
        self._idle_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._idle_text.setStyleSheet("""
            background: transparent;
            color: #444444;
            font-family: 'JetBrains Mono';
            font-size: 12px;
            letter-spacing: 4px;
        """)

        idle_layout.addWidget(icon_lbl)
        idle_layout.addWidget(self._idle_text)
        self._layout.addWidget(self._idle)

        # ── camera feed label (hidden until start)
        self._label = QLabel()
        self._label.setObjectName("cameraFeed")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._label.setStyleSheet("background-color: #0A0A0A;")
        self._label.hide()
        self._layout.addWidget(self._label)

    def update_frame(self, qimg):
        if self._idle.isVisible():
            self._idle.hide()
            self._label.show()

        pixmap = QPixmap.fromImage(qimg).scaled(
            self._label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(pixmap)

    def reset(self):
        self._label.hide()
        self._label.clear()
        self._idle.show()
        self._idle_text.setText("TAP START TO BEGIN")
    
    def set_idle_text(self, text: str):
        self._idle_text.setText(text)

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
        title.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #fff; background: transparent;"
        )
        layout.addWidget(title)
        layout.addSpacing(8)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.45); background: transparent;"
        )
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
                background: #141414;
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
        self._pip              = None

        # live dot pulse
        self._dot_visible = True
        self._dot_timer   = QTimer()
        self._dot_timer.setInterval(900)
        self._dot_timer.timeout.connect(self._pulse_dot)

        self._bridge = FrameBridge()
        self._bridge.frame_ready.connect(self._update_frame)

        self._build_ui()
        self._load_stylesheet()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("centralWidget")
        self.setCentralWidget(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # ── custom title bar
        tb = QWidget()
        tb.setFixedHeight(46)
        tb.setObjectName("titlebar")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(16, 0, 16, 0)
        tbl.setSpacing(0)

        icon_lbl = QLabel()
        icon_pix = QPixmap(resource_path("icon.png"))
        if not icon_pix.isNull():
            icon_lbl.setPixmap(
                icon_pix.scaled(
                    22, 22,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        icon_lbl.setStyleSheet("background: transparent;")

        brand_gesture = QLabel("GESTURE")
        brand_gesture.setStyleSheet(
            "color: #FFE600; font-family: 'Bebas Neue'; font-size: 17px; "
            "letter-spacing: 1px; background: transparent; padding-left: 8px;"
        )
        brand_controller = QLabel("CONTROLLER")
        brand_controller.setStyleSheet(
            "color: #F5F5F5; font-family: 'Bebas Neue'; font-size: 17px; "
            "letter-spacing: 1px; background: transparent; padding-left: 5px;"
        )

        self._dot = QLabel("●")
        self._dot.setStyleSheet(
            "color: transparent; font-size: 8px; background: transparent; padding-left: 10px;"
        )

        tbl.addWidget(icon_lbl)
        tbl.addWidget(brand_gesture)
        tbl.addWidget(brand_controller)
        tbl.addWidget(self._dot)
        tbl.addStretch()
        rl.addWidget(tb)

        # title bar separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(255,230,0,0.15);")
        rl.addWidget(sep)

        # ── camera feed
        self._feed = FeedWidget()
        rl.addWidget(self._feed, stretch=1)

        # bottom bar separator
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: rgba(255,230,0,0.15);")
        rl.addWidget(sep2)

        # ── bottom bar
        bot = QWidget()
        bot.setFixedHeight(72)
        bot.setObjectName("bottomBar")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(16, 0, 16, 0)

        self._btn_start = QPushButton("▶  START")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._toggle_pipeline)

        bl.addWidget(self._btn_start)
        rl.addWidget(bot)

    # ── Stylesheet ────────────────────────────────────────────────────────────

    def _load_stylesheet(self):
        qss_path = resource_path("style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def _set_button_state(self, state: str):
        if state == "stop":
            self._btn_start.setObjectName("btnStop")
            self._btn_start.setText("■  STOP")
        else:
            self._btn_start.setObjectName("btnStart")
            self._btn_start.setText("▶  START")
        self._btn_start.setStyle(self._btn_start.style())

    # ── Live dot pulse ────────────────────────────────────────────────────────

    def _pulse_dot(self):
        self._dot_visible = not self._dot_visible
        color = "#FFE600" if self._dot_visible else "rgba(255,230,0,0.15)"
        self._dot.setStyleSheet(
            f"color: {color}; font-size: 8px; background: transparent; padding-left: 10px;"
        )

    # ── PiP ───────────────────────────────────────────────────────────────────

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

    # ── Pipeline toggle ───────────────────────────────────────────────────────

    def _toggle_pipeline(self):
        if self._pipeline is None:
            self._btn_start.setEnabled(False)
            self._btn_start.setText("STARTING...")
            self._feed.set_idle_text("STARTING CAMERA...\nTHIS MAY TAKE A FEW SECONDS")
            self._btn_start.setStyle(self._btn_start.style())
            QApplication.processEvents()
 
            self._pipeline = GesturePipeline()
            self._pipeline.on_frame = self._bridge.push
 
            self._worker = PipelineStartWorker(self._pipeline)
            self._thread = QThread()
            self._worker.moveToThread(self._thread)
 
            self._thread.started.connect(self._worker.run)
            self._worker.success.connect(self._on_start_success)
            self._worker.error.connect(self._on_start_error)
            self._worker.success.connect(self._thread.quit)
            self._worker.error.connect(self._thread.quit)
 
            self._thread.start()
 
        else:
            self._accepting_frames = False
            self._pipeline.stop()
            self._pipeline = None
            self._dot_timer.stop()
            self._dot.setStyleSheet(
                "color: transparent; font-size: 8px; "
                "background: transparent; padding-left: 10px;"
            )
            self._feed.reset()
            self._set_button_state("start")
 
    def _on_start_success(self):
        self._accepting_frames = True
        self._btn_start.setEnabled(True)
        self._set_button_state("stop")
        self._dot_timer.start()
 
    def _on_start_error(self, message):
        self._pipeline = None
        self._feed.reset()
        self._btn_start.setEnabled(True)
        self._set_button_state("start")
        ErrorDialog(message, parent=self).exec()

    # ── Frame update ──────────────────────────────────────────────────────────

    def _update_frame(self, qimg):
        if not self._accepting_frames:
            return
        self._feed.update_frame(qimg)

    # ── Window events ─────────────────────────────────────────────────────────

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