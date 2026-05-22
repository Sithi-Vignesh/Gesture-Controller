import sys
import cv2

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPixmap

from core.pipeline import GesturePipeline, LDPlayerNotFoundError, CameraNotFoundError


# ─── Gesture reference ────────────────────────────────────────────────────────

GESTURES = [
    ("Left fist drag",   "Movement",       "WASD"),
    ("Right pinch tap",  "Instant attack",  "E"),
    ("Right pinch drag", "Aimed attack",    "X + mouse"),
    ("Right fist tap",   "Instant super",   "F"),
    ("Right fist drag",  "Aimed super",     "C + mouse"),
    ("Right peace sign", "Hypercharge",     "R"),
    ("Right L-shape",    "Gadget",          "Q"),
]


# ─── Thread-safe frame bridge ─────────────────────────────────────────────────

class FrameBridge(QObject):
    frame_ready = pyqtSignal(QImage)

    def push(self, frame):
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg     = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.frame_ready.emit(qimg.copy())


# ─── Error dialog ─────────────────────────────────────────────────────────────

class ErrorDialog(QDialog):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setModal(True)
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 28)
        layout.setSpacing(0)

        # icon + title row
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        icon = QLabel("⚠")
        icon.setObjectName("errIcon")
        title_row.addWidget(icon)

        title = QLabel("Something went wrong")
        title.setObjectName("errTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        layout.addSpacing(16)

        # message
        msg = QLabel(message)
        msg.setObjectName("errMsg")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(msg)

        layout.addSpacing(28)

        # ok button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("errBtn")
        ok_btn.setFixedWidth(100)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self.setStyleSheet("""
            QDialog {
                background-color: #12121f;
                border: 1px solid #2d2d4a;
                border-radius: 12px;
            }
            QLabel#errIcon {
                font-size: 28px;
                color: #ef4444;
            }
            QLabel#errTitle {
                font-size: 16px;
                font-weight: 600;
                color: #f1f5f9;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#errMsg {
                font-size: 13px;
                color: #94a3b8;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.6;
            }
            QPushButton#errBtn {
                background-color: #ef4444;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 9px 0;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#errBtn:hover   { background-color: #dc2626; }
            QPushButton#errBtn:pressed { background-color: #b91c1c; }
        """)

    def showEvent(self, event):
        # center over parent window
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width()  - self.width())  // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        super().showEvent(event)


# ─── Guide panel ──────────────────────────────────────────────────────────────

class GuidePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("guidePanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("GESTURE GUIDE")
        header.setObjectName("guideHeader")
        layout.addWidget(header)

        table = QTableWidget(len(GESTURES), 3)
        table.setObjectName("guideTable")
        table.setHorizontalHeaderLabels(["Gesture", "Action", "Key"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)

        for row, (gesture, action, key) in enumerate(GESTURES):
            for col, text in enumerate([gesture, action, key]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                table.setItem(row, col, item)

        table.resizeRowsToContents()
        layout.addWidget(table)
        self.hide()


# ─── Main window ──────────────────────────────────────────────────────────────

class GestureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesture Controller")
        self.setMinimumSize(900, 620)

        self._pipeline = None
        self._accepting_frames = False
        self._bridge   = FrameBridge()
        self._bridge.frame_ready.connect(self._update_frame)

        self._build_ui()
        self._apply_styles()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        self._feed = QLabel()
        self._feed.setObjectName("cameraFeed")
        self._feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._feed.setMinimumHeight(300)
        self._feed.setText("Camera feed will appear here")
        main.addWidget(self._feed, stretch=1)

        self._guide = GuidePanel()
        main.addWidget(self._guide)

        bar = QHBoxLayout()
        bar.setSpacing(10)

        self._btn_start = QPushButton("▶  Start")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._toggle_pipeline)

        self._btn_guide = QPushButton("☰  Guide")
        self._btn_guide.setObjectName("btnGuide")
        self._btn_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_guide.setCheckable(True)
        self._btn_guide.clicked.connect(self._toggle_guide)

        bar.addWidget(self._btn_start, stretch=1)
        bar.addWidget(self._btn_guide)
        main.addLayout(bar)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f0f1a;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLabel#cameraFeed {
                background-color: #07070f;
                border-radius: 8px;
                color: #4b5563;
                font-size: 14px;
            }
            QWidget#guidePanel {
                background-color: #0f0f1a;
            }
            QLabel#guideHeader {
                background-color: #16213e;
                color: #64748b;
                padding: 8px 14px;
                font-size: 11px;
                letter-spacing: 1px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTableWidget#guideTable {
                background-color: #0a0a16;
                border: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                color: #cbd5e1;
            }
            QTableWidget#guideTable QHeaderView::section {
                background-color: #16213e;
                color: #64748b;
                padding: 6px 14px;
                border: none;
                font-size: 11px;
            }
            QTableWidget#guideTable::item {
                padding: 7px 14px;
                border-bottom: 1px solid #1e2a3a;
            }
            QPushButton#btnStart {
                background-color: #4f46e5;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton#btnStart:hover   { background-color: #4338ca; }
            QPushButton#btnStart:pressed { background-color: #3730a3; }
            QPushButton#btnGuide {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 14px;
            }
            QPushButton#btnGuide:hover   { background-color: #16213e; color: #e2e8f0; }
            QPushButton#btnGuide:checked { background-color: #16213e; color: #e2e8f0; border-color: #334155; }
        """)

    # ── slots ─────────────────────────────────────────────────────────────────

    def _toggle_pipeline(self):
        if self._pipeline is None:
            # show loading state immediately
            self._feed.setText("Starting camera...")
            self._btn_start.setEnabled(False)
            QApplication.processEvents()

            try:
                self._pipeline = GesturePipeline()
                self._pipeline.on_frame = self._bridge.push
                self._pipeline.start()
                self._accepting_frames = True

                # success — switch to stop mode
                self._btn_start.setEnabled(True)
                self._btn_start.setText("■  Stop")
                self._btn_start.setStyleSheet("""
                    QPushButton#btnStart {
                        background-color: #dc2626;
                        color: #ffffff;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 18px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                    QPushButton#btnStart:hover { background-color: #b91c1c; }
                """)

            except (LDPlayerNotFoundError, CameraNotFoundError) as e:
                # reset state
                self._pipeline = None
                self._feed.setText("Camera feed will appear here")
                self._btn_start.setEnabled(True)
                self._apply_styles()

                # show error dialog centered on window
                dlg = ErrorDialog(str(e), parent=self)
                dlg.exec()

        else:
            self._accepting_frames = False
            self._pipeline.stop()
            self._pipeline = None
            self._feed.setText("Camera feed will appear here")
            self._btn_start.setText("▶  Start")
            self._apply_styles()

    def _toggle_guide(self, checked: bool):
        self._guide.setVisible(checked)

    def _update_frame(self, qimg: QImage):
        if not self._accepting_frames:
            return
        pixmap = QPixmap.fromImage(qimg).scaled(
            self._feed.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._feed.setPixmap(pixmap)

    def closeEvent(self, event):
        if self._pipeline:
            self._pipeline.stop()
        event.accept()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gesture Controller")
    window = GestureApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()