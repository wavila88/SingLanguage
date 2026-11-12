CREATE TABLE IF NOT EXISTS epression (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label TEXT NOT NULL UNIQUE
);

INSERT INTO epression (label) VALUES ('a'), ('e'), ('i'), ('o'), ('u') ON CONFLICT (label) DO NOTHING;

CREATE TABLE IF NOT EXISTS samples (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    epression_id BIGINT NOT NULL REFERENCES epression (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Every sample is a recording of frames now (sample_frames). The static `points` and `kind` columns were removed
-- (spec 007): to migrate an older database run `DELETE FROM samples` for its static rows, then
-- `ALTER TABLE samples DROP COLUMN IF EXISTS points, DROP COLUMN IF EXISTS kind`.

CREATE TABLE IF NOT EXISTS sample_frames (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sample_id BIGINT NOT NULL REFERENCES samples (id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,
    ms INTEGER NOT NULL,
    hands JSONB NOT NULL
);
