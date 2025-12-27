-- HyperGPU Database Initialization Script

-- Training Sessions Table
CREATE TABLE IF NOT EXISTS training_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    dataset VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    epochs INTEGER DEFAULT 10,
    batch_size INTEGER DEFAULT 64,
    learning_rate DECIMAL(10, 8) DEFAULT 0.001,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    final_accuracy DECIMAL(5, 4),
    final_loss DECIMAL(10, 6)
);

-- Nodes Table
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(255) UNIQUE NOT NULL,
    address VARCHAR(255),
    status VARCHAR(50) DEFAULT 'offline',
    gpu_model VARCHAR(100),
    gpu_memory_gb INTEGER,
    compute_capability DECIMAL(5, 2),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP
);

-- Training Metrics Table
CREATE TABLE IF NOT EXISTS training_metrics (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES training_sessions(session_id),
    epoch INTEGER NOT NULL,
    step INTEGER NOT NULL,
    loss DECIMAL(10, 6),
    accuracy DECIMAL(5, 4),
    learning_rate DECIMAL(10, 8),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Node Contributions Table
CREATE TABLE IF NOT EXISTS node_contributions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES training_sessions(session_id),
    node_id VARCHAR(255) REFERENCES nodes(node_id),
    compute_time_seconds DECIMAL(10, 2),
    gradients_accepted INTEGER DEFAULT 0,
    gradients_rejected INTEGER DEFAULT 0,
    quality_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_metrics_session ON training_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON training_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_contributions_session ON node_contributions(session_id);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
