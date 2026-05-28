from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QIcon
from config import resource_path

PIP_WIDTH  = 280
PIP_HEIGHT = 200

class PiPWindow(QWidget):
    expand_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedSize(PIP_WIDTH, PIP_HEIGHT)
        self._drag_pos = None
        self._build_ui()
        self._apply_styles()
        self._position_bottom_right()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # top bar
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setObjectName("pipBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 0, 6, 0)

        title = QLabel("● LIVE")
        title.setObjectName("pipTitle")

        self._btn_expand = QPushButton("↗")
        self._btn_expand.setFixedSize(20, 20)
        self._btn_expand.setObjectName("pipExpand")
        self._btn_expand.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_expand.clicked.connect(self.expand_clicked.emit)

        bar_layout.addWidget(title)
        bar_layout.addStretch()
        bar_layout.addWidget(self._btn_expand)
        layout.addWidget(bar)

        # feed
        self._feed = QLabel()
        self._feed.setObjectName("pipFeed")
        self._feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._feed, stretch=1)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: #09090f;
                border-radius: 12px;
            }
            QWidget#pipBar {
                background: rgba(0,0,0,0.6);
                border-radius: 0px;
            }
            QLabel#pipTitle {
                color: #10b981;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 2px;
                background: transparent;
            }
            QPushButton#pipExpand {
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.6);
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton#pipExpand:hover {
                background: rgba(255,255,255,0.18);
                color: #fff;
            }
            QLabel#pipFeed {
                background: #09090f;
                color: rgba(255,255,255,0.15);
                font-size: 10px;
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

    # ── Dragging ──────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None