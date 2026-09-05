# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: MẠNG DOANH NGHIỆP CISCO & QUY TRÌNH CHẨN ĐOÁN THEO MÔ HÌNH 5 TẦNG OSI

---

## Document ID
`KB-NET-2026-001`

## Category
`Network / Cisco Systems / Infrastructure`

## Department
`IT`

## Title
Quy trình Chẩn đoán và Xử lý Sự cố Mạng Doanh nghiệp theo Mô hình 5 Tầng OSI (Cisco Catalyst & Router)

## Problem
Người dùng tại một phòng ban hoặc toàn bộ chi nhánh mất kết nối mạng LAN, không nhận được IP DHCP, không truy cập được máy chủ nội bộ hoặc chập chờn mất gói (packet loss). Cần quy trình chẩn đoán chuẩn mực từ tầng vật lý đến tầng ứng dụng để cô lập sự cố chính xác.

## Symptoms
1. Máy tính hiển thị biểu tượng mạng tam giác vàng hoặc *"No Internet Access"*, nhận dải IP tự gán APIPA `169.254.x.x`.
2. Ping gateway nội bộ chập chờn, tỷ lệ mất gói (packet loss) > 30% hoặc ping báo *"Destination Host Unreachable"*.
3. Đèn cổng Switch (Link LED) nhấp nháy màu cam (Amber) hoặc tắt hoàn toàn; cổng switch rơi vào trạng thái `err-disabled`.
4. Không thể ping các VLAN khác nhau trong công ty mặc dù cùng cắm vào switch Core.
5. Ứng dụng nội bộ (ERP, File Server) báo lỗi kết nối ngắt quãng (`Connection timed out`).

## Error Message
* Cisco CLI Syslog Messages:
  - `%ETHCNTR-3-LOOP_BACK_DETECTED: Loopback packet received on GigabitEthernet0/1`
  - `%PM-4-ERR_DISABLE: bpduguard err-disable detected on Gi0/2, putting Gi0/2 in err-disable state`
  - `%SPANTREE-2-BLOCK_PVID_LOCAL: Blocking GigabitEthernet0/24 on VLAN0020. Inconsistent local vlan`
  - `%OSPF-5-ADJCHG: Process 1, Nbr 10.0.0.2 on GigabitEthernet0/0 from EXSTART to DOWN, Neighbor Down: Too many Retransmissions`

## Environment
* **Core Switch**: Cisco Catalyst 3850 / 9300 Series (Layer 3 Routing Enabled).
* **Access Switch**: Cisco Catalyst 2960X / 1000 Series (Layer 2 Switching).
* **Router / Firewall**: Cisco ISR 4321 / Cisco Firepower 1010.
* **Topologies**: Phân chia VLAN (VLAN 10: Ban Giám đốc, VLAN 20: Kế toán, VLAN 30: IT, VLAN 40: Nhân viên chung, VLAN 99: Quản trị Native).

## Possible Causes (Phân bổ theo 5 tầng OSI)
1. **Layer 1 (Physical)**: Cáp mạng đứt ngầm, đầu bấm RJ45 oxy hóa hoặc cong chân, module quang SFP lỗi công suất phát (Tx/Rx), switchport bị bụi hoặc cắm lỏng.
2. **Layer 2 (Data Link)**:
   - Native VLAN Mismatch giữa 2 đầu đường Trunk 802.1Q.
   - Vòng lặp mạng (Switching Loop) do cắm dây 2 đầu vào cùng một switch khiến STP kích hoạt Broadcast Storm.
   - Vi phạm tính năng an toàn cổng (`Port-Security` hoặc `BPDU Guard`) khiến port bị shutdown sang `err-disabled`.
   - Bất đối xứng tốc độ/chế độ song công (Duplex Mismatch: một đầu Full, một đầu Half) gây ra va chạm (Collisions) và Late Collisions.
3. **Layer 3 (Network)**:
   - Thiếu cấu hình `ip helper-address` (DHCP Relay) trên SVI của Router/L3 Switch khiến client không lấy được IP từ DHCP Server.
   - Trùng địa chỉ IP (IP Conflict) với Gateway hoặc Server.
   - Sai lệch MTU giữa 2 Router chạy OSPF khiến quá trình bắt tay Neighbor bị kẹt ở trạng thái `EXSTART / EXCHANGE`.
   - ACL (Access Control List) chặn nhầm traffic giữa các VLAN.
4. **Layer 4 (Transport)**:
   - Quá tải bảng dịch địa chỉ NAT/PAT trên Router Gateway khiến session mới bị từ chối (`NAT table exhaustion`).
   - Cổng TCP/UDP bị firewall hoặc ACL nội bộ drop (ví dụ TCP 445 cho SMB, TCP 3389 cho RDP).
5. **Layer 7 (Application)**:
   - Máy chủ DNS nội bộ bị treo service, trả về `DNS Request Timed Out` dù mạng IP thông suốt.

---

## Diagnosis (Quy trình chẩn đoán tuần tự 5 tầng OSI)

### TẦNG 1: LAYER 1 — PHYSICAL LAYER TROUBLESHOOTING
Kiểm tra tín hiệu vật lý đầu tiên:
```cisco
! 1. Kiểm tra trạng thái cổng và tốc độ
show interfaces status | include Gi0/1

! 2. Xem chi tiết thông số lỗi cáp và công suất quang (nếu dùng SFP)
show interfaces GigabitEthernet0/1
! Chú ý các chỉ số:
! - input errors, CRC errors -> Thường do cáp hỏng hoặc nhiễu điện từ
! - output drops -> Nghẽn hàng đợi cổng (buffer overflow)
! - collisions, late collision -> 100% là Duplex Mismatch!

! 3. Đối với cổng quang SFP, kiểm tra công suất quang thu/phát:
show interfaces GigabitEthernet0/24 transceiver detail
! Đảm bảo Rx Power nằm trong ngưỡng tiêu chuẩn: -3 dBm đến -15 dBm
```

### TẦNG 2: LAYER 2 — DATA LINK LAYER TROUBLESHOOTING
Kiểm tra cấu hình VLAN, Trunking và Spanning Tree:
```cisco
! 1. Kiểm tra đường Trunk kết nối giữa các Switch:
show interfaces trunk
! Đảm bảo:
! - Mode: on hoặc trunk
! - Encapsulation: 802.1q
! - Native VLAN: Phải trùng khớp ở cả 2 Switch (mặc định VLAN 99 hoặc 1)
! - Vlans allowed on trunk: Đã cho phép VLAN của client đi qua chưa!

! 2. Kiểm tra gán VLAN trên cổng Access:
show vlan brief
show mac address-table interface GigabitEthernet0/1

! 3. Kiểm tra cổng có bị Spanning Tree / Port-Security khóa không:
show interfaces status err-disabled
show spanning-tree interface GigabitEthernet0/1
```

### TẦNG 3: LAYER 3 — NETWORK LAYER TROUBLESHOOTING
Kiểm tra Routing, Inter-VLAN và DHCP Relay:
```cisco
! 1. Kiểm tra bảng định tuyến trên L3 Switch / Router:
show ip route
show ip route vlan 20

! 2. Kiểm tra Interface VLAN (SVI) có UP/UP không:
show ip interface brief | include Vlan
! Nếu Status là UP nhưng Protocol là DOWN: Chưa có port nào thuộc VLAN đó đang cắm thiết bị hoạt động!

! 3. Kiểm tra cấu hình DHCP Relay (ip helper-address) trên SVI:
show run interface Vlan20
! Phải có dòng: ip helper-address 192.168.1.10 (IP của DHCP Server)

! 4. Đối với giao thức định tuyến OSPF:
show ip ospf neighbor
! Nếu State kẹt ở EXSTART/EXCHANGE: Kiểm tra MTU bằng lệnh:
! show interfaces GigabitEthernet0/0 | include MTU
```

### TẦNG 4: LAYER 4 — TRANSPORT & NAT TROUBLESHOOTING
```cisco
! 1. Kiểm tra số lượng NAT translation đang hoạt động:
show ip nat statistics
show ip nat translations | count

! 2. Kiểm tra Access List có drop packet không:
show access-lists
! Quan sát số lượt match (matches) trên từng dòng deny/permit
```

### TẦNG 5: LAYER 7 — APPLICATION & DNS TROUBLESHOOTING
Trên máy trạm Windows Client:
```cmd
ping 127.0.0.1                     :: Kiểm tra TCP/IP stack của OS
ping 192.168.20.1                  :: Kiểm tra Default Gateway
ping 192.168.1.10                  :: Kiểm tra Core Server / DNS Server
nslookup dc01.enterprise.local     :: Kiểm tra phân giải DNS
```

---

## Solution (Các giải pháp khắc phục chuẩn hóa)

### Trường hợp 1: Cổng bị rơi vào trạng thái `err-disabled` (Do BPDU Guard hoặc Loop)
> [!WARNING]
> **PRODUCTION IMPACT**: Trước khi mở lại cổng, phải xác minh nguyên nhân cắm nhầm switch phụ / hub của nhân viên, nếu không vòng lặp mạng sẽ làm sập toàn bộ hệ thống!

