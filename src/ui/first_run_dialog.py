"""First-run setup and initial model download dialog."""

import os
import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QMessageBox, QFrame
)

from src.engine.model_downloader import (
    ModelDownloadWorker,
    is_model_installed,
    MODELS_CATALOG,
)


class FirstRunDialog(QDialog):
    """Clean onboarding dialog to download the base Whisper model."""

    setup_completed = pyqtSignal()

    def __init__(self, parent=None, default_model: str = "small"):
        super().__init__(parent)
        self.default_model = default_model
        self.worker = None

        self.setWindowTitle("🚀 Добро пожаловать в VoxTurbo AI")
        self.setFixedSize(500, 320)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Inter, sans-serif;
            }
            QLabel {
                color: #cdd6f4;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 6px;
                text-align: center;
                background-color: #313244;
                color: #ffffff;
                font-weight: bold;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Title
        title_lbl = QLabel("🎙️ Первоначальная настройка VoxTurbo AI")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #89b4fa;")
        layout.addWidget(title_lbl)

        # Description
        desc_lbl = QLabel(
            "Для ультрабыстрого распознавания речи без задержек необходимо "
            "загрузить стартовую нейросетевую модель **Whisper Small** (~465 МБ).\n\n"
            "После этого приложение будет работать полностью локально без интернета."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #a6adc8; font-size: 13px; line-height: 1.4;")
        layout.addWidget(desc_lbl)

        # Progress bar & status
        self.status_lbl = QLabel("Готов к загрузке")
        self.status_lbl.setStyleSheet("color: #fab387; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ Скачать модель и начать")
        self.btn_download.clicked.connect(self._start_download)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

    def _start_download(self):
        """Start downloading the default model via background thread."""
        self.btn_download.setEnabled(False)
        self.progress_bar.show()
        self.status_lbl.setText("Соединение с сервером...")

        self.worker = ModelDownloadWorker(self.default_model, self)
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.download_finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, percent: int, dl_mb: float, total_mb: float):
        self.progress_bar.setValue(percent)
        self.status_lbl.setText(f"Загрузка: {dl_mb:.1f} МБ из {total_mb:.1f} МБ ({percent}%)")

    def _on_finished(self, model_key: str, success: bool, error_msg: str):
        if success:
            self.status_lbl.setText("✅ Модель успешно установлена!")
            self.status_lbl.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.btn_download.setText("🚀 Запустить VoxTurbo")
            self.btn_download.setEnabled(True)
            self.btn_download.clicked.disconnect()
            self.btn_download.clicked.connect(self.accept)
        else:
            self.status_lbl.setText(f"❌ Ошибка: {error_msg}")
            self.status_lbl.setStyleSheet("color: #f38ba8;")
            self.btn_download.setEnabled(True)
            self.btn_download.setText("🔄 Повторить загрузку")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)
