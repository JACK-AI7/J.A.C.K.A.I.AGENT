import sys
import os

# Suppress technical noise in the console for a premium feel
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

import math
import random
import time

# Safe import for OpenCV (not a hard dependency)
try:
    import cv2
except ImportError:
    cv2 = None

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFrame, QTextEdit, QGraphicsView, 
                             QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
                             QGraphicsTextItem, QProgressBar, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, Slot, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient, QFont, QPixmap, QImage, QLinearGradient, QPainterPath
import psutil
import subprocess
import threading
from nexus_bridge import get_signals
try:
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None


# =============================================================================
# PIPELINE STATUS BAR — Shows LISTENING → THINKING → EXECUTING → SPEAKING
# =============================================================================

class PipelineStatusBar(QFrame):
    """Real-time pipeline visualization showing what JACK is doing RIGHT NOW."""
    
    STAGES = ["IDLE", "LISTENING", "TRANSCRIBED", "THINKING", "EXECUTING", "SPEAKING", "ERROR"]
    STAGE_COLORS = {
        "IDLE": QColor(80, 80, 100),
        "LISTENING": QColor(0, 191, 255),
        "TRANSCRIBED": QColor(0, 255, 200),
        "THINKING": QColor(255, 140, 0),
        "EXECUTING": QColor(255, 60, 60),
        "SPEAKING": QColor(0, 255, 127),
        "ERROR": QColor(255, 30, 30),
    }
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(70)
        self.setStyleSheet("background: rgba(5, 10, 20, 220); border: 1px solid rgba(0, 191, 255, 40); border-radius: 8px;")
        self.current_stage = "IDLE"
        self.detail_text = "Standing by..."
        self.pulse_alpha = 0
        self.pulse_dir = 1
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)
    
    def set_stage(self, stage, detail=""):
        self.current_stage = stage if stage in self.STAGES else "IDLE"
        self.detail_text = detail or self.current_stage
        self.update()
    
    def _animate(self):
        self.pulse_alpha += self.pulse_dir * 8
        if self.pulse_alpha >= 180: self.pulse_dir = -1
        if self.pulse_alpha <= 40: self.pulse_dir = 1
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        
        # Header
        painter.setPen(QPen(QColor(0, 191, 255, 120), 1))
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(10, 14, "PROCESS_PIPELINE // REAL-TIME")
        
        # Draw pipeline stages
        stage_w = (w - 40) / 5
        display_stages = ["LISTENING", "TRANSCRIBED", "THINKING", "EXECUTING", "SPEAKING"]
        stage_idx = display_stages.index(self.current_stage) if self.current_stage in display_stages else -1
        
        for i, stage in enumerate(display_stages):
            x = 15 + i * stage_w
            color = self.STAGE_COLORS.get(stage, QColor(80, 80, 100))
            
            is_active = (stage == self.current_stage)
            is_past = (stage_idx >= 0 and i < stage_idx)
            
            if is_active:
                # Pulsing active node
                glow = QRadialGradient(QPointF(x + stage_w/2, 38), 18)
                glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), self.pulse_alpha))
                glow.setColorAt(1, Qt.transparent)
                painter.setBrush(QBrush(glow))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x + stage_w/2, 38), 18, 18)
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.white, 2))
                painter.drawEllipse(QPointF(x + stage_w/2, 38), 8, 8)
            elif is_past:
                painter.setBrush(QBrush(color.darker(150)))
                painter.setPen(QPen(color, 1))
                painter.drawEllipse(QPointF(x + stage_w/2, 38), 6, 6)
            else:
                painter.setBrush(QBrush(QColor(40, 40, 60)))
                painter.setPen(QPen(QColor(60, 60, 80), 1))
                painter.drawEllipse(QPointF(x + stage_w/2, 38), 5, 5)
            
            # Connection line
            if i < len(display_stages) - 1:
                next_color = color if (is_active or is_past) else QColor(40, 40, 60)
                painter.setPen(QPen(next_color, 1 if is_past else 1))
                painter.drawLine(QPointF(x + stage_w/2 + 10, 38), QPointF(x + stage_w + stage_w/2 - 10, 38))
            
            # Label
            label_color = QColor(255, 255, 255, 200) if is_active else QColor(120, 120, 140)
            painter.setPen(label_color)
            painter.setFont(QFont("Consolas", 6))
            short_labels = {"LISTENING": "LISTEN", "TRANSCRIBED": "HEARD", "THINKING": "THINK", "EXECUTING": "EXEC", "SPEAKING": "SPEAK"}
            painter.drawText(int(x), 58, int(stage_w), 14, Qt.AlignCenter, short_labels.get(stage, stage[:5]))
        
        # Detail text
        painter.setPen(QColor(200, 200, 220, 180))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(w - 300, 8, 290, 14, Qt.AlignRight, self.detail_text[:50])


