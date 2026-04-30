import socket
import qrcode
import json
import base64
import os
from io import BytesIO

class PairingManager:
    """Manages secure pairing between PC Agent and Mobile Controller."""
    
    SECRET_TOKEN = os.getenv("JACK_RELAY_TOKEN", "jack_secure_neural_link_2026")
    PORT = 8001
    
    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @classmethod
    def generate_pairing_payload(cls):
        """Creates a secure pairing string for QR generation."""
        data = {
            "v": "1.0",
            "ip": cls.get_local_ip(),
            "port": cls.PORT,
            "token": cls.SECRET_TOKEN,
            "name": socket.gethostname()
        }
        # Encode as base64 to keep the QR code simple and clean
        json_str = json.dumps(data)
        b64_str = base64.b64encode(json_str.encode()).decode()
        return f"jack_link:{b64_str}"

    @classmethod
    def generate_qr_pixmap_data(cls):
        """Generates QR code as raw bytes for PySide6 display."""
        payload = cls.generate_pairing_payload()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        img = qr.make_image(fill_color="white", back_color="transparent")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
