from ee315_24_lib import SwitchFabric, Packet
import re

class Host:
    def __init__(self, mac, interface):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []

    def send_packet(self, dst_mac, payload, switch):
        packet = Packet(self.mac, dst_mac, payload)
        switch.handle_packet(packet)

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            self.buffer.append(packet)
            print(f"Host {self.mac} received packet: {packet.payload}")

class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.fabric = fabric
        self.firewall_rules = []  # 新增防火墙规则列表
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

    def add_firewall_rule(self, rule):
        self.firewall_rules.append(rule)
        print(f"Firewall rule added: {rule}")

    def handle_packet(self, packet):
        # Learn the source MAC address and store the interface number
        src_mac = packet.src
        dst_mac = packet.dst

        # Check if the source MAC is already in the MAC table
        if src_mac not in self.mac_table:
            # Learn the source MAC address and associate it with the incoming interface
            self.mac_table[src_mac] = 0
            print(f"Switch learned MAC {src_mac}")
        else:
            self.mac_table[src_mac] = 1

        # Check firewall rules before forwarding
        if self.check_firewall(packet):
            # Selective forwarding or flooding
            if dst_mac in self.mac_table:
                # Forward to the known destination interface
                dst_interface = None
                for interface, mac in self.fabric.physical_map.items():
                    if mac == dst_mac:
                        dst_interface = interface
                        break
                self.mac_table[dst_mac] = 1
                print(f"Switch forwarding packet to known interface {dst_interface}")
                self.fabric.forward_to_interface(packet, dst_interface)
            else:
                # Update the MAC table with the new interface
                self.mac_table[dst_mac] = 1
                # Flood to all interfaces except the incoming one
                print(f"Switch flooding packet to all interfaces")
                for i, host in self.interfaces.items():
                    if host and i != src_mac:
                        self.fabric.forward_to_interface(packet, i)
        else:
            print(f"Firewall blocked packet from {src_mac} to {dst_mac}")

    def check_firewall(self, packet):
        # 默认允许所有数据包通过
        allowed = True
        for rule in self.firewall_rules:
            if rule['action'] == 'block':
                # 如果规则中包含 src_mac，则检查源MAC地址
                if 'src_mac' in rule and rule['src_mac'] == packet.src:
                    allowed = False
                    break
                # 如果规则中包含 dst_mac，则检查目的MAC地址
                if 'dst_mac' in rule and rule['dst_mac'] == packet.dst:
                    allowed = False
                    break
        return allowed

# 创建网络
shared_fabric = SwitchFabric()
switch = Switch(shared_fabric)

host1 = Host("00:00:00:00:00:01", 0)
host2 = Host("00:00:00:00:00:02", 1)
host3 = Host("00:00:00:00:00:03", 2)

# 连接主机到交换机
shared_fabric.connect_host_to_switch(host1, switch)
shared_fabric.connect_host_to_switch(host2, switch)
shared_fabric.connect_host_to_switch(host3, switch)

# 添加防火墙规则，阻止00:00:00:00:00:04的通信
switch.add_firewall_rule({'action': 'block', 'dst_mac': '00:00:00:00:00:04'})

# 模拟通信
host1.send_packet("00:00:00:00:00:02", "Hello from A", switch)
host2.send_packet("00:00:00:00:00:03", "Hello from B", switch)
host1.send_packet("00:00:00:00:00:04", "Hello from A", switch)  # 这个包将被防火墙阻止
host3.send_packet("00:00:00:00:00:01", "Hello from C", switch)
host3.send_packet("00:00:00:00:00:02", "Hello from C", switch)