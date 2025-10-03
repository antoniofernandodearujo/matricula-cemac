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
    # Esta validação será desnecessária se o format_date funcionar, mas mantemos por segurança
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
    # --------------------------

    # 1. Cálculo da idade em anos completos na data de corte
    idade_anos_corte = data_corte.year - data_nasc.year - (
        (data_corte.month, data_corte.day) < (data_nasc.month, data_nasc.day)
    )

    # 2. Cálculo da idade em meses completos na data de corte (Para Berçário e Infantil I)
    idade_meses_corte = (data_corte.year - data_nasc.year) * 12 + data_corte.month - data_nasc.month
    if data_corte.day < data_nasc.day:
        idade_meses_corte -= 1
        
    # Lógica de Faixa Etária (USANDO A IDADE EM ANOS NA DATA DE CORTE)
    
    # Exclusão: Acima de 6 anos completos (Pré II vai até 6 anos incompletos)
    if idade_anos_corte >= 6:
        return "Fora da Faixa Etária ( > 6 anos)" 

    # Pré II: 5 anos completos até < 6 anos
    elif idade_anos_corte == 5:
        return "Pré II"
        
    # Pré I: 4 anos completos até < 5 anos
    elif idade_anos_corte == 4:
        return "Pré I"
        
    # Infantil III: 3 anos completos até < 4 anos
    elif idade_anos_corte == 3:
        return "Infantil III" 
        
    # Infantil II: 2 anos completos até < 3 anos
    elif idade_anos_corte == 2:
        return "Infantil II" 
        
    # Infantil I: 1 ano e 6 meses (18 meses) até < 2 anos (24 meses)
    elif idade_anos_corte == 1 and idade_meses_corte >= 18:
        return "Infantil I" 
        
    # Berçário: 6 meses (6 meses) até < 1 ano e 6 meses (18 meses)
    elif idade_anos_corte == 0 and idade_meses_corte >= 6: 
         return "Berçário" 
         
    # Exclusão: Abaixo de 1 ano e 6 meses (18 meses)
    else:
        return "Fora da Faixa Etária ( < 1 ano e 6 meses)"

# ====================================================================
# FUNÇÕES DE MÁSCARA (FocusOut/Bind)
# ====================================================================

def format_date(entry):
    """Formata a data para dd/mm/aaaa ao perder o foco."""
    text = ''.join(filter(str.isdigit, entry.get()))
    
    # Assumimos que a entrada pode ser ddmmYYYY
    if len(text) > 8: text = text[:8]
    
    formatted_text = ""
    if len(text) > 4:
        formatted_text = f"{text[:2]}/{text[2:4]}/{text[4:]}"
    elif len(text) > 2:
        formatted_text = f"{text[:2]}/{text[2:]}"
    elif len(text) > 0:
        formatted_text = f"{text[:2]}"
    
    # Usa o método 'set' anexado ao Entry para atualizar o StringVar
    if hasattr(entry, 'set'):
        entry.set(formatted_text) 
    
    # Retornar o valor formatado para uso imediato no bind, se necessário
    return formatted_text

# --- Funções format_cpf e format_phone permanecem INALTERADAS ---

def format_cpf(entry):
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

def format_phone(entry):
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

# --- Funções de Validação permanecem INALTERADAS ---

def is_valid_name(name: str) -> bool:
    """Validação: Deve ter pelo menos 2 palavras e apenas letras/espaços/acentos."""
    name = name.strip()
    if len(name.split()) < 2:
        return False
    return bool(re.fullmatch(r"^[a-zA-ZáàâãéèêíïóôõöúüçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÇÑ\s]+$", name))

def is_valid_date_format(date_str: str) -> bool:
    """Verifica se a string está no formato dd/mm/aaaa."""
    return bool(re.fullmatch(r'\d{2}/\d{2}/\d{4}', date_str))