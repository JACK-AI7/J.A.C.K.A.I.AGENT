import socket
import json
import threading
from PySide6.QtCore import QObject, Signal

class NexusSignals(QObject):
    """Global bridge for JACK's neural telemetry."""
    # node_added: id, label, type, parent_id
    node_added = Signal(str, str, str, str)
    
    # thought_received: text, reasoning_type (thought/decision/log)
    thought_received = Signal(str, str)
    
    # status_updated: mission_name, progress, current_node_id
    status_updated = Signal(str, int, str)
    
    # headlines_updated: list of strings
    headlines_updated = Signal(list)
    
    # telemetry_pulsed: dict of stats {cpu: 50, ram: 40, gpu: 30, net_up: 1.2, net_down: 5.6}
    telemetry_pulsed = Signal(dict)
    
    # neural_pulse: intensity/count of neurons to fire
    neural_pulse = Signal(int)
    
    # weather_pulsed: str condition (e.g., "Partly Cloudy, 24°C")
    weather_pulsed = Signal(str)
    
    # chat_received: speaker, text
    chat_received = Signal(str, str)
    
    # model_active: model_name, profile
    model_active = Signal(str, str)
    
    # launcher signals
    dashboard_requested = Signal()

    # --- NEW: Real-time Process Visualization Signals ---
    
    # pipeline_stage: stage_name (LISTENING/TRANSCRIBING/THINKING/EXECUTING/SPEAKING/IDLE), detail
    pipeline_stage = Signal(str, str)
    
    # tool_executed: tool_name, args_summary, result_summary
    tool_executed = Signal(str, str, str)
    
    # bot_status: bot_name, status (DEPLOYED/RUNNING/SUCCESS/FAILED), detail
    bot_status = Signal(str, str, str)
    
    # thinking_token: raw reasoning text token from the AI (for live stream)
    thinking_token = Signal(str)

    # --- NEW: Agent Lifecycle Signals ---
    
    # agent_status: agent_name, status (INITIALIZED/ACTIVE/IDLE/ERROR), detail
    agent_status = Signal(str, str, str)
    
    # agent_thought: agent_name, thought_text, confidence
    agent_thought = Signal(str, str, float)
    
    # agent_action: agent_name, action_type, target, result
    agent_action = Signal(str, str, str, str)
    
    # agent_visualization: agent_name, visualization_data (dict)
    agent_visualization = Signal(str, dict)

    def __init__(self):
        super().__init__()
        self._bridge_port = 55050
        self._is_server = False
        self._forwarders = [] # List of callables to forward telemetry

    def emit_bridge(self, signal_name, *args):
        """Emit locally AND send across the IPC bridge if acting as client."""
        # Always emit locally for internal components
        try:
            signal = getattr(self, signal_name)
            signal.emit(*args)
        except (RuntimeError, AttributeError):
            # Signal source or object has been deleted (common on GUI close)
            pass
        except Exception:
            pass
        
        # Call external forwarders (e.g. Mobile Relay)
        for forwarder in self._forwarders:
            try:
                forwarder(signal_name, *args)
            except: pass
        
        # If we are the Agent (Client), send to the Dashboard (Server)
        if not self._is_server:
            try:
                # Convert non-serializable args to strings
                safe_args = []
                for a in args:
                    if isinstance(a, (str, int, float, bool, type(None))):
                        safe_args.append(a)
                    elif isinstance(a, (list, dict)):
                        safe_args.append(a)
                    else:
                        safe_args.append(str(a))
                msg = json.dumps({"signal": signal_name, "args": safe_args}).encode('utf-8')
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(msg, ('127.0.0.1', self._bridge_port))
            except:
                pass

    def start_bridge_server(self):
        """Dashboard uses this to listen for remote signals."""
        self._is_server = True
        def _listen():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('127.0.0.1', self._bridge_port))
                    s.settimeout(1.0)  # Allow periodic checking
                    while True:
                        try:
                            data, addr = s.recvfrom(8192)  # Larger buffer for richer payloads
                            if not data: continue
                            payload = json.loads(data.decode('utf-8'))
                            signal_name = payload["signal"]
                            args = payload["args"]
                            # Emit the signal in the Dashboard process
                            try:
                                signal = getattr(self, signal_name)
                                signal.emit(*args)
                            except (RuntimeError, AttributeError):
                                pass
                            except:
                                pass
                        except socket.timeout:
                            continue
                except Exception as e:
                    print(f"Bridge Server Error: {e}")

        threading.Thread(target=_listen, daemon=True).start()
        print(f"Nexus Bridge: Listening on port {self._bridge_port}")

# Singleton instance
nexus_signals = NexusSignals()

def get_signals():
    return nexus_signals

def register_forwarder(callback):
    """Register a function to receive all bridge signals (e.g. for remote sync)."""
    signals = get_signals()
    if callback not in signals._forwarders:
        signals._forwarders.append(callback)
