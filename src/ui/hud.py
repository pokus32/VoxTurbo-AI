"""Modern frameless floating voice HUD with live waveform and amplitude animations."""

import time
import math
import random
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient, QBitmap, QPixmap


class WaveformVisualizer(QWidget):
    """Dynamic audio waveform / equalizer bar visualizer with smooth physics."""

    def __init__(self, num_bars: int = 7, parent=None):
        super().__init__(parent)
        self.num_bars = num_bars
        self.bar_heights = [0.15] * num_bars
        self.target_amplitude = 0.0
        self.phase = 0.0
        self.setFixedSize(100, 32)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Smooth render tick timer (~50 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_step)
        self._timer.start(20)

    def set_amplitude(self, amp: float):
        """Update target normalized audio amplitude (0.0 .. 1.0)."""
        self.target_amplitude = max(0.0, min(1.0, amp))

    def _animate_step(self):
        """Perform spring-like decay and wave modulation."""
        self.phase += 0.18
        decay_factor = 0.35

        for i in range(self.num_bars):
            # Harmonic wave factor across bars
            wave_mod = math.sin(self.phase + (i * 0.9)) * 0.3 + 0.7
            target = 0.15 + (self.target_amplitude * wave_mod * 0.85)
            
            # Add small organic noise when active
            if self.target_amplitude > 0.05:
                target += random.uniform(-0.05, 0.05)

            target = max(0.12, min(1.0, target))
            # Linear interpolation / decay
            self.bar_heights[i] += (target - self.bar_heights[i]) * decay_factor

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()
        bar_w = 4.0
        spacing = 6.0
        total_w = (self.num_bars * bar_w) + ((self.num_bars - 1) * spacing)
        start_x = (w - total_w) / 2.0

        for i, bh in enumerate(self.bar_heights):
            x = start_x + i * (bar_w + spacing)
            bar_h = max(4.0, bh * (h - 4.0))
            y = (h - bar_h) / 2.0

            # Gradient from cyan/blue to magenta/coral based on height
            grad = QLinearGradient(x, y + bar_h, x, y)
            if bh > 0.6:
                grad.setColorAt(0.0, QColor("#f38ba8"))  # Red / Coral
                grad.setColorAt(1.0, QColor("#fab387"))  # Peach
            else:
                grad.setColorAt(0.0, QColor("#89b4fa"))  # Blue
                grad.setColorAt(1.0, QColor("#a6e3a1"))  # Green

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 2, 2)


class VoiceHUDWidget(QWidget):
    """Frameless, semi-transparent desktop HUD showing recording & transcription state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "idle"
        self._record_start_time = 0.0

        # Window flags: Frameless, Topmost, Non-focusable, Tool
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background: transparent;")

        # UI Setup
        self._init_ui()

        # Opacity effect for hardware/Qt composition without breaking 32-bit ARGB per-pixel alpha
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)

        # Fade animations targeting opacity effect
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        # Elapsed timer for recording duration
        self.duration_timer = QTimer(self)
        self.duration_timer.timeout.connect(self._update_duration)

    def _init_ui(self):
        self.setFixedSize(310, 68)

        # Container layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(12)

        # Left: Status indicator dot / icon
        self.lbl_icon = QLabel("🔴", self)
        self.lbl_icon.setStyleSheet("font-size: 16px; background: transparent;")
        main_layout.addWidget(self.lbl_icon)

        # Middle: Text status & duration/model info
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.lbl_title = QLabel("Recording...", self)
        self.lbl_title.setStyleSheet("color: #cdd6f4; font-weight: 600; font-size: 13px; background: transparent;")
        text_layout.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel("00:00 • GigaAM v2", self)
        self.lbl_subtitle.setStyleSheet("color: #a6adc8; font-size: 11px; background: transparent;")
        text_layout.addWidget(self.lbl_subtitle)

        main_layout.addLayout(text_layout)
        main_layout.addStretch()

        # Right: Waveform visualizer
        self.visualizer = WaveformVisualizer(num_bars=7, parent=self)
        main_layout.addWidget(self.visualizer)

        self._apply_mask()

    def _apply_mask(self):
        """Apply hardware circular arc mask to ensure X11 cuts rounded corners precisely by radius."""
        mask = QBitmap(self.size())
        mask.fill(Qt.color0)
        p = QPainter(mask)
        p.setBrush(Qt.color1)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.end()
        self.setMask(mask)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_mask()

    def set_amplitude(self, amp: float):
        """Pass live audio amplitude to visualizer."""
        self.visualizer.set_amplitude(amp)

    def _reposition(self):
        """Position the HUD at the bottom-center of the primary active screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() - self.height() - 75
            self.move(x, y)

    def paintEvent(self, event):
        """Draw sleek dark glassmorphism card background with ultra-smooth antialiased rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Background card rect
        rect = self.rect().adjusted(1, 1, -1, -1)

        # Dark glass fill
        painter.setBrush(QBrush(QColor(24, 24, 37, 235)))  # Catppuccin Mocha base #181825

        # Glowing accent border depending on state
        if self.state == "recording":
            painter.setPen(QPen(QColor("#f38ba8"), 1.4))
        elif self.state == "processing":
            painter.setPen(QPen(QColor("#f9e2af"), 1.4))
        elif self.state == "success":
            painter.setPen(QPen(QColor("#a6e3a1"), 1.4))
        else:
            painter.setPen(QPen(QColor(69, 71, 90, 180), 1.0))

        painter.drawRoundedRect(rect, 16.0, 16.0)

    def set_state(self, state_name: str, model_label: str = "GigaAM v2", detail: str = ""):
        """Switch HUD visual state."""
        self.state = state_name

        if state_name == "recording":
            self._record_start_time = time.time()
            self.lbl_icon.setText("🔴")
            self.lbl_title.setText("Listening...")
            self.lbl_subtitle.setText(f"00:00 • {model_label}")
            self.visualizer.setVisible(True)
            self.duration_timer.start(250)
            self._reposition()
            self._fade_in()

        elif state_name == "processing":
            self.duration_timer.stop()
            self.lbl_icon.setText("⏳")
            self.lbl_title.setText("Transcribing speech...")
            self.lbl_subtitle.setText(model_label)
            self.visualizer.set_amplitude(0.0)
            self.visualizer.setVisible(False)
            self.update()
            self._fade_in()

        elif state_name == "success":
            self.duration_timer.stop()
            self.lbl_icon.setText("✅")
            self.lbl_title.setText("Text Pasted")
            self.lbl_subtitle.setText(detail[:28] if detail else model_label)
            self.visualizer.setVisible(False)
            self.update()
            # Auto fade-out after brief display
            QTimer.singleShot(1400, self._fade_out)

        elif state_name == "idle":
            self.duration_timer.stop()
            self.visualizer.set_amplitude(0.0)
            self._fade_out()

    def _update_duration(self):
        """Update live recording timer."""
        if self.state == "recording":
            elapsed = int(time.time() - self._record_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            model_info = self.lbl_subtitle.text().split("•")[-1].strip()
            self.lbl_subtitle.setText(f"{mins:02d}:{secs:02d} • {model_info}")

    def _fade_in(self):
        """Smoothly animate HUD opacity to visible."""
        self.show()
        self.anim.stop()
        self.anim.setDuration(160)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

    def _fade_out(self):
        """Smoothly fade HUD out and hide."""
        self.anim.stop()
        self.anim.setDuration(220)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_fade_out_finished)
        self.anim.start()

    def _on_fade_out_finished(self):
        if self.opacity_effect.opacity() <= 0.01:
            self.hide()

