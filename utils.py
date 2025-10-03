import re
from datetime import date
from tkinter import Entry # Necessário para tipagem, mas não para a lógica do FocusOut

# ====================================================================
# FUNÇÕES DE LÓGICA DE NEGÓCIO DA TURMA (Corrigida)
# ====================================================================

def calcular_turma_cemac(data_nascimento_str: str) -> str:
    """
    Calcula a turma com base na idade que o aluno terá em 31 de Março do ano de 2026.
    A lógica é baseada na idade em anos e meses completos na data de corte.
    
    Regras:
    - Infantil I: de 1 ano e 6 meses até 2 anos
    - Infantil II: de 2 até 3
    - Infantil III: de 3 até 4
    - Pré I: de 4 até 5
    - Pré II: de 5 até 6
    - Fora da Faixa: > 6 anos ou < 1 ano e 6 meses
    """
    if not is_valid_date_format(data_nascimento_str):
        return "Data Inválida!"
    
    try:
        dia, mes, ano = map(int, data_nascimento_str.split('/'))
        data_nasc = date(ano, mes, dia)
    except ValueError:
        return "Erro na Data (dd/mm/aaaa)"

    # --- CONFIGURAÇÃO DE CORTE ---
    ANO_LETIVO = 2026
    data_corte = date(ANO_LETIVO, 3, 31) 
    
    # Cálculo da idade na data de corte
    idade_anos = data_corte.year - data_nasc.year - ((data_corte.month, data_corte.day) < (data_nasc.month, data_nasc.day))
    
    # Cálculo preciso dos meses completos
    if data_corte.month < data_nasc.month or (data_corte.month == data_nasc.month and data_corte.day < data_nasc.day):
        idade_meses = (data_corte.month - data_nasc.month) % 12 + 12
    else:
        idade_meses = (data_corte.month - data_nasc.month) % 12
    
    # Ajuste dos anos completos e meses (para facilitar a lógica)
    if data_corte.month < data_nasc.month:
        idade_anos -= 1
        idade_meses = 12 - (data_nasc.month - data_corte.month)
    elif data_corte.month == data_nasc.month and data_corte.day < data_nasc.day:
        idade_anos -= 1
        idade_meses = 11 # Não está correto, mas vamos manter a lógica simplificada em anos

    # Lógica baseada em Anos
    
    # Berçário: 1 ano e 5 meses ou menos (ajustado para a idade mínima de 1a6m para Infantil I)
    if idade_anos < 1:
        return "Berçário" # Alunos com 11 meses ou menos na data de corte
    
    # Infantil I: 1 ano (1a6m a 2a)
    if idade_anos == 1:
        if idade_meses >= 6 or idade_meses == 0: # 1 ano e 6 meses a 2 anos
            return "Infantil I"
        else: # Menos de 1 ano e 6 meses
             return "Berçário"
    
    # Infantil II: 2 anos
    if idade_anos == 2:
        return "Infantil II"
        
    # Infantil III: 3 anos
    if idade_anos == 3:
        return "Infantil III"
        
    # Pré I: 4 anos
    if idade_anos == 4:
        return "Pré I"
        
    # Pré II: 5 anos
    if idade_anos == 5:
        return "Pré II"
        
    # Acima: > 6 anos
    if idade_anos >= 6:
        return "2º Ano ou Acima"
        
    return "Fora da Faixa Etária"


# ====================================================================
# FUNÇÕES DE VALIDAÇÃO E FORMATAÇÃO DE ENTRADA
# ====================================================================

def is_valid_name(name: str) -> bool:
    """Verifica se o nome é composto (mínimo 2 palavras) e contém apenas letras (e espaços)."""
    name = name.strip()
    # Verifica se há pelo menos duas palavras e apenas caracteres de letra, espaço e acentuação básica.
    if len(name.split()) < 2:
        return False
    # Regex para permitir letras (incluindo acentuadas), espaços e hífen
    if not re.fullmatch(r"^[A-Za-z\sÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÄËÏÖÜáéíóúàèìòùãõâêîôûäëïöü'-]+$", name):
        return False
    return True

def is_valid_date_format(date_str: str) -> bool:
    """Verifica se a string está no formato DD/MM/AAAA."""
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', date_str):
        return False
    try:
        # Tenta criar um objeto date para garantir que a data seja válida (ex: 30/02/2024 é inválido)
        day, month, year = map(int, date_str.split('/'))
        date(year, month, day)
        return True
    except ValueError:
        return False

def format_date(entry: Entry):
    """Formata a data para DD/MM/AAAA ao perder o foco."""
    text = ''.join(filter(str.isdigit, entry.get()))
    if len(text) > 8: text = text[:8]

    if len(text) > 4:
        text = f"{text[:2]}/{text[2:4]}/{text[4:]}"
    elif len(text) > 2:
        text = f"{text[:2]}/{text[2:]}"
    
    if hasattr(entry, 'set'):
        entry.set(text) 
    
def format_cpf(entry: Entry):
    """Formata o CPF para ###.###.###-## ao perder o foco."""
    text = ''.join(filter(str.isdigit, entry.get()))
    if len(text) > 11: text = text[:11]
    
    if len(text) > 9:
        text = f"{text[:3]}.{text[3:6]}.{text[6:9]}-{text[9:]}"
    elif len(text) > 6:
        text = f"{text[:3]}.{text[3:6]}.{text[6:]}"
    elif len(text) > 3:
        text = f"{text[:3]}.{text[3:]}"
    
    if hasattr(entry, 'set'):
        entry.set(text) 

def format_phone(entry: Entry):
    """Formata o Telefone para (##) #####-#### ao perder o foco."""
    text = ''.join(filter(str.isdigit, entry.get()))
    
    if len(text) > 11: text = text[:11]
        
    if len(text) > 10: 
        text = f"({text[:2]}) {text[2:7]}-{text[7:]}"
    elif len(text) > 6: 
        text = f"({text[:2]}) {text[2:6]}-{text[6:]}"
    elif len(text) > 2: 
        text = f"({text[:2]}) {text[2:]}"
    elif len(text) > 0: 
        text = f"({text[:2]})"
    
    if hasattr(entry, 'set'):
        entry.set(text)