import paramiko
import os
from core.logger import log_event

class SSHExecutor:
    """Remote execution backend via SSH, inspired by Hermes Agent."""
    
    def __init__(self):
        self.client = None

    def execute_remote(self, host, username, password_or_key, command):
        """Execute a command on a remote server via SSH."""
        log_event(f"SSH_EXEC: Connecting to {host}...")
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Simple password auth or key file
            if os.path.exists(password_or_key):
                self.client.connect(host, username=username, key_filename=password_or_key)
            else:
                self.client.connect(host, username=username, password=password_or_key)
                
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            self.client.close()
            
            if error and not output:
                return f"SSH Error:\n{error}"
            return f"SSH Output:\n{output}"
            
        except Exception as e:
            return f"SSH Connection Failed: {str(e)}"

# Singleton
ssh_executor = SSHExecutor()

def execute_on_remote_server(host, username, auth, command):
    """Tool for JACK to manage remote servers. 'auth' can be a password or path to a private key."""
    return ssh_executor.execute_remote(host, username, auth, command)
