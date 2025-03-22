-- Initialisation de la base de données pour Polyad en production

-- Création des extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Configuration des paramètres de sécurité
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Création des schémas
CREATE SCHEMA IF NOT EXISTS polyad;
CREATE SCHEMA IF NOT EXISTS cache;
CREATE SCHEMA IF NOT EXISTS metrics;
CREATE SCHEMA IF NOT EXISTS audit;

-- Configuration des permissions
GRANT USAGE ON SCHEMA polyad TO polyad;
GRANT USAGE ON SCHEMA cache TO polyad;
GRANT USAGE ON SCHEMA metrics TO polyad;
GRANT USAGE ON SCHEMA audit TO polyad;

-- Création des tables principales
CREATE TABLE IF NOT EXISTS polyad.settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS polyad.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS polyad.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES polyad.users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS polyad.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES polyad.users(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS cache.items (
    key VARCHAR(512) PRIMARY KEY,
    value BYTEA NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics.system_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    gpu_usage FLOAT,
    network_rx BIGINT,
    network_tx BIGINT,
    disk_usage FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS audit.events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES polyad.users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    details JSONB
);

-- Création des index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON polyad.tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON polyad.tasks(type);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON polyad.tasks(status);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache.items(expires_at);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics.system_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit.events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit.events(action);

-- Création des triggers pour la mise à jour automatique des timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_polyad_settings_updated_at
BEFORE UPDATE ON polyad.settings
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_polyad_users_updated_at
BEFORE UPDATE ON polyad.users
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_polyad_tasks_updated_at
BEFORE UPDATE ON polyad.tasks
FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Insertion des paramètres par défaut
INSERT INTO polyad.settings (key, value, description)
VALUES 
('app_name', 'Polyad', 'Nom de l''application'),
('version', '1.0.0', 'Version de l''application'),
('environment', 'production', 'Environnement d''exécution'),
('cache_ttl', '3600', 'Durée de vie du cache en secondes'),
('max_parallel_tasks', '4', 'Nombre maximum de tâches parallèles'),
('default_model', 'gemma3:12b-it-q4_K_M', 'Modèle par défaut')
ON CONFLICT (key) DO NOTHING;
