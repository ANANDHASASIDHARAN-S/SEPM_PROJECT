-- SRM Cybersecurity Moonshot MVP schema

CREATE TYPE role_enum AS ENUM ('STUDENT', 'FACULTY', 'SOC_ANALYST', 'ADMIN');
CREATE TYPE asset_type_enum AS ENUM ('DEVICE', 'SERVER', 'IP_RANGE');
CREATE TYPE asset_status_enum AS ENUM ('ACTIVE', 'QUARANTINED', 'RETIRED');
CREATE TYPE alert_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE threat_status_enum AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE');

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role role_enum NOT NULL,
  mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR(128) UNIQUE NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  hostname VARCHAR(255),
  os VARCHAR(100),
  ip_address VARCHAR(64),
  is_trusted BOOLEAN NOT NULL DEFAULT FALSE,
  last_seen TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assets (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  asset_type asset_type_enum NOT NULL,
  ip_range VARCHAR(64),
  owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  status asset_status_enum NOT NULL DEFAULT 'ACTIVE',
  criticality INTEGER NOT NULL DEFAULT 3,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS threat_events (
  id SERIAL PRIMARY KEY,
  alert_level alert_level_enum NOT NULL,
  source VARCHAR(255) NOT NULL,
  event_type VARCHAR(255) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  status threat_status_enum NOT NULL DEFAULT 'OPEN',
  details TEXT,
  asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(255) NOT NULL,
  path VARCHAR(500) NOT NULL,
  method VARCHAR(10) NOT NULL,
  status_code INTEGER NOT NULL,
  ip_address VARCHAR(64),
  user_agent VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threat_events_timestamp ON threat_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_threat_events_status ON threat_events(status);
CREATE INDEX IF NOT EXISTS idx_threat_events_level ON threat_events(alert_level);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
