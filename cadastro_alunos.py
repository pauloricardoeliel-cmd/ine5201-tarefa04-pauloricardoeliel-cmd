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


# ============================== Interface gráfica ==============================

def criar_layout():
    def campo(rotulo, chave, dica=''):
        return [sg.Text(rotulo, size=(10, 1)),
                sg.Input(key=chave, size=(40, 1), tooltip=dica)]

    formulario = [
        campo('Matrícula*', '-MATRICULA-', '8 dígitos, ex.: 24100434'),
        campo('Nome*', '-NOME-'),
        campo('Curso*', '-CURSO-'),
        campo('E-mail', '-EMAIL-', 'Opcional, ex.: nome@grad.ufsc.br'),
        [sg.Text('* campos obrigatórios', font=('Helvetica', 9))],
    ]

    botoes = [
        sg.Button('Cadastrar', key='-CADASTRAR-', size=(10, 1), button_color=('white', '#27AE60')),
        sg.Button('Editar', key='-EDITAR-', size=(10, 1), disabled=True),
        sg.Button('Excluir', key='-EXCLUIR-', size=(10, 1), disabled=True,
                  button_color=('white', '#C0392B')),
        sg.Button('Limpar', key='-LIMPAR-', size=(10, 1)),
    ]

    busca = [
        sg.Text('Buscar por nome ou matrícula:'),
        sg.Input(key='-BUSCA-', size=(30, 1)),
        sg.Button('Buscar', key='-BUSCAR-', size=(8, 1)),
        sg.Button('Mostrar todos', key='-TODOS-'),
        sg.Push(),
        sg.Button('Exportar CSV', key='-CSV-'),
    ]

    tabela = sg.Table(values=[], headings=TITULOS, key='-TABELA-',
                      col_widths=LARGURAS, auto_size_columns=False,
                      justification='left', num_rows=12, enable_events=True,
                      select_mode=sg.TABLE_SELECT_MODE_BROWSE, expand_x=True)

    return [
        [sg.Text('Cadastro de Alunos', font=('Helvetica', 20, 'bold'))],
        [sg.Frame('Dados do aluno', formulario + [botoes])],
        [sg.HorizontalSeparator()],
        busca,
        [tabela],
        [sg.Text('', key='-TOTAL-'), sg.Push(),
         sg.Text('', key='-STATUS-', font=('Helvetica', 11, 'bold'))],
    ]


def atualizar_tabela(window, alunos):
    window['-TABELA-'].update(values=alunos)
    window['-TOTAL-'].update(f'{len(alunos)} aluno(s) na lista')


def mostrar_status(window, texto, cor=COR_INFO):
    window['-STATUS-'].update(texto, text_color=cor)


def ler_formulario(values):
    return {
        'matricula': limpar_texto(values['-MATRICULA-']),
        'nome': limpar_texto(values['-NOME-']),
        'curso': limpar_texto(values['-CURSO-']),
        'email': limpar_texto(values['-EMAIL-']).lower(),
    }


def preencher_formulario(window, aluno):
    """Carrega um aluno no formulário e entra no modo de edição."""
    for campo in CAMPOS:
        window[f'-{campo.upper()}-'].update(aluno[campo] or '')
    window['-MATRICULA-'].update(disabled=True)    # chave primária não muda
    window['-CADASTRAR-'].update(disabled=True)
    window['-EDITAR-'].update(disabled=False)
    window['-EXCLUIR-'].update(disabled=False)


def limpar_formulario(window):
    for campo in CAMPOS:
        window[f'-{campo.upper()}-'].update('')
    window['-MATRICULA-'].update(disabled=False)
    window['-CADASTRAR-'].update(disabled=False)
    window['-EDITAR-'].update(disabled=True)
    window['-EXCLUIR-'].update(disabled=True)
    window['-MATRICULA-'].set_focus()


def mostrar_erros(erros):
    sg.popup_error('Corrija os campos abaixo:\n\n' + '\n'.join(f'• {e}' for e in erros),
                   title='Dados inválidos')


# ============================== Programa principal ==============================

def main():
    sg.theme('DarkBlue3')

    try:
        conexao = criar_conexao()
        criar_tabela(conexao)
    except FileNotFoundError:
        sg.popup_error(f'Script SQL não encontrado:\n{ARQUIVO_SQL}', title='Erro')
        return
    except sqlite3.Error as erro:
        sg.popup_error(f'Erro ao abrir o banco de dados:\n{erro}', title='Erro')
        return

    window = sg.Window('INE5201 - Cadastro de Alunos', criar_layout(), finalize=True)
    window['-BUSCA-'].bind('<Return>', '_ENTER')     # Enter no campo de busca
    lista_atual = listar_todos(conexao)
    atualizar_tabela(window, lista_atual)
    mostrar_status(window, 'Banco carregado.')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        try:
            if event == '-CADASTRAR-':
                dados = ler_formulario(values)
                erros = validar_dados(dados)
                if not erros and buscar_aluno(conexao, dados['matricula']):
                    erros.append(f'A matrícula {dados["matricula"]} já está cadastrada.')
                if erros:
                    mostrar_erros(erros)
                    mostrar_status(window, 'Cadastro não realizado.', COR_ERRO)
                    continue
                inserir_aluno(conexao, dados)
                lista_atual = listar_todos(conexao)
                atualizar_tabela(window, lista_atual)
                limpar_formulario(window)
                mostrar_status(window, f'Aluno {dados["nome"]} cadastrado!', COR_SUCESSO)

            elif event == '-TABELA-':
                selecionados = values['-TABELA-']
                if selecionados:
                    matricula = lista_atual[selecionados[0]][0]
                    aluno = buscar_aluno(conexao, matricula)
                    if aluno:
                        preencher_formulario(window, aluno)
                        mostrar_status(window, f'Editando {aluno["nome"]}.')

            elif event == '-EDITAR-':
                dados = ler_formulario(values)
                erros = validar_dados(dados)
                if erros:
                    mostrar_erros(erros)
                    continue
                if atualizar_aluno(conexao, dados):
                    mostrar_status(window, f'Dados de {dados["nome"]} atualizados!', COR_SUCESSO)
                else:
                    mostrar_status(window, 'Aluno não encontrado.', COR_ERRO)
                lista_atual = listar_todos(conexao)
                atualizar_tabela(window, lista_atual)
                limpar_formulario(window)

            elif event == '-EXCLUIR-':
                dados = ler_formulario(values)
                resposta = sg.popup_yes_no(
                    f'Excluir {dados["nome"]} (matrícula {dados["matricula"]})?\n'
                    'Essa ação não pode ser desfeita.', title='Confirmar exclusão')
                if resposta == 'Yes':
                    excluir_aluno(conexao, dados['matricula'])
                    lista_atual = listar_todos(conexao)
                    atualizar_tabela(window, lista_atual)
                    limpar_formulario(window)
                    mostrar_status(window, f'Aluno {dados["nome"]} excluído.', COR_SUCESSO)
                else:
                    mostrar_status(window, 'Exclusão cancelada.')

            elif event in ('-BUSCAR-', '-BUSCA-_ENTER'):
                termo = limpar_texto(values['-BUSCA-'])
                lista_atual = pesquisar_alunos(conexao, termo) if termo else listar_todos(conexao)
                atualizar_tabela(window, lista_atual)
                if termo and not lista_atual:
                    mostrar_status(window, f'Nenhum aluno encontrado para "{termo}".', COR_ERRO)
                else:
                    mostrar_status(window, f'{len(lista_atual)} resultado(s).')

            elif event in ('-TODOS-', '-LIMPAR-'):
                window['-BUSCA-'].update('')
                limpar_formulario(window)
                lista_atual = listar_todos(conexao)
                atualizar_tabela(window, lista_atual)
                mostrar_status(window, 'Formulário limpo.' if event == '-LIMPAR-'
                               else 'Mostrando todos os alunos.')

            elif event == '-CSV-':
                caminho = sg.popup_get_file('Salvar lista como', save_as=True,
                                            default_path='alunos.csv',
                                            file_types=(('CSV', '*.csv'),),
                                            default_extension='.csv', no_window=True)
                if caminho:
                    exportar_csv(lista_atual, caminho)
                    mostrar_status(window, f'Lista exportada para {os.path.basename(caminho)}.',
                                   COR_SUCESSO)

        except sqlite3.IntegrityError:
            mostrar_status(window, 'Matrícula já cadastrada.', COR_ERRO)
            sg.popup_error('Essa matrícula já está cadastrada.', title='Matrícula repetida')
        except (sqlite3.Error, OSError) as erro:
            mostrar_status(window, 'Erro na operação.', COR_ERRO)
            sg.popup_error(f'Não foi possível concluir a operação:\n{erro}', title='Erro')

    window.close()
    conexao.close()


if __name__ == '__main__':
    main()
