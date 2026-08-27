"""Settings and preferences graphical dialog (PyQt5)."""

import os
import sys
import logging
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QProgressBar, QGroupBox, QFormLayout, QMessageBox, QLineEdit
)

from src.config import (
    CONFIG_FILE,
    WAKEWORDS_DIR,
    load_user_config,
    save_user_config,
    get_model_path,
    WHISPER_CPP_MODELS_DIR,
)


class SettingsDialog(QDialog):
    """Modern dark-themed preferences and configuration window."""

    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None, detector=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ VoxTurbo AI — Настройки")
        self.resize(560, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.cfg = load_user_config()
        self.detector = detector
        self._test_stream = None
        self._test_timer = QTimer(self)
        self._test_timer.timeout.connect(self._update_meter)
        self._latest_volume = 0.0

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Construct tabs and layout."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Inter, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                border-radius: 8px;
                background-color: #181825;
                padding: 10px;
            }
            QTabBar::tab {
                background: #181825;
                color: #a6adc8;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #313244;
                color: #89b4fa;
                font-weight: bold;
            }
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 14px;
                color: #89b4fa;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                min-height: 22px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
            QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
            }
            QProgressBar {
                background-color: #313244;
                border-radius: 4px;
                text-align: center;
                color: #11111b;
                font-weight: bold;
                height: 16px;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton#btnCancel {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
            }
            QPushButton#btnCancel:hover {
                background-color: #45475a;
            }
        """)

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tab_audio = QWidget()
        self.tab_engine = QWidget()
        self.tab_wakeword = QWidget()
        self.tab_hotkey = QWidget()
        self.tab_models = QWidget()

        self._build_audio_tab()
        self._build_engine_tab()
        self._build_wakeword_tab()
        self._build_hotkey_tab()
        self._build_models_tab()

        self.tabs.addTab(self.tab_audio, "🎙️ Аудио")
        self.tabs.addTab(self.tab_engine, "⚡ Движок")
        self.tabs.addTab(self.tab_wakeword, "🗣️ Wake Word")
        self.tabs.addTab(self.tab_hotkey, "⌨️ Хоткеи")
        self.tabs.addTab(self.tab_models, "📦 Модели")

        main_layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 Сохранить и применить")
        self.btn_save.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _build_audio_tab(self):
        """Audio device selection and live level meter."""
        layout = QVBoxLayout(self.tab_audio)

        grp_dev = QGroupBox("Источник звука (Микрофон)")
        form_dev = QFormLayout(grp_dev)

        self.combo_mic = QComboBox()
        self._populate_audio_devices()
        form_dev.addRow("Устройство ввода:", self.combo_mic)

        layout.addWidget(grp_dev)

        grp_meter = QGroupBox("Проверка микрофона")
        vbox_meter = QVBoxLayout(grp_meter)

        self.meter_bar = QProgressBar()
        self.meter_bar.setRange(0, 100)
        self.meter_bar.setValue(0)
        vbox_meter.addWidget(self.meter_bar)

        self.btn_test_mic = QPushButton("▶ Тест микрофона")
        self.btn_test_mic.setObjectName("btnCancel")
        self.btn_test_mic.clicked.connect(self._toggle_mic_test)
        vbox_meter.addWidget(self.btn_test_mic)

        layout.addWidget(grp_meter)
        layout.addStretch()

    def _build_engine_tab(self):
        """AI engines and performance settings."""
        layout = QVBoxLayout(self.tab_engine)

        grp_engine = QGroupBox("Нейросетевой движок распознавания")
        form_eng = QFormLayout(grp_engine)

        self.combo_engine = QComboBox()
        self.combo_engine.addItem("⚡ GigaAM v2 Conformer (SOTA Русский язык ~0.5x)", "gigaam_v2")
        self.combo_engine.addItem("🎯 Whisper Large-v3-Turbo Q5_0 (548 MB)", "q5_0")
        self.combo_engine.addItem("🚀 Whisper Large-v3-Turbo Q8_0 (833 MB)", "q8_0")
        self.combo_engine.addItem("📦 Whisper Small (466 MB)", "small")
        self.combo_engine.addItem("⚡ Whisper Base (142 MB)", "base")
        form_eng.addRow("Активная модель:", self.combo_engine)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("⚡ Автоопределение на лету (Auto)", "auto")
        self.combo_lang.addItem("🇷🇺 Русский (ru)", "ru")
        self.combo_lang.addItem("🇰🇿 Казахский (kk)", "kk")
        self.combo_lang.addItem("🇬🇧 Английский (en)", "en")
        self.combo_lang.addItem("🇹🇷 Турецкий (tr / Türkçe)", "tr")
        form_eng.addRow("Язык диктовки:", self.combo_lang)

        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 32)
        self.spin_threads.setValue(4)
        form_eng.addRow("Потоки CPU:", self.spin_threads)

        layout.addWidget(grp_engine)

        grp_opt = QGroupBox("Улучшения и функции")
        vbox_opt = QVBoxLayout(grp_opt)

        self.chk_punct = QCheckBox("🔤 Умная пунктуация и капитализация (Silero TE)")
        vbox_opt.addWidget(self.chk_punct)

        self.chk_hud = QCheckBox("✨ Всплывающий оверлей громкости (Floating Voice HUD)")
        vbox_opt.addWidget(self.chk_hud)

        layout.addWidget(grp_opt)
        layout.addStretch()

    def _build_wakeword_tab(self):
        """Voice wake word activation settings."""
        layout = QVBoxLayout(self.tab_wakeword)

        grp_ww = QGroupBox("Активация голосом (Hands-Free)")
        form_ww = QFormLayout(grp_ww)

        self.chk_wakeword = QCheckBox("🎙️ Включить постоянную голосовую активацию (Wake Word)")
        form_ww.addRow(self.chk_wakeword)

        self.combo_ww_model = QComboBox()
        available = self.detector.get_available_models() if self.detector else [
            "hey_jarvis", "alexa", "hey_mycroft", "hey_rhasspy", "timer", "weather"
        ]
        labels = {
            "hey_jarvis": "🤖 Hey Jarvis (Рекомендуется)",
            "alexa": "🔵 Alexa",
            "hey_mycroft": "🦊 Hey Mycroft",
            "hey_rhasspy": "🗣️ Hey Rhasspy",
            "timer": "⏱️ Timer",
            "weather": "⛅ Weather"
        }
        for m in available:
            lbl = labels.get(m, f"📦 {m} (Кастомная ONNX)")
            self.combo_ww_model.addItem(lbl, m)
        form_ww.addRow("Ключевое слово:", self.combo_ww_model)

        self.spin_ww_thresh = QDoubleSpinBox()
        self.spin_ww_thresh.setRange(0.1, 1.0)
        self.spin_ww_thresh.setSingleStep(0.05)
        self.spin_ww_thresh.setValue(0.6)
        form_ww.addRow("Чувствительность (Порог):", self.spin_ww_thresh)

        self.spin_ww_silence = QDoubleSpinBox()
        self.spin_ww_silence.setRange(0.3, 3.0)
        self.spin_ww_silence.setSingleStep(0.1)
        self.spin_ww_silence.setValue(0.8)
        self.spin_ww_silence.setSuffix(" сек")
        form_ww.addRow("Автозавершение при паузе:", self.spin_ww_silence)

        self.chk_ww_beep = QCheckBox("🔔 Звуковой сигнал при срабатывании")
        form_ww.addRow(self.chk_ww_beep)

        layout.addWidget(grp_ww)

        grp_info = QGroupBox("Кастомные модели и новые слова")
        vbox_info = QVBoxLayout(grp_info)
        lbl_info = QLabel(
            f"Вы можете добавить свои обученные модели (на русском, турецком или английском), "
            f"поместив <b>.onnx</b> файлы в директорию:<br>"
            f"<code style='color: #89b4fa;'>{WAKEWORDS_DIR}</code>"
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #a6adc8; font-size: 12px;")
        vbox_info.addWidget(lbl_info)
        layout.addWidget(grp_info)

        layout.addStretch()

    def _build_hotkey_tab(self):
        """Global shortcut settings."""
        layout = QVBoxLayout(self.tab_hotkey)

        grp_hk = QGroupBox("Глобальный хоткей записи")
        form_hk = QFormLayout(grp_hk)

        self.combo_hotkey = QComboBox()
        self.combo_hotkey.addItem("Super + Space (Win + Space)", "super_space")
        self.combo_hotkey.addItem("Alt + Space", "alt_space")
        self.combo_hotkey.addItem("Ctrl + Shift + Space", "ctrl_shift_space")
        self.combo_hotkey.addItem("F8 (Одиночная клавиша)", "f8")
        form_hk.addRow("Комбинация:", self.combo_hotkey)

        lbl_desc = QLabel(
            "ℹ️ Нажатие хоткея включает запись. Повторное нажатие "
            "останавливает запись и сразу вставляет распознанный текст под курсор."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #a6adc8; font-size: 12px;")
        form_hk.addRow(lbl_desc)

        layout.addWidget(grp_hk)
        layout.addStretch()

    def _build_models_tab(self):
        """Dynamic model manager with download / delete actions and live progress."""
        from src.engine.model_downloader import (
            MODELS_CATALOG,
            is_model_installed,
            ModelDownloadWorker,
        )

        layout = QVBoxLayout(self.tab_models)

        grp_info = QGroupBox("Управление языковыми моделями")
        self.vbox_models = QVBoxLayout(grp_info)

        self.model_rows = {}
        self.active_downloader = None

        for key, info in MODELS_CATALOG.items():
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 4, 0, 4)

            name_lbl = QLabel(f"<b>{info['name']}</b> (~{info['size_mb']} МБ)")
            name_lbl.setStyleSheet("color: #cdd6f4;")
            row_layout.addWidget(name_lbl, 1)

            status_lbl = QLabel()
            status_lbl.setObjectName(f"status_{key}")
            row_layout.addWidget(status_lbl)

            btn_action = QPushButton()
            btn_action.setObjectName(f"btn_{key}")
            row_layout.addWidget(btn_action)

            self.model_rows[key] = {
                "widget": row_widget,
                "status_lbl": status_lbl,
                "btn_action": btn_action,
                "info": info
            }

            self.vbox_models.addWidget(row_widget)
            self._update_model_row_state(key)

        layout.addWidget(grp_info)

        # Global download progress bar in models tab
        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 100)
        self.model_progress.setValue(0)
        self.model_progress.hide()
        layout.addWidget(self.model_progress)

        self.lbl_download_status = QLabel("")
        self.lbl_download_status.setStyleSheet("color: #fab387; font-size: 11px;")
        layout.addWidget(self.lbl_download_status)

        grp_paths = QGroupBox("Расположение файлов")
        form_p = QFormLayout(grp_paths)
        lbl_cfg_path = QLabel(CONFIG_FILE)
        lbl_cfg_path.setStyleSheet("color: #89b4fa; font-size: 11px;")
        form_p.addRow("Конфигурация:", lbl_cfg_path)

        lbl_models_path = QLabel(WHISPER_CPP_MODELS_DIR)
        lbl_models_path.setStyleSheet("color: #89b4fa; font-size: 11px;")
        form_p.addRow("Папка моделей:", lbl_models_path)

        layout.addWidget(grp_paths)
        layout.addStretch()

    def _update_model_row_state(self, key: str):
        """Update single model row button and status label."""
        from src.engine.model_downloader import is_model_installed
        row = self.model_rows.get(key)
        if not row:
            return

        installed = is_model_installed(key)
        if installed:
            row["status_lbl"].setText("✅ Установлена")
            row["status_lbl"].setStyleSheet("color: #a6e3a1; font-weight: bold;")
            row["btn_action"].setText("🗑️ Удалить")
            row["btn_action"].setStyleSheet("background-color: #313244; color: #f38ba8;")
            row["btn_action"].setEnabled(True)
            try:
                row["btn_action"].clicked.disconnect()
            except Exception:
                pass
            row["btn_action"].clicked.connect(lambda checked, k=key: self._delete_model(k))
        else:
            row["status_lbl"].setText("❌ Не скачана")
            row["status_lbl"].setStyleSheet("color: #6c7086;")
            row["btn_action"].setText(f"⬇️ Скачать")
            row["btn_action"].setStyleSheet("background-color: #89b4fa; color: #11111b;")
            row["btn_action"].setEnabled(True)
            try:
                row["btn_action"].clicked.disconnect()
            except Exception:
                pass
            row["btn_action"].clicked.connect(lambda checked, k=key: self._download_model(k))

    def _download_model(self, key: str):
        """Start downloading requested model."""
        if self.active_downloader and self.active_downloader.isRunning():
            QMessageBox.information(self, "Загрузка", "В данный момент уже загружается другая модель.")
            return

        from src.engine.model_downloader import ModelDownloadWorker, MODELS_CATALOG
        info = MODELS_CATALOG.get(key)
        if not info:
            return

        row = self.model_rows.get(key)
        if row:
            row["btn_action"].setEnabled(False)
            row["status_lbl"].setText("⏳ Загрузка...")
            row["status_lbl"].setStyleSheet("color: #fab387;")

        self.model_progress.show()
        self.lbl_download_status.setText(f"Подключение для скачивания {info['name']}...")

        self.active_downloader = ModelDownloadWorker(key, self)
        self.active_downloader.progress_changed.connect(
            lambda pct, dl, tot: self._on_model_progress(key, pct, dl, tot)
        )
        self.active_downloader.download_finished.connect(self._on_model_finished)
        self.active_downloader.start()

    def _on_model_progress(self, key: str, percent: int, dl_mb: float, total_mb: float):
        self.model_progress.setValue(percent)
        self.lbl_download_status.setText(f"Загрузка {key}: {dl_mb:.1f} МБ / {total_mb:.1f} МБ ({percent}%)")

    def _on_model_finished(self, key: str, success: bool, error: str):
        self.model_progress.hide()
        if success:
            self.lbl_download_status.setText(f"✅ Модель {key} успешно загружена!")
            self.lbl_download_status.setStyleSheet("color: #a6e3a1;")
        else:
            self.lbl_download_status.setText(f"❌ Ошибка загрузки {key}: {error}")
            self.lbl_download_status.setStyleSheet("color: #f38ba8;")
        self._update_model_row_state(key)

    def _delete_model(self, key: str):
        """Delete model file from disk to free up space."""
        from src.engine.model_downloader import MODELS_CATALOG
        info = MODELS_CATALOG.get(key)
        if not info:
            return

        path = os.path.join(WHISPER_CPP_MODELS_DIR, info["filename"])
        if os.path.exists(path):
            reply = QMessageBox.question(
                self, "Удаление модели",
                f"Вы уверены, что хотите удалить модель {info['name']}?\nФайл: {path}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    os.remove(path)
                    self._update_model_row_state(key)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить файл: {e}")

    def _populate_audio_devices(self):
        """Query available audio input devices."""
        self.combo_mic.clear()
        self.combo_mic.addItem("По умолчанию (Системный микрофон)", -1)
        try:
            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    name = dev.get('name', f"Устройство {idx}")
                    self.combo_mic.addItem(f"{name} (ID: {idx})", idx)
        except Exception as e:
            logging.error(f"[Settings] Error querying sound devices: {e}")

    def _toggle_mic_test(self):
        """Start or stop live microphone VU-meter test."""
        if self._test_stream is None:
            try:
                dev_idx = self.combo_mic.currentData()
                device = None if dev_idx == -1 else dev_idx
                self._test_stream = sd.InputStream(
                    device=device,
                    channels=1,
                    samplerate=16000,
                    callback=self._audio_test_callback
                )
                self._test_stream.start()
                self._test_timer.start(50)
                self.btn_test_mic.setText("⏹ Остановить тест")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка аудио", f"Не удалось открыть микрофон: {e}")
        else:
            self._stop_mic_test()

    def _stop_mic_test(self):
        """Stop mic testing stream."""
        if self._test_stream:
            try:
                self._test_stream.stop()
                self._test_stream.close()
            except Exception:
                pass
            self._test_stream = None
        self._test_timer.stop()
        self.meter_bar.setValue(0)
        self.btn_test_mic.setText("▶ Тест микрофона")

    def _audio_test_callback(self, indata, frames, time_info, status):
        """Compute RMS volume level."""
        rms = np.sqrt(np.mean(indata**2))
        self._latest_volume = float(np.clip(rms * 300, 0, 100))

    def _update_meter(self):
        """Update VU meter progress bar."""
        self.meter_bar.setValue(int(self._latest_volume))

    def _load_values(self):
        """Load values from config dict to UI controls."""
        quant = self.cfg.get("model_quant", "gigaam_v2")
        idx = self.combo_engine.findData(quant)
        if idx >= 0:
            self.combo_engine.setCurrentIndex(idx)

        lang = self.cfg.get("language", "auto")
        idx_lang = self.combo_lang.findData(lang)
        if idx_lang >= 0:
            self.combo_lang.setCurrentIndex(idx_lang)

        self.spin_threads.setValue(self.cfg.get("threads", 4))
        self.chk_punct.setChecked(self.cfg.get("enable_punctuation", True))
        self.chk_hud.setChecked(self.cfg.get("enable_hud", True))

        # Wake word values
        self.chk_wakeword.setChecked(self.cfg.get("enable_wakeword", False))
        ww_model = self.cfg.get("wakeword_model", "hey_jarvis")
        idx_ww = self.combo_ww_model.findData(ww_model)
        if idx_ww >= 0:
            self.combo_ww_model.setCurrentIndex(idx_ww)
        self.spin_ww_thresh.setValue(float(self.cfg.get("wakeword_threshold", 0.6)))
        self.spin_ww_silence.setValue(float(self.cfg.get("wakeword_silence_duration", 0.8)))
        self.chk_ww_beep.setChecked(self.cfg.get("wakeword_beep", True))

    def _save_and_apply(self):
        """Save form to config file and emit signal."""
        self._stop_mic_test()

        new_cfg = {
            "model_quant": self.combo_engine.currentData(),
            "engine": "gigaam" if self.combo_engine.currentData() == "gigaam_v2" else "whisper",
            "language": self.combo_lang.currentData(),
            "threads": self.spin_threads.value(),
            "enable_punctuation": self.chk_punct.isChecked(),
            "enable_hud": self.chk_hud.isChecked(),
            "audio_device_id": self.combo_mic.currentData(),
            "enable_wakeword": self.chk_wakeword.isChecked(),
            "wakeword_model": self.combo_ww_model.currentData(),
            "wakeword_threshold": self.spin_ww_thresh.value(),
            "wakeword_silence_duration": self.spin_ww_silence.value(),
            "wakeword_beep": self.chk_ww_beep.isChecked()
        }

        self.cfg.update(new_cfg)
        save_user_config(self.cfg)
        self.settings_saved.emit(self.cfg)
        self.accept()

    def closeEvent(self, event):
        self._stop_mic_test()
        super().closeEvent(event)
