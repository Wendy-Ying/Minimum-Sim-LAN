from queue import Queue
class Bus:
    def __init__(self):
        self.hosts = []
        self.log_file = "bus_log.txt"
        with open(self.log_file, 'w') as f:
            f.write("Bus Log Started\n")
        self.log_event("Bus initialized")

    def log_event(self, message, category="INFO"):
        with open(self.log_file, 'a') as f:
            f.write(f"[{category}] {message}\n")

    def connect_host(self, host):
        self.hosts.append(host)
        self.log_event(f"Host {host.mac} connected to bus")

    def broadcast(self, packet):
        self.log_event(f"Broadcasting packet: {packet}")
        for host in self.hosts:
            if host.mac != packet.src:
                host.receive_packet(packet)

class Packet:
    def __init__(self, src, dst, payload):
        self.src = src
        self.dst = dst
        self.payload = payload

    def __str__(self):
        return f"Packet(src={self.src}, dst={self.dst}, payload={self.payload})"
    
class SwitchFabric:  
    def __init__(self):
        self.queue = Queue()
        self.physical_map = {}  # interface -> MAC mapping
        self.interfaces = {}    # interface -> host mapping
        self.log_file = "fabric_log.txt" 
        with open(self.log_file, 'w') as f:
            f.write("Switch Fabric Log Started\n")
        self.log_event("Switch Fabric initialized")

    def log_event(self, message, category="INFO"):
        with open(self.log_file, 'a') as f:
            f.write(f"[{category}] {message}\n")

    def connect_host_to_switch(self, host, switch):
        switch.interfaces[host.interface] = host
        self.physical_map[host.interface] = host.mac
        self.interfaces[host.interface] = host

    def forward_to_interface(self, packet, interface):
        if interface in self.interfaces:
            self.interfaces[interface].receive_packet(packet)
            self.log_event(f"Packet forwarded - Interface: {interface}, {packet}", f"SWITCH->{interface}")
        else:
            self.log_event(f"Forward failed - Invalid interface: {interface}", "ERROR")

    def forward_to_switch(self, packet):
        dst_interface = 0
        if packet.dst in self.physical_map.values():
            for interface, mac in self.physical_map.items():
                if mac == packet.dst:
                    dst_interface = interface
                    break

        src_interface = 0
        if packet.dst in self.physical_map.values():
            for interface, mac in self.physical_map.items():
                if mac == packet.src:
                    src_interface = interface
                    break
        self.log_event(f"{packet} forwarded to switch", f"SWITCH@{dst_interface}")
        return src_interface, packet

    def log_packet(self, message):       
        with open(self.log_file, 'a') as f:
            f.write(f"{message}\n")
