-- 1. Criação e selecção da base de dados
CREATE DATABASE IF NOT EXISTS kanban_ia_db;
USE kanban_ia_db;

-- 2. Tabela de empresas / clientes (Modelo Multi-tenant)
CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(150) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insere a empresa padrão de testes se ela não existir
INSERT INTO empresas (id, nome_empresa) 
SELECT 1, 'Minha Empresa S/A' 
FROM DUAL 
WHERE NOT EXISTS (SELECT * FROM empresas WHERE id = 1);

-- 3. Tabela de tarefas estruturada para KPIs e gestão corporativa
CREATE TABLE IF NOT EXISTS tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT DEFAULT 1,
    titulo VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'A Fazer',
    responsavel VARCHAR(100) NOT NULL,
    prazo DATETIME NULL,
    prioridade VARCHAR(50) DEFAULT 'Média',
    categoria VARCHAR(100) DEFAULT 'Geral',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
);

-- 4. Garantia de compatibilidade: adiciona a coluna empresa_id caso a tabela antiga não a tenha


USE kanban_ia_db;
ALTER TABLE tarefas ADD COLUMN empresa_id INT DEFAULT 1;