"""Settings and preferences graphical dialog (PyQt5)."""

import os
import sys
import logging
import sounddevice as sd
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QProgressBar, QGroupBox, QFormLayout, QMessageBox, QLineEdit
)

from src.config import (
    CONFIG_FILE,
    load_user_config,
    save_user_config,
    get_model_path,
    WHISPER_CPP_MODELS_DIR,
)


class SettingsDialog(QDialog):
    """Modern dark-themed preferences and configuration window."""

    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ VoxTurbo AI — Настройки")
        self.resize(540, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.cfg = load_user_config()
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
            QComboBox, QSpinBox, QLineEdit {
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
                padding: 8px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton#btnCancel {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#btnCancel:hover {
                background-color: #45475a;
            }
        """)

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tab_audio = QWidget()
        self.tab_engine = QWidget()
        self.tab_hotkey = QWidget()
        self.tab_models = QWidget()

        self._build_audio_tab()
        self._build_engine_tab()
        self._build_hotkey_tab()
        self._build_models_tab()

        self.tabs.addTab(self.tab_audio, "🎙️ Аудио")
        self.tabs.addTab(self.tab_engine, "⚡ Движок")
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
        """Local model cache directory and status."""
        layout = QVBoxLayout(self.tab_models)

        grp_status = QGroupBox("Статус локальных моделей")
        form_st = QFormLayout(grp_status)

        # Check GigaAM v2
        lbl_gigaam = QLabel("✅ Загружается в RAM при старте (~480 MB)")
        form_st.addRow("GigaAM v2 Conformer:", lbl_gigaam)

        # Check Silero TE
        lbl_te = QLabel("✅ Silero TE v2 (~25 MB)")
        form_st.addRow("Silero Punctuator:", lbl_te)

        # Check Whisper Large Turbo
        q5_exists = os.path.exists(os.path.join(WHISPER_CPP_MODELS_DIR, "ggml-large-v3-turbo-q5_0.bin"))
        st_whisper = "✅ Загружен (548 MB)" if q5_exists else "⚠️ Не загружен"
        lbl_w = QLabel(st_whisper)
        form_st.addRow("Whisper Turbo Q5_0:", lbl_w)

        layout.addWidget(grp_status)

        grp_paths = QGroupBox("Расположение файлов")
        form_p = QFormLayout(grp_paths)
        lbl_cfg_path = QLabel(CONFIG_FILE)
        lbl_cfg_path.setStyleSheet("color: #89b4fa; font-size: 11px;")
        form_p.addRow("Конфигурация:", lbl_cfg_path)

        layout.addWidget(grp_paths)
        layout.addStretch()

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
            "audio_device_id": self.combo_mic.currentData()
        }

        self.cfg.update(new_cfg)
        save_user_config(self.cfg)
        self.settings_saved.emit(self.cfg)
        self.accept()

    def closeEvent(self, event):
        self._stop_mic_test()
        super().closeEvent(event)
