BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE topics (
    id VARCHAR(40) NOT NULL, 
    title VARCHAR(100) NOT NULL, 
    description VARCHAR(500) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id VARCHAR(36) NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE learning_recommendations (
    user_id VARCHAR(36) NOT NULL, 
    reason VARCHAR(500) NOT NULL, 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE lessons (
    id VARCHAR(40) NOT NULL, 
    topic_id VARCHAR(40) NOT NULL, 
    title VARCHAR(100) NOT NULL, 
    equation VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id)
);

CREATE TABLE quiz_questions (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    topic_id VARCHAR(40) NOT NULL, 
    equation VARCHAR(200) NOT NULL, 
    difficulty INTEGER NOT NULL, 
    hinted BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_quiz_questions_user_id ON quiz_questions (user_id);

CREATE TABLE refresh_tokens (
    digest VARCHAR(64) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    family VARCHAR(36) NOT NULL, 
    expires INTEGER NOT NULL, 
    revoked BOOLEAN NOT NULL, 
    PRIMARY KEY (digest), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_refresh_tokens_family ON refresh_tokens (family);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);

CREATE TABLE topic_mastery (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    topic_id VARCHAR(40) NOT NULL, 
    difficulty INTEGER NOT NULL, 
    accuracy DOUBLE PRECISION NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(topic_id) REFERENCES topics (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id, topic_id)
);

CREATE INDEX ix_topic_mastery_user_id ON topic_mastery (user_id);

CREATE TABLE tutor_messages (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    question VARCHAR(2000) NOT NULL, 
    answer VARCHAR(4000) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_tutor_messages_user_id ON tutor_messages (user_id);

CREATE TABLE uploaded_solutions (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    filename VARCHAR(255) NOT NULL, 
    width INTEGER NOT NULL, 
    height INTEGER NOT NULL, 
    confirmed BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_uploaded_solutions_user_id ON uploaded_solutions (user_id);

CREATE TABLE user_settings (
    user_id VARCHAR(36) NOT NULL, 
    muted BOOLEAN NOT NULL, 
    voice VARCHAR(200) NOT NULL, 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE extracted_solution_steps (
    id VARCHAR(36) NOT NULL, 
    upload_id VARCHAR(36) NOT NULL, 
    position INTEGER NOT NULL, 
    equation VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(upload_id) REFERENCES uploaded_solutions (id)
);

CREATE INDEX ix_extracted_solution_steps_upload_id ON extracted_solution_steps (upload_id);

CREATE TABLE learning_sessions (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    lesson_id VARCHAR(40) NOT NULL, 
    completed BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(lesson_id) REFERENCES lessons (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id, lesson_id)
);

CREATE INDEX ix_learning_sessions_user_id ON learning_sessions (user_id);

CREATE TABLE lesson_steps (
    id VARCHAR(36) NOT NULL, 
    lesson_id VARCHAR(40) NOT NULL, 
    position INTEGER NOT NULL, 
    content JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(lesson_id) REFERENCES lessons (id)
);

CREATE INDEX ix_lesson_steps_lesson_id ON lesson_steps (lesson_id);

CREATE TABLE quiz_attempts (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    question_id VARCHAR(36) NOT NULL, 
    correct BOOLEAN NOT NULL, 
    hinted BOOLEAN NOT NULL, 
    created INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(question_id) REFERENCES quiz_questions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (question_id)
);

CREATE INDEX ix_quiz_attempts_user_id ON quiz_attempts (user_id);

CREATE TABLE solution_feedback (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    upload_id VARCHAR(36), 
    result JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(upload_id) REFERENCES uploaded_solutions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_solution_feedback_user_id ON solution_feedback (user_id);

CREATE TABLE student_answers (
    id VARCHAR(36) NOT NULL, 
    attempt_id VARCHAR(36) NOT NULL, 
    answer VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(attempt_id) REFERENCES quiz_attempts (id), 
    UNIQUE (attempt_id)
);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

-- Running upgrade 0001 -> 0002

ALTER TABLE quiz_attempts ADD COLUMN submitted_at BIGINT DEFAULT '0' NOT NULL;

UPDATE quiz_attempts SET submitted_at = CAST(created AS BIGINT) * 1000000000 WHERE submitted_at = 0;

CREATE INDEX ix_quiz_attempts_submitted_at ON quiz_attempts (submitted_at);

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

COMMIT;