# =============================================================================
# TOOL EXECUTION LOG — Live feed of every tool call and result
# =============================================================================

class ToolExecutionLog(QFrame):
    """Real-time log of every tool execution with status indicators."""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(5, 10, 20, 200); border: 1px solid rgba(255, 140, 0, 30); border-radius: 8px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        header = QLabel("TOOL_EXECUTION_FEED // LIVE")
        header.setStyleSheet("color: rgba(255, 140, 0, 180); font-weight: bold; font-family: 'Consolas'; font-size: 9px;")
        layout.addWidget(header)
        
        self.feed = QTextEdit()
        self.feed.setReadOnly(True)
        self.feed.setStyleSheet("""
            background: rgba(0, 0, 0, 80); border: none; color: #e1f0ff; 
            font-family: 'Consolas'; font-size: 10px; padding: 4px;
        """)
        layout.addWidget(self.feed)
        self.entry_count = 0
    
    def log_tool(self, tool_name, args_summary, result_summary):
        self.entry_count += 1
        timestamp = time.strftime("[%H:%M:%S]")
        
        # Color code by result
        is_running = result_summary == "Running..."
        color = "#ffaa00" if is_running else "#00ff7f"
        icon = "⚡" if is_running else "✓"
        
        if is_running:
            self.feed.append(
                f"<font color='gray'>{timestamp}</font> "
                f"<font color='{color}'>{icon} {tool_name}</font> "
                f"<font color='#666'>← {args_summary[:60]}</font>"
            )
        else:
            self.feed.append(
                f"<font color='gray'>{timestamp}</font> "
                f"<font color='{color}'>{icon} {tool_name}</font> "
                f"→ <font color='#aaddff'>{result_summary[:80]}</font>"
            )
        
        self.feed.verticalScrollBar().setValue(self.feed.verticalScrollBar().maximum())


# =============================================================================
# BOT SWARM STATUS — Shows all active agents and what they're doing
# =============================================================================

