-- Create users table for authentication

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for email lookups
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Create index for active users
CREATE INDEX idx_users_is_active ON users(is_active);

COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON COLUMN users.email IS 'User email address (unique)';
COMMENT ON COLUMN users.hashed_password IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active';
