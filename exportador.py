import psycopg2
import csv

DB_CONFIG = {
    "host": "localhost",
    "database": "bot_empregos_db",
    "user": "postgres",
    "password": "Root123",
    "port": "5432"
}

def exportador_para_excel():
    print("\nA ligar à Base de Dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT titulo, empresa, link, site, data_descoberta FROM vagas")
    vagas = cur.fetchall()
    print(f"Encontrei {len(vagas)} vagas. A criar o ficheiro Excel (CSV)...")

    with open('vagas_extraidas.csv', 'w', newline='', encoding='utf-8') as ficheiro:
        write = csv .writer(ficheiro, delimiter=';')
        write.writerow(['Título', 'Empresa', 'Link', 'Site', 'Data de recolheu'])
        write.writerows(vagas)
    
    cur.close()
    conn.close()
    print("Ficheiro 'vagas_extraidas.csv' criado com sucesso na tua pasta!\n")



if __name__ == "__main__":
    exportador_para_excel()