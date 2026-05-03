"""
Agent Status Panel Widget for HUD
Shows real-time status, thoughts, and actions of all JACK agents
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont
import time


class AgentStatusWidget(QFrame):
    """Visual panel showing a single agent's status and activity"""
    
    def __init__(self, agent_name, parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.current_status = "INITIALIZED"
        self.last_action = ""
        self.last_thought = ""
        self.thought_tokens = []
        self.activity_timestamp = time.time()
        
        self.setup_ui()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
    def setup_ui(self):
        """Create the visual layout for this agent widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        
        # Header: Agent name + status indicator
        header_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.agent_name.upper())
        self.name_label.setStyleSheet("""
            color: rgba(0, 191, 255, 220);
            font-family: 'Segoe UI Light';
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        self.status_label = QLabel(self.current_status)
        self.status_label.setStyleSheet("""
            color: rgba(0, 255, 127, 200);
            font-family: 'Consolas', 'Courier New';
            font-size: 9px;
            padding: 2px 6px;
            background: rgba(0, 255, 127, 20);
            border-radius: 3px;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Last action (single line)
        self.action_label = QLabel("...")
        self.action_label.setStyleSheet("""
            color: rgba(255, 255, 255, 160);
            font-family: 'Segoe UI';
            font-size: 9px;
            padding: 2px 4px;
        """)
        self.action_label.setWordWrap(True)
        layout.addWidget(self.action_label)
        
        # Last thought (small, cyan, scrolling)
        self.thought_label = QLabel("...")
        self.thought_label.setStyleSheet("""
            color: rgba(0, 255, 255, 140);
            font-family: 'Consolas', 'Courier New';
            font-size: 8px;
            padding: 2px 4px;
        """)
        self.thought_label.setWordWrap(True)
        layout.addWidget(self.thought_label)
        
        # Visual pulse indicator
        self.pulse_label = QLabel("●")
        self.pulse_label.setStyleSheet("""
            color: rgba(0, 191, 255, 200);
            font-size: 10px;
        """)
        header_layout.addWidget(self.pulse_label)
        
        # Set background
        self.setStyleSheet("""
            AgentStatusWidget {
                background: rgba(10, 10, 20, 180);
                border: 1px solid rgba(0, 191, 255, 60);
                border-radius: 6px;
            }
        """)
        
    def update_status(self, status, detail=""):
        """Update agent status display"""
        self.current_status = status
        self.status_label.setText(status)
        
        # Color code status
        if status == "ACTIVE" or status == "RUNNING":
            color = QColor(0, 255, 127)  # Green
        elif status == "THINKING" or status == "EXECUTING":
            color = QColor(0, 191, 255)  # Cyan
        elif status == "ERROR" or status == "FAILED":
            color = QColor(255, 50, 50)  # Red
        else:
            color = QColor(180, 180, 180)  # Gray
            
        self.status_label.setStyleSheet(f"""
            color: {color.name()};
            font-family: 'Consolas', 'Courier New';
            font-size: 9px;
            padding: 2px 6px;
            background: rgba({color.red()}, {color.green()}, {color.blue()}, 30);
            border-radius: 3px;
        """)
        
    def update_action(self, action_type, target, result):
        """Show last action performed"""
        self.last_action = f"[{action_type}] {target} → {result}"
        self.action_label.setText(self.last_action[:100])
        self.activity_timestamp = time.time()
        
    def add_thought(self, thought_text):
        """Add a reasoning thought (streaming)"""
        self.thought_tokens.append(thought_text)
        # Keep last 3 thoughts
        if len(self.thought_tokens) > 3:
            self.thought_tokens.pop(0)
            
        display = " | ".join(self.thought_tokens[-2:])
        self.thought_label.setText(display[:150])
        
    def paintEvent(self, event):
        """Custom painting for visual effects"""
        super().paintEvent(event)
        
        # Optional: Draw subtle glow based on recency
        age = time.time() - self.activity_timestamp
        if age < 2.0:  # Recent activity
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Pulsing glow at bottom
            intensity = int(50 * (1.0 - age / 2.0))
            color = QColor(0, 191, 255, intensity)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawRoundedRect(1, self.height()-3, self.width()-2, 2, 1, 1)


class AgentDashboard(QWidget):
    """Container for all agent status panels"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_widgets = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Create the dashboard layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("🤖 AGENT MATRIX")
        header.setStyleSheet("""
            color: rgba(0, 191, 255, 255);
            font-family: 'Segoe UI Light';
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 8px;
            background: rgba(0, 191, 255, 20);
            border-radius: 4px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Container for agent widgets
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 50);
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 191, 255, 100);
                border-radius: 3px;
            }
        """)
        
        self.agents_container = QWidget()
        self.agents_layout = QVBoxLayout(self.agents_container)
        self.agents_layout.setSpacing(6)
        self.agents_layout.addStretch()
        
        scroll.setWidget(self.agents_container)
        layout.addWidget(scroll)
        
        # Styling
        self.setStyleSheet("""
            AgentDashboard {
                background: rgba(5, 5, 15, 220);
                border: 1px solid rgba(0, 191, 255, 80);
                border-radius: 8px;
            }
        """)
        
    def register_agent(self, agent_name):
        """Create a new agent status widget"""
        if agent_name in self.agent_widgets:
            return self.agent_widgets[agent_name]
            
        widget = AgentStatusWidget(agent_name)
        self.agent_widgets[agent_name] = widget
        
        # Insert before stretch (at position count-1)
        insert_pos = self.agents_layout.count() - 1
        self.agents_layout.insertWidget(insert_pos, widget)
        
        return widget
        
    def update_agent_status(self, agent_name, status, detail=""):
        """Update agent status"""
        widget = self.register_agent(agent_name)
        widget.update_status(status, detail)
        
    def update_agent_action(self, agent_name, action_type, target, result):
        """Show agent's last action"""
        widget = self.register_agent(agent_name)
        widget.update_action(action_type, target, result)
        
    def add_agent_thought(self, agent_name, thought):
        """Add a thought from agent"""
        widget = self.register_agent(agent_name)
        widget.add_thought(thought)


# Test standalone
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dashboard = AgentDashboard()
    dashboard.show()
    
    # Simulate updates
    dashboard.register_agent("DesktopAgent")
    dashboard.register_agent("SystemController")
    dashboard.register_agent("VisualOrchestrator")
    
    dashboard.update_agent_status("DesktopAgent", "ACTIVE", "Executing click")
    dashboard.update_agent_action("DesktopAgent", "CLICK", "button", "Success")
    dashboard.add_agent_thought("DesktopAgent", "Moving to target coordinates")
    
    sys.exit(app.exec())