1. Rút thiết bị lạ / dây cắm lặp ra khỏi cổng.
2. Khôi phục cổng trên Cisco Switch:
   ```cisco
   configure terminal
   interface GigabitEthernet0/2
    shutdown
    no shutdown
   exit
   ```
3. Thiết lập tính năng tự động phục hồi an toàn sau 300 giây:
   ```cisco
   errdisable recovery cause bpduguard
   errdisable recovery interval 300
   ```

### Trường hợp 2: Lỗi Native VLAN Mismatch trên đường Trunk
Nếu console báo `%SPANTREE-2-BLOCK_PVID_LOCAL`:
1. Đồng bộ lại Native VLAN trên cả 2 đầu Switch:
   ```cisco
   ! Tại Switch A:
   interface TenGigabitEthernet1/1/1
    switchport trunk native vlan 99
   
   ! Tại Switch B:
   interface TenGigabitEthernet1/1/1
    switchport trunk native vlan 99
   ```

### Trường hợp 3: Client không nhận được IP DHCP (Lỗi DHCP Relay)
Cấu hình bổ sung `ip helper-address` trên Core Switch Layer 3:
```cisco
configure terminal
interface Vlan20
 description KETOAN_NETWORK
 ip address 192.168.20.1 255.255.255.0
 ip helper-address 192.168.1.10
 no shutdown
exit
write memory
```

### Trường hợp 4: OSPF Neighbor bị kẹt ở EXSTART do MTU Mismatch
Nếu một bên MTU là 1500 và một bên là 9000 (Jumbo frame) hoặc do chạy qua đường hầm VPN:
```cisco
interface GigabitEthernet0/0
 ! Cách 1: Đưa MTU 2 đầu về cùng chuẩn 1500
 ip mtu 1500
 
 ! Hoặc Cách 2 (Khẩn cấp): Bỏ qua kiểm tra MTU trong bắt tay OSPF
 ip ospf mtu-ignore
exit
```

---

## Verification (Quy trình xác nhận)
1. **Kiểm tra trạng thái cổng**: `show interfaces status` ➔ Cổng hiển thị `connected`, màu xanh lá cây.
2. **Kiểm tra bảng MAC**: `show mac address-table interface Gi0/1` ➔ Nhìn thấy MAC của card mạng máy trạm.
3. **Kiểm tra nhận IP từ Client**: `ipconfig /all` ➔ Nhận đúng dải IP của phòng ban, gateway chuẩn, DNS trỏ đúng về Domain Controller.
4. **Kiểm tra lưu lượng**: Ping 100 gói tin liên tục với kích thước chuẩn:
   ```cmd
   ping 192.168.1.10 -n 100 -l 1000
   ```
   ➔ Tỷ lệ mất gói (Packet Loss) phải bằng **0%**, độ trễ trung bình < 1ms trong mạng LAN.

## Prevention (Biện pháp phòng ngừa)
1. Bật **PortFast** và **BPDU Guard** trên tất cả các cổng Access cắm máy người dùng (`spanning-tree portfast edge`, `spanning-tree bpduguard enable`).
2. Bật **DHCP Snooping** để ngăn chặn nhân viên tự ý cắm router Wi-Fi cá nhân phát IP giả mạo làm sập mạng LAN (`ip dhcp snooping`, `ip dhcp snooping vlan 10,20,30,40`).
3. Khóa tốc độ và song công cố định ở các cổng uplink quan trọng: `speed auto`, `duplex auto` hoặc cố định `speed 1000`, `duplex full`.

## Escalation
* Chuyển cấp **Level 3 (Senior Network Engineer / Infrastructure Lead)** nếu: Bảng định tuyến OSPF bị flapping liên tục, hiện tượng Broadcast Storm gây nghẽn toàn bộ switch Core hoặc module quang SFP Core bị suy hao nghiêm trọng không thể kết nối.

## Risk Level
`Critical` (Sự cố mạng LAN có thể ảnh hưởng đến toàn bộ hoạt động giao dịch của công ty)

## Required Permission
`Cisco Privilege EXEC Mode (Level 15 - enable)`

## Related Documents
* `KB-FIBER-2026-001`: Quy trình xử lý sự cố đứt gãy và đo kiểm suy hao tuyến cáp quang ODF/ODS.
* `KB-DNS-2026-001`: Khắc phục lỗi phân giải DNS trong Active Directory Domain.

## Tags
`Cisco`, `Network`, `OSI 5 Layers`, `VLAN`, `Trunking`, `Err-disabled`, `BPDU Guard`, `OSPF`, `DHCP Relay`, `Duplex Mismatch`
