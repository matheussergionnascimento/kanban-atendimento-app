import os
import json
from datetime import datetime
from openai import OpenAI
import pymysql

# Inicializa o cliente da OpenAI
cliente = OpenAI()

# Configurações de Ligação à Base de Dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "m02041996M.",  # A sua senha do MySQL
    "database": "kanban_ia_db",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def processar_mensagem_para_kanban(mensagem_bruta):
    data_atual_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt_sistema = f"""
    Você é um assistente de IA avançado especializado em gestão de projetos corporativos e metodologias ágeis (Kanban).
    Sua missão é ler mensagens de texto informais (áudios de WhatsApp, notas de reuniões de fábrica ou apontamentos rápidos) 
    e extrair tarefas estruturadas em formato JSON estrito, prontas para um ambiente empresarial.
    
    Data e hora atual de referência: {data_atual_str}
    
    Cada tarefa extraída deve conter exatamente as seguintes chaves:
    - "titulo": Uma descrição clara, objetiva e profissional da tarefa.
    - "status": Obrigatoriamente um destes valores: "A Fazer", "Em Andamento", "Bloqueado" ou "Concluído".
    - "responsavel": O nome da pessoa mencionada ou "Equipe" se não for especificado.
    - "prazo": Converta qualquer menção temporal (como "amanhã", "sexta-feira", "daqui a dois dias") numa data e hora absoluta no formato estrito do MySQL "AAAA-MM-DD HH:MM:SS" (Ex: "2026-10-03 08:00:00"). Se nenhum horário for especificado, assuma "08:00:00". Se não houver prazo nenhum, defina null.
    - "prioridade": O nível de urgência inferido: "Baixa", "Média", "Alta" ou "Urgente".
    - "categoria": A área provável da tarefa (ex: "Manutenção", "Administrativo", "Produção", "Qualidade" ou "Geral").
    
    Retorne APENAS um array JSON contendo as tarefas encontradas. Não adicione textos explicativos fora do JSON.
    """

    try:
        resposta = cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensagem_bruta}
            ],
            temperature=0.3
        )
        
        conteudo = resposta.choices[0].message.content
        conteudo_limpo = conteudo.replace("```json", "").replace("```", "").strip()
        return json.loads(conteudo_limpo)
        
    except Exception as e:
        return {"erro": str(e)}

def salvar_tarefas_mysql(novas_tarefas, empresa_id=1):
    conexao = pymysql.connect(**DB_CONFIG)

    try:
        with conexao.cursor() as cursor:
            sql = """
                INSERT INTO tarefas (empresa_id, titulo, status, responsavel, prazo, prioridade, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            if not isinstance(novas_tarefas, list):
                novas_tarefas = [novas_tarefas]

            for tarefa in novas_tarefas:
                if "erro" in tarefa:
                    print(f"Erro gerado pela IA: {tarefa['erro']}")
                    continue
                    
                cursor.execute(sql, (
                    empresa_id,
                    tarefa.get("titulo"),
                    tarefa.get("status", "A Fazer"),
                    tarefa.get("responsavel", "Equipe"),
                    tarefa.get("prazo"),  # Já vai no formato YYYY-MM-DD HH:MM:SS ou null
                    tarefa.get("prioridade", "Média"),
                    tarefa.get("categoria", "Geral")
                ))
            
            conexao.commit()
            print("\n[Sucesso] Tarefas guardadas e estruturadas no MySQL com sucesso!")
            
    finally:
        conexao.close()

def obter_kpis_e_metricas(empresa_id=1):
    """
    Função de tratamento de dados analíticos (KPIs) pronta para alimentar gráficos 
    e dashboards gerenciais do cliente.
    """
    conexao = pymysql.connect(**DB_CONFIG)
    metricas = {}
    
    try:
        with conexao.cursor() as cursor:
            # 1. Contagem por Status (Ideal para gráficos de Rosca/Pizza)
            cursor.execute("SELECT status, COUNT(*) as total FROM tarefas WHERE empresa_id = %s GROUP BY status", (empresa_id,))
            metricas["por_status"] = cursor.fetchall()
            
            # 2. Contagem por Prioridade (Ideal para gráficos de Alerta/Urgência)
            cursor.execute("SELECT prioridade, COUNT(*) as total FROM tarefas WHERE empresa_id = %s GROUP BY prioridade", (empresa_id,))
            metricas["por_prioridade"] = cursor.fetchall()
            
            # 3. Carga de Trabalho por Responsável (Ideal para gráficos de Barras)
            cursor.execute("SELECT responsavel, COUNT(*) as total FROM tarefas WHERE empresa_id = %s GROUP BY responsavel", (empresa_id,))
            metricas["por_responsavel"] = cursor.fetchall()
            
        return metricas
    finally:
        conexao.close()

if __name__ == "__main__":
    try:
        with open("entrada.txt", "r", encoding="utf-8") as f:
            texto_bruto = f.read()
            
        print("Processando notas informais para a base corporativa...")
        resultado = processar_mensagem_para_kanban(texto_bruto)
        
        print("\n--- JSON ESTRUTURADO PELA IA ---")
        print(json.dumps(resultado, indent=4, ensure_ascii=False))
        
        # Grava na base de dados
        salvar_tarefas_mysql(resultado, empresa_id=1)
        
        # Testa a extração de KPIs analíticos para futuros gráficos
        print("\n--- KPIs / MÉTRICAS ANALÍTICAS PARA GRÁFICOS ---")
        kpis = obter_kpis_e_metricas(empresa_id=1)
        print(json.dumps(kpis, indent=4, ensure_ascii=False))
        
    except FileNotFoundError:
        print("Erro: O ficheiro 'entrada.txt' não foi encontrado.")