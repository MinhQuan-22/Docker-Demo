# Docker Topic 5: Flask + PostgreSQL + UI

Dự án mini-app cho Đề bài 5: containerize ứng dụng web bằng Docker, chạy với `docker-compose` gồm 2 service `api` và `db`, có UI để thao tác trực quan với task.

## Cấu trúc thư mục

- `api/`: Flask app, Dockerfile, giao diện UI (`templates/`, `static/`), dependencies.
- `db/`: SQL script khởi tạo bảng và dữ liệu mẫu.
- `docker-compose.yml`: định nghĩa 2 service `api` và `db`.
- `.env.example`: mẫu biến môi trường cho kết nối database.

## Công nghệ

- Backend: Flask
- Database: PostgreSQL
- UI: HTML/CSS/JavaScript (render từ Flask templates)
- Containerization: Docker + Docker Compose

## Chạy nhanh

1. Tạo file môi trường:
   ```bash
   cp .env.example .env
   ```
2. Khởi động hệ thống:
   ```bash
   docker compose up -d --build
   ```
3. Truy cập:
   - UI chính: `http://localhost:8080/`
   - Trang API docs UI: `http://localhost:8080/api`
   - API JSON tổng quan: `http://localhost:8080/api/json`

## Endpoint hiện tại (khớp code)

- `GET /`: UI mini-app.
- `GET /api`: UI mô tả API.
- `GET /api/json`: thông tin tổng quan service và endpoints.
- `GET /health`: trạng thái API, trả về `{"status":"up","service":"api"}`.
- `GET /db-check`: kiểm tra kết nối DB.
- `GET /tasks`: lấy danh sách task (sắp xếp mới nhất trước).
- `POST /tasks`: tạo task mới, body JSON `{"title":"..."}`.
- `PATCH /tasks/<id>/toggle`: đổi trạng thái hoàn thành task.
- `DELETE /tasks/<id>`: xóa task theo id.

## Luồng kết nối service

- Trình duyệt gọi vào `api` qua cổng host `8080`.
- `api` đọc biến môi trường `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Trong mạng Docker Compose, `api` kết nối PostgreSQL bằng service name `db` (không dùng IP tĩnh).
- `db` mở cổng nội bộ `5432`, map ra host `5433` để kiểm tra khi cần.

## Đáp ứng 3 bài tập ứng dụng

### Bài 1

- Có `api/Dockerfile` cho web app Python Flask.
- App chạy cổng `8080` (`EXPOSE 8080`, Flask bind `0.0.0.0:8080`).

### Bài 2

- `docker-compose.yml` có đúng 2 service chính: `api` và `db`.
- `api` dùng biến môi trường `DB_HOST/DB_PORT` để kết nối DB.
- Kết nối DB bằng service name `db`.

### Bài 3

- Có tài liệu triển khai chi tiết tại `DEPLOYMENT.md`:
  - chuẩn bị môi trường,
  - cấu hình biến môi trường,
  - triển khai bằng Docker Compose,
  - kiểm tra sau deploy.

## Lệnh kiểm tra nhanh

```bash
curl http://localhost:8080/health
curl http://localhost:8080/db-check
curl http://localhost:8080/tasks
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"Demo task"}'
```

## Dừng hệ thống

```bash
docker compose down
```

Xóa luôn dữ liệu volume:

```bash
docker compose down -v
```
