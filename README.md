# Docker Topic 5: Flask API & PostgreSQL

Dự án này thực hiện containerize một ứng dụng Flask API kết nối cơ sở dữ liệu PostgreSQL theo yêu cầu của Đề bài 5.

## Cấu trúc thư mục
- `api/`: Backend Flask, Dockerfile và các dependencies.
- `db/`: SQL script khởi tạo database ban đầu.
- `docker-compose.yml`: Quản lý các service và biến môi trường.

## Hướng dẫn chạy nhanh
1. Sao chép cấu hình môi trường:
   ```bash
   cp .env.example .env
   ```
2. Khởi động hệ thống:
   ```bash
   docker compose up -d --build
   ```
3. Kiểm tra API tại: `http://localhost:8080/`

---

## Giải quyết các bài tập

### Bài 1: Dockerfile cho Web Application
Dockerfile được đặt tại `api/Dockerfile`. Các điểm lưu ý:
- Sử dụng base image `python:3.12-slim` để giảm dung lượng image.
- Lắng nghe tại cổng `8080` (đã `EXPOSE` và cấu hình trong code).
- Tận dụng cơ chế layer caching bằng cách copy `requirements.txt` và install trước khi copy source code.

**Lệnh build thủ công:**
```bash
docker build -t my-api ./api
```

### Bài 2: Docker Compose với 2 service (API + DB)
Hệ thống sử dụng Docker Compose để quản lý đồng thời Flask API và PostgreSQL.
- **Biến môi trường:** API nhận `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` từ file `.env` thông qua `docker-compose.yml`.
- **Kết nối:** Trong mạng nội bộ của Docker, API kết nối tới database bằng tên service là `db` thay vì dùng IP.
- **Thứ tự khởi động:** Sử dụng `depends_on` kèm `healthcheck` để đảm bảo PostgreSQL sẵn sàng trước khi API khởi chạy.

### Bài 3: Quy trình Deployment
Quy trình triển khai ứng dụng gồm các bước chính:
1. **Chuẩn bị:** Cài đặt Docker và Docker Compose trên server.
2. **Cấu hình:** Thiết lập file `.env` với các thông số bảo mật cho production (đổi password mặc định).
3. **Triển khai:** Chạy `docker compose up -d`. Hệ thống sẽ tự động pull image, tạo network, và thực thi script `init.sql` để tạo bảng.
4. **Kiểm tra:** 
   - Kiểm tra log: `docker compose logs -f`.
   - Kiểm tra kết nối: Truy cập endpoint `/db-check` để xác nhận API đã thông tới database.

---

## Kiểm tra các Endpoint
- `GET /health`: Kiểm tra trạng thái API.
- `GET /db-check`: Kiểm tra kết nối tới PostgreSQL.
- `GET /tasks`: Lấy danh sách task mẫu từ database (đã seed qua `init.sql`).

## Xử lý sự cố (Troubleshooting)
- Nếu bị lỗi cổng 8080: Kiểm tra xem có app nào đang chiếm dụng cổng không bằng lệnh `lsof -i:8080`.
- Reset lại dữ liệu: Chạy `docker compose down -v` để xóa toàn bộ volume và khởi động lại.
