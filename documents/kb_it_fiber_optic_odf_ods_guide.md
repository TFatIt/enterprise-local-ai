# HỆ THỐNG CƠ SỞ TRI THỨC CNTT DOANH NGHIỆP (ENTERPRISE IT KNOWLEDGE BASE)
# CHUYÊN ĐỀ: HẠ TẦNG TRUYỀN DẪN CÁP QUANG DOANH NGHIỆP (ODS - ODF - BACKBONE - OTDR)

---

## Document ID
`KB-FIBER-2026-001`

## Category
`Fiber Optic / Telecommunications / Physical Infrastructure`

## Department
`IT`

## Title
Quy trình Đo kiểm, Dò tìm Điểm đứt và Xử lý Suy hao Tuyến Cáp Quang Doanh nghiệp (ODS → ODF → Backbone → Tủ con → Thiết bị)

## Problem
Tuyến kết nối quang đường trục (Backbone) giữa Trung tâm Dữ liệu (Server Room / Data Center) với các Tủ mạng tầng (IDF / Tủ con) hoặc giữa các tòa nhà bị mất tín hiệu hoàn toàn (`Link Down`) hoặc công suất quang suy hao vượt ngưỡng kỹ thuật khiến cổng SFP/SFP+ bị nghẽn và rớt gói (packet drop).

## Symptoms
1. Đèn báo cổng quang trên Switch quang (SFP LED) tắt hẳn (`Status: notconnect` hoặc `down`).
2. Tốc độ truyền tải dữ liệu giữa các tầng hoặc chi nhánh giảm đột ngột từ 10Gbps xuống dưới 100Mbps hoặc chập chờn ngắt quãng.
3. Lệnh kiểm tra DDM (Digital Diagnostic Monitoring) trên Switch báo công suất thu (Rx Power) dưới **-22 dBm** (ngưỡng nhạy tối thiểu) hoặc báo `Low Alarm`.
4. Không có ánh sáng đỏ phát ra khi kiểm tra bằng bút soi quang (VFL) tại đầu Adapter ODF tương ứng.

## Error Message
* Cisco / Aruba CLI Syslog:
  - `%SFP-4-RX_LOW_WARN: Gi1/1/1: Rx power low warning; -24.8 dBm (threshold -20.0 dBm)`
  - `%LINK-3-UPDOWN: Interface TenGigabitEthernet1/1/2, changed state to down`
  - `%OPTICAL-3-RX_LOS: Optical receiver signal lost on port Te1/1/2`
* OTDR (Optical Time Domain Reflectometer) Screen:
  - *"Non-reflective event detected at 145.2m with attenuation > 4.5 dB"* (Điểm suy hao uốn cong hoặc mối hàn hỏng).
  - *"Reflective break at 320.8m with 0 dB transmission"* (Điểm đứt gãy sợi quang hoàn toàn).

## Environment
* **Chuẩn cáp quang**:
  - Single Mode (SMF - 9/125 µm, màu vàng, bước sóng 1310nm / 1550nm) dùng cho tuyến trục Backbone giữa các tòa nhà / khoảng cách > 500m.
  - Multi Mode (MMF - OM3 / OM4, 50/125 µm, màu xanh ngọc Aqua, bước sóng 850nm / 1300nm) dùng cho nội bộ Data Center.
* **Hộp phối quang (ODF)**: ODF 24-core / 48-core chuẩn Rack 19 inch, Adapter LC Duplex / SC Duplex.
* **Hộp phân phối quang ngoài trời (ODS - Optical Distribution Server / Splice Enclosure)**: Măng-xông quang ngoài trời chuẩn IP68 chống nước, đặt tại hố ga hoặc cột viễn thông.
* **Đầu nối (Connectors)**: LC-UPC (màu xanh dương), LC-APC (vát góc 8 độ màu xanh lá cây cho hệ thống yêu cầu độ phản xạ cực thấp).

