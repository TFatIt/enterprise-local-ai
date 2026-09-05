# TIÊU CHUẨN THIẾT KẾ VÀ CẤU HÌNH VLAN & 802.1Q TRUNKING TRÊN CISCO CATALYST
**Mã tài liệu:** DOC-NET-001  
**Phòng ban:** IT Network  
**Thẩm quyền:** Cisco IOS Software Configuration Guide  
**Phiên bản:** 15.2 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Nguyên lý Hoạt động của Mạng Cục bộ Ảo (VLAN)
VLAN (Virtual Local Area Network) cho phép phân tách một switch vật lý thành nhiều miền quảng bá (Broadcast Domains) logic độc lập.
Lợi ích cốt lõi:
- Nâng cao an ninh: Ngăn cách luồng dữ liệu giữa các phòng ban (Kế toán, Nhân sự, Khách, Máy chủ nội bộ).
- Giảm thiểu bão quảng bá (Broadcast Storms).
- Tối ưu hóa hiệu năng chuyển mạch gói tin Lớp 2 (Data Link Layer).

---

## 2. Tiêu Chuẩn Phân Bổ Dải VLAN Doanh nghiệp

| VLAN ID | Tên VLAN | Mục đích sử dụng | Dải mạng IP (Subnet) |
| :---: | :--- | :--- | :--- |
| **10** | `MGMT_VLAN` | Quản trị thiết bị mạng (Switch, Router, AP) | `10.10.10.0/24` |
| **20** | `CORP_DATA` | Máy tính người dùng nội bộ doanh nghiệp | `10.10.20.0/23` |
| **30** | `VOIP_PHONE`| Hệ thống điện thoại thoại IP | `10.10.30.0/24` |
| **40** | `SERVERS`   | Cụm máy chủ ứng dụng và cơ sở dữ liệu | `10.10.40.0/24` |
| **50** | `GUEST_WIFI`| Mạng khách ngoài doanh nghiệp (Cách ly) | `172.16.50.0/24` |

---

## 3. Cấu hình Cổng Access và Cổng 802.1Q Trunk trên Switch Cisco

### Cấu hình Cổng Access cho Máy tính Người dùng:
```cisco
Switch# configure terminal
Switch(config)# vlan 20
Switch(config-vlan)# name CORP_DATA
Switch(config-vlan)# exit
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# description PC-User-Accountant
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 20
Switch(config-if)# spanning-tree portfast
Switch(config-if)# spanning-tree bpduguard enable
Switch(config-if)# no shutdown
```

### Cấu hình Cổng 802.1Q Trunk Kết nối giữa các Switch:
```cisco
Switch(config)# interface GigabitEthernet0/24
Switch(config-if)# description UPLINK-TO-CORE-SWITCH
Switch(config-if)# switchport trunk encapsulation dot1q
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk native vlan 999
Switch(config-if)# switchport trunk allowed vlan 10,20,30,40
Switch(config-if)# no shutdown
```
