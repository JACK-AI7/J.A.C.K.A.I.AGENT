import sys
import os
import math
import tempfile
import time
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QSystemTrayIcon,
    QMenu,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    Property,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QSize,
    QPoint,
    QPointF,
    Signal,
    QObject,
)
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QRadialGradient,
    QLinearGradient,
    QConicalGradient,
    QIcon,
    QAction,
    QPixmap,
    QRegion,
)
import math

# Explicit fallback for environment-specific symbol binding issues
try:
    from PySide6.QtCore import QPointF, QRectF, QSize, QPoint, QRect, Qt
except ImportError:
    from PySide6.QtCore import Qt, QPoint, QSize, QRect
    QPointF = QPoint
    QRectF = QRect


class JACKSideRail(QWidget):
    """Minimalist vertical dock for the left edge of the screen."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(30, 150)
        self.status = "idle"
        self.pulse = 0

        # Ensure it stays on top of everything
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.X11BypassWindowManagerHint
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(33)
        self.pulse_timer = 0

    def update_animation(self):
        self.pulse_timer += 0.08  # Faster pulse for a snappier feel
        self.pulse = (math.sin(self.pulse_timer) + 1) / 2
        self.update()

    def set_status(self, status):
        self.status = status
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Draw Side Rail Pill (Dark/Semi-Transparent)
        pill_color = QColor(20, 20, 20, 180)
        painter.setBrush(QBrush(pill_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

        # 2. Draw The "Dot" (Status Core)
        center_x = self.width() // 2
        center_y = self.height() // 2

        base_color = QColor(0, 162, 255)  # Stark Deep Blue (Idle)
        if self.status == "listening":
            base_color = QColor(0, 255, 127)  # Green
        elif self.status == "thinking":
            base_color = QColor(0, 255, 255)  # Cyan
        elif self.status == "speaking":
            base_color = QColor(255, 50, 50)  # Stark Crimson (Speaking)

        # Dynamic Outer Glow (Pulse)
        glow_radius = 12 + (4 * self.pulse)
        glow = QRadialGradient(center_x, center_y, glow_radius)
        glow.setColorAt(0, base_color)
        glow.setColorAt(1, Qt.transparent)

        painter.setBrush(QBrush(glow))
        painter.setOpacity(0.3 + (0.4 * self.pulse))
        painter.drawEllipse(
            center_x - int(glow_radius),
            center_y - int(glow_radius),
            int(glow_radius * 2),
            int(glow_radius * 2),
        )

        # High-Fidelity Core Dot
        painter.setOpacity(1.0)
        painter.setBrush(QBrush(base_color.lighter(150)))
        painter.setPen(QPen(base_color, 1))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)


class GUISignals(QObject):
    """Signal bridge to handle updates from background threads safely."""

    status_changed = Signal(str, str)
    transcription_received = Signal(str)
    response_received = Signal(str)
    tool_log_received = Signal(str)
    activity_received = Signal(str)  # New signal for real-time activities
    restore_requested = Signal()
    mini_mode_toggled = Signal()
    dashboard_requested = Signal()
    mission_updated = Signal(int, str)


class JACKCore(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.angle = 0
        self.pulse = 0
        self.status = "idle"  # idle, listening, thinking, speaking

        # Animations
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS

        self.pulse_timer = 0

    def update_animation(self):
        # Multiple rotation speeds for Arc Reactor effect
        self.angle = (self.angle + 3) % 360
        self.angle_fast = (self.angle * 2) % 360
        self.angle_slow = (self.angle // 2) % 360
        
        self.pulse_timer += 0.08
        self.pulse = (math.sin(self.pulse_timer) + 1) / 2
        self.update()

    def set_status(self, status):
        self.status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 20

        # Colors based on status (JACK Palette)
        base_color = QColor(0, 255, 255)  # Cyan (Default)
        if self.status == "listening":
            base_color = QColor(0, 255, 127)  # SpringGreen
        elif self.status == "thinking":
            base_color = QColor(0, 191, 255)  # DeepSkyBlue
        elif self.status == "speaking":
            base_color = QColor(255, 0, 100)  # Neon Pink/Red
        elif self.status == "executing":
            base_color = QColor(138, 43, 226)  # BlueViolet
        elif self.status == "vision_analyzing":
            base_color = QColor(255, 255, 0)  # Yellow (Scanning)

        # 1. Background Glow (Aura)
        glow = QRadialGradient(center, radius + 30)
        glow.setColorAt(0, base_color.lighter(150))
        glow.setColorAt(0.5, QColor(base_color.red(), base_color.green(), base_color.blue(), 50))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.setOpacity(0.4 + (0.2 * self.pulse))
        painter.drawEllipse(center, radius + 30, radius + 30)
        painter.setOpacity(1.0)

        # 2. Segmented Middle Ring (The Reactor Ring)
        pen = QPen(base_color)
        pen.setWidth(10)
        pen.setCapStyle(Qt.FlatCap)
        pen.setDashPattern([15, 10]) # Segmented look
        painter.setPen(pen)
        
        r_mid = radius - 15
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(self.angle)
        painter.drawEllipse(QPointF(0, 0), r_mid, r_mid)
        painter.restore()

        # 3. Inner Rotating Gear (Thin Dashed)
        pen = QPen(Qt.white)
        pen.setWidth(2)
        pen.setDashPattern([5, 5])
        painter.setPen(pen)
        
        r_inner = radius - 40
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(-self.angle_fast) # Reverse rotation
        painter.drawEllipse(QPointF(0, 0), r_inner, r_inner)
        painter.restore()

        # 4. Outer Brackets (Semi-circles)
        pen = QPen(base_color)
        pen.setWidth(3)
        painter.setPen(pen)
        r_outer = radius + 5
        rect_outer = QRectF(center.x() - r_outer, center.y() - r_outer, 2*r_outer, 2*r_outer)
        painter.drawArc(rect_outer, (self.angle_slow + 45) * 16, 90 * 16)
        painter.drawArc(rect_outer, (self.angle_slow + 225) * 16, 90 * 16)

        # 5. The "Power Core"
        core_radius = 35 + (self.pulse * 8 if self.status != "idle" else 2)
        core_grad = QRadialGradient(center, core_radius)
        core_grad.setColorAt(0, Qt.white)
        core_grad.setColorAt(0.3, base_color.lighter(200))
        core_grad.setColorAt(1, base_color.darker(300))
        
        painter.setBrush(QBrush(core_grad))
        painter.setPen(QPen(base_color.lighter(250), 2))
        painter.drawEllipse(center, core_radius, core_radius)


        # Draw "Immortal Eye" Scanning Line if analyzing vision
        if self.status == "vision_analyzing":
            scan_gradient = QConicalGradient(center, self.angle)
            scan_gradient.setColorAt(0, QColor(0, 255, 255, 100))
            scan_gradient.setColorAt(0.1, QColor(0, 255, 255, 0))
            scan_gradient.setColorAt(1, Qt.transparent)
            painter.setBrush(QBrush(scan_gradient))
            painter.drawEllipse(center, radius + 20, radius + 20)

            # Draw Horizontal Scan Line
            scan_y = center.y() - radius + (self.pulse * 2 * radius)
            painter.setPen(QPen(QColor(0, 255, 255, 100), 2))
            painter.drawLine(
                center.x() - radius, int(scan_y), center.x() + radius, int(scan_y)
            )

        # Draw status text in center (minimal)
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        # painter.drawText(self.rect(), Qt.AlignCenter, self.status.upper())


class HUDWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent; border: none;")

        # State Management
        # Initialize Side Rail (Hidden by default)
        self.side_rail = JACKSideRail()
        self.side_rail.clicked.connect(self.toggle_mini_mode)

        self.is_mini_mode = False
        self.normal_geometry = None
        self.last_toggle_time = 0  # Cooldown to prevent resonance loops

        # Mission Dashboard Data
        self.mission_active = False
        self.mission_progress = 0
        self.mission_label_text = "NEXUS IDLE"

        # Real-time activity log
        self.activity_log = []
        self.max_log_entries = 5

        # Absolute round mask to kill rectangular artifacts

        self.mask_timer = QTimer(self)
        self.mask_timer.timeout.connect(self._apply_circular_mask)
        self.mask_timer.start(100)  # Periodic refresh for safety

        # Main layout
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background: transparent; border: none;")
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setSpacing(0)
        self.layout.setStretch(0, 1)
        self.layout.setStretch(1, 1)
        self.layout.setStretch(2, 1)
        self.layout.setStretch(3, 1)
        self.layout.setStretch(4, 1)
        self.layout.setStretch(5, 2)  # Extra space for log

        # Top Control Bar (Minimize) - Stylized Ghost Mode
        self.control_bar = QWidget()
        self.control_bar.setStyleSheet("background: transparent; border: none;")
        self.control_bar_layout = QVBoxLayout(self.control_bar)
        self.control_bar_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.min_btn = QFrame()
        self.min_btn.setFixedSize(30, 20)
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QFrame {
                background: rgba(0, 191, 255, 10);
                border: 1px solid rgba(0, 191, 255, 50);
                border-radius: 4px;
            }
            QFrame:hover {
                background: rgba(0, 191, 255, 60);
            }
        """)
        # Draw a '-' in the middle
        min_label = QLabel("─", self.min_btn)
        min_label.setStyleSheet(
            "color: rgba(255, 255, 255, 150); font-weight: Bold; background: transparent; border: none;"
        )
        min_label.setAlignment(Qt.AlignCenter)
        min_label.setGeometry(0, 0, 30, 20)

        self.min_btn.mousePressEvent = lambda e: self.toggle_mini_mode()
        self.control_bar_layout.addWidget(self.min_btn)
        self.layout.addWidget(self.control_bar)

        # JACK Core
        self.core = JACKCore()
        self.core.mousePressEvent = self._on_core_clicked
        self.layout.addWidget(self.core)

        # Status Labels
        self.status_label = QLabel("JACK IDLE")
        self.status_label.setStyleSheet(
            "color: rgba(0, 191, 255, 200); font-family: 'Segoe UI Light'; font-size: 14px; letter-spacing: 2px;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Transcription Label
        self.transcription_label = QLabel("")
        self.transcription_label.setStyleSheet(
            "color: rgba(255, 255, 255, 150); font-family: 'Segoe UI'; font-size: 12px;"
        )
        self.transcription_label.setAlignment(Qt.AlignCenter)
        self.transcription_label.setWordWrap(True)
        self.layout.addWidget(self.transcription_label)

        # Tool Log Label
        self.tool_log_label = QLabel("")
        self.tool_log_label.setStyleSheet(
            "color: rgba(255, 165, 0, 200); font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;"
        )
        self.tool_log_label.setAlignment(Qt.AlignCenter)
        self.tool_log_label.setWordWrap(True)
        self.layout.addWidget(self.tool_log_label)

        # LIVE SUBTITLE LABEL — Shows what JACK is speaking in real-time
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(
            "color: rgba(255, 255, 255, 230); font-family: 'Segoe UI'; font-size: 13px;"
            "background: rgba(0, 0, 0, 120); border-radius: 8px; padding: 6px 12px;"
        )
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setMaximumWidth(450)
        self.subtitle_label.hide()
        self.layout.addWidget(self.subtitle_label)

        # Real-time activity log
        self.activity_log_label = QLabel("")
        self.activity_log_label.setStyleSheet(
            "color: rgba(100, 100, 255, 150); font-family: 'Consolas', 'Courier New'; font-size: 9px; margin-top: 5px;"
        )
        self.activity_log_label.setAlignment(Qt.AlignCenter)
        self.activity_log_label.setWordWrap(True)
        self.layout.addWidget(self.activity_log_label)

        # Thinking Log (Real-Time Telemetry)
        self.thinking_label = QLabel("")
        self.thinking_label.setStyleSheet(
            "color: rgba(0, 255, 255, 100); font-family: 'Consolas', 'Courier New'; font-size: 9px; margin-top: 5px;"
        )
        self.thinking_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.thinking_label)
        # Mission Progress Bar (Hidden by default)
        self.mission_container = QFrame()
        self.mission_container.setFixedHeight(30)
        self.mission_container.setStyleSheet(
            "background: rgba(0, 0, 0, 50); border-radius: 15px; border: 1px solid rgba(0, 191, 255, 30);"
        )
        self.mission_layout = QVBoxLayout(self.mission_container)
        self.mission_layout.setContentsMargins(10, 0, 10, 0)

        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet(
            "background: rgba(0, 191, 255, 50); border-radius: 2px;"
        )
        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setFixedHeight(4)
        self.progress_fill.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 191, 255, 255), stop:1 rgba(0, 255, 255, 255)); border-radius: 2px;"
        )

        self.mission_layout.addWidget(self.progress_bar)
        self.mission_container.hide()
        self.layout.addWidget(self.mission_container)

        self.setCentralWidget(self.central_widget)

        # System Tray Initialization
        self.setup_tray()

        # Positioning: Bottom Center (Taskbar Aware)
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.resize(500, 400)

        # Center horizontally, and place 20px above the available bottom (taskbar)
        x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
        y = screen_geo.y() + screen_geo.height() - self.height() - 20
        self.move(x, y)

        # Dashboard Auto-Orchestration
        QTimer.singleShot(2000, self.launch_nexus_dashboard)

        # Force to front
        self.raise_()
        self.activateWindow()

    def setup_tray(self):
        """Setup the system tray icon and context menu."""
        self.tray_icon = QSystemTrayIcon(self)

        # Use the project-local TITAN icon (portable path)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jack_titan_icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback: generate a simple icon
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(0, 191, 255)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(4, 4, 56, 56)
            painter.end()
            self.tray_icon.setIcon(QIcon(pixmap))

        # Tray Menu
        self.tray_menu = QMenu()
        restore_action = QAction("Restore Nexus", self)
        restore_action.triggered.connect(self.showNormal)

        mini_action = QAction("Side Rail Mode", self)
        mini_action.triggered.connect(self.toggle_mini_mode)

        nexus_action = QAction("Nexus Dashboard", self)
        nexus_action.triggered.connect(self.launch_nexus_dashboard)

        quit_action = QAction("Deactivate JACK", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(mini_action)
        self.tray_menu.addAction(nexus_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Tooltip
        self.tray_icon.setToolTip("JACK TITAN: Nexus Active")

    def update_mission_progress(self, progress, label="MISSION ACTIVE"):
        """Update the mission dashboard UI."""
        self.mission_active = True
        self.mission_container.show()
        self.mission_progress = progress

        # Calculate width
        max_width = self.progress_bar.width()
        fill_width = int((progress / 100) * max_width)
        self.progress_fill.setFixedWidth(fill_width)

        self.status_label.setText(label.upper())
        if progress >= 100:
            QTimer.singleShot(3000, self.mission_container.hide)
            self.mission_active = False

    def _on_core_clicked(self, event):
        """Restore to full mode if clicked while in mini mode."""
        if self.is_mini_mode:
            self.toggle_mini_mode()
        event.accept()

    def toggle_mini_mode(self):
        """Animate between Bottom-Center (Full) and Left-Rail (Mini)."""
        # --- RESONANCE COOLDOWN ---
        now = time.time()
        if now - self.last_toggle_time < 2:
            print("HUD: Toggle blocked (Cooldown active)")
            return
        self.last_toggle_time = now
        # -------------------------

        screen = QApplication.primaryScreen().geometry()

        if not self.is_mini_mode:
            # Entering MINI mode
            print("HUD: Docking to Side Rail...")
            self.normal_geometry = self.geometry()
            self.is_mini_mode = True

            # Position Side Rail
            screen = QApplication.primaryScreen().geometry()
            rail_x = 0
            rail_y = (screen.height() - self.side_rail.height()) // 2
            self.side_rail.move(rail_x, rail_y)

            # Hide Main HUD and show Rail
            self.hide()
            self.side_rail.show()
        else:
            # Restoring to NORMAL mode
            print("HUD: Restoring from Side Rail...")
            self.is_mini_mode = False

            # Hide Rail and show HUD
            self.side_rail.hide()
            self.show()

            # Animate/Move back
            if self.normal_geometry:
                self.move(self.normal_geometry.topLeft())
                self.activateWindow()
                self.raise_()

    def launch_nexus_dashboard(self):
        """Independently boot the Titan Nexus Dashboard."""
        import subprocess
        import sys

        root_dir = os.path.dirname(os.path.abspath(__file__))
        dash_script = os.path.join(root_dir, "dashboard.py")
        
        try:
            if os.name == 'nt':
                # On Windows, don't use start_new_session (causes WinError 87)
                subprocess.Popen(
                    [sys.executable, dash_script],
                    cwd=root_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            else:
                subprocess.Popen(
                    [sys.executable, dash_script],
                    cwd=root_dir,
                    start_new_session=True,
                )
            print("HUD: Nexus Dashboard launched successfully.")
            self.update_status("NEXUS LINK ESTABLISHED", "idle")
        except Exception as e:
            print(f"HUD: Failed to launch dashboard: {e}")
            self.update_status("NEXUS LINK FAILED", "executing")

    def _animate_to(self, target_rect):
        """Smoothly animate the window to a target rectangle."""
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(400)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(target_rect)
        self.anim.setEasingCurve(QEasingCurve.InOutQuart)
        self.anim.start()

    def _apply_circular_mask(self):
        """Force a circular mask to hide any rectangular window fragments."""

        # Mask only the center circular area
        rect = self.centralWidget().geometry()
        # Offset slightly for shadows/glow if needed, but here we want strict circle
        radius = min(self.width(), self.height()) // 2
        center = self.rect().center()
        region = QRegion(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2,
            QRegion.Ellipse,
        )
        # Add the minimize button area to the mask so it remains clickable
        btn_region = QRegion(self.control_bar.geometry())
        self.setMask(region.united(btn_region))

    def update_status(self, text, status_type):
        """Update the main status pulse and internal telemetry."""
        self.status_label.setText(text.upper())
        self.core.set_status(status_type)
        self.side_rail.set_status(status_type)

        # New Thinking Stream (Telemetry)
        if text.lower() == "idle":
            self.thinking_label.setText("")
        else:
            self.thinking_label.setText(f"> {text}...")
        self.update()

    def set_transcription(self, text):
        self.transcription_label.setText(f'"{text}"')
        QTimer.singleShot(5000, lambda: self.transcription_label.setText(""))

    def set_response(self, text):
        """Show the AI response as live subtitles on the HUD."""
        if not text or len(text.strip()) < 2:
            return
        # Truncate very long responses for display
        display_text = text[:200] + "..." if len(text) > 200 else text
        self.subtitle_label.setText(display_text)
        self.subtitle_label.show()
        # Auto-hide after a duration proportional to text length
        hide_delay = max(4000, min(len(text) * 40, 15000))
        QTimer.singleShot(hide_delay, lambda: self.subtitle_label.hide())
        print(f"HUD: Displaying response subtitle")

    def set_tool_log(self, text):
        self.tool_log_label.setText(text)
        QTimer.singleShot(3000, lambda: self.tool_log_label.setText(""))

    def add_activity(self, text):
        """Add an activity to the real-time log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {text}"
        self.activity_log.append(entry)
        if len(self.activity_log) > self.max_log_entries:
            self.activity_log.pop(0)
        self.activity_log_label.setText("\n".join(self.activity_log))
        # Also update tool log for single-line visibility
        if "Executing" in text or "Tool" in text:
            self.tool_log_label.setText(text)
            QTimer.singleShot(5000, lambda: self.tool_log_label.setText(""))


class HUDManager:
    def _create_tray_icon(self):
        """Create a stylized JACK icon for the system tray."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        center = pixmap.rect().center()
        radius = 25

        # Draw Glow
        glow = QRadialGradient(center, radius + 5)
        glow.setColorAt(0, QColor(0, 191, 255, 150))
        glow.setColorAt(1, Qt.transparent)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius + 5, radius + 5)

        # Draw Ring
        painter.setPen(QPen(QColor(0, 191, 255), 3))
        painter.drawArc(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2,
            45 * 16,
            270 * 16,
        )

        # Draw Core
        painter.setBrush(QBrush(QColor(0, 191, 255)))
        painter.setPen(QPen(Qt.white, 1))
        painter.drawEllipse(center, 8, 8)

        painter.end()
        return QIcon(pixmap)

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = HUDWindow()
        self.signals = GUISignals()

        # Connect signals
        self.signals.status_changed.connect(self.window.update_status)
        self.signals.transcription_received.connect(self.window.set_transcription)
        self.signals.response_received.connect(self.window.set_response)
        self.signals.tool_log_received.connect(self.window.set_tool_log)
        self.signals.activity_received.connect(
            self.window.add_activity
        )  # Connect new activity signal
        self.signals.restore_requested.connect(self.restore_window)
        self.signals.mini_mode_toggled.connect(self.window.toggle_mini_mode)
        self.signals.mission_updated.connect(self.window.update_mission_progress)

        # Tray Icon Setup
        self.tray_icon = QSystemTrayIcon(self._create_tray_icon(), self.app)
        self.tray_icon.setToolTip("JACK TITAN: Nexus Active")

        # Tray Menu
        self.tray_menu = QMenu()

        self.toggle_ai_action = QAction("Deactivate AI Brain", self.app)
        self.toggle_ai_action.triggered.connect(self.toggle_ai)

        restore_action = QAction("Restore HUD", self.app)
        restore_action.triggered.connect(self.restore_window)

        quit_action = QAction("Shut Down JACK", self.app)
        quit_action.triggered.connect(self.app.quit)

        self.tray_menu.addAction(self.toggle_ai_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def set_assistant(self, assistant):
        """Reference to the JACK assistant core."""
        self.assistant = assistant

    def toggle_ai(self):
        """Toggle the AI active state from the tray."""
        if hasattr(self, "assistant"):
            new_state = not self.assistant.is_active
            self.assistant.set_active(new_state)
            label = "Deactivate AI Brain" if new_state else "Activate AI Brain"
            self.toggle_ai_action.setText(label)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Single click
            self.restore_window()

    def restore_window(self):
        # Explicitly force restore from Side Rail if active (Bypasses any 2s toggle cooldown)
        if hasattr(self.window, "is_mini_mode") and self.window.is_mini_mode:
            print("HUD: Force Restoring from Side Rail (Voice/Summon)...")
            self.window.is_mini_mode = False
            self.window.side_rail.hide()

            if self.window.normal_geometry:
                self.window.move(self.window.normal_geometry.topLeft())

        # Pythonic way to show
        if self.window.isMinimized():
            self.window.showNormal()
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

        # Windows-Specific 'Force' way
        try:
            import ctypes

            hwnd = self.window.winId()
            # Bring to front using User32
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Summon Error: {e}")

    def show(self):
        self.window.show()

    def update_status(self, status, state="idle"):
        self.signals.status_changed.emit(status, state)
        if hasattr(self, "tray_icon"):
            self.tray_icon.setToolTip(f"JACK TITAN: {status}")

    def update_mission(self, progress, label):
        """Triggered from background thread."""
        self.signals.mission_updated.emit(progress, label)

    def set_transcription(self, text):
        self.signals.transcription_received.emit(text)

    def set_response(self, text):
        self.signals.response_received.emit(text)

    def set_tool_log(self, text):
        self.signals.tool_log_received.emit(text)

    def run_loop(self):
        self.app.processEvents()


if __name__ == "__main__":
    manager = HUDManager()
    manager.show()
    sys.exit(manager.app.exec())
