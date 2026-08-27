"""Dynamic vector icon generation for system tray indicators."""

from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter


def create_tray_icon(bg_hex: str, fg_hex: str = "#11111b") -> QIcon:
    """Generate circular vector microphone icon with specified theme colors."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor(bg_hex))
    painter.setPen(QColor(bg_hex))
    painter.drawEllipse(2, 2, 28, 28)

    painter.setBrush(QColor(fg_hex))
    painter.setPen(QColor(fg_hex))
    painter.drawRoundedRect(13, 8, 6, 12, 3, 3)

    painter.drawLine(16, 22, 16, 26)
    painter.drawLine(12, 26, 20, 26)

    painter.end()
    return QIcon(pixmap)
