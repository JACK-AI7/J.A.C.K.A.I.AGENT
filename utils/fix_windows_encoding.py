import sys
import io

def setup_windows_encoding():
    """
    Ensures that stdout and stderr can handle Unicode characters on Windows terminals.
    If the terminal doesn't support UTF-8, it falls back to a safe writer that replaces
    incompatible characters.
    """
    if sys.platform == 'win32':
        try:
            # Try to force UTF-8 output if possible
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, io.UnsupportedOperation):
            # For older Python versions or restricted environments, use a safe wrapper
            class SafeStream:
                def __init__(self, stream):
                    self.stream = stream
                def write(self, data):
                    try:
                        self.stream.write(data)
                    except UnicodeEncodeError:
                        # Replace incompatible characters with ASCII equivalents or '?'
                        safe_data = data.encode('ascii', 'replace').decode('ascii')
                        self.stream.write(safe_data)
                def flush(self):
                    self.stream.flush()
                def __getattr__(self, name):
                    return getattr(self.stream, name)

            sys.stdout = SafeStream(sys.stdout)
            sys.stderr = SafeStream(sys.stderr)

if __name__ == "__main__":
    setup_windows_encoding()
    print("Testing Unicode: [OK] [DONE] [FAIL]")