## Kiến trúc Phân bổ Tuyến Cáp Quang Doanh nghiệp
```text
[Phòng Máy chủ Trung tâm]
         │
         ▼
[ODS / Tủ Phối Cáp Tổng] (Optical Distribution System)
         │
         ▼
[ODF Tổng (MDF)] (Hộp phối quang 48-core tại Data Center)
         │  (Cáp quang luồn cống ngầm / thang máng cáp Backbone)
         ▼
[ODF Tầng / Tủ con (IDF)] (Hộp phối quang 12/24-core tại từng Tầng 1, 2, 3...)
         │  (Dây nhảy quang - Fiber Patch Cord LC-LC)
         ▼
[Switch Quang / Module SFP+ 10G] (Thiết bị mạng cuối)
```

---

## Possible Causes
1. **Bụi bẩn bám trên bề mặt tiếp xúc (Ferrule Contamination)**: Nguyên nhân chiếm tới 80% trường hợp suy hao quang. Hạt bụi mịn trên đầu sứ LC làm lệch khúc xạ ánh sáng.
2. **Uốn cong sợi quang quá bán kính cho phép (Macro-bending)**: Bán kính uốn cong sợi quang nhỏ hơn 30mm (chuẩn G.652D) khiến ánh sáng rò rỉ ra ngoài lớp vỏ bọc (Cladding).
3. **Mối hàn cáp quang (Fusion Splice) bị thoái hóa hoặc bọt khí**: Mối hàn lâu năm bị ẩm xâm nhập hoặc tác động ngoại lực làm độ suy hao tăng vọt (> 0.3 dB/mối).
4. **Cáp quang bị đứt ngầm (Cable Breakage)**: Chuột cắn, công trình xây dựng khoan cắt hố ga làm đứt gãy sợi thủy tinh bên trong cáp Backbone.
5. **Cắm nhầm chuẩn tiếp xúc (UPC vs APC)**: Cắm đầu phẳng UPC (xanh dương) vào đầu vát APC (xanh lá cây) làm hỏng mặt sứ và gây ra khe hở không khí phản xạ cực lớn.
6. **Lệch cặp sợi thu phát (Tx/Rx Roll-over)**: Sợi truyền (Tx) của Switch A cắm nhầm vào sợi Tx của Switch B thay vì cắm vào cổng Rx.

---

## Diagnosis (Quy trình đo kiểm và dò tìm điểm lỗi)

### Bước 1: Kiểm tra chẩn đoán kỹ thuật số DDM trên Switch
Truy cập console Switch:
```cisco
show interfaces TenGigabitEthernet1/1/1 transceiver detail
```
*Đọc các giá trị:*
* **Optical Transmit Power (Tx)**: Tiêu chuẩn từ **-1.0 dBm đến -6.0 dBm**.
* **Optical Receive Power (Rx)**:
  - Mức lý tưởng: **-8.0 dBm đến -15.0 dBm**.
  - Mức cảnh báo suy hao: **-18.0 dBm đến -21.0 dBm**.
  - Mất tín hiệu hoàn toàn (LOS): **< -24.0 dBm** hoặc **-40 dBm**.

### Bước 2: Kiểm tra đảo cực sợi quang (Tx/Rx Polarity Test)
1. Rút cặp dây nhảy quang (Patch Cord) cắm vào cổng SFP.
2. Nhìn nghiêng (hoặc dùng camera điện thoại): Xác định sợi có ánh sáng đỏ phát ra (Tx của switch).
3. Thử đảo ngược 2 đầu dây nối LC (đổi sợi 1 sang 2) để đảm bảo Tx cắm vào Rx.

### Bước 3: Dò tìm sợi quang và điểm gãy bằng Bút soi quang VFL (Visual Fault Locator - 650nm)
1. Tắt laser trên cổng switch hoặc rút patch cord ra khỏi thiết bị.
2. Cắm đầu phát laser đỏ của bút soi quang VFL vào Adapter ODF tại Phòng Server.
3. Bật chế độ nhấp nháy (CW/Flash 2Hz, công suất 10mW - 30mW).
4. Quan sát:
   * **Tại tủ con (IDF)**: Nếu nhìn thấy ánh sáng đỏ rực rỡ phát ra ở đầu cáp tương ứng ➔ Sợi quang thông suốt, không bị đứt gãy hoàn toàn.
   * **Dọc theo máng cáp / hố cáp**: Nếu có điểm uốn cong hoặc đứt gãy sợi bên trong ống đệm lỏng, ánh sáng đỏ sẽ **phát sáng rực rỡ xuyên qua lớp vỏ cáp (Light Bleeding)** tại đúng vị trí lỗi!

### Bước 4: Đo kiểm suy hao tuyệt đối bằng Máy đo công suất quang (Optical Power Meter - OPM)
1. Sử dụng Nguồn phát quang chuẩn (Optical Light Source - OLS) phát bước sóng 1310nm tại ODF Tổng.
2. Tại ODF Tầng, cắm máy đo OPM:
   ```text
   Độ suy hao toàn tuyến (Total Loss) = Công suất phát (Tx OLS) - Công suất thu (Rx OPM)
   ```
3. Công thức tiêu chuẩn:
   - Suy hao sợi SMF: **0.35 dB/km** ở bước sóng 1310nm.
   - Suy hao mỗi mối hàn quang (Splice): tối đa **0.1 dB/mối**.
   - Suy hao mỗi cặp Adapter/Connector: tối đa **0.5 dB/cặp**.
   *Nếu tuyến cáp dài 200m có 2 mối hàn và 2 cặp ODF, suy hao tiêu chuẩn phải < 1.3 dB. Nếu đo thực tế > 3.5 dB ➔ Có điểm suy hao bất thường!*

### Bước 5: Định vị chính xác tọa độ điểm đứt bằng Máy đo OTDR
1. Kết nối máy OTDR vào sợi quang thông qua **Cuộn cáp bù (Launch Cable / Dummy Fiber)** tối thiểu 150m để loại trừ Vùng mù sự kiện (Event Dead Zone).
2. Thiết lập thông số OTDR: Bước sóng 1310nm, độ rộng xung (Pulse Width) 10ns - 30ns (cho khoảng cách ngắn nội bộ), chỉ số khúc xạ $IOR = 1.467$.
3. Bấm quét (Real-time hoặc Average scan 30s):
4. Phân tích đồ thị suy hao (OTDR Trace Analysis):
   * **Đỉnh nhọn hướng lên kèm dốc đứng xuống (Reflective Event)**: Đầu nối Connector bị bẩn, hở hoặc điểm đứt gãy cơ học sợi thủy tinh.
   * **Bậc thang tụt dốc không có đỉnh nhọn (Non-reflective Event)**: Mối hàn quang suy hao nặng hoặc điểm cáp quang bị kẹp, uốn cong quá mức (Macro-bending).
   * **Độ cao của bậc thang**: Thể hiện chính xác số dB suy hao tại vị trí đó (ví dụ: tụt 3.2 dB tại mét thứ 145.2).

---

## Solution (Quy trình khắc phục chuyên nghiệp)

### Quy trình 1: Vệ sinh bề mặt đầu sứ quang (Dry & Wet Cleaning)
> [!IMPORTANT]
> **90% sự cố suy hao cao được giải quyết bằng việc vệ sinh đúng kỹ thuật!**

1. Sử dụng bút vệ sinh đầu quang tự động chuyên dụng (One-Click Fiber Cleaner 1.25mm cho LC, 2.5mm cho SC):
   - Đút đầu bút vào bên trong Adapter của ODF, bấm dứt khoát 2 lần (nghe tiếng "tách").
2. Vệ sinh đầu dây nhảy Patch Cord:
   - Dùng giấy lau quang chuyên dụng không xơ (Lint-free Kimwipes) thấm dung dịch cồn Isopropyl Alcohol (IPA) độ tinh khiết > 99%.
   - Kéo đầu sứ theo một đường thẳng duy nhất trên bề mặt giấy lau (tuyệt đối không lau xoay tròn làm xước mặt sứ).
3. Cắm lại vào SFP và kiểm tra lại Rx Power trên switch.

### Quy trình 2: Xử lý điểm uốn cong sợi quang (Macro-bending Repair)
1. Dựa trên vị trí ánh sáng đỏ của bút VFL hoặc mét đo của OTDR, mở máng cáp hoặc máng ODF.
2. Kiểm tra các vị trí bị thắt dây thít (Cable Tie) quá chặt hoặc sợi quang bị kẹt dưới góc tủ rack.
3. Nới lỏng dây thít, thay thế bằng dây dán xé (Velcro).
4. Uốn lượn sợi quang trong khay hàn (Splice Tray) với bán kính vòng cua tối thiểu **> 30mm**.

### Quy trình 3: Hàn nối xử lý điểm đứt cáp quang (Fusion Splicing)
Nếu OTDR xác định đứt hoàn toàn bên trong cáp:
1. Xác định vị trí đứt (tính từ khoảng cách mét đo OTDR nhân với hệ số co cáp thực tế ~ 1.02).
2. Mở măng-xông hoặc kéo đoạn cáp chùng dự phòng (Slack loop) đến vị trí bàn máy hàn.
3. Dùng kìm tuốt cáp quang chuyên dụng (Miller stripper) tuốt lớp vỏ bảo vệ 250µm.
4. Vệ sinh sợi thủy tinh trần bằng cồn IPA.
5. Dắt ống co nhiệt (Protection Sleeve) vào một đầu sợi cáp.
6. Cắt sợi quang bằng dao cắt chính xác (Precision Cleaver) đảm bảo góc cắt < 0.5 độ.
7. Đặt 2 đầu sợi vào máy hàn quang tự động (Fujikura / Sumitomo):
   - Kiểm tra căn chỉnh lõi (Core alignment).
   - Tiến hành hàn hồ quang (Arc fusion).
   - Kiểm tra suy hao mối hàn trên máy: Phải đạt tiêu chuẩn **$\le 0.02 \text{ dB}$**.
8. Lồng ống co nhiệt vào vị trí mối hàn và gia nhiệt trong lò sấy 30 giây.
9. Xếp sợi vào khay ODF cẩn thận.

---

## Verification (Tiêu chuẩn nghiệm thu sau xử lý)
1. Đo kiểm lại bằng OPM: Tổng suy hao toàn tuyến từ ODF Server đến ODF Tủ con phải **$\le 1.5 \text{ dB}$**.
2. Kiểm tra DDM trên Switch:
   - Công suất thu $Rx \ge -14 \text{ dBm}$ (trên module 10G LR).
   - Lệnh `show interfaces status` hiển thị: `connected`, tốc độ `10G-full`.
3. Kiểm tra thông lưu lượng dữ liệu: Chạy công cụ `iperf3 -c <server_ip> -P 10 -t 60` ➔ Đạt băng thông đường truyền tối đa, 0% packet loss.

## Prevention (Quy tắc phòng ngừa hỏng hóc hạ tầng quang)
1. **Luôn luôn đậy nắp chống bụi (Dust Cap)**: Bất kỳ cổng quang ODF hoặc module SFP nào chưa cắm dây đều phải đậy nắp bảo vệ ngay lập tức. Không bao giờ để hở ferrule ra không khí.
2. **Tuân thủ mã màu sợi quang (Tia-598C)**: 1-Dương, 2-Cam, 3-Lục, 4-Nâu, 5-Xám, 6-Trắng, 7-Đỏ, 8-Đen, 9-Vàng, 10-Tím, 11-Hồng, 12-Aqua. Lập sơ đồ đấu nối (Patching Matrix) và dán nhãn ODF rõ ràng.
3. Dự phòng tối thiểu 10 mét cáp cuộn tròn (Fiber Slack) tại mỗi đầu ODS / ODF phục vụ công tác hàn nối lại khi xảy ra sự cố.

## Escalation
* Chuyển cấp **Level 3 (Viễn thông / Nhà thầu Hạ tầng Cáp)** nếu: Cáp quang chôn ngầm bị đứt gãy hàng loạt không thể tiếp cận điểm đứt hoặc suy hao sợi vượt ngưỡng cho phép do cáp bị ngâm nước ngầm ăn mòn sợi thủy tinh.

## Risk Level
`High` (Đứt cáp quang đường trục làm cô lập mạng của toàn bộ chi nhánh hoặc tầng văn phòng)

## Required Permission
`IT Infrastructure Specialist / Certified Optical Technician`

## Related Documents
* `KB-NET-2026-001`: Quy trình Chẩn đoán Mạng Doanh nghiệp theo Mô hình 5 Tầng OSI.

## Tags
`Fiber Optic`, `ODF`, `ODS`, `OTDR`, `VFL`, `Single Mode`, `Multi Mode`, `Fusion Splice`, `Attenuation`, `SFP+`, `DDM`
