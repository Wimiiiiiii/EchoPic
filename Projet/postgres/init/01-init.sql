-- Création de la table rp_curves avec les types PostgreSQL
CREATE TABLE IF NOT EXISTS rp_curves (
    id SERIAL PRIMARY KEY,
    query_image VARCHAR(255) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    rp_file_path VARCHAR(255) NOT NULL,
    rp_image_path VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    top_k INTEGER NOT NULL,
    models_used JSONB NOT NULL,
    search_params JSONB NOT NULL
);

-- Création des index
CREATE INDEX IF NOT EXISTS idx_rp_curves_query_image ON rp_curves(query_image);
CREATE INDEX IF NOT EXISTS idx_rp_curves_model_name ON rp_curves(model_name);
CREATE INDEX IF NOT EXISTS idx_rp_curves_created_at ON rp_curves(created_at); 