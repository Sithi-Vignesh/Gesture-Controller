from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from config import resource_path

PIP_WIDTH  = 300
PIP_HEIGHT = 214  # 30 top bar + 154 feed + 30 bottom bar

class PiPWindow(QWidget):
    expand_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedSize(PIP_WIDTH, PIP_HEIGHT)
        self._drag_pos = None
        self._build_ui()
        self._apply_styles()
        self._position_bottom_right()

    def _build_ui(self):
        # Simple vertical stack: top bar → feed → bottom bar
        # No transparency tricks — everything is opaque
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── top bar
        top_bar = QWidget()
        top_bar.setObjectName("pipTopBar")
        top_bar.setFixedHeight(30)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 8, 0)
        top_layout.setSpacing(6)

        self._live_label = QLabel("● LIVE")
        self._live_label.setObjectName("pipLive")

        self._btn_expand = QPushButton("↗")
        self._btn_expand.setObjectName("pipExpand")
        self._btn_expand.setFixedSize(22, 22)
        self._btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_expand.clicked.connect(self.expand_clicked.emit)

        top_layout.addWidget(self._live_label)
        top_layout.addStretch()
        top_layout.addWidget(self._btn_expand)
        layout.addWidget(top_bar)

        # ── camera feed
        self._feed = QLabel()
        self._feed.setObjectName("pipFeed")
        self._feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._feed, stretch=1)

        # ── bottom bar
        bot_bar = QWidget()
        bot_bar.setObjectName("pipBotBar")
        bot_bar.setFixedHeight(30)
        bot_layout = QHBoxLayout(bot_bar)
        bot_layout.setContentsMargins(10, 0, 10, 0)

        self._gesture_label = QLabel("—")
        self._gesture_label.setObjectName("pipGesture")
        self._gesture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bot_layout.addWidget(self._gesture_label)
        layout.addWidget(bot_bar)

    def _apply_styles(self):
        self.setStyleSheet("""
            /* window border */
            QWidget#pipWindow {
                border: 1px solid rgba(255, 230, 0, 0.35);
                border-radius: 10px;
                background-color: #0A0A0A;
            }

            /* top bar */
            QWidget#pipTopBar {
                background-color: #111111;
                border-bottom: 1px solid rgba(255, 230, 0, 0.12);
            }

            /* live label */
            QLabel#pipLive {
                font-family: 'JetBrains Mono';
                font-size: 10px;
                color: #FFE600;
                letter-spacing: 2px;
                background: transparent;
            }

            /* expand button */
            QPushButton#pipExpand {
                background: rgba(255, 230, 0, 0.07);
                border: 1px solid rgba(255, 230, 0, 0.2);
                border-radius: 4px;
                color: #888888;
                font-size: 12px;
            }
            QPushButton#pipExpand:hover {
                background: rgba(255, 230, 0, 0.15);
                border-color: rgba(255, 230, 0, 0.5);
                color: #FFE600;
            }
            QPushButton#pipExpand:pressed {
                background: rgba(255, 230, 0, 0.05);
            }

            /* camera feed */
            QLabel#pipFeed {
                background-color: #0A0A0A;
            }

            /* bottom bar */
            QWidget#pipBotBar {
                background-color: #111111;
                border-top: 1px solid rgba(255, 230, 0, 0.12);
            }

            /* gesture label */
            QLabel#pipGesture {
                font-family: 'JetBrains Mono';
                font-size: 10px;
                color: #555555;
                background: transparent;
                letter-spacing: 1px;
            }
        """)

    def _position_bottom_right(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right()  - PIP_WIDTH  - 16
        y = screen.bottom() - PIP_HEIGHT - 16
        self.move(x, y)

    def update_frame(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg).scaled(
            self._feed.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._feed.setPixmap(pixmap)

    def set_gesture(self, gesture: str):
        if gesture:
            self._gesture_label.setText(gesture)
            self._gesture_label.setStyleSheet(
                "font-family: 'JetBrains Mono'; font-size: 10px; "
                "color: #F5F5F5; background: transparent; letter-spacing: 1px;"
            )
        else:
            self._gesture_label.setText("—")
            self._gesture_label.setStyleSheet(
                "font-family: 'JetBrains Mono'; font-size: 10px; "
                "color: #555555; background: transparent; letter-spacing: 1px;"
            )

    # ── Dragging ──────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None