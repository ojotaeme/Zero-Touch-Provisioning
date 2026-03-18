from app.network.base_vendor import BaseVendor

class VyOSVendor(BaseVendor):

    def generate_boot_script(self, config: dict) -> str:
        safe_hostname = config['name'].replace(' ', '-').replace('_', '-').upper()
        return f"""#!/bin/vbash
source /opt/vyatta/etc/functions/script-template

logger "ZTP: PHASE 1: Starting boot script for {config['name']}"

set system host-name 'CPE-{safe_hostname}'
set interfaces ethernet eth0 vif {config['vlan']} address '{config['ip']}'
set interfaces ethernet eth0 vif {config['vlan']} description 'WAN-ACCESS'
set interfaces ethernet eth0 description 'WAN'
set protocols static route 0.0.0.0/0 next-hop {config['gw']}

echo "Cleaning eth1 configuration..."
delete interfaces ethernet eth1 || true

echo "--- COMMIT PHASE 1 ---"
commit
save

logger "ZTP: Scheduling Reboot..."
sudo reboot
"""
    
    def generate_silence_script(self) -> str:
        return """#!/bin/vbash

logger "ZTP: PHASE 2: Starting ssh commands and validating configuration"
exit 0
"""

    def get_lan_qos_commands(self, wan_ip: str, lan_gw: str, lan_prefix: str, down_kbps: int, up_kbps: int) -> list:
        return [
            # LAN & CLEANUP
            "delete interfaces ethernet eth1 address",
            f"set interfaces bridge br0 address '{lan_gw}/{lan_prefix}'",
            "set interfaces bridge br0 description 'LAN-GATEWAY'",
            "set interfaces bridge br0 member interface eth1",
            "delete interfaces ethernet eth0 address dhcp",
            
            # QoS POLICY
            f"set qos policy shaper CLIENT-UPLOAD default bandwidth '{up_kbps}kbit'",
            f"set qos policy limiter CLIENT-DOWNLOAD default bandwidth '{down_kbps}kbit'",
            
            # QoS INTERFACE APPLICATION
            f"set qos interface eth0 egress 'CLIENT-UPLOAD'",
            f"set qos interface eth0 ingress 'CLIENT-DOWNLOAD'"
        ]