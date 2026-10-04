import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import altair as alt
import io

# Configuração da página
st.set_page_config(
    page_title="Gestão de Tarefas e Atendimento", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS Customizado Corporativo e Profissional
st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #0f172a !important;
    }
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }
    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 2rem !important;
        font-weight: 600;
    }
    hr {
        border-color: #e2e8f0;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Função para ligar à base de dados MySQL
def obter_conexao():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="m02041996M.",
        database="kanban_ia_db"
    )

# Garantir existência das tabelas necessárias
def inicializar_tabelas():
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comentarios_tarefa (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tarefa_id INT,
                autor VARCHAR(100),
                comentario TEXT,
                data_criacao DATETIME
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mensagens_whatsapp (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_nome VARCHAR(150),
                telefone VARCHAR(50),
                mensagem TEXT,
                remetente VARCHAR(50),
                data_envio DATETIME
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass

inicializar_tabelas()

# Menu Lateral de Navegação e Controlo de Acesso
with st.sidebar:
    st.markdown("### Painel Operacional")
    st.markdown("<br>", unsafe_allow_html=True)
    
    perfil_usuario = st.selectbox(
        "Perfil de Acesso",
        ["Administrador", "Gestor", "Supervisor", "Atendente"]
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    opcoes_menu = ["Dashboard", "Quadro Kanban", "Atendimento WhatsApp", "Busca Global e Relatórios"]
    
    if perfil_usuario == "Atendente":
        opcoes_menu = ["Quadro Kanban", "Atendimento WhatsApp", "Busca Global e Relatórios"]
    elif perfil_usuario == "Supervisor":
        opcoes_menu = ["Quadro Kanban", "Atendimento WhatsApp", "Busca Global e Relatórios"]
    
    menu_opcao = st.radio(
        "Navegação",
        opcoes_menu,
        label_visibility="collapsed"
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### Filtros Globais")
    
    filtro_periodo = st.selectbox(
        "Período",
        ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Período Personalizado"]
    )
    
    paleta_cores = st.selectbox(
        "Paleta de Cores",
        ["Azul Corporativo", "Grafite Industrial", "Verde Operacional"]
    )
    
    mapa_cores = {
        "Azul Corporativo": "#0284c7",
        "Grafite Industrial": "#334155",
        "Verde Operacional": "#0d9488"
    }
    cor_selecionada = mapa_cores[paleta_cores]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(f"Utilizador: Matheus | Nível: {perfil_usuario}")

# Carregar dados do MySQL com segurança
try:
    conexao = obter_conexao()
    query = "SELECT id, titulo, status, responsavel, prazo, prioridade, categoria FROM tarefas WHERE empresa_id = 1"
    df_tarefas = pd.read_sql(query, conexao)
    conexao.close()
except Exception as e:
    st.error(f"Erro ao ligar à base de dados MySQL: {e}")
    df_tarefas = pd.DataFrame()

# Lógica dos Ecrãs
if menu_opcao == "Dashboard":
    st.title("Painel Executivo de Indicadores")
    st.markdown("Monitorização em tempo real do fluxo operacional, cargas de trabalho e cumprimento de SLA.")
    st.markdown("---")

    if df_tarefas.empty:
        st.warning("Não existem tarefas registadas na base de dados para esta empresa.")
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        total_tarefas = len(df_tarefas)
        concluidas = len(df_tarefas[df_tarefas['status'] == 'Concluído'])
        em_andamento = len(df_tarefas[df_tarefas['status'] == 'Em andamento'])
        aguardando = len(df_tarefas[df_tarefas['status'].str.contains('Aguardando', na=False)])
        canceladas = len(df_tarefas[df_tarefas['status'] == 'Cancelado'])
        
        col1.metric("Total", total_tarefas)
        col2.metric("Concluídos", concluidas)
        col3.metric("Em Andamento", em_andamento)
        col4.metric("Aguardando", aguardando)
        col5.metric("Cancelados", canceladas)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### Carga de Trabalho por Responsável")
            df_resp = df_tarefas['responsavel'].value_counts().reset_index()
            df_resp.columns = ['Responsável', 'Total']
            st.bar_chart(df_resp.set_index('Responsável'), color=cor_selecionada)
            st.caption("Distribuição do volume de tarefas ativas por colaborador.")
            
        with col_g2:
            st.markdown("#### Distribuição por Prioridade e SLA")
            df_prio = df_tarefas['prioridade'].value_counts().reset_index()
            df_prio.columns = ['Prioridade', 'Total']
            st.bar_chart(df_prio.set_index('Prioridade'), horizontal=True, color=cor_selecionada)
            st.caption("Classificação volumétrica baseada no grau de urgência das solicitações.")

elif menu_opcao == "Quadro Kanban":
    st.title("Quadro Operacional Kanban")
    st.markdown("Gestão avançada do fluxo de trabalho, prazos/SLA e painel de discussão interna por tarefa.")
    st.markdown("---")

    with st.expander("Registar Nova Tarefa / Atendimento"):
        with st.form("form_nova_tarefa", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                novo_titulo = st.text_input("Título / Descrição resumida")
                novo_responsavel = st.text_input("Responsável Atribuído")
            with f_col2:
                novo_status = st.selectbox("Status", ["A Fazer", "Em andamento", "Aguardando cliente", "Aguardando setor", "Concluído", "Cancelado"])
                nova_prioridade = st.selectbox("Prioridade", ["Urgente", "Alta", "Média", "Baixa"])
            with f_col3:
                data_prazo = st.date_input("Data Limite (SLA)")
                hora_prazo = st.time_input("Hora Limite")
                
            btn_criar = st.form_submit_button("Guardar Registo")
            if btn_criar:
                if novo_titulo.strip() == "":
                    st.warning("O título da tarefa é obrigatório.")
                else:
                    try:
                        prazo_completo = datetime.combine(data_prazo, hora_prazo)
                        conn_ins = obter_conexao()
                        cursor = conn_ins.cursor()
                        sql_insert = """
                            INSERT INTO tarefas (empresa_id, titulo, status, responsavel, prazo, prioridade, categoria)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_insert, (1, novo_titulo, novo_status, novo_responsavel, prazo_completo, nova_prioridade, "Geral"))
                        conn_ins.commit()
                        cursor.close()
                        conn_ins.close()
                        st.success("Registo criado com sucesso!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao inserir na base de dados: {err}")

    st.markdown("<br>", unsafe_allow_html=True)

    if df_tarefas.empty:
        st.warning("Não existem tarefas registadas.")
    else:
        cols_kanban = st.columns(6)
        statuses = [
            "A Fazer", 
            "Em andamento", 
            "Aguardando cliente", 
            "Aguardando setor", 
            "Concluído", 
            "Cancelado"
        ]
        
        cores_prioridade = {
            "Urgente": "#991b1b",
            "Alta": "#ef4444",
            "Média": "#f59e0b",
            "Baixa": "#10b981"
        }
        
        for i, status_nome in enumerate(statuses):
            with cols_kanban[i]:
                st.markdown(
                    f"<div style='background-color: #e2e8f0; padding: 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; color: #0f172a; margin-bottom: 10px; text-align: center;'>{status_nome}</div>", 
                    unsafe_allow_html=True
                )
                
                tarefas_coluna = df_tarefas[df_tarefas['status'].str.lower() == status_nome.lower()]
                
                if tarefas_coluna.empty:
                    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.75rem; font-style: italic;'>Sem registos</p>", unsafe_allow_html=True)
                
                for _, tarefa in tarefas_coluna.iterrows():
                    with st.container(border=True):
                        prio = str(tarefa['prioridade']).strip()
                        cor_etiqueta = cores_prioridade.get(prio, "#0284c7")
                        
                        st.markdown(
                            f"<span style='background-color: {cor_etiqueta}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;'>{prio}</span>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"**{tarefa['titulo']}**")
                        st.caption(f"ID: #{tarefa['id']} | Resp: {tarefa['responsavel']}")
                        
                        if pd.notna(tarefa['prazo']):
                            try:
                                data_convertida = pd.to_datetime(tarefa['prazo'])
                                st.text(f"SLA: {data_convertida.strftime('%d/%m %H:%M')}")
                            except Exception:
                                pass

        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.subheader("Gestão e Comentários Internos por Tarefa")
        st.markdown("Selecione uma tarefa pelo ID para visualizar os detalhes e debater notas internamente com a equipa.")

        tarefa_ids = df_tarefas['id'].tolist()
        tarefa_selecionada_id = st.selectbox("Escolher Tarefa (ID e Título)", options=tarefa_ids, format_func=lambda x: f"ID #{x} — {df_tarefas[df_tarefas['id'] == x]['titulo'].values[0]}")

        if tarefa_selecionada_id:
            tarefa_dados = df_tarefas[df_tarefas['id'] == tarefa_selecionada_id].iloc[0]
            
            col_det1, col_det2 = st.columns(2)
            with col_det1:
                st.markdown(f"**Título:** {tarefa_dados['titulo']}")
                st.markdown(f"**Responsável Atual:** {tarefa_dados['responsavel']}")
                st.markdown(f"**Status Atual:** {tarefa_dados['status']}")
            with col_det2:
                st.markdown(f"**Prioridade:** {tarefa_dados['prioridade']}")
                st.markdown(f"**Prazo/SLA:** {tarefa_dados['prazo']}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Histórico de Comentários Internos (Notas da Equipa)")
            
            try:
                conn_c = obter_conexao()
                query_c = f"SELECT autor, comentario, data_criacao FROM comentarios_tarefa WHERE tarefa_id = {tarefa_selecionada_id} ORDER BY data_criacao DESC"
                df_comentarios = pd.read_sql(query_c, conn_c)
                conn_c.close()
            except Exception:
                df_comentarios = pd.DataFrame()

            if df_comentarios.empty:
                st.info("Ainda não existem comentários internos registados para esta tarefa.")
            else:
                for _, com in df_comentarios.iterrows():
                    st.markdown(f"> **{com['autor']}** ({com['data_criacao']}):\n> {com['comentario']}")
                    st.markdown("---")

            with st.form(f"form_comentario_{tarefa_selecionada_id}", clear_on_submit=True):
                novo_comentario = st.text_area("Adicionar Nota Interna (visível apenas para a equipa)")
                autor_comentario = st.text_input("Seu Nome / Autor", value="Matheus")
                btn_enviar_comentario = st.form_submit_button("Guardar Comentário")
                
                if btn_enviar_comentario:
                    if novo_comentario.strip() == "":
                        st.warning("O texto do comentário não pode estar vazio.")
                    else:
                        try:
                            conn_ins_c = obter_conexao()
                            cursor_c = conn_ins_c.cursor()
                            sql_ins_c = "INSERT INTO comentarios_tarefa (tarefa_id, autor, comentario, data_criacao) VALUES (%s, %s, %s, %s)"
                            cursor_c.execute(sql_ins_c, (tarefa_selecionada_id, autor_comentario, novo_comentario, datetime.now()))
                            conn_ins_c.commit()
                            cursor_c.close()
                            conn_ins_c.close()
                            st.success("Comentário interno guardado com sucesso!")
                            st.rerun()
                        except Exception as e_com:
                            st.error(f"Erro ao guardar comentário: {e_com}")

elif menu_opcao == "Atendimento WhatsApp":
    st.title("Central de Atendimento WhatsApp")
    st.markdown("Módulo ativo de gestão de conversas com clientes e conversão direta em tickets operacionais.")
    st.markdown("---")

    try:
        conn_w = obter_conexao()
        df_whats = pd.read_sql("SELECT DISTINCT cliente_nome, telefone FROM mensagens_whatsapp", conn_w)
        conn_w.close()
    except Exception:
        df_whats = pd.DataFrame()

    col_w1, col_w2 = st.columns([1, 2])

    with col_w1:
        st.subheader("Conversas Ativas")
        
        with st.expander("Simular Novo Cliente / Mensagem"):
            with st.form("form_novo_cliente_w"):
                cli_nome = st.text_input("Nome do Cliente")
                cli_tel = st.text_input("Telefone (Ex: 48999998888)")
                cli_msg = st.text_area("Mensagem Inicial")
                btn_simular = st.form_submit_button("Receber Mensagem")
                
                if btn_simular:
                    if cli_nome.strip() == "" or cli_msg.strip() == "":
                        st.warning("Preencha o nome e a mensagem.")
                    else:
                        try:
                            conn_ins_w = obter_conexao()
                            cursor_w = conn_ins_w.cursor()
                            cursor_w.execute(
                                "INSERT INTO mensagens_whatsapp (cliente_nome, telefone, mensagem, remetente, data_envio) VALUES (%s, %s, %s, %s, %s)",
                                (cli_nome, cli_tel, cli_msg, "Cliente", datetime.now())
                            )
                            conn_ins_w.commit()
                            cursor_w.close()
                            conn_ins_w.close()
                            st.success("Mensagem recebida com sucesso!")
                            st.rerun()
                        except Exception as e_w:
                            st.error(f"Erro: {e_w}")

        if df_whats.empty:
            st.info("Nenhuma conversa registada. Simule uma nova mensagem acima.")
            cliente_selecionado = None
        else:
            lista_clientes = df_whats['cliente_nome'].tolist()
            cliente_selecionado = st.selectbox("Selecionar Cliente", options=lista_clientes)

    with col_w2:
        if cliente_selecionado:
            st.subheader(f"Chat com: {cliente_selecionado}")
            
            try:
                conn_hist = obter_conexao()
                query_hist = f"SELECT mensagem, remetente, data_envio FROM mensagens_whatsapp WHERE cliente_nome = '{cliente_selecionado}' ORDER BY data_envio ASC"
                df_hist = pd.read_sql(query_hist, conn_hist)
                conn_hist.close()
            except Exception:
                df_hist = pd.DataFrame()

            chat_container = st.container(height=350)
            with chat_container:
                for _, row in df_hist.iterrows():
                    rem = row['remetente']
                    msg = row['mensagem']
                    data_m = row['data_envio']
                    if rem == "Cliente":
                        st.markdown(f"**{cliente_selecionado}** ({data_m}):\n{msg}")
                    else:
                        st.markdown(f"**Atendente (Equipa)** ({data_m}):\n{msg}")
                    st.markdown("---")

            with st.form("form_resposta_chat", clear_on_submit=True):
                resposta_texto = st.text_input("Escrever resposta ao cliente...")
                btn_enviar_resposta = st.form_submit_button("Enviar Mensagem")
                
                if btn_enviar_resposta:
                    if resposta_texto.strip() != "":
                        try:
                            tel_cliente = df_whats[df_whats['cliente_nome'] == cliente_selecionado]['telefone'].values[0]
                            conn_resp = obter_conexao()
                            cursor_resp = conn_resp.cursor()
                            cursor_resp.execute(
                                "INSERT INTO mensagens_whatsapp (cliente_nome, telefone, mensagem, remetente, data_envio) VALUES (%s, %s, %s, %s, %s)",
                                (cliente_selecionado, tel_cliente, resposta_texto, "Atendente", datetime.now())
                            )
                            conn_resp.commit()
                            cursor_resp.close()
                            conn_resp.close()
                            st.rerun()
                        except Exception as err_r:
                            st.error(f"Erro ao enviar resposta: {err_r}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Converter Conversa em Tarefa no Kanban"):
                try:
                    ultima_msg = df_hist.iloc[-1]['mensagem'] if not df_hist.empty else f"Atendimento WhatsApp - {cliente_selecionado}"
                    conn_conv = obter_conexao()
                    cursor_conv = conn_conv.cursor()
                    sql_conv = """
                        INSERT INTO tarefas (empresa_id, titulo, status, responsavel, prazo, prioridade, categoria)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor_conv.execute(sql_conv, (1, f"Cliente: {cliente_selecionado} - {ultima_msg[:40]}...", "A Fazer", "Equipe Atendimento", datetime.now() + timedelta(days=1), "Alta", "WhatsApp"))
                    conn_conv.commit()
                    cursor_conv.close()
                    conn_conv.close()
                    st.success(f"Conversa com {cliente_selecionado} convertida com sucesso numa tarefa no quadro Kanban!")
                except Exception as ex_c:
                    st.error(f"Erro ao converter: {ex_c}")

elif menu_opcao == "Busca Global e Relatórios":
    st.title("Busca Global e Relatórios Executivos")
    st.markdown("Pesquisa transversal de registos e exportação de relatórios consolidados.")
    st.markdown("---")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        termo_busca = st.text_input("Pesquisa Global (Título, Responsável, ID ou Categoria)")
    with col_s2:
        filtro_status_busca = st.selectbox("Filtrar por Status no Resultado", ["Todos", "A Fazer", "Em andamento", "Aguardando cliente", "Aguardando setor", "Concluído", "Cancelado"])

    if not df_tarefas.empty:
        df_filtrado = df_tarefas.copy()
        
        if termo_busca:
            mask = df_filtrado.apply(lambda row: row.astype(str).str.contains(termo_busca, case=False).any(), axis=1)
            df_filtrado = df_filtrado[mask]
            
        if filtro_status_busca != "Todos":
            df_filtrado = df_filtrado[df_filtrado['status'].str.lower() == filtro_status_busca.lower()]
            
        st.markdown(f"**Resultados encontrados:** {len(df_filtrado)} registos")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.subheader("Exportação de Relatórios Executivos")
        st.markdown("Gere e descarregue relatórios consolidados em formato Excel para análise gerencial.")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_tarefas.to_excel(writer, index=False, sheet_name='Relatorio_Geral')
        processed_data = output.getvalue()
        
        st.download_button(
            label="Descarregar Relatório Completo em Excel (.xlsx)",
            data=processed_data,
            file_name=f"relatorio_executivo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Não existem dados disponíveis para pesquisa ou exportação.")