import logging
import os

# Ensure logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename="logs/jack.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def log_event(msg):
    """Log an event to the production log file."""
    logging.info(msg)
    print(f"TITAN LOG: {msg}")
