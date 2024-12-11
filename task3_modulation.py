from ee315_24_lib import SwitchFabric, Packet
import re

def string2digital(message):
    digital_list = [ord(char) for char in message]
    return digital_list

def digital2string(message):
    string = ''.join(chr(num) for num in message)
    return string

class Host:
    def __init__(self, mac, interface):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []

    def send_packet(self, dst_mac, payload, switch):
        print(f"Host {self.mac} sending payload: '{payload}'")
        digital_payload = string2digital(payload)
        print(f"Host {self.mac} digital payload: {digital_payload}")
        packet = Packet(self.mac, dst_mac, digital_payload)
        switch.handle_packet(packet)

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            print(f"Host {self.mac} received digital packet: {packet.payload}")
            string_payload = digital2string(packet.payload)
            if string_payload:
                self.buffer.append(string_payload)
                print(f"Host {self.mac} string payload: '{string_payload}'")
            else:
                print("Failed to decrypt the packet.")

class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.fabric = fabric
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

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

# 模拟通信
host1.send_packet("00:00:00:00:00:02", "Hello from A", switch)
host2.send_packet("00:00:00:00:00:03", "Hello from B", switch)
host1.send_packet("00:00:00:00:00:03", "Hello from A", switch)
host3.send_packet("00:00:00:00:00:01", "Hello from C", switch)
host3.send_packet("00:00:00:00:00:02", "Hello from C", switch)