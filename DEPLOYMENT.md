# Hướng dẫn deployment (khớp code hiện tại)

Tài liệu này mô tả quy trình chạy và kiểm tra hệ thống hiện tại trong thư mục `DockerDemo` gồm:

- `api`: Flask app có UI + REST API
- `db`: PostgreSQL
- `docker-compose.yml`: orchestration 2 service

> **Tip**: Đọc hết tài liệu này trước khi bắt đầu. Mình đã gặp vài lỗi ngớ ngẩn vì skip qua một số bước.

## 1) Yêu cầu môi trường

- Docker Engine
- Docker Compose v2

Kiểm tra nhanh:

```bash
docker --version
docker compose version
```

## 2) Chuẩn bị cấu hình

Tạo file `.env` từ mẫu:

```bash
cp .env.example .env
```

Giá trị mặc định đang dùng:

```bash
DB_HOST=db
DB_PORT=5432
DB_NAME=fullstack_demo
DB_USER=fullstack_user
DB_PASSWORD=fullstack_pass
```

**Warning**: Đừng commit file `.env` lên git nhé! (Mặc dù đây là demo app nhưng vẫn nên giữ thói quen tốt)

## 3) Deploy local

Từ thư mục project:

```bash
docker compose up -d --build
docker compose ps
```

Kỳ vọng:

- `topic5_api` trạng thái `Up`
- `topic5_db` trạng thái `Up (healthy)`

**Troubleshooting**: Nếu container không start được, check logs bằng `docker compose logs api` hoặc `docker compose logs db`. Thường là do port bị conflict hoặc thiếu file `.env`.

## 4) Truy cập sau deploy

- UI chính: `http://localhost:8080/`
- API docs UI: `http://localhost:8080/api`
- API JSON overview: `http://localhost:8080/api/json`

Port mapping hiện tại:

- API: `8080:8080`
- DB: `5433:5432`

Note: Mình dùng port 5433 cho DB thay vì 5432 vì máy mình đã có PostgreSQL chạy sẵn ở 5432. Nếu bạn cũng vậy thì giữ nguyên, không thì có thể đổi lại 5432:5432 trong docker-compose.yml

## 5) Kiểm tra chức năng (đúng endpoint thật)

### 5.1 Health check API

```bash
curl http://localhost:8080/health
```

Response mẫu:

```json
{ "status": "up", "service": "api" }
```

### 5.2 Kiểm tra kết nối database

```bash
curl http://localhost:8080/db-check
```

Response mẫu thành công:

```json
{
  "connection": "successful",
  "info": {
    "database": "fullstack_demo",
    "user": "fullstack_user"
  }
}
```

Nếu thấy error ở đây thì 99% là do DB chưa ready. Đợi thêm vài giây rồi thử lại.

### 5.3 Test task API

Lấy danh sách:

```bash
curl http://localhost:8080/tasks
```

Tạo task:

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Demo task from deployment guide"}'
```

Toggle trạng thái task id=1:

```bash
curl -X PATCH http://localhost:8080/tasks/1/toggle
```

Xóa task id=1:

```bash
curl -X DELETE http://localhost:8080/tasks/1
```

## 6) Luồng service communication

- Trình duyệt/host gọi API qua `localhost:8080`.
- Flask API đọc biến môi trường DB (`DB_HOST`, `DB_PORT`, ...).
- API kết nối PostgreSQL qua service name `db` trong mạng Docker Compose.
- Dữ liệu DB được lưu qua volume `postgres_data`.

**Important**: Service name `db` chỉ work trong Docker network. Nếu bạn muốn connect từ host machine (ví dụ dùng pgAdmin), phải dùng `localhost:5433`.

## 7) Xem logs và xử lý sự cố

Xem logs:

```bash
docker compose logs -f api
docker compose logs -f db
```

Lỗi thường gặp:

- **Cổng `8080` bận**:
  ```bash
  lsof -i :8080
  ```
  Giải pháp: Kill process đang dùng port 8080 hoặc đổi port trong docker-compose.yml
- **Cổng `5433` bận**:
  ```bash
  lsof -i :5433
  ```
  Giải pháp: Tương tự như trên
- **Container restart liên tục**: Thường là do DB connection failed. Check xem DB container có healthy không bằng `docker compose ps`. Nếu không healthy thì xem logs của db container.

Reset toàn bộ dữ liệu DB (khi mọi thứ rối quá):

```bash
docker compose down -v
docker compose up -d --build
```

## 8) Dừng hệ thống

Dừng container:

```bash
docker compose down
```

Dừng và xóa volume dữ liệu:

```bash
docker compose down -v
```

## 9) Checklist nộp báo cáo

- [x] Có Dockerfile cho web app (`api/Dockerfile`)
- [x] Web app chạy cổng `8080`
- [x] Có `docker-compose.yml` gồm 2 service `api` + `db`
- [x] API đọc `DB_HOST/DB_PORT` và kết nối DB bằng service name `db`
- [x] Có mô tả deploy: chuẩn bị, cấu hình env, deploy, kiểm tra sau deploy
- [x] Có UI trực quan cho mini-app và endpoint API đầy đủ
