from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "google_tokens" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "token" TEXT NOT NULL,
    "refresh_token" TEXT,
    "token_uri" TEXT NOT NULL,
    "client_id" TEXT NOT NULL,
    "client_secret" TEXT NOT NULL,
    "scopes" JSONB NOT NULL,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "google_tokens" IS 'Stores Google API authorization tokens for a user.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "google_tokens";"""
