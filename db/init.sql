-- Initial schema - kept it simple for now
-- TODO: might need to add user_id later if we add auth

-- Previous iteration had a description field but we removed it
-- CREATE TABLE IF NOT EXISTS tasks (
--     id SERIAL PRIMARY KEY,
--     title VARCHAR(255) NOT NULL,
--     description TEXT,
--     is_done BOOLEAN DEFAULT FALSE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    is_done BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: using VARCHAR(255) for title - should be enough for most cases
-- Could switch to TEXT if we need longer titles but this keeps it simple

-- Old test data - too generic
-- INSERT INTO tasks (title, is_done) VALUES ('Task 1', false), ('Task 2', true);

-- More realistic sample data based on actual dev workflow
INSERT INTO tasks (title, is_done)
VALUES
    ('Fix bug in user authentication flow', false),
    ('Update Docker compose config for prod', false),
    ('Write API documentation', false),
    ('Refactor database connection logic', true),
    ('Add error handling to task endpoints', true);

-- Keeping this around for quick testing
-- INSERT INTO tasks (title, is_done) VALUES ('Test task', false);
