"""
Script principal para executar todos os scripts de download em sequência.
"""
import os
import sys
import time
import importlib
from datetime import datetime

def run_download_script(script_name):
    try:
        print(f"\n{'=' * 50}")
        print(f"Executando {script_name}...")
        print(f"{'=' * 50}")
        
        # Importar o script dinamicamente
        module_name = f"downloads.{script_name.replace('.py', '')}"
        module = importlib.import_module(module_name)
        
        # Executar a função main do script
        module.main()
        
        print(f"Script {script_name} concluído com sucesso!")
        print(f"Exit code: 0")
        return True
    except Exception as e:
        print(f"Erro ao executar {script_name}: {e}")
        print(f"Exit code: 1")
        return False

def main():
    print(f"Iniciando download de todos os dados em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Lista de scripts de download para executar (sem a extensão .py)
    download_scripts = [
        'download_users',
        'download_teams',
        'download_segments',
        'download_task_types',
        'download_services',
        'download_products',
        'download_customers',
        'download_keywords',
        'download_equipments_new',
        'download_questionnaires',
        'download_tasks',
        'download_tasks_this_month',
        'download_all_user_tasks'
    ]
    
    success_count = 0
    fail_count = 0
    
    for script in download_scripts:
        script_path = os.path.join('downloads', f"{script}.py")
        if os.path.exists(script_path):
            success = run_download_script(script)
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # Pausa entre execuções para evitar sobrecarga na API
            time.sleep(2)
        else:
            print(f"Script {script_path} não encontrado. Pulando...")
    
    print(f"\n{'=' * 50}")
    print(f"RESUMO FINAL")
    print(f"{'=' * 50}")
    print(f"Total de scripts: {len(download_scripts)}")
    print(f"Executados com sucesso: {success_count}")
    print(f"Falhas: {fail_count}")
    print(f"Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
