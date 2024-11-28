import os
from skeleton_bus import Host
from ee315_24_lib import Bus, Packet

def test_bus_functionality():
    total_score = 0
    bus = Bus()
    
    # Create and connect hosts
    host1 = Host("00:00:00:00:00:01")
    host2 = Host("00:00:00:00:00:02")
    host3 = Host("00:00:00:00:00:03")
    
    bus.connect_host(host1)
    bus.connect_host(host2)
    bus.connect_host(host3)

    # Test 1: Broadcast Packet (20 points)
    print("\nTesting Broadcast Packet (20 points)...")
    try:
        host1.send_packet("00:00:00:00:00:02","Test 1",bus)
        open(bus.log_file, 'w').close()  # Clear log
        
        assert "Test 1" in [i.payload for i in host2.buffer], "Packet not received by the correct host"
        assert "Test 1" not in [i.payload for i in host1.buffer], "Packet incorrectly received by the source host"
        assert "Test 1" not in [i.payload for i in host3.buffer], "Packet incorrectly received by an unrelated host"

        host2.send_packet("00:00:00:00:00:03","Test 2",bus)
        open(bus.log_file, 'w').close()  # Clear log

        assert "Test 2" in [i.payload for i in host3.buffer], "Packet not received by the correct host"
        assert "Test 2" not in [i.payload for i in host1.buffer], "Packet incorrectly received by the source host"
        assert "Test 2" not in [i.payload for i in host2.buffer], "Packet incorrectly received by an unrelated host"

        total_score += 20
        print("✓ Broadcast Packet test passed")
    except AssertionError as e:
        print(f"✗ Broadcast Packet test failed: {str(e)}")

    # Test 2: Discard Unaddressed Packet (20 points)
    print("\nTesting Discard Unaddressed Packet (20 points)...")
    try:
        packet = Packet(src="00:00:00:00:00:01", dst="00:00:00:00:00:02", payload="Test Packet")
        bus.broadcast(packet)
        
        assert packet not in host1.buffer, "Source host should not receive its own packet"
        assert packet not in host3.buffer, "Unrelated host should not receive the packet"
        assert packet in host2.buffer, "Destination host should receive the packet"
        
        total_score += 20
        print("✓ Discard Unaddressed Packet test passed")
    except AssertionError as e:
        print(f"✗ Discard Unaddressed Packet test failed: {str(e)}")

    print(f"\nTotal Score: {total_score}/40")
    return total_score

if __name__ == "__main__":
    test_bus_functionality()