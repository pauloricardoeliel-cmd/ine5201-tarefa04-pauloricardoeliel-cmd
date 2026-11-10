-- Script de criação do banco do Cadastro de Alunos (INE5201 - Tarefa 04)
-- Executado automaticamente por cadastro_alunos.py na primeira vez que o programa abre.
-- Para criar o banco manualmente: sqlite3 alunos.db < banco.sql

CREATE TABLE IF NOT EXISTS alunos (
    matricula     TEXT PRIMARY KEY,                     -- única: impede alunos repetidos
    nome          TEXT NOT NULL,
    curso         TEXT NOT NULL,
    email         TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- preenchida pelo próprio banco
);
