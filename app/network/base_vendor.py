from abc import ABC, abstractmethod

class BaseVendor(ABC):

    @abstractmethod
    def generate_boot_script(self, config: dict) -> str:
        """Generate a boot script based on the provided configuration."""
        pass

    @abstractmethod
    def generate_silence_script(self) -> str:
        """Generate a script to silence console output during provisioning."""
        pass

    @abstractmethod
    def get_lan_qos_commands(self, wan_ip: str,  lan_gw: str, lan_prefix: str, down_kbps: int, up_kbps: int) -> list:
        """Generate QoS and LAN commands."""
        pass