-- Script de création de la base de données EmpManager
-- Exécutez ce script dans pgAdmin ou psql

-- Créer la base de données
CREATE DATABASE empmanager_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'French_France.1252'
    LC_CTYPE = 'French_France.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Se connecter à la base de données
\c empmanager_db

-- Message de confirmation
SELECT 'Base de données empmanager_db créée avec succès!' as message;
