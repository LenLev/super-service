CREATE TABLE IF NOT EXISTS moderation_results (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    is_violation BOOLEAN,
    probability DOUBLE PRECISION,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP
);