class BotSwarmPanel(QFrame):
    """Real-time visualization of all active bots/agents."""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(160)
        self.setStyleSheet("background: rgba(5, 10, 20, 200); border: 1px solid rgba(0, 255, 127, 30); border-radius: 8px;")
        self.bots = {}  # {name: {"status": "RUNNING", "detail": "...", "time": timestamp}}
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(200)
    
    def update_bot(self, bot_name, status, detail):
        self.bots[bot_name] = {
            "status": status,
            "detail": detail[:50],
            "time": time.time()
        }
        # Auto-remove completed/failed bots after 15 seconds
        cutoff = time.time() - 15
        self.bots = {k: v for k, v in self.bots.items() 
                     if v["time"] > cutoff or v["status"] in ("DEPLOYED", "RUNNING")}
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Header
        painter.setPen(QPen(QColor(0, 255, 127, 180), 1))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        active = sum(1 for b in self.bots.values() if b["status"] in ("DEPLOYED", "RUNNING"))
        painter.drawText(10, 16, f"AGENT_SWARM // {active} ACTIVE / {len(self.bots)} TOTAL")
        
        if not self.bots:
            painter.setPen(QColor(80, 80, 100))
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(10, 80, "No agents deployed. Standing by...")
            return
        
        # Draw each bot
        y = 30
        status_colors = {
            "DEPLOYED": QColor(0, 191, 255),
            "RUNNING": QColor(255, 140, 0),
            "SUCCESS": QColor(0, 255, 127),
            "FAILED": QColor(255, 60, 60),
        }
        
        for name, info in list(self.bots.items())[:5]:  # Max 5 visible
            status = info["status"]
            color = status_colors.get(status, QColor(120, 120, 140))
            
            # Status dot (pulsing for RUNNING)
            if status == "RUNNING":
                pulse = int(abs(math.sin(time.time() * 4)) * 180) + 75
                dot_color = QColor(color.red(), color.green(), color.blue(), pulse)
            else:
                dot_color = color
            
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(20, y + 8), 4, 4)
            
            # Bot name
            painter.setPen(color)
            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            painter.drawText(32, y + 12, name)
            
            # Status badge
            painter.setPen(QColor(160, 160, 180))
            painter.setFont(QFont("Consolas", 7))
            painter.drawText(150, y + 12, f"[{status}]")
            
            # Detail
            painter.setPen(QColor(140, 170, 200))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(220, y + 12, info["detail"])
            
            y += 24


# =============================================================================
# ENHANCED NEURAL ACTIVITY GRID — Tied to real AI processing
# =============================================================================

class NeuralActivityGrid(QFrame):
    """TensorFlow-inspired grid of pulsating neurons — reflects REAL AI activity."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(280, 150)
        self.setStyleSheet("background: rgba(5, 10, 20, 200); border: 1px solid rgba(0, 191, 255, 30); border-radius: 8px;")
        self.rows = 8
        self.cols = 12
        self.neurons = [[0.1 for _ in range(self.cols)] for _ in range(self.rows)]
        self.total_fires = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.decay)
        self.timer.start(50)

    def decay(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.neurons[r][c] = max(0.05, self.neurons[r][c] - 0.03)
        self.update()

    def pulse(self, intensity=5):
        count = min(intensity, 30)
        self.total_fires += count
        for _ in range(count):
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            self.neurons[r][c] = min(1.0, self.neurons[r][c] + 0.6)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Label with fire counter
        painter.setPen(QPen(QColor(0, 191, 255, 150), 1))
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(10, 15, f"NEURAL_GRID // {self.total_fires} SYNAPSES FIRED")

        w = self.width() - 20
        h = self.height() - 30
        dx = w / self.cols
        dy = h / self.rows

        for r in range(self.rows):
            for c in range(self.cols):
                val = self.neurons[r][c]
                
                # Color shifts from cool blue to hot orange based on intensity
                if val > 0.7:
                    color = QColor(255, int(140 * val), 0)  # Hot orange
                elif val > 0.4:
                    color = QColor(0, 255, int(255 * val))  # Bright cyan
                else:
                    color = QColor(0, int(191 * val * 2), 255)  # Cool blue
                color.setAlpha(int(val * 255))
                
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                
                radius = 2 + (val * 5)
                cx = 15 + c * dx
                cy = 25 + r * dy
                painter.drawEllipse(QPointF(cx, cy), radius, radius)
                
                # Glow for hot neurons
                if val > 0.5:
                    glow = QRadialGradient(QPointF(cx, cy), radius * 2.5)
                    glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 80))
                    glow.setColorAt(1, Qt.transparent)
                    painter.setBrush(QBrush(glow))
                    painter.drawEllipse(QPointF(cx, cy), radius * 2.5, radius * 2.5)


# =============================================================================
# THINKING STREAM — Live AI reasoning tokens
# =============================================================================

class NeuralThinkingStream(QFrame):
    """Real-time scrolling visualizer for AI reasoning — shows actual thinking tokens."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(55)
        self.setStyleSheet("background: rgba(0, 5, 10, 220); border: 1px solid rgba(255, 140, 0, 40); border-radius: 5px;")
        self.stream_tokens = []
        self.matrix_chars = "01"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stream)
        self.timer.start(80)
        self.active_time = 0

    def trigger(self, _intensity=None):
        self.active_time = max(self.active_time, 25)

    def add_token(self, text):
        """Add a real reasoning token to the stream."""
        words = text.split()[:3]
        for w in words:
            self.stream_tokens.append({"text": w[:8], "alpha": 255, "type": "real"})
        self.active_time = max(self.active_time, 30)
        if len(self.stream_tokens) > 50:
            self.stream_tokens = self.stream_tokens[-50:]

    def update_stream(self):
        if self.active_time > 0:
            # Add matrix-style background noise
            noise = "".join(random.choices(self.matrix_chars, k=3))
            self.stream_tokens.append({"text": noise, "alpha": 100, "type": "noise"})
            self.active_time -= 1
        
        # Fade old tokens
        for t in self.stream_tokens:
            t["alpha"] = max(0, t["alpha"] - 6)
        self.stream_tokens = [t for t in self.stream_tokens if t["alpha"] > 0]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Header
        painter.setPen(QColor(255, 140, 0, 100))
        painter.setFont(QFont("Consolas", 6))
        status = "ACTIVE" if self.active_time > 0 else "STANDBY"
        painter.drawText(5, 10, f"THINKING_STREAM // {status}")
        
        x = 10
        for token in self.stream_tokens[-35:]:
            alpha = token["alpha"]
            if token["type"] == "real":
                painter.setPen(QColor(0, 255, 255, alpha))
                painter.setFont(QFont("Consolas", 8, QFont.Bold))
            else:
                painter.setPen(QColor(0, 191, 255, min(alpha, 60)))
                painter.setFont(QFont("Consolas", 7))
            
            painter.drawText(x, 35, token["text"])
            x += len(token["text"]) * 7 + 4
            if x > self.width() - 20:
                break
        
        # Scanline effect when active
        if self.active_time > 0:
            scan_pos = (int(time.time() * 300) % self.width())
            painter.setPen(QPen(QColor(255, 140, 0, 120), 1))
            painter.drawLine(scan_pos, 15, scan_pos, 50)


