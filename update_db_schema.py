import sqlite3
import os

# Obtém o caminho absoluto para o diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Constrói o caminho para o banco de dados
db_path = os.path.join(script_dir, 'auvo.db')

def add_validation_column():
    """Adiciona a coluna 'is_link_valid' à tabela 'tasks' se ela não existir."""
    conn = None
    try:
        print(f"Conectando ao banco de dados em: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'is_link_valid' in columns:
            print("A coluna 'is_link_valid' já existe na tabela 'tasks'. Nenhuma ação necessária.")
        else:
            print("Adicionando a coluna 'is_link_valid' à tabela 'tasks'...")
            # Adiciona a nova coluna. DEFAULT NULL é implícito.
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_link_valid INTEGER")
            conn.commit()
            print("Coluna 'is_link_valid' adicionada com sucesso.")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro no banco de dados: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    add_validation_column()
