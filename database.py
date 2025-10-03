import sqlite3

class DatabaseManager:
    """Gerencia a conexão e operações com o banco de dados SQLite."""
    
    def __init__(self, db_name="matriculas.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        # O método _create_tables DEVE ser rodado após excluir matriculas.db
        self._create_tables() 

    def _connect(self):
        """Estabelece a conexão com o banco de dados."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """
        Cria a tabela 'alunos' com 20 colunas. 
        O campo 'data_matricula' foi adicionado.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data_nascimento TEXT NOT NULL,
                turma TEXT NOT NULL,
                idade INTEGER, 
                endereco TEXT, 
                nome_mae TEXT,
                nome_pai TEXT,
                tel_mae TEXT,
                tel_pai TEXT,
                cpf_responsavel TEXT, 
                responsavel_legal TEXT, 
                tel_responsavel_emergencia TEXT,
                alergia TEXT,
                problema_medicamento TEXT,
                metodo_pagamento TEXT,
                status_pagamento INTEGER,  
                status_assinatura INTEGER, 
                status_matricula TEXT,
                data_matricula TEXT    -- NOVO CAMPO ADICIONADO
            );
        """)
        self.conn.commit()

    def insert_aluno(self, dados):
        """Insere um novo registro de aluno (Matrícula). Espera 16 valores na tupla 'dados'."""
        # Colunas na ordem esperada: 16 bindings (?) no SQL
        sql = """
            INSERT INTO alunos (
                nome, data_nascimento, turma, idade, endereco, nome_mae, nome_pai, 
                tel_mae, tel_pai, cpf_responsavel, responsavel_legal,
                tel_responsavel_emergencia, alergia, problema_medicamento, 
                metodo_pagamento, data_matricula, status_pagamento, status_assinatura, status_matricula
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'Matrícula Efetivada')
        """
        try:
            # 'dados' deve ser uma tupla de 16 elementos
            self.cursor.execute(sql, dados)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir: {e}")
            return False

    def get_aluno_by_id(self, aluno_id):
        """Retorna TODOS os dados de um aluno específico (20 campos)."""
        self.cursor.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,))
        return self.cursor.fetchone()

    def update_status_matricula(self, aluno_id, pagamento_ok, assinatura_ok, metodo_pagto):
        sql = """
            UPDATE alunos SET 
                status_pagamento = ?, 
                status_assinatura = ?, 
                metodo_pagamento = ?,
                status_matricula = 'Matrícula Efetivada' 
            WHERE id = ?
        """
        try:
            self.cursor.execute(sql, (pagamento_ok, assinatura_ok, metodo_pagto, aluno_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar matrícula: {e}")
            return False

    def get_alunos(self):
        """Retorna TODOS os campos para a tela de listagem."""
        self.cursor.execute("SELECT * FROM alunos ORDER BY id DESC")
        return self.cursor.fetchall()
        
    def close(self):
        if self.conn:
            self.conn.close()