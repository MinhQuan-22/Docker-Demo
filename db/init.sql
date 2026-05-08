CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    is_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tasks (title, is_done)
VALUES
    ('Learn Docker image and container', false),
    ('Write Dockerfile for API service', false),
    ('Run api and db with Docker Compose', true);
