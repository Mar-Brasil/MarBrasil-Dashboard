import sqlite3
import requests
import time
import os
from tqdm import tqdm

# Obtém o caminho absoluto para o diretório do script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Constrói o caminho para o banco de dados
db_path = os.path.join(script_dir, 'auvo.db')

def validate_links():
    """Verifica a validade dos links de tarefas e atualiza o banco de dados."""
    conn = None
    try:
        print(f"Conectando ao banco de dados em: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Força a revalidação de todas as tarefas para garantir consistência
        print("Resetando o status de validação de todas as tarefas...")
        cursor.execute("UPDATE tasks SET is_link_valid = NULL")
        conn.commit()
        print("Status resetado.")

        # Seleciona todas as tarefas com URL para validar
        cursor.execute("SELECT taskID, taskUrl FROM tasks WHERE taskUrl IS NOT NULL AND taskUrl != ''")
        tasks_to_validate = cursor.fetchall()

        if not tasks_to_validate:
            print("Nenhuma tarefa com URL encontrada para validar.")
            return

        print(f"Encontradas {len(tasks_to_validate)} tarefas para revalidar. Iniciando verificação...")
        
        # Configura a sessão de requisições para reutilizar a conexão
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        session.headers.update(headers)

        # Itera sobre as tarefas com uma barra de progresso
        for task_id, task_url in tqdm(tasks_to_validate, desc="Validando links de tarefas"):
            is_valid = 0  # Assume que é inválido por padrão
            try:
                # Usamos GET para baixar o conteúdo da página
                response = session.get(task_url, timeout=15, allow_redirects=True)
                
                # Verifica o status e o conteúdo da página
                if response.status_code == 200 and "Não encontramos o seu relatório" not in response.text:
                    is_valid = 1
                
            except requests.RequestException as e:
                # Se ocorrer qualquer erro de requisição, consideramos o link inválido
                # print(f"\nErro ao verificar a tarefa {task_id} (URL: {task_url}): {e}")
                is_valid = 0
            
            # Atualiza o banco de dados com o resultado
            cursor.execute("UPDATE tasks SET is_link_valid = ? WHERE taskID = ?", (is_valid, task_id))
            conn.commit()
            
            # Pequeno atraso para não sobrecarregar o servidor
            time.sleep(0.2)

        print("\nValidação concluída com sucesso!")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro no banco de dados: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    validate_links()
