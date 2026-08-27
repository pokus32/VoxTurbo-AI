"""System tray integration and context menu management."""

from typing import Callable, Optional
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from src.ui.icons import create_tray_icon


class TrayManager:
    """Manager for system tray icon and configuration context menu."""

    def __init__(
        self,
        parent_app,
        on_toggle_recording: Callable[[], None],
        on_change_quant: Callable[[str], None],
        on_change_threads: Callable[[int], None],
        on_change_language: Callable[[str], None],
        on_toggle_punctuation: Optional[Callable[[bool], None]] = None,
        on_toggle_hud: Optional[Callable[[bool], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ):
        self.parent_app = parent_app
        self.on_toggle_recording = on_toggle_recording
        self.on_change_quant = on_change_quant
        self.on_change_threads = on_change_threads
        self.on_change_language = on_change_language
        self.on_toggle_punctuation = on_toggle_punctuation
        self.on_toggle_hud = on_toggle_hud
        self.on_open_settings = on_open_settings
        self.on_quit = on_quit or (lambda: None)

        # Status color themes
        self.icon_idle = create_tray_icon("#a6e3a1", "#11111b")       # 🟢 Green - Ready in RAM
        self.icon_recording = create_tray_icon("#f38ba8", "#11111b")  # 🔴 Red - Recording active
        self.icon_processing = create_tray_icon("#f9e2af", "#11111b") # 🟡 Yellow - Loading / Processing

        self.tray = QSystemTrayIcon(self.icon_idle, self.parent_app)
        self.last_text = "(no recordings yet)"

        self._create_menu()

    def show(self):
        """Show tray icon in system notification area."""
        self.tray.show()

    def _create_menu(self):
        """Create context menu structure."""
        self.menu = QMenu()

        self.action_toggle = QAction("🟢 START Recording (Super+Space)", self.menu)
        self.action_toggle.triggered.connect(self.on_toggle_recording)
        self.menu.addAction(self.action_toggle)

        self.menu.addSeparator()

        # Engine & Model selection submenu
        self.menu_model = QMenu("🌟 Engine & Model", self.menu)
        self.action_gigaam = QAction("⚡ 🇷🇺 GigaAM v2 Conformer (SOTA Realtime ~0.5x)", self.menu, checkable=True)
        self.action_gigaam.triggered.connect(lambda: self.on_change_quant("gigaam_v2"))
        self.menu_model.addAction(self.action_gigaam)

        self.menu_model.addSeparator()

        self.action_quant_q5 = QAction("⚡ Whisper Large-v3-Turbo Q5_0 (548 MB)", self.menu, checkable=True)
        self.action_quant_q5.triggered.connect(lambda: self.on_change_quant("q5_0"))
        self.menu_model.addAction(self.action_quant_q5)

        self.action_quant_q8 = QAction("🎯 Whisper Large-v3-Turbo Q8_0 (833 MB)", self.menu, checkable=True)
        self.action_quant_q8.triggered.connect(lambda: self.on_change_quant("q8_0"))
        self.menu_model.addAction(self.action_quant_q8)

        self.menu_model.addSeparator()

        self.action_quant_small = QAction("🚀 Whisper Small (466 MB)", self.menu, checkable=True)
        self.action_quant_small.triggered.connect(lambda: self.on_change_quant("small"))
        self.menu_model.addAction(self.action_quant_small)

        self.action_quant_base = QAction("⚡ Whisper Base (142 MB)", self.menu, checkable=True)
        self.action_quant_base.triggered.connect(lambda: self.on_change_quant("base"))
        self.menu_model.addAction(self.action_quant_base)

        self.menu.addMenu(self.menu_model)

        # CPU Threads submenu
        self.menu_threads = QMenu("🧵 CPU Threads", self.menu)
        self.action_t4 = QAction("4 Threads (Balanced)", self.menu, checkable=True)
        self.action_t4.triggered.connect(lambda: self.on_change_threads(4))
        self.menu_threads.addAction(self.action_t4)

        self.action_t6 = QAction("6 Threads (Maximum CPU)", self.menu, checkable=True)
        self.action_t6.triggered.connect(lambda: self.on_change_threads(6))
        self.menu_threads.addAction(self.action_t6)
        self.menu.addMenu(self.menu_threads)

        # Language selection submenu
        self.menu_lang = QMenu("🌐 Language", self.menu)
        self.action_lang_auto = QAction("⚡ Auto-detect in-flight (Parallel)", self.menu, checkable=True)
        self.action_lang_auto.triggered.connect(lambda: self.on_change_language("auto"))
        self.menu_lang.addAction(self.action_lang_auto)

        self.action_lang_ru = QAction("🇷🇺 Russian (ru)", self.menu, checkable=True)
        self.action_lang_ru.triggered.connect(lambda: self.on_change_language("ru"))
        self.menu_lang.addAction(self.action_lang_ru)

        self.action_lang_kk = QAction("🇰🇿 Kazakh (kk / Қазақша)", self.menu, checkable=True)
        self.action_lang_kk.triggered.connect(lambda: self.on_change_language("kk"))
        self.menu_lang.addAction(self.action_lang_kk)

        self.action_lang_en = QAction("🇬🇧 English (en)", self.menu, checkable=True)
        self.action_lang_en.triggered.connect(lambda: self.on_change_language("en"))
        self.menu_lang.addAction(self.action_lang_en)
        self.menu.addMenu(self.menu_lang)

        self.menu.addSeparator()

        # Enhancement features toggles
        self.action_punct = QAction("🔤 Smart Punctuation (Silero TE)", self.menu, checkable=True)
        self.action_punct.triggered.connect(
            lambda checked: self.on_toggle_punctuation(checked) if self.on_toggle_punctuation else None
        )
        self.menu.addAction(self.action_punct)

        self.action_hud = QAction("✨ Floating Voice HUD (Waveform)", self.menu, checkable=True)
        self.action_hud.triggered.connect(
            lambda checked: self.on_toggle_hud(checked) if self.on_toggle_hud else None
        )
        self.menu.addAction(self.action_hud)

        self.menu.addSeparator()

        self.action_last_text = QAction(f"💬 Last: {self.last_text[:25]}", self.menu)
        self.action_last_text.setEnabled(False)
        self.menu.addAction(self.action_last_text)

        self.action_hint = QAction("ℹ️ Shortcut: Super + Space (Win + Space)", self.menu)
        self.action_hint.setEnabled(False)
        self.menu.addAction(self.action_hint)

        self.menu.addSeparator()

        if self.on_open_settings:
            action_settings = QAction("⚙️ Настройки...", self.menu)
            action_settings.triggered.connect(self.on_open_settings)
            self.menu.addAction(action_settings)

        action_quit = QAction("❌ Quit VoxTurbo AI", self.menu)
        action_quit.triggered.connect(self.on_quit)
        self.menu.addAction(action_quit)

        self.tray.setContextMenu(self.menu)

    def set_state(self, state_name: str, model_quant: str, cpu_threads: int, language: str):
        """Update tray visual icon and tooltip status."""
        q_label = model_quant.upper()
        if state_name in ("idle", "success"):
            self.tray.setIcon(self.icon_idle)
            self.action_toggle.setText("🟢 START Recording (Super+Space)")
            self.tray.setToolTip(f"VoxTurbo [{q_label} | {cpu_threads}T | {language.upper()}] (Win+Space)")
        elif state_name == "loading":
            self.tray.setIcon(self.icon_processing)
            self.action_toggle.setText("⏳ Loading Model into RAM...")
            self.tray.setToolTip(f"VoxTurbo: Loading {q_label} into RAM...")
        elif state_name == "recording":
            self.tray.setIcon(self.icon_recording)
            self.action_toggle.setText("🔴 STOP Recording (Win+Space)")
            self.tray.setToolTip(f"🔴 VoxTurbo Recording [{q_label}]... (Win+Space)")
        elif state_name == "processing":
            self.tray.setIcon(self.icon_processing)
            self.action_toggle.setText("⏳ Transcribing audio...")
            self.tray.setToolTip(f"🟡 VoxTurbo Processing [{q_label}]...")

    def update_checks(
        self,
        model_quant: str,
        cpu_threads: int,
        language: str,
        enable_punctuation: bool = True,
        enable_hud: bool = True
    ):
        """Synchronize checkmarks across menus."""
        self.action_gigaam.setChecked(model_quant == "gigaam_v2")
        self.action_quant_q5.setChecked(model_quant == "q5_0")
        self.action_quant_q8.setChecked(model_quant == "q8_0")
        self.action_quant_small.setChecked(model_quant == "small")
        self.action_quant_base.setChecked(model_quant == "base")

        self.action_t4.setChecked(cpu_threads == 4)
        self.action_t6.setChecked(cpu_threads == 6)

        self.action_lang_auto.setChecked(language == "auto")
        self.action_lang_ru.setChecked(language == "ru")
        self.action_lang_kk.setChecked(language == "kk")
        self.action_lang_en.setChecked(language == "en")

        self.action_punct.setChecked(bool(enable_punctuation))
        self.action_hud.setChecked(bool(enable_hud))

        label = "GigaAM-v2" if model_quant == "gigaam_v2" else f"Whisper-{model_quant.upper()}"
        self.tray.setToolTip(f"VoxTurbo [{label} | {cpu_threads}T | {language.upper()}] (Win+Space)")

    def update_last_text(self, text: str, success: bool, model_quant: str):
        """Update last transcribed text display."""
        q_label = model_quant.upper()
        if success:
            self.last_text = text
            self.tray.setToolTip(f"VoxTurbo [{q_label}]: {text[:25]}")
            self.action_last_text.setText(f"💬 Last: {text[:25]}...")
        else:
            self.tray.setToolTip(f"VoxTurbo [{q_label}]: {text}")
            self.action_last_text.setText(f"💬 {text}")

    def show_notification(self, title: str, message: str):
        """Display desktop notification popup."""
        self.tray.showMessage(title, message, QSystemTrayIcon.Information, 3000)

