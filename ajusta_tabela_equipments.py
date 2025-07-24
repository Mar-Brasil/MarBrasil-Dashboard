import sqlite3

DB_PATH = 'auvo.db'  # Altere o caminho se necessário

columns = [
    ("externalId", "TEXT"),
    ("parentEquipmentId", "INTEGER"),
    ("associatedCustomerId", "INTEGER"),
    ("associatedUserId", "INTEGER"),
    ("categoryId", "INTEGER"),
    ("identifier", "TEXT"),
    ("urlImage", "TEXT"),
    ("uriAnexos", "TEXT"),
    ("active", "INTEGER"),
    ("creationDate", "TEXT"),
    ("expirationDate", "TEXT"),
    ("equipmentSpecifications", "TEXT"),
    ("description", "TEXT"),
    ("warrantyStartDate", "TEXT"),
    ("warrantyEndDate", "TEXT"),
]

def ajusta_tabela():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for col, typ in columns:
        try:
            cursor.execute(f"ALTER TABLE equipments ADD COLUMN {col} {typ};")
            print(f"Coluna adicionada: {col}")
        except Exception as e:
            if 'duplicate column name' in str(e):
                print(f"Coluna já existe: {col}")
            else:
                print(f"Erro ao adicionar coluna {col}: {e}")
    conn.commit()
    conn.close()
    print("Ajuste concluído!")

if __name__ == "__main__":
    ajusta_tabela()
