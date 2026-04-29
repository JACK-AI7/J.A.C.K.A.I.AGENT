import threading

def start_guardian_background(guardian_instance):
    """Start the Guardian service in a non-blocking background thread."""
    thread = threading.Thread(target=guardian_instance.start)
    thread.daemon = True # Shutdown with main process
    thread.start()
    return thread