# =============================================================================
# EXISTING WIDGETS (cleaned up)
# =============================================================================

class SentinelFrame(QLabel):
    """The Sentinel Eye: Integrated camera feed."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 160)
        self.setStyleSheet("background: rgba(0, 0, 0, 100); border: 2px solid rgba(0, 191, 255, 30); border-radius: 10px;")
        self.setAlignment(Qt.AlignCenter)
        self.setText("SENTINEL LINKING...")
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
    def start_feed(self):
        if cv2 is None:
            self.setText("SENTINEL OFFLINE\n(OpenCV not installed)")
            return
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == 'nt' else cv2.VideoCapture(0)
            self.timer.start(33)
        except:
            self.setText("SENTINEL OFFLINE")
        
    def update_frame(self):
        if not self.cap or cv2 is None: return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_BONE)
            frame = cv2.resize(frame, (280, 160))
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
            self.setPixmap(QPixmap.fromImage(qt_image))


class ModelSentinel(QFrame):
    """Displays active LLM status."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(280, 80)
        self.setStyleSheet("background: rgba(5, 20, 35, 100); border: 1px solid rgba(0, 191, 255, 30); border-radius: 8px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.title = QLabel("MODEL_SENTINEL")
        self.title.setStyleSheet("color: rgba(0, 191, 255, 180); font-weight: bold; font-family: 'Consolas'; font-size: 9px;")
        layout.addWidget(self.title)
        
        self.model_label = QLabel("BRAIN: SEARCHING...")
        self.model_label.setStyleSheet("color: #00ff7f; font-family: 'Segoe UI'; font-size: 11px;")
        layout.addWidget(self.model_label)
        
        self.profile_label = QLabel("PROFILE: DEFAULT")
        self.profile_label.setStyleSheet("color: #a9d6ff; font-family: 'Segoe UI'; font-size: 9px;")
        layout.addWidget(self.profile_label)

    def update_model(self, model, profile):
        self.model_label.setText(f"BRAIN: {model.upper()}")
        self.profile_label.setText(f"PROFILE: {profile.upper()}")


class TelemetryGraph(QFrame):
    """Real-time data visualization for system metrics."""
    def __init__(self, color, label="Metric"):
        super().__init__()
        self.points = [0] * 50
        self.color = color
        self.label = label
        self.setFixedSize(280, 80)
        self.setStyleSheet("background: rgba(5, 15, 25, 150); border: 1px solid rgba(0, 191, 255, 20); border-radius: 8px;")

    def add_point(self, value):
        self.points.pop(0)
        self.points.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(QPen(self.color.lighter(120), 1))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(10, 16, f"{self.label}: {int(self.points[-1])}%")

        if not self.points: return
        w = self.width() - 20
        h = self.height() - 30
        step = w / (len(self.points) - 1)
        
        # Fill gradient under the graph line
        path = QPainterPath()
        path.moveTo(10, self.height() - 5)
        for i in range(len(self.points)):
            y = self.height() - 5 - (self.points[i] / 100 * h)
            path.lineTo(10 + i * step, y)
        path.lineTo(10 + (len(self.points) - 1) * step, self.height() - 5)
        path.closeSubpath()
        
        fill_color = QColor(self.color)
        fill_color.setAlpha(30)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Line
        painter.setPen(QPen(self.color, 2))
        for i in range(len(self.points) - 1):
            y1 = self.height() - 5 - (self.points[i] / 100 * h)
            y2 = self.height() - 5 - (self.points[i+1] / 100 * h)
            painter.drawLine(QPointF(10 + i*step, y1), QPointF(10 + (i+1)*step, y2))


class WeatherWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedSize(280, 60)
        self.setStyleSheet("background: rgba(5, 20, 35, 100); border: 1px solid rgba(0, 191, 255, 30); border-radius: 8px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self.temp_label = QLabel("ATMOSPHERE: 22°C")
        self.temp_label.setStyleSheet("color: #00bfff; font-family: 'Segoe UI Light'; font-size: 12px;")
        self.condition_label = QLabel("STATUS: OPTIMAL")
        self.condition_label.setStyleSheet("color: rgba(0, 255, 127, 180); font-family: 'Consolas'; font-size: 9px;")
        layout.addWidget(self.temp_label)
        layout.addWidget(self.condition_label)

    def update_weather(self, data):
        if isinstance(data, str):
            self.condition_label.setText(f"STATUS: {data.upper()}")
        elif isinstance(data, dict):
            self.temp_label.setText(f"ATMOSPHERE: {data.get('temp', 22)}°C")
            self.condition_label.setText(f"STATUS: {data.get('condition', 'OPTIMAL').upper()}")


class ReasoningGraph(QGraphicsView):
    """Neural-inspired visual node graph for AI decision tracking."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(180)
        self.setStyleSheet("background: #050a10; border: none;")
        self.setScene(QGraphicsScene())
        self.scene().setSceneRect(0, 0, 600, 180)
        self.nodes = []
        self.last_pos = QPointF(50, 90)
        self.add_node("CORE", "origin")

    def add_node(self, label_or_id, node_type_or_label="decision", *args):
        if args:
            label = node_type_or_label
            node_type = args[0] if len(args) >= 1 else "decision"
        else:
            label = label_or_id
            node_type = node_type_or_label

        type_colors = {
            "origin": QColor(0, 191, 255),
            "decision": QColor(255, 140, 0),
            "search": QColor(0, 255, 127),
            "url": QColor(255, 100, 100),
            "code": QColor(200, 100, 255),
            "tool": QColor(255, 200, 0),
        }
        color = type_colors.get(node_type, QColor(255, 140, 0))
        
        pos = QPointF(self.last_pos.x() + 70, 90 + random.randint(-40, 40))
        if pos.x() > self.scene().width() - 50:
            self.scene().clear()
            self.last_pos = QPointF(50, 90)
            pos = QPointF(120, 90)
            self.add_node("CORE", "origin")
            return

        if self.last_pos:
            line = QGraphicsLineItem(self.last_pos.x(), self.last_pos.y(), pos.x(), pos.y())
            line.setPen(QPen(color.darker(150), 1))
            self.scene().addItem(line)

        dot = QGraphicsEllipseItem(pos.x()-5, pos.y()-5, 10, 10)
        dot.setBrush(QBrush(color))
        dot.setPen(QPen(Qt.white, 1))
        self.scene().addItem(dot)

        text = QGraphicsTextItem(label[:25])
        text.setDefaultTextColor(color.lighter(150))
        text.setFont(QFont("Consolas", 7))
        text.setPos(pos.x()+5, pos.y()-15)
        self.scene().addItem(text)
        
        self.last_pos = pos


# =============================================================================
# MAIN DASHBOARD — The full JACK AGENT DASHBOARD
# =============================================================================

class NexusDashboard(QMainWindow):
    """The High-Fidelity JACK AGENT DASHBOARD with real-time process visualization."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JACK AGENT DASHBOARD — NEURAL COMMAND CENTER")
        self.setMinimumSize(1360, 860)
        self.setStyleSheet("background-color: #050a10; color: #00bfff;")
        
        self.start_time = time.time()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(8, 8, 8, 4)
        self.root_layout.setSpacing(6)
        
        # === TOP: Pipeline Status Bar ===
        self.pipeline = PipelineStatusBar()
        self.root_layout.addWidget(self.pipeline)
        
        # === MIDDLE: 3-Column Layout ===
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(8)
        
        # --- LEFT PANEL (Telemetry + Model) ---
        self.left_panel = QVBoxLayout()
        self.left_panel.setSpacing(4)
        
        self.sentinel = SentinelFrame()
        self.left_panel.addWidget(self.sentinel)
        
        self.model_sentinel = ModelSentinel()
        self.left_panel.addWidget(self.model_sentinel)
        
        self.cpu_graph = TelemetryGraph(QColor(0, 191, 255), "CPU")
        self.left_panel.addWidget(self.cpu_graph)
        
        self.ram_graph = TelemetryGraph(QColor(0, 255, 127), "RAM/GPU")
        self.left_panel.addWidget(self.ram_graph)
        
        self.neural_grid = NeuralActivityGrid()
        self.left_panel.addWidget(self.neural_grid)
        
        self.weather = WeatherWidget()
        self.left_panel.addWidget(self.weather)
        
        self.left_panel.addStretch()
        self.main_layout.addLayout(self.left_panel, 1)
        
        # --- CENTER PANEL (Chat + Thinking + Graph) ---
        self.center_panel = QVBoxLayout()
        self.center_panel.setSpacing(4)
        
        chat_header = QLabel("NEURAL_CHAT_FEED")
        chat_header.setStyleSheet("color: rgba(255, 140, 0, 180); font-weight: bold; font-family: 'Consolas'; font-size: 10px;")
        self.center_panel.addWidget(chat_header)
        
        self.chat_feed = QTextEdit()
        self.chat_feed.setReadOnly(True)
        self.chat_feed.setStyleSheet("background: #08111a; border: 1px solid rgba(255, 140, 0, 30); color: #e1f0ff; font-family: 'Segoe UI'; font-size: 12px; padding: 8px;")
        self.center_panel.addWidget(self.chat_feed, 2)
        
        self.thinking_stream = NeuralThinkingStream()
        self.center_panel.addWidget(self.thinking_stream)
        
        self.graph = ReasoningGraph()
        self.center_panel.addWidget(self.graph)
        
        # Bot Swarm Panel
        self.bot_swarm = BotSwarmPanel()
        self.center_panel.addWidget(self.bot_swarm)
        
        self.main_layout.addLayout(self.center_panel, 2)
        
        # --- RIGHT PANEL (Reasoning + Tools + News) ---
        self.right_panel = QVBoxLayout()
        self.right_panel.setSpacing(4)
        
        log_header = QLabel("CORE_REASONING_LOG")
        log_header.setStyleSheet("color: rgba(0, 191, 255, 180); font-weight: bold; font-family: 'Consolas'; font-size: 10px;")
        self.right_panel.addWidget(log_header)
        
        self.thought_log = QTextEdit()
        self.thought_log.setReadOnly(True)
        self.thought_log.setStyleSheet("background: #08111a; border: none; color: #a9d6ff; font-family: 'Consolas'; font-size: 10px;")
        self.right_panel.addWidget(self.thought_log, 2)
        
        # Tool Execution Log
        self.tool_log = ToolExecutionLog()
        self.right_panel.addWidget(self.tool_log, 2)
        
        news_header = QLabel("GLOBAL_NEWS_DECRYPTED")
        news_header.setStyleSheet("color: rgba(0, 255, 127, 180); font-weight: bold; font-family: 'Consolas'; font-size: 10px;")
        self.right_panel.addWidget(news_header)
        
        self.headline_log = QTextEdit()
        self.headline_log.setReadOnly(True)
        self.headline_log.setFixedHeight(100)
        self.headline_log.setStyleSheet("background: rgba(0, 0, 0, 50); border: 1px solid rgba(0, 255, 127, 20); color: #888; font-family: 'Segoe UI'; font-size: 10px;")
        self.right_panel.addWidget(self.headline_log)
        
        self.main_layout.addLayout(self.right_panel, 1)
        self.root_layout.addLayout(self.main_layout, 1)
        
        # === CONNECT ALL SIGNALS ===
        self.signals = get_signals()
        self.signals.start_bridge_server()
        
        # Existing signals
        self.signals.thought_received.connect(self.log_thought)
        self.signals.chat_received.connect(self.log_chat)
        self.signals.model_active.connect(self.model_sentinel.update_model)
        self.signals.node_added.connect(self.graph.add_node)
        self.signals.headlines_updated.connect(self.update_headlines)
        self.signals.telemetry_pulsed.connect(self.update_telemetry)
        self.signals.weather_pulsed.connect(self.weather.update_weather)
        self.signals.neural_pulse.connect(self.neural_grid.pulse)
        self.signals.neural_pulse.connect(self.thinking_stream.trigger)
        
        # NEW: Real-time process signals
        self.signals.pipeline_stage.connect(self._on_pipeline_stage)
        self.signals.tool_executed.connect(self._on_tool_executed)
        self.signals.bot_status.connect(self._on_bot_status)
        self.signals.thinking_token.connect(self._on_thinking_token)
        
        # Timers
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.poll_telemetry)
        self.telemetry_timer.start(2000)
        
        self.news_timer = QTimer(self)
        self.news_timer.timeout.connect(self.fetch_live_news)
        self.news_timer.start(300000)
        QTimer.singleShot(2000, self.fetch_live_news)
        
        QTimer.singleShot(3000, self.sentinel.start_feed)
        
        self.uptime_timer = QTimer(self)
        self.uptime_timer.timeout.connect(self.update_status_bar)
        self.uptime_timer.start(1000)

    # === NEW SIGNAL HANDLERS ===
    
    @Slot(str, str)
    def _on_pipeline_stage(self, stage, detail):
        """Update the pipeline visualization."""
        self.pipeline.set_stage(stage, detail)
        # Also pulse the neural grid based on stage
        intensity_map = {"LISTENING": 2, "TRANSCRIBED": 5, "THINKING": 10, "EXECUTING": 15, "SPEAKING": 4}
        intensity = intensity_map.get(stage, 1)
        self.neural_grid.pulse(intensity)
    
    @Slot(str, str, str)
    def _on_tool_executed(self, tool_name, args_summary, result_summary):
        """Log tool execution to the tool panel."""
        self.tool_log.log_tool(tool_name, args_summary, result_summary)
        # Add as a node in the reasoning graph
        self.graph.add_node(tool_name, "tool")
    
    @Slot(str, str, str)
    def _on_bot_status(self, bot_name, status, detail):
        """Update bot swarm panel."""
        self.bot_swarm.update_bot(bot_name, status, detail)
        # Add as a node in the reasoning graph
        self.graph.add_node(bot_name, "code")
    
    @Slot(str)
    def _on_thinking_token(self, token):
        """Stream thinking tokens to the visualizer."""
        self.thinking_stream.add_token(token)

    # === EXISTING HANDLERS (updated) ===
    
    def update_status_bar(self):
        uptime = int(time.time() - self.start_time)
        hrs = uptime // 3600
        mins = (uptime % 3600) // 60
        secs = uptime % 60
        tools = self.tool_log.entry_count
        synapses = self.neural_grid.total_fires
        self.statusBar().showMessage(
            f"JACK AGENT DASHBOARD | UPTIME: {hrs:02}:{mins:02}:{secs:02} | "
            f"TOOLS: {tools} | SYNAPSES: {synapses} | HUD: ONLINE | ENCRYPTION: AES-256"
        )
        self.statusBar().setStyleSheet("color: #4488aa; font-family: 'Consolas'; font-size: 9px;")

    def poll_telemetry(self):
        try:
            def _poll():
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                gpu = 0
                try:
                    res = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], text=True)
                    gpu = int(res.strip())
                except: pass
                self.signals.telemetry_pulsed.emit({"cpu": cpu, "ram": ram, "gpu": gpu})
            threading.Thread(target=_poll, daemon=True).start()
        except: pass

    @Slot(dict)
    def update_telemetry(self, data):
        self.cpu_graph.add_point(data['cpu'])
        self.ram_graph.add_point(data.get('gpu', data['ram']))
        self.ram_graph.label = "GPU" if data.get('gpu', 0) > 0 else "RAM"

    @Slot(str, str)
    def log_chat(self, speaker, text):
        timestamp = time.strftime("[%H:%M]")
        color = "#00ff7f" if speaker == "USER" else "#ff8c00"
        prefix = f"<b>{speaker}:</b>"
        self.chat_feed.append(f"<font color='gray'>{timestamp}</font> <font color='{color}'>{prefix}</font> {text}")
        self.chat_feed.verticalScrollBar().setValue(self.chat_feed.verticalScrollBar().maximum())

    @Slot(str, str)
    def log_thought(self, text, thought_type):
        timestamp = time.strftime("[%H:%M:%S]")
        color_map = {"thought": "#00bfff", "decision": "#ff8c00", "log": "#888"}
        color = color_map.get(thought_type, "#00bfff")
        self.thought_log.append(f"<font color='gray'>{timestamp}</font> <font color='{color}'><b>{thought_type.upper()}:</b></font> {text}")
        self.thought_log.verticalScrollBar().setValue(self.thought_log.verticalScrollBar().maximum())

    def fetch_live_news(self):
        if not DDGS: return
        try:
            def _fetch():
                results = DDGS().news("global tech AI breakthroughs", max_results=5)
                lines = [r['title'] for r in results]
                self.signals.headlines_updated.emit(lines)
            threading.Thread(target=_fetch, daemon=True).start()
        except: pass

    @Slot(list)
    def update_headlines(self, lines):
        self.headline_log.clear()
        for line in lines:
            self.headline_log.append(f"• {line}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexusDashboard()
    window.show()
    sys.exit(app.exec())
