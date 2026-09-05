# TIÊU CHUẨN VẬN HÀNH HẠ TẦNG CỤM MÁY CHỦ VMWARE VSPHERE 8 VÀ DOCKER
**Mã tài liệu:** DOC-INFRA-001  
**Phòng ban:** Hạ tầng CNTT (IT Infrastructure)  
**Thẩm quyền:** VMware by Broadcom & Docker Inc.  
**Phiên bản:** 8.0 | **Cấp độ bảo mật:** INTERNAL

---

## 1. Tiêu Chuẩn Cụm Ảo Hóa VMware vSphere HA / DRS
- Cụm máy chủ (Cluster) tối thiểu gồm 03 máy chủ vật lý (ESXi Hosts) để đảm bảo tính sẵn sàng cao $N+1$.
- Bật tính năng **vSphere High Availability (HA):** Khi một host vật lý bị mất nguồn hoặc treo cứng, toàn bộ máy ảo (VM) trên host đó tự động khởi động lại trên các host còn lại trong vòng dưới 3 phút.
- Bật tính năng **Distributed Resource Scheduler (DRS)** ở chế độ Fully Automated để tự động cân bằng tải CPU và RAM giữa các máy chủ.

---

## 2. Tiêu Chuẩn Vận Hành Docker Container Doanh Nghiệp
- Toàn bộ container chạy dịch vụ nghiệp vụ phải có giới hạn tài nguyên rõ ràng trong file `docker-compose.yml`:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4096M
  ```
- Định cấu hình `restart: always` và thiết lập kịch bản kiểm tra sức khỏe `healthcheck` trên cổng nội bộ.
- Dữ liệu cơ sở dữ liệu và tệp người dùng tải lên bắt buộc phải ánh xạ ra khối lưu trữ ngoài (Named Volumes hoặc Host Mounts).
