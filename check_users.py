import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'auvo.db')

def check_users():
    if not os.path.exists(DB_PATH):
        print(f"Erro: O banco de dados '{DB_PATH}' não foi encontrado.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Verificando usuários na tabela 'usuarios_painel':")
        cursor.execute("SELECT id, nome_completo, username FROM usuarios_painel")
        users = cursor.fetchall()
        
        if not users:
            print("Nenhum usuário encontrado na tabela.")
        else:
            for user in users:
                print(f"  - ID: {user['id']}, Nome: {user['nome_completo']}, Username: {user['username']}")
                
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_users()
