"""
Script para verificar o status de todos os scripts de download.
Verifica se todos os scripts estão presentes, se estão usando o módulo de utilitários,
e se estão configurados corretamente.
"""
import os
import sys
import importlib
import inspect
from datetime import datetime

def check_script(script_name):
    """Verifica se um script está configurado corretamente."""
    print(f"\nVerificando {script_name}...")
    
    # Verificar se o arquivo existe
    script_path = os.path.join('downloads', f"{script_name}.py")
    if not os.path.exists(script_path):
        print(f"  [ERRO] Script {script_path} não encontrado!")
        return False
    
    # Verificar se o módulo pode ser importado
    try:
        module_name = f"downloads.{script_name}"
        module = importlib.import_module(module_name)
        print(f"  [OK] Módulo {module_name} importado com sucesso.")
    except Exception as e:
        print(f"  [ERRO] Não foi possível importar o módulo {module_name}: {e}")
        return False
    
    # Verificar se o módulo tem a função main()
    if not hasattr(module, 'main'):
        print(f"  [ERRO] O script {script_name} não possui uma função main()!")
        return False
    print(f"  [OK] Função main() encontrada.")
    
    # Verificar se o módulo importa os utilitários
    source_code = inspect.getsource(module)
    if "from downloads.utils import" not in source_code:
        print(f"  [AVISO] O script {script_name} não parece importar o módulo utils.")
    else:
        print(f"  [OK] Importação do módulo utils encontrada.")
    
    if "from downloads.common import" not in source_code:
        print(f"  [AVISO] O script {script_name} não parece importar o módulo common.")
    else:
        print(f"  [OK] Importação do módulo common encontrada.")
    
    # Verificar se o módulo usa get_db_connection
    if "get_db_connection()" not in source_code:
        print(f"  [AVISO] O script {script_name} não parece usar get_db_connection().")
    else:
        print(f"  [OK] Uso de get_db_connection() encontrado.")
    
    print(f"  [INFO] Script {script_name} verificado.")
    return True

def main():
    print(f"Iniciando verificação de scripts em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Lista de scripts de download para verificar
    download_scripts = [
        'download_users',
        'download_teams',
        'download_segments',
        'download_task_types',
        'download_services',
        'download_products',
        'download_customers',
        'download_keywords',
        'download_equipments',
        'download_questionnaires',
        'download_tasks',
        'download_tasks_this_month',
        'download_all_user_tasks'
    ]
    
    ok_count = 0
    error_count = 0
    
    for script in download_scripts:
        if check_script(script):
            ok_count += 1
        else:
            error_count += 1
    
    print(f"\n{'=' * 50}")
    print(f"RESUMO DA VERIFICAÇÃO")
    print(f"{'=' * 50}")
    print(f"Total de scripts verificados: {len(download_scripts)}")
    print(f"Scripts OK: {ok_count}")
    print(f"Scripts com problemas: {error_count}")
    print(f"Verificação concluída em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
