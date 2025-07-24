"""
Script para agendar sincronização diária de equipamentos
Executa o download_equipments_new.py automaticamente todos os dias
"""

import schedule
import time
import subprocess
import os
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('equipment_sync.log'),
        logging.StreamHandler()
    ]
)

def run_equipment_sync():
    """Executa o script de sincronização de equipamentos"""
    try:
        logging.info("🚀 Iniciando sincronização diária de equipamentos...")
        
        # Caminho para o script de download
        script_path = os.path.join(os.path.dirname(__file__), 'downloads', 'download_equipments_new.py')
        
        # Executar o script
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            logging.info("✅ Sincronização de equipamentos concluída com sucesso!")
            logging.info(f"Output: {result.stdout[-500:]}")  # Últimas 500 chars do output
        else:
            logging.error(f"❌ Erro na sincronização de equipamentos!")
            logging.error(f"Error: {result.stderr}")
            
    except Exception as e:
        logging.error(f"❌ Erro crítico na sincronização: {e}")

def main():
    """Função principal do agendador"""
    print("📅 AGENDADOR DE SINCRONIZAÇÃO DIÁRIA DE EQUIPAMENTOS")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🕐 Agendado para executar todos os dias às 06:00")
    print("📝 Logs salvos em: equipment_sync.log")
    print("⚠️  Pressione Ctrl+C para parar o agendador")
    print("=" * 60)
    
    # Agendar para executar todos os dias às 06:00
    schedule.every().day.at("06:00").do(run_equipment_sync)
    
    # Executar uma vez imediatamente para teste (opcional)
    print("🧪 Executando sincronização inicial para teste...")
    run_equipment_sync()
    
    # Loop principal do agendador
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    except KeyboardInterrupt:
        print("\n⚠️  Agendador interrompido pelo usuário!")
        logging.info("Agendador parado pelo usuário")

if __name__ == "__main__":
    main()
