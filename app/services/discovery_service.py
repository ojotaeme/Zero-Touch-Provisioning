import time
import re
from app.network.connection import NetworkConnection
from app.config import Config
from app.utils.logger import get_logger

log = get_logger('DISCOVERY')

class DiscoveryService:

    @staticmethod
    def get_mac_from_pe_arp(cpe_ip: str):
        log.info(f"Discovering MAC address for {cpe_ip} via PE ARP table...")

        for _ in range(3):
            conn = NetworkConnection({"host": Config.PE_MGMT_IP, **Config.DEVICE_CREDS})
            if conn.connect():
                output = conn.send_command(f"ip neigh show {cpe_ip}")
                conn.disconnect()

                if output:
                    match = re.search(r'lladdr\s+([0-9a-fA-F:]{17})', output)
                    if match:
                        mac = match.group(1)
                        log.info(f"Found MAC address for {cpe_ip}: {mac}")
                        return mac
                    time.sleep(1)
                
                log.warning(f"MAC address for {cpe_ip} not found in ARP table. Retrying...")
                return None
            
    @staticmethod
    def get_port_and_desc_from_pop(pop_ip: str, mac: str):
        log.info(f"Discovering port and description for MAC {mac} via FDB on POP {pop_ip}...")

        conn = NetworkConnection({"host": pop_ip, **Config.DEVICE_CREDS})
        if not conn.connect():
            log.error(f"Failed to connect to POP {pop_ip} for FDB discovery.")
            return None, None

        out_mac = conn.send_command(f"sudo bridge fdb show | grep {mac}")
        port = None

        if out_mac and "dev" in out_mac:
            parts = out_mac.split()
            port = parts[parts.index("dev") + 1]

        if not port:
            log.warning(f"Port for MAC {mac} not found in FDB on POP {pop_ip}.")
            conn.disconnect()
            return None, None
        
        out_desc = conn.send_command(f"show interfaces ethernet {port}")
        conn.disconnect()

        desc = "Unknown" 
        if out_desc:
            for line in out_desc.splitlines():
                if "Description" in line:
                    desc = line.split("Description:")[1].strip()

        log.info(f"Found port {port} with description '{desc}' for MAC {mac} on POP {pop_ip}.")
        return port, desc