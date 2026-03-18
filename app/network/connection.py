from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException

class NetworkConnection:

    def __init__(self, device_creds):
        self.creds = device_creds
        self.connection = None

    def connect(self):
        try:
            self.connection = ConnectHandler(**self.creds)
            return True
        except NetMikoTimeoutException:
            print(f"[NET-ERROR] Connection timed out for {self.creds['host']}")
            return False
        except NetMikoAuthenticationException:
            print(f"[NET-ERROR] Authentication failed for {self.creds['host']}")
            return False
        except Exception as e:
            print(f"[NET-ERROR] Failed to connect to {self.creds['host']}: {e}")
        
    def send_command(self, command):
        if self.connection:
            return self.connection.send_command(command)    
        return None
        
    def send_config_set(self, commands):
        if self.connection:
            self.connection.config_mode()
            output = self.connection.send_config_set(commands)
            self.connection.commit()
            
            try:
                self.connection.save_config()
            except Exception:
                pass
            return output
        return None
        
    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            self.connection = None  

        