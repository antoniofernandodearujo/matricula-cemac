import tkinter as tk
from tkinter import messagebox, filedialog
from ttkbootstrap import Style, ttk
from PIL import Image, ImageTk 
from datetime import date
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import sqlite3
import re

from utils import format_date 

# Componentes de Domínio/Lógica Separados
try:
    from database import DatabaseManager
    from utils import (
        calcular_turma_cemac, 
        is_valid_name, 
        format_cpf, 
        format_phone, 
        is_valid_date_format
    )
except ImportError as e:
    # Saída de erro aprimorada, caso o usuário não tenha os arquivos
    print(f"ERRO CRÍTICO ao importar módulos: {e}. Verifique se database.py e utils.py existem e estão na mesma pasta.")
    exit(1)


# ====================================================================
# CLASSE PRINCIPAL DA APLICAÇÃO (Controller/Container)
# ====================================================================

class MatriculaApp(tk.Tk):
    """Classe principal que gerencia o banco de dados, estilos e troca de telas."""
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager() 
        
        self.title("CEMAC - Sistema de Matrícula")
        self.geometry("1000x700") 
        self.style = Style(theme='litera')
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._configure_styles()
        
        self.frames = {}
        self._create_frames()
        self.show_frame("HomeFrame")

    def _configure_styles(self):
        """Configura os estilos globais TTK/Bootstrap."""
        self.style.configure('C.TButton', font=('default', 11, 'bold'))
        self.style.configure('Title.TLabel', font=('default', 20, 'bold', 'underline'))
        self.style.configure('N.TLabel', font=('default', 11))
        self.style.configure('Turma.TLabel', font=('default', 12, 'bold'), foreground=self.style.colors.info)
        
        self.style.configure('Treeview.Heading', font=('default', 12, 'bold')) 
        self.style.configure('T.Treeview', rowheight=25)
        self.style.map('Treeview', background=[('selected', self.style.colors.primary)])
        
    def _create_frames(self):
        """Instancia todas as telas/frames da aplicação."""
        home_frame = HomeFrame(self, self) 
        home_frame.grid(row=0, column=0, sticky="nsew")
        self.frames["HomeFrame"] = home_frame

        forms_frame = FormsFrame(self, self)
        forms_frame.grid(row=0, column=0, sticky="nsew")
        self.frames["FormsFrame"] = forms_frame
        
        list_frame = ListFrame(self, self)
        list_frame.grid(row=0, column=0, sticky="nsew")
        self.frames["ListFrame"] = list_frame

    def show_frame(self, frame_name):
        """Exibe o Frame solicitado e executa ações específicas ao carregamento."""
        frame = self.frames.get(frame_name)
        if frame:
            if frame_name == "ListFrame":
                self.frames["ListFrame"].load_alunos() 
            frame.tkraise() 
        else:
            messagebox.showerror("Erro de Navegação", f"Frame '{frame_name}' não encontrado.")


# ====================================================================
# TELA 1: HOME (Menu Principal)
# ====================================================================

class HomeFrame(ttk.Frame):
    """Tela inicial com botões de navegação."""
    def __init__(self, parent, controller):
        super().__init__(parent, padding="50")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 4), weight=1) 

        # Título
        ttk.Label(self, text="CEMAC - Sistema de Matrícula", style='Title.TLabel', bootstyle="primary").grid(row=1, column=0, pady=20)
        
        # Frame para os botões
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, pady=30)
        
        # Botões
        ttk.Button(button_frame, text="Nova Matrícula", 
                   command=lambda: controller.show_frame("FormsFrame"),
                   bootstyle="success", width=25, style='C.TButton').pack(pady=15, padx=10)
                   
        ttk.Button(button_frame, text="Ver Lista de Alunos", 
                   command=lambda: controller.show_frame("ListFrame"),
                   bootstyle="info", width=25, style='C.TButton').pack(pady=15, padx=10)
                   
        ttk.Button(button_frame, text="Sair", 
                   command=controller.destroy,
                   bootstyle="danger", width=25, style='C.TButton').pack(pady=15, padx=10)
                   
# ====================================================================
# TELA 2: FORMULÁRIO DE MATRÍCULA (Com Scrollbar e Layout Fixado)
# ====================================================================

class FormsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding="20")
        self.controller = controller
        self.db = controller.db
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Container Principal (centraliza e mantém o tamanho)
        self.central_container = ttk.Frame(self)
        self.central_container.grid(row=0, column=0, sticky="nsew")
        self.central_container.grid_rowconfigure(0, weight=1)
        self.central_container.grid_columnconfigure(0, weight=1)

        # 2. Canvas para permitir a rolagem
        self.canvas = tk.Canvas(self.central_container, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # 3. Scrollbar vertical
        scrollbar = ttk.Scrollbar(self.central_container, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # 4. Frame Interno (Onde todos os widgets do formulário serão colocados)
        # Este frame irá rolar dentro do Canvas
        self.scrollable_frame = ttk.Frame(self.canvas, padding="30")
        
        # Cria a janela no Canvas, anexando o Frame que rola
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar coluna 1 do frame interno para expandir
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Configuração de Rolagem
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"),
                # Garante que a largura do Canvas corresponda à largura do Frame Interno
                width=e.width 
            )
        )
        # Permite rolagem com a roda do mouse (opcional, mas recomendado)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self._setup_form_widgets()


    def _on_mousewheel(self, event):
        """Permite rolar o canvas com a roda do mouse."""
        # Verifica se a rolagem deve ser aplicada a este canvas
        if self.canvas.winfo_exists() and self.canvas.winfo_ismapped():
             # Verifica se o evento aconteceu sobre o canvas ou seus descendentes
             # É uma forma de evitar que role quando o mouse está sobre outros widgets que não pertencem ao scrollable_frame
             if self.canvas.winfo_containing(event.x_root, event.y_root) in self.canvas.winfo_children() or self.scrollable_frame.winfo_containing(event.x_root, event.y_root):
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _setup_form_widgets(self):
        """Cria todos os widgets do formulário dentro do container central."""
        
        form_frame = self.scrollable_frame # Usando o frame interno que rola
        
        # Variáveis de controle
        self.vars = {
            "nome": tk.StringVar(), "data_nasc": tk.StringVar(), 
            "turma": tk.StringVar(value="..."), "idade": tk.StringVar(), 
            "endereco": tk.StringVar(), 
            "mae": tk.StringVar(), "pai": tk.StringVar(), 
            "tel_mae": tk.StringVar(), "tel_pai": tk.StringVar(),
            "cpf_resp": tk.StringVar(), 
            "resp_legal": tk.StringVar(), 
            "tel_resp_emerg": tk.StringVar(), 
            "alergia": tk.StringVar(value="Não"), 
            "problema_med": tk.StringVar(value="Não"),
            "metodo_pagamento": tk.StringVar(value="Pix") 
        }
        
        row = 0
        
        # Título
        ttk.Label(form_frame, text="Nova Matrícula", style='Title.TLabel', bootstyle="primary").grid(row=row, columnspan=2, pady=(0, 30), sticky=tk.W)
        row += 1

        # --- DADOS PESSOAIS (Aluno) ---
        self._create_label_entry(form_frame, row, "Nome da Criança:", self.vars["nome"]); row += 1
        self._create_label_entry(form_frame, row, "Endereço Completo:", self.vars["endereco"]); row += 1

        # Data, Idade e Turma
        row = self._create_data_turma_line(form_frame, row)
        
        ttk.Separator(form_frame, bootstyle="info").grid(row=row, columnspan=2, sticky="ew", pady=15)
        row += 1

        # --- DADOS DOS PAIS/RESPONSÁVEIS ---
        self._create_label_entry(form_frame, row, "Nome da Mãe:", self.vars["mae"]); row += 1
        tel_mae_entry = self._create_label_entry(form_frame, row, "Tel. da Mãe:", self.vars["tel_mae"])
        tel_mae_entry.bind('<FocusOut>', lambda e: format_phone(tel_mae_entry)); row += 1 
        
        self._create_label_entry(form_frame, row, "Nome do Pai:", self.vars["pai"]); row += 1
        tel_pai_entry = self._create_label_entry(form_frame, row, "Tel. do Pai:", self.vars["tel_pai"])
        tel_pai_entry.bind('<FocusOut>', lambda e: format_phone(tel_pai_entry)); row += 1
        
        self._create_label_entry(form_frame, row, "Responsável Legal:", self.vars["resp_legal"]); row += 1
        
        cpf_entry = self._create_label_entry(form_frame, row, "CPF do Responsável:", self.vars["cpf_resp"])
        cpf_entry.bind('<FocusOut>', lambda e: format_cpf(cpf_entry)); row += 1
        
        tel_emerg_entry = self._create_label_entry(form_frame, row, "Tel. Emergência:", self.vars["tel_resp_emerg"])
        tel_emerg_entry.bind('<FocusOut>', lambda e: format_phone(tel_emerg_entry)); row += 1

        ttk.Separator(form_frame, bootstyle="info").grid(row=row, columnspan=2, sticky="ew", pady=15)
        row += 1

        # --- INFORMAÇÕES DE SAÚDE / PAGAMENTO ---
        self._create_label_entry(form_frame, row, "Alergia? (Descreva ou 'Não'):", self.vars["alergia"]); row += 1
        self._create_label_entry(form_frame, row, "Problema c/ Medicamento? ('Não'):", self.vars["problema_med"]); row += 1

        ttk.Separator(form_frame, bootstyle="info").grid(row=row, columnspan=2, sticky="ew", pady=15)
        row += 1
        
        # Método de Pagamento e Status
        ttk.Label(form_frame, text="Método de Pagamento (PAGO):", style='N.TLabel').grid(row=row, column=0, sticky=tk.W, padx=5, pady=8)
        pagto_combobox = ttk.Combobox(
            form_frame, textvariable=self.vars["metodo_pagamento"],
            values=["Pix", "Cartão", "Dinheiro", "Boleto", "Transferência"], 
            state="readonly" 
        )
        pagto_combobox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=8)
        pagto_combobox.set("Pix")
        row += 1

        ttk.Label(form_frame, text="Status Final:", style='N.TLabel').grid(row=row, column=0, sticky=tk.W, padx=5, pady=8)
        ttk.Label(form_frame, text="Matrícula Efetivada (Pagto e Assinatura OK)", bootstyle="success", style='N.TLabel').grid(row=row, column=1, sticky=tk.W, padx=5, pady=8)
        row += 1
        
        # Botões de Ação
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky=tk.E, pady=20)

        ttk.Button(button_frame, text="Cancelar / Voltar ao Menu", bootstyle="secondary", 
                   command=self._clear_and_go_home, style='C.TButton').pack(side=tk.LEFT, padx=5)
                   
        ttk.Button(button_frame, text="Efetivar Matrícula", bootstyle="success", 
                   command=self._save_forms, style='C.TButton').pack(side=tk.LEFT, padx=5)


    # --- Métodos de Componentização/Auxílio ---

    def _create_label_entry(self, parent_frame, row, label_text, textvariable): 
        """Cria um Label e um Entry com largura expansível em uma linha do formulário."""
        ttk.Label(parent_frame, text=label_text, style='N.TLabel').grid(row=row, column=0, sticky=tk.W, padx=5, pady=8)
        
        entry = ttk.Entry(parent_frame, textvariable=textvariable) 
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=8) # Sticky="ew" faz expandir
        setattr(entry, 'set', textvariable.set) 
        return entry
        
    def _create_data_turma_line(self, parent_frame, row):
        """Cria a linha específica de Data de Nascimento, Idade e Turma."""
        
        ttk.Label(parent_frame, text="Data Nasc. (dd/mm/aaaa):", style='N.TLabel').grid(row=row, column=0, sticky=tk.W, padx=5, pady=8)

        # Usando um Frame para conter os campos de data, idade e turma para melhor organização na coluna 1
        data_frame = ttk.Frame(parent_frame)
        data_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=8)
        
        data_entry = ttk.Entry(data_frame, textvariable=self.vars["data_nasc"], width=15)
        data_entry.pack(side=tk.LEFT)
        
        # --- LINHA CORRIGIDA AQUI ---
        # 1. Primeiro formata a data
        # 2. Depois atualiza a turma (que agora encontrará o formato correto)
        data_entry.bind('<FocusOut>', lambda e: (format_date(data_entry), self._update_turma_and_idade())); 
        data_entry.bind('<Return>', lambda e: (format_date(data_entry), self._update_turma_and_idade()))
        
        
        ttk.Label(data_frame, text="Idade:", style='N.TLabel').pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(data_frame, textvariable=self.vars["idade"], bootstyle="info", style='Turma.TLabel').pack(side=tk.LEFT)
        
        ttk.Label(data_frame, text="Turma Sugerida:", style='N.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(data_frame, textvariable=self.vars["turma"], bootstyle="info", style='Turma.TLabel').pack(side=tk.LEFT)
        
        return row + 1 

    # --- Métodos de Lógica/Validação ---

    def _update_turma_and_idade(self):
        """Atualiza a idade e a turma sugerida com base na data de nascimento."""
        data_str = self.vars["data_nasc"].get()
        nome = self.vars["nome"].get()

        if not is_valid_name(nome):
             self.vars["turma"].set("Nome Inválido!")
             self.vars["idade"].set("?")
             return
             
        if not is_valid_date_format(data_str):
             self.vars["turma"].set("Data Inválida!")
             self.vars["idade"].set("?")
             return
        
        try:
            turma = calcular_turma_cemac(data_str) 
            
            dia, mes, ano = map(int, data_str.split('/'))
            data_nasc = date(ano, mes, dia)
            hoje = date.today()
            idade_anos = hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
            
            self.vars["idade"].set(str(idade_anos))
            self.vars["turma"].set(turma)
            
        except Exception:
            self.vars["turma"].set("Erro Desconhecido!")
            self.vars["idade"].set("?")
        

    def _clear_forms(self):
        """Limpa todas as variáveis do formulário."""
        for key in self.vars:
            self.vars[key].set("")
        self.vars["alergia"].set("Não")
        self.vars["problema_med"].set("Não")
        self.vars["turma"].set("...")
        self.vars["idade"].set("")
        self.vars["metodo_pagamento"].set("Pix") 

    def _clear_and_go_home(self):
        """Limpa o formulário e navega para a Home."""
        self._clear_forms()
        self.controller.show_frame("HomeFrame")


    def _save_forms(self):
        """Valida e salva os dados no banco de dados."""
        # --- VALIDAÇÕES CRÍTICAS ---
        campos_obg = {
            "Nome": self.vars["nome"].get().strip(),
            "Data Nasc.": self.vars["data_nasc"].get().strip(),
            "Endereço": self.vars["endereco"].get().strip(),
            "Nome Mãe": self.vars["mae"].get().strip(),
            "Tel. Mãe": self.vars["tel_mae"].get().strip(),
            "Responsável Legal": self.vars["resp_legal"].get().strip(),
            "CPF do Responsável": self.vars["cpf_resp"].get().strip(),
            "Método Pagto": self.vars["metodo_pagamento"].get().strip()
        }
        
        for nome, valor in campos_obg.items():
            if not valor:
                messagebox.showerror("Erro de Validação", f"O campo '{nome}' é **obrigatório**.")
                return

        if not is_valid_name(campos_obg["Nome"]):
            messagebox.showerror("Erro de Validação", "Nome do aluno deve ser completo (mínimo 2 palavras) e conter apenas letras.")
            return

        turma = self.vars["turma"].get()
        if "Erro" in turma or "Inválida" in turma or "Aguardando" in turma or "..." in turma or "Fora" in turma:
            messagebox.showerror("Erro de Validação", "Verifique a data de nascimento. Turma sugerida inválida ou fora da faixa etária.")
            return

        # Verifica se o CPF está no formato ##.###.###-##, mas permite se for vazio, já que é opcional se o responsável for a mãe/pai já listado.
        # No seu código, você o listou como obrigatório (campos_obg), então vamos reforçar a validação:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}\-\d{2}', campos_obg["CPF do Responsável"]):
             messagebox.showwarning("Atenção", "Formato do CPF do responsável incorreto. Use ###.###.###-##.")
             return 

        # --- CAPTURAR DATA ATUAL DA MATRÍCULA ---
        data_matricula = date.today().strftime('%d/%m/%Y')

        # --- PREPARAÇÃO E INSERÇÃO DE DADOS (16 CAMPOS) ---
        try:
            # Garante que a idade seja um inteiro ou 0 se for texto inválido
            idade_int = int(self.vars["idade"].get().strip()) if self.vars["idade"].get().strip().isdigit() else 0

            dados = (
                campos_obg["Nome"], 
                campos_obg["Data Nasc."], 
                turma, 
                idade_int, 
                campos_obg["Endereço"], 
                campos_obg["Nome Mãe"], 
                self.vars["pai"].get().strip(), # Pode ser vazio
                campos_obg["Tel. Mãe"], 
                self.vars["tel_pai"].get().strip(), # Pode ser vazio
                campos_obg["CPF do Responsável"], 
                campos_obg["Responsável Legal"], 
                self.vars["tel_resp_emerg"].get().strip(), 
                self.vars["alergia"].get().strip() if self.vars["alergia"].get().strip() else "Não", 
                self.vars["problema_med"].get().strip() if self.vars["problema_med"].get().strip() else "Não", 
                campos_obg["Método Pagto"],
                data_matricula # Campo 16: Data da Matrícula
            )

            if self.db.insert_aluno(dados): 
                 messagebox.showinfo("Sucesso", f"Matrícula de {dados[0]} efetivada com sucesso! Turma: {dados[2]}")
                 self._clear_forms()
                 self.controller.show_frame("HomeFrame")
            else:
                 messagebox.showerror("Erro", "Falha ao salvar a Matrícula. Verifique o console para erros de banco.")

        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro inesperado ao salvar: {e}")


# ====================================================================
# TELA 3: LISTA DE ALUNOS (Com Turmas Corrigidas e Layout OK)
# ====================================================================

class ListFrame(ttk.Frame):
    
    # Lista de turmas atualizada com a nomenclatura correta
    TURMAS = ["Todas", "Berçário", "Infantil I", "Infantil II", "Infantil III", "Pré I", "Pré II", "2º Ano ou Acima"] 

    def __init__(self, parent, controller):
        super().__init__(parent, padding="15")
        self.controller = controller
        self.db = controller.db
        
        self.page_size = 15
        self.current_page = 1
        self.total_alunos = 0
        self.all_alunos_data = [] 
        self.filtered_alunos_data = [] 

        self.grid_rowconfigure(2, weight=1) 
        self.grid_columnconfigure(0, weight=1)
        
        ttk.Label(self, text="Lista de Alunos Cadastrados", style='Title.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self._setup_filter_frame()
        self._setup_treeview()
        self._setup_bottom_actions()
        
        self.tree.bind("<Double-1>", self._confirmar_matricula_modal)
        
        self.load_alunos() 

    def _setup_filter_frame(self):
        """Cria e configura a seção de filtros e pesquisa."""
        filter_frame = ttk.Frame(self, padding="5", bootstyle="secondary")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1) # Faz a barra de pesquisa expandir
        
        self.turma_filter_var = tk.StringVar(value="Todas")
        self.search_name_var = tk.StringVar()

        # Filtro de Turma
        ttk.Label(filter_frame, text="Filtrar por Turma:", style='N.TLabel').grid(row=0, column=0, padx=5, sticky=tk.W)
        turma_combo = ttk.Combobox(filter_frame, textvariable=self.turma_filter_var, values=self.TURMAS, state="readonly", width=18, style='N.TLabel')
        turma_combo.grid(row=0, column=1, padx=5, sticky=tk.W)
        turma_combo.bind("<<ComboboxSelected>>", self._apply_filter)
        
        # Pesquisa por Nome
        ttk.Label(filter_frame, text="Pesquisar por Nome:", style='N.TLabel').grid(row=0, column=2, padx=(20, 5), sticky=tk.W)
        name_entry = ttk.Entry(filter_frame, textvariable=self.search_name_var)
        name_entry.grid(row=0, column=3, padx=5, sticky="ew")
        name_entry.bind('<KeyRelease>', self._apply_filter) 
        
        # Botão Limpar Filtros
        ttk.Button(filter_frame, text="Limpar Filtros", bootstyle="light", command=self._clear_filter, style='C.TButton').grid(row=0, column=4, padx=10, sticky=tk.E)

    def _setup_treeview(self):
        """Cria e configura o widget Treeview (Tabela)."""
        # Adicionado 'MatriculaEm' para mostrar o campo DataMatricula (índice 19)
        self.tree = ttk.Treeview(self, columns=("ID", "Nome", "Turma", "MatriculaEm", "Status", "Pagto"), 
                                 show="headings", bootstyle="primary", selectmode="browse") 
        self.tree.grid(row=2, column=0, sticky="nsew")

        # Configuração das Colunas 
        self.tree.column("ID", width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("Nome", minwidth=280, stretch=tk.YES) 
        self.tree.column("Turma", width=120, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("MatriculaEm", width=100, stretch=tk.NO, anchor=tk.CENTER) 
        self.tree.column("Status", width=150, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("Pagto", width=70, stretch=tk.NO, anchor=tk.CENTER)
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome do Aluno")
        self.tree.heading("Turma", text="Turma")
        self.tree.heading("MatriculaEm", text="Matrícula Em")
        self.tree.heading("Status", text="Status Matrícula")
        self.tree.heading("Pagto", text="Pagto")

        # Barra de Rolagem Vertical (para a Tabela)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
    def _setup_bottom_actions(self):
        """Cria a seção de botões de ação e paginação."""
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Botões
        ttk.Button(bottom_frame, text="Voltar ao Menu", bootstyle="secondary", 
                   command=lambda: self.controller.show_frame("HomeFrame"), 
                   style='C.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(bottom_frame, text="Confirmar Matrícula", bootstyle="success", 
                   command=self._confirmar_matricula_modal, 
                   style='C.TButton').pack(side=tk.LEFT, padx=10)
                   
        ttk.Button(bottom_frame, text="Imprimir Ficha", bootstyle="primary", 
                   command=self._imprimir_ficha, 
                   style='C.TButton').pack(side=tk.LEFT, padx=10)
        
        # Controles de Paginação (à Direita)
        pag_frame = ttk.Frame(bottom_frame)
        pag_frame.pack(side=tk.RIGHT)
        
        ttk.Button(pag_frame, text="< Anterior", bootstyle="light", command=lambda: self._navigate_page(-1), style='C.TButton').pack(side=tk.LEFT)
        self.page_label = ttk.Label(pag_frame, text="Página 1/1", width=10, anchor=tk.CENTER, style='N.TLabel')
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(pag_frame, text="Próxima >", bootstyle="light", command=lambda: self._navigate_page(1), style='C.TButton').pack(side=tk.LEFT)

    # --- Métodos de Filtro e Paginação ---

    def load_alunos(self):
        """Carrega todos os dados do banco e aplica o filtro inicial."""
        try:
            self.all_alunos_data = self.db.get_alunos() 
        except Exception as e:
            messagebox.showerror("Erro de Banco", f"Falha ao carregar alunos. Tente recriar o banco de dados (deletar o .db): {e}")
            self.all_alunos_data = []
            
        self._apply_filter() 

    def _apply_filter(self, event=None):
        """Filtra os dados em memória com base na turma e no nome."""
        turma_selecionada = self.turma_filter_var.get()
        termo_pesquisa = self.search_name_var.get().strip().lower()

        self.filtered_alunos_data = []

        for aluno in self.all_alunos_data:
            
            # Turma está no índice 3
            if turma_selecionada != "Todas" and aluno[3] != turma_selecionada:
                continue

            # Nome está no índice 1
            if termo_pesquisa and termo_pesquisa not in aluno[1].lower():
                continue
            
            self.filtered_alunos_data.append(aluno)
        
        self.current_page = 1
        self.total_alunos = len(self.filtered_alunos_data)
        self.total_pages = (self.total_alunos + self.page_size - 1) // self.page_size
        if self.total_pages == 0: self.total_pages = 1
        
        self._display_current_page()

    def _clear_filter(self):
        """Reseta todos os filtros e recarrega a lista."""
        self.turma_filter_var.set("Todas")
        self.search_name_var.set("")
        self._apply_filter()

    def _display_current_page(self):
        """Atualiza a Treeview com os dados da página atual."""
        self.tree.delete(*self.tree.get_children())
            
        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        
        alunos_page = self.filtered_alunos_data[start_index:end_index] 
        
        for aluno in alunos_page:
            # Posições dos campos no SELECT *:
            # ID(0), Nome(1), Turma(3), StatusMatricula(18), StatusPagto(16), DataMatricula(19)
            
            id, nome, turma, status_matricula, status_pagto, data_matricula = aluno[0], aluno[1], aluno[3], aluno[18], aluno[16], aluno[19] 
            
            pagto_status = "Pago" if status_pagto == 1 else "PENDENTE"
            tag = "efetivada" if status_matricula == 'Matrícula Efetivada' else "pendente" 
            
            self.tree.insert("", tk.END, iid=id, values=(id, nome, turma, data_matricula, status_matricula, pagto_status), tags=(tag,))

        self.tree.tag_configure('pendente', background='#FFEBE6') 
        self.tree.tag_configure('efetivada', background='#E6FFE6')
        
        self.page_label.config(text=f"Pág. {self.current_page}/{self.total_pages}")

    def _navigate_page(self, direction):
        """Muda para a página anterior ou próxima."""
        new_page = self.current_page + direction
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            self._display_current_page()
    
    # --- Métodos de Ação (Matrícula e Impressão) ---
    
    def _get_selected_aluno_id(self):
        """Retorna o ID do aluno selecionado na Treeview."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Seleção", "Selecione um aluno na lista primeiro.")
            return None
        return self.tree.item(selected_item, 'values')[0]

    def _get_aluno_data_map(self, aluno_id):
        """Busca os dados do aluno no DB e mapeia para um dicionário legível."""
        aluno_data_list = self.db.get_aluno_by_id(aluno_id)
        if not aluno_data_list: return None
        
        # Mapeamento do SELECT * (20 campos: índice 0 a 19)
        data = aluno_data_list
        return {
            "ID": data[0], "Nome": data[1], "DataNasc": data[2], "Turma": data[3], 
            "Idade": data[4], "Endereco": data[5],
            "NomeMae": data[6], "NomePai": data[7], "TelMae": data[8], "TelPai": data[9], 
            "CPFRM": data[10], "RespLegal": data[11],
            "TelEmerg": data[12], 
            "Alergia": data[13], "ProbMed": data[14], 
            "PagtoMetodo": data[15],       
            "PagtoStatus": data[16],       
            "AssinaturaStatus": data[17],  
            "MatriculaStatus": data[18],
            "DataMatricula": data[19] 
        }


    def _confirmar_matricula_modal(self, event=None):
        """Cria o modal para confirmação de pagamento/assinatura e efetivação."""
        aluno_id = self._get_selected_aluno_id()
        if not aluno_id: return
        
        aluno_data = self._get_aluno_data_map(aluno_id)
        if not aluno_data: return
        
        if aluno_data['MatriculaStatus'] == 'Matrícula Efetivada':
            messagebox.showinfo("Status", f"A matrícula de {aluno_data['Nome']} já está Efetivada.")
            return

        # Modal Setup
        modal = tk.Toplevel(self)
        modal.title("Efetivar Matrícula")
        modal.geometry("400x300")
        modal.transient(self.controller) 
        modal.grab_set()
        
        frame = ttk.Frame(modal, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"Confirmar Matrícula de:\n{aluno_data['Nome']}", style='N.TLabel', font=('default', 12, 'bold')).pack(pady=10)
        
        ttk.Label(frame, text=f"Método Registrado: {aluno_data['PagtoMetodo']}", style='N.TLabel').pack(pady=(10,0), anchor=tk.W)
        
        ttk.Label(frame, text="Confirmação de Status:", bootstyle="primary", style='N.TLabel').pack(pady=(10,0), anchor=tk.W)
        self.var_assinatura = tk.IntVar(value=aluno_data['AssinaturaStatus']) 
        self.var_pagamento = tk.IntVar(value=aluno_data['PagtoStatus'])
        
        ttk.Checkbutton(frame, text="Pagamento Confirmado", 
                        variable=self.var_pagamento, bootstyle="success-square", style='N.TLabel').pack(pady=5, anchor=tk.W)
        ttk.Checkbutton(frame, text="Contrato Assinado/Ficha Conferida", 
                        variable=self.var_assinatura, bootstyle="success-square", style='N.TLabel').pack(pady=5, anchor=tk.W)
        
        ttk.Button(frame, text="Efetivar Matrícula", bootstyle="success", style='C.TButton',
                   command=lambda: self._finalizar_confirmacao(modal, aluno_id, aluno_data['PagtoMetodo'])).pack(pady=20)


    def _finalizar_confirmacao(self, modal, aluno_id, metodo_pagto):
        """Atualiza o status final da matrícula no banco de dados."""
        pagamento_ok = self.var_pagamento.get()
        assinatura_ok = self.var_assinatura.get()
        
        if pagamento_ok == 0 or assinatura_ok == 0:
            messagebox.showwarning("Atenção", "É necessário confirmar o pagamento e a assinatura para efetivar a matrícula.")
            return

        # Chamada ao método do DB para atualização
        if self.db.update_status_matricula(aluno_id, pagamento_ok, assinatura_ok, metodo_pagto):
            messagebox.showinfo("Sucesso", f"Matrícula Efetivada! (Pagamento: {metodo_pagto})")
            self.load_alunos() 
            modal.destroy()
        else:
            messagebox.showerror("Erro", "Falha ao atualizar o status da matrícula no banco.")


    def _imprimir_ficha(self):
        """Gera um PDF com os dados completos do aluno selecionado."""
        aluno_id = self._get_selected_aluno_id()
        if not aluno_id: return
        
        aluno_data = self._get_aluno_data_map(aluno_id)
        if not aluno_data: return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Ficha_Matricula_{aluno_data['Nome'].replace(' ', '_')}.pdf"
        )
        if not file_path:
            return 
        
        # --- Configuração das Imagens (USANDO CAMINHO DO ARQUIVO) ---
        escudo_path = "escudo.png"
        logo_path = "logo.jpg"
        
        # Variáveis booleanas para controle, não mais buffers BytesIO
        escudo_disponivel = os.path.exists(escudo_path)
        logo_disponivel = os.path.exists(logo_path)
        
        if not escudo_disponivel or not logo_disponivel:
            print("AVISO: Arquivos de logo/escudo não encontrados. O PDF será gerado sem imagens.")


        try:
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            y_pos = height - 100 
            
            # --- CABEÇALHO (Logos e Info da Escola) ---
            
            # AGORA PASSAMOS O CAMINHO (str) DIRETAMENTE PARA drawImage
            if escudo_disponivel: 
                # Certifique-se de que as dimensões são adequadas
                c.drawImage(escudo_path, 50, height - 90, width=60, height=75) 
            if logo_disponivel: 
                c.drawImage(logo_path, width - 110, height - 90, width=80, height=80) 

            # Título principal
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, height - 50, "FICHA DE MATRÍCULA - CEMAC")
            
            # Subtítulo e CNPJ
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, height - 70, "Centro Educacional Mariano Cavalcanti")
            c.drawCentredString(width/2, height - 85, "CNPJ: 48.932.962/0001-05")
            
            # Informação de Matrícula/Emissão
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, height - 110, "Ficha de Matrícula - 2026")
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, height - 125, f"Emitido em {date.today().strftime('%d/%m/%Y')}")

            y_pos = height - 180 # Ajusta a posição inicial após o novo cabeçalho
            
            # Formatação de campos vazios/padrão
            alergia = aluno_data['Alergia'] if aluno_data['Alergia'] not in ('Não', '') else 'Nenhuma'
            prob_med = aluno_data['ProbMed'] if aluno_data['ProbMed'] not in ('Não', '') else 'Nenhum'
            
            # 1. DADOS DO ALUNO
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "1. DADOS DO ALUNO:")
            y_pos -= 18 
            
            c.setFont("Helvetica", 11)
            c.drawString(50, y_pos, f"Nome da Criança: {aluno_data['Nome']}")
            c.drawString(350, y_pos, f"Data Nasc: {aluno_data['DataNasc']} (Idade: {aluno_data['Idade']} anos)")
            y_pos -= 18
            c.drawString(50, y_pos, f"Endereço: {aluno_data['Endereco']}")
            c.drawString(350, y_pos, f"Turma / Ano: {aluno_data['Turma']}")
            y_pos -= 25
            
            # 2. DADOS DOS RESPONSÁVEIS
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "2. DADOS DOS RESPONSÁVEIS:")
            y_pos -= 18
            
            c.setFont("Helvetica", 11)
            c.drawString(50, y_pos, f"Nome da Mãe: {aluno_data['NomeMae']} - Tel: {aluno_data['TelMae']}")
            y_pos -= 18
            c.drawString(50, y_pos, f"Nome do Pai: {aluno_data['NomePai']} - Tel: {aluno_data['TelPai']}")
            y_pos -= 18
            c.drawString(50, y_pos, f"Responsável Legal: {aluno_data['RespLegal']}")
            c.drawString(350, y_pos, f"CPF: {aluno_data['CPFRM']}")
            y_pos -= 18
            c.drawString(50, y_pos, f"Telefone Emergência: {aluno_data['TelEmerg']}")
            y_pos -= 25
         
            # 3. SAÚDE E MATRÍCULA
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "3. SAÚDE E MATRÍCULA:")
            y_pos -= 18
            
            c.setFont("Helvetica", 11)
            c.drawString(50, y_pos, f"Alergias: {alergia}")
            c.drawString(350, y_pos, f"Problemas c/ Med.: {prob_med}")
            y_pos -= 18
            
            c.drawString(50, y_pos, f"Pagamento: {'PAGO' if aluno_data['PagtoStatus'] == 1 else 'PENDENTE'} - Método: {aluno_data['PagtoMetodo']}")
            c.drawString(350, y_pos, f"Status Matrícula: {aluno_data['MatriculaStatus']}")
            y_pos -= 50
            
            # --- 4. ASSINATURAS (Verticais e Centralizadas) ---
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "4. ASSINATURAS:")
            y_pos -= 30
            
            # Ponto central horizontal da página
            PAGE_CENTER_X = width / 2 
            # Largura da linha para centralização (pode ser ajustada)
            LINE_WIDTH = 300 
            # Offset do texto em relação à linha
            TEXT_OFFSET = 10 
            # Espaço entre as assinaturas (20 é o espaço adicional ao y_pos padrão)
            SPACE_BETWEEN_SIGNS = 175

            # Coordenadas da linha: (center_x - metade_largura) até (center_x + metade_largura)
            line_x_start = PAGE_CENTER_X - (LINE_WIDTH / 2)
            line_x_end = PAGE_CENTER_X + (LINE_WIDTH / 2)
            
            # -----------------------------------------------------
            # 1. Assinatura do Responsável Legal (Topo)
            # -----------------------------------------------------
            
            # Linha horizontal para assinatura do Responsável
            c.line(line_x_start, y_pos, line_x_end, y_pos) 
            c.setFont("Helvetica", 10)
            c.drawCentredString(PAGE_CENTER_X, y_pos - TEXT_OFFSET, f"Assinatura do Responsável Legal: {aluno_data['RespLegal']}")
            
            y_pos -= SPACE_BETWEEN_SIGNS # Aumenta o espaço para a próxima linha
            
            # -----------------------------------------------------
            # 2. Espaço para Assinatura do Diretor (Base)
            # -----------------------------------------------------
            
            # Linha horizontal para assinatura do Diretor
            c.line(line_x_start, y_pos, line_x_end, y_pos)
            c.setFont("Helvetica", 10)
            c.drawCentredString(PAGE_CENTER_X, y_pos - TEXT_OFFSET, "Assinatura do Diretor: Antonio Claudio da Silva")
            
            y_pos -= 40 # Move o cursor para o rodapé

            # --- RODAPÉ DA ESCOLA (Fixo na parte inferior) ---
            c.setFont("Helvetica", 8)
            rodape_text = "Rua Governador Nilo Coelho, 198 - Bairro Centro - Macaparana, PE | Tel: (81) 99813-3609 | cemac.contato@gmail.com"
            c.drawCentredString(width/2, 30, rodape_text)
            
            c.showPage()
            c.save()
            
            messagebox.showinfo("Sucesso", f"Ficha de Matrícula salva em: {file_path}")

        except Exception as e:
            # Captura erros gerais (como problemas de fonte ou outras falhas do reportlab)
            messagebox.showerror("Erro de Impressão", f"Falha ao gerar o PDF. Verifique se o caminho do arquivo está correto e as bibliotecas estão instaladas. Erro: {e}")