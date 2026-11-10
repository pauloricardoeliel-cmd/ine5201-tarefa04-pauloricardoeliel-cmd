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


