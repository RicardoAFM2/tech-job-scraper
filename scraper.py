import requests
import os
from bs4 import BeautifulSoup
import psycopg2
import time
from dotenv import load_dotenv 

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": os.getenv("DB_PORT"),
}

def iniciar_db():
    print("A preparar a Base de Dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255),
                empresa VARCHAR(255),
                link VARCHAR(255) UNIQUE,
                site VARCHAR(255),
                data_descoberta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tabale 'vagas' pronta!")

def procurar_vagas():
    print("\nA procurar novas vagas no ITjobs...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    palavras_proibidas_titulo = [
        "senior", "sénior", "sr", "mid", "middle", "pleno", "intermediate",
        "expert", "specialist", "especialista", "principal", "staff", "distinguished",
        "lead", "leader", "lider", "leadership", "manager", "gestor", "management", 
        "head", "director", "diretor", "vp", "chief", "owner", "scrum master",
        "architect", "arquiteto"
    ]
    
    palavras_proibidas_descricao = [
        "3 anos", "4 anos", "5 anos", "10 anos",
        "3+ years", "4+ years", "5+ years", "10+ years",
        "years of experience", "proven experience",
        "solid experience", "experiência sólida", "vasta experiência", "pro", 
        "deep knowledge", "conhecimento profundo", "expert level",
        "senior level", "nível sénior",
        "mentoring", "mentorar", "leading teams", "liderar equipas",
        "strategic direction", "decisões estratégicas"
    ]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    novas_vagas = 0
    pagina_atual = 1

    while True:
        print(f"\n A ler página {pagina_atual}...")

        url = f'https://www.itjobs.pt/emprego?page={pagina_atual}'
        
        resposta = requests.get(url, headers=headers)
        site_html = BeautifulSoup(resposta.text, 'html.parser')

        titulo_html = site_html.find_all('div', class_="list-title")
        anuncios = [t.parent for t in titulo_html]

        if len(anuncios) == 0:
            print(f"Chegamos ao fim! a página {pagina_atual} está vazia.")
            break

        print(f"Encontrei {len(anuncios)} anúcios. A anlisar...")

        vagas_reais_na_pagina = 0

        for anuncio in anuncios:
            titulo_el = anuncio.find('div', class_='list-title')
            if not titulo_el:
                continue

                
            vagas_reais_na_pagina += 1
                
            titulo = titulo_el.text.strip()
            titulo_minusculas = titulo.lower()

            e_para_ignorar_titulo = False
            palavra_culpada_titulo = ""
            for proibido in palavras_proibidas_titulo:
                if proibido in titulo_minusculas:
                    e_para_ignorar_titulo = True
                    palavra_culpada_titulo = proibido
                    break
            
            if e_para_ignorar_titulo:
                print(f"[TÍTULO] Rejeitei '{titulo}' por causa da palavra: '{palavra_culpada_titulo}'")
                continue
                
            link_tag = titulo_el.find('a')
            link = "https://www.itjobs.pt" + link_tag['href'] if link_tag else None

            if not link:
                continue

            empresa_el = anuncio.find('div', class_='list-name')
            empresa = empresa_el.find('a').text.strip() if empresa_el else "Empresa não encontrada"

            try:
                resp_vaga = requests.get(link, headers=headers)
                site_vaga = BeautifulSoup(resp_vaga.text, 'html.parser')
                texto_da_pagina = site_vaga.text.lower()

                e_muito_experiente = False
                palavra_culpada_desc = ""
                for proibida_desc in palavras_proibidas_descricao:

                    if proibida_desc.strip() == "":
                        continue

                    if proibida_desc in texto_da_pagina:
                        e_muito_experiente = True
                        palavra_culpada_desc = proibida_desc
                        break
                
                if not e_muito_experiente:
                    cur.execute(
                        "INSERT INTO vagas (titulo, empresa, link, site) VALUES (%s, %s, %s, %s) ON CONFLICT (link) DO NOTHING",
                        (titulo, empresa, link, "ITJobs")
                    )
                    if cur.rowcount > 0:
                        print(f"Vaga Aprovada: {titulo} | {empresa}")
                        novas_vagas += 1

                        texto_alerta = f"Nova Vaga:\n\n {titulo}\n Emrpeda: {empresa}\n {link}"
                        enviar_mensagem_telegram(texto_alerta)
                    else:
                        print(f"Já existia na BD: {titulo} | {empresa}")
                    time.sleep(1)
                else:
                    print(f"[DESCRIÇÃO] Rejeitei '{titulo}' por causa da palavra: '{palavra_culpada_desc}'")

            except Exception as e:
                print(f"Erro ao analisar a vaga {titulo}: {e}")
        
        if vagas_reais_na_pagina == 0:
            print(f"Fim da linha! A página {pagina_atual} já não tinha vagas verdadeiras.")
            break

        pagina_atual += 1
        time.sleep(2)


    conn.commit()
    cur.close()
    conn.close()

    print(f"\nConcluído! Lemos {pagina_atual - 1} páginas e guardámos {novas_vagas} novas vagas na Base de Dados e enviamos para o telegram.")

def enviar_mensagem_telegram(mesagem):
    if not TOKEN or not CHAT_ID:
        print("Falta o token ou o od do telegram")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    dados = {
        "chat_id": CHAT_ID,
        "text": mesagem
    }

    try:
        requests.post(url, data=dados)
    except Exception as e:
        print(f"Erro ao contactar o Telegram: {e}")

if __name__ == "__main__":
    iniciar_db()
    enviar_mensagem_telegram("O Bot começou a procurar vagas")
    
    
    while True:
        try:
            procurar_vagas()
            time.sleep(43200)
        except Exception as e:
            print(f"Acorreu um erro fatal: {e}")
            enviar_mensagem_telegram("O Boi foi abaixo com um erro")
            time.sleep(60)
    
