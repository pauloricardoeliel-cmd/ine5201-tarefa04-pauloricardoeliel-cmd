"""
Cadastro de Alunos com SQLite e interface gráfica
INE5201 - Introdução à Ciência da Computação com Python - UFSC
Tarefa 04

Participantes:
    Paulo Ricardo Eliel Mendes Peres dos Santos (24100434)
    Matheus da Silva Farani (24202994)

Como usar:
    Preencha o formulário e clique em Cadastrar. Clique em um aluno da
    tabela para carregá-lo no formulário e então Editar ou Excluir.
    Os dados ficam salvos no arquivo alunos.db.
"""

import csv
import os
import re
import sqlite3

import FreeSimpleGUI as sg

# ============================== Constantes ==============================

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BANCO = os.path.join(PASTA, 'alunos.db')
ARQUIVO_SQL = os.path.join(PASTA, 'banco.sql')

CAMPOS = ['matricula', 'nome', 'curso', 'email']
TITULOS = ['Matrícula', 'Nome', 'Curso', 'E-mail', 'Cadastrado em']
LARGURAS = [10, 26, 20, 28, 15]

# Matrícula da UFSC: 8 dígitos (ex.: 24100434)
PADRAO_MATRICULA = re.compile(r'^\d{8}$')
# E-mail: algo@dominio.ext (aceita pontos, + e - antes do @)
PADRAO_EMAIL = re.compile(r'^[\w.+-]+@[\w-]+(\.[\w-]+)+$')

COR_SUCESSO = '#2ECC71'
COR_ERRO = '#FF6B6B'
COR_INFO = '#F5F5F5'


# ============================== Banco de dados ==============================

def criar_conexao(arquivo=ARQUIVO_BANCO):
    """Abre (ou cria, se não existir) o arquivo do banco SQLite."""
    return sqlite3.connect(arquivo)


def criar_tabela(conexao, arquivo_sql=ARQUIVO_SQL):
    """Executa o script banco.sql. Como ele usa CREATE TABLE IF NOT EXISTS,
    pode rodar toda vez que o programa abre sem apagar os dados."""
    with open(arquivo_sql, encoding='utf-8') as f:
        conexao.executescript(f.read())


def inserir_aluno(conexao, dados):
    """Insere um aluno. Lança sqlite3.IntegrityError se a matrícula já existir.

    Os '?' fazem o sqlite3 colocar os valores com segurança, evitando
    que um texto digitado seja interpretado como comando SQL.
    """
    with conexao:   # confirma (commit) ao sair do bloco, ou desfaz se der erro
        conexao.execute(
            'INSERT INTO alunos (matricula, nome, curso, email) VALUES (?, ?, ?, ?)',
            (dados['matricula'], dados['nome'], dados['curso'], dados['email'] or None))


def buscar_aluno(conexao, matricula):
    """Devolve o aluno com essa matrícula, ou None."""
    cursor = conexao.execute(
        'SELECT matricula, nome, curso, email FROM alunos WHERE matricula = ?',
        (matricula,))
    linha = cursor.fetchone()
    return dict(zip(CAMPOS, linha)) if linha else None


def atualizar_aluno(conexao, dados):
    """Atualiza nome, curso e e-mail. Devolve True se o aluno existia."""
    with conexao:
        cursor = conexao.execute(
            'UPDATE alunos SET nome = ?, curso = ?, email = ? WHERE matricula = ?',
            (dados['nome'], dados['curso'], dados['email'] or None, dados['matricula']))
    return cursor.rowcount == 1


def excluir_aluno(conexao, matricula):
    """Exclui o aluno. Devolve True se algum registro foi apagado."""
    with conexao:
        cursor = conexao.execute('DELETE FROM alunos WHERE matricula = ?', (matricula,))
    return cursor.rowcount == 1


SELECT_LISTA = """
    SELECT matricula, nome, curso, COALESCE(email, ''),
           strftime('%d/%m/%Y %H:%M', data_cadastro, 'localtime')
    FROM alunos
"""


def listar_todos(conexao):
    """Todos os alunos em ordem alfabética, prontos para a tabela."""
    return conexao.execute(SELECT_LISTA + ' ORDER BY nome COLLATE NOCASE').fetchall()


def pesquisar_alunos(conexao, termo):
    """Alunos cujo nome ou matrícula contém o termo (sem diferenciar maiúsculas)."""
    padrao = f'%{termo}%'
    return conexao.execute(
        SELECT_LISTA + ' WHERE nome LIKE ? OR matricula LIKE ? ORDER BY nome COLLATE NOCASE',
        (padrao, padrao)).fetchall()


def exportar_csv(alunos, caminho):
    """Salva a lista em CSV com ';' e BOM, para abrir certo no Excel em português."""
    with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
        escritor = csv.writer(f, delimiter=';')
        escritor.writerow(TITULOS)
        escritor.writerows(alunos)


# ============================== Validação ==============================

def limpar_texto(texto):
    """Tira espaços das pontas e espaços repetidos no meio."""
    return ' '.join(str(texto or '').split())


def validar_dados(dados):
    """Devolve a lista de erros encontrados (vazia se estiver tudo certo)."""
    erros = []
    if not dados['matricula']:
        erros.append('Matrícula é obrigatória.')
    elif not PADRAO_MATRICULA.match(dados['matricula']):
        erros.append('Matrícula deve ter 8 dígitos (ex.: 24100434).')
    if not dados['nome']:
        erros.append('Nome é obrigatório.')
    elif len(dados['nome']) < 3:
        erros.append('Nome deve ter pelo menos 3 letras.')
    if not dados['curso']:
        erros.append('Curso é obrigatório.')
    if dados['email'] and not PADRAO_EMAIL.match(dados['email']):
        erros.append('E-mail inválido (ex.: nome@grad.ufsc.br).')
    return erros


