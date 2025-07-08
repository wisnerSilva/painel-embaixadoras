import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import datetime
import time
import numpy as np

hide_streamlit_style = """
    <style>
        #MainMenu { visibility: hidden; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Configurações da página
st.set_page_config(
    page_title="Painel Embaixadoras",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração do Supabase
SUPABASE_URL = "https://vfxxifttzhwusaqvqohn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZmeHhpZnR0emh3dXNhcXZxb2huIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODYyNzM4NCwiZXhwIjoyMDY0MjAzMzg0fQ.5aGbDKaxw3IrUx_5Bop3aso-lVVDIikMK1l0QtP6j08"
SUPABASE_TABLE = 'resultados_embaixadoras'

# Inicializar o cliente Supabase
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Função para buscar dados do Supabase
@st.cache_data(ttl=0)
def fetch_data(email):
    response = supabase.table(SUPABASE_TABLE).select("*").eq("email", email).order("mes").execute()
    return pd.DataFrame(response.data)

# Função para formatar o mês
def formatar_mes(dt):
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"{meses[dt.month - 1]} {dt.year}"

# Função para gerar meses em ordem cronológica
def gerar_meses_cronologicos():
    hoje = datetime.datetime.now()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Lista de todos os meses do ano atual em ordem cronológica
    meses = []
    for mes in range(1, mes_atual + 1):
        meses.append(datetime.datetime(ano_atual, mes, 1))
    
    return meses

# Tela de login
def login_screen():
    st.title("📊 Painel Embaixadoras")
    st.image("https://www.queimadiaria.com.br/assets/img/icons/thumb-qd-logo.png", width=200)
    st.subheader("Por favor, faça login para acessar o dashboard")
    
    with st.form(key='login_form'):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Fazer Login")
        
        if submitted:
            if email and password:
                st.session_state['authenticated'] = True
                st.session_state['user_email'] = email
                st.success("Login realizado com sucesso!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Por favor, preencha e-mail e senha")

# Dashboard principal
def main_dashboard():
    # Topbar
    st.markdown(
        f"""
        <style>
        .topbar {{
            background-color: #67BCBF;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            z-index: 1000;
        }}
        .topbar-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.2rem;
            font-weight: 600;
        }}
        .topbar-welcome {{
            font-size: 0.95rem;
        }}
        .topbar-logout {{
            background: transparent;
            border: 1px solid rgba(255,255,255,0.4);
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
        }}
        .topbar-logout:hover {{
            background: rgba(255,255,255,0.1);
        }}
        </style>
        <div class="topbar">
            <div class="topbar-logo">
                <i class="fas fa-chart-line"></i>
                <span>Embaixadoras</span>
            </div>
            <div class="topbar-welcome">
                Bem-vindo, <strong>{st.session_state['user_email']}</strong>
            </div>
            <a class="topbar-logout" href="?logout=true">Sair</a>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Adicionar Font Awesome
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">',
        unsafe_allow_html=True
    )
    
    # Espaço para a topbar
    st.markdown("<div style='height: 70px;'></div>", unsafe_allow_html=True)
    
    # Título da página
    st.header("Dashboard de Desempenho")
    st.caption("Análise de sessões e vendas das embaixadoras")
    
    # Carregar dados
    with st.spinner('Carregando dados...'):
        df = fetch_data(st.session_state['user_email'])
        
        if df.empty:
            st.warning("Nenhum dado encontrado para este usuário.")
            return
            
        # Converter a coluna 'mes' para datetime
        df['mes'] = pd.to_datetime(df['mes'])
        
        # Agrupar por mês e tipo
        df_grouped = df.groupby(['mes', 'tipo']).agg({'valor': 'sum'}).reset_index()
        
        # Pivot para ter sessões e vendas em colunas separadas
        df_pivot = df_grouped.pivot(index='mes', columns='tipo', values='valor').reset_index()
        df_pivot.fillna(0, inplace=True)
        
        # Garantir que as colunas necessárias existem
        if 'Vendas' not in df_pivot.columns:
            df_pivot['Vendas'] = 0
        if 'Sessões' not in df_pivot.columns:
            df_pivot['Sessões'] = 0
        
        # Manter apenas meses com sessões OU vendas > 0
        df_pivot = df_pivot[(df_pivot['Sessões'] > 0) | (df_pivot['Vendas'] > 0)]
        
        if df_pivot.empty:
            st.warning("Nenhum dado positivo encontrado para este usuário.")
            return
        
        # Calcular a taxa de conversão com tratamento seguro
        df_pivot['Taxa de Conversão'] = df_pivot.apply(
            lambda row: (row['Vendas'] / row['Sessões']) * 100 if row['Sessões'] > 0 else 0,
            axis=1
        )
        df_pivot['Taxa de Conversão'] = df_pivot['Taxa de Conversão'].round(1)
        
        # Ordenar por mês (ordem cronológica)
        df_pivot = df_pivot.sort_values('mes')
        
        # Calcular variação percentual da taxa de conversão
        df_pivot['Variação Percentual'] = df_pivot['Taxa de Conversão'].pct_change() * 100
        df_pivot['Variação Percentual'] = df_pivot['Variação Percentual'].fillna(0).round(1)
        
        # GERAR TODOS OS MESES DO ANO ATUAL EM ORDEM CRONOLÓGICA
        todos_meses = gerar_meses_cronologicos()
        meses_formatados = [formatar_mes(m) for m in todos_meses]
        meses_dict = {formatar_mes(m): m for m in todos_meses}
        
    # Filtro de mês
    col1, col2 = st.columns([0.7, 0.3])
    with col2:
        # Selecionar o último mês como padrão
        default_index = len(meses_formatados) - 1 if meses_formatados else 0
        mes_selecionado = st.selectbox(
            "Selecione o mês:",
            options=meses_formatados,
            index=default_index
        )
    
    # Cards de resumo
    st.subheader("Resumo")
    col1, col2, col3 = st.columns(3)
    
    # Filtrar dados para o mês selecionado
    mes_data = meses_dict[mes_selecionado]
    dados_mes = df_pivot[df_pivot['mes'] == mes_data]
    
    # Valores padrão se não houver dados
    sessoes = 0
    vendas = 0
    taxa = 0
    variacao = 0
    
    if not dados_mes.empty:
        dados_mes = dados_mes.iloc[0]
        sessoes = int(dados_mes['Sessões'])
        vendas = int(dados_mes['Vendas'])
        taxa = dados_mes['Taxa de Conversão']
        variacao = dados_mes.get('Variação Percentual', 0)
    
    with col1:
        st.metric(
            label="SESSÕES REALIZADAS",
            value=sessoes,
            help=f"Total de sessões em {mes_selecionado}"
        )
    
    with col2:
        st.metric(
            label="VENDAS CONCLUÍDAS",
            value=vendas,
            help=f"Total de vendas em {mes_selecionado}"
        )
    
    with col3:
        delta_value = f"{variacao}%" if variacao != 0 else None
        st.metric(
            label="TAXA DE CONVERSÃO",
            value=f"{taxa}%" if sessoes > 0 else "0%",
            delta=delta_value,
            delta_color="normal",
            help=f"Taxa de conversão em {mes_selecionado}"
        )
    
    # Histórico mensal - AGORA EM ORDEM CRONOLÓGICA
    st.subheader("Histórico Mensal")
    
    # Criar DataFrame com todos os meses em ordem cronológica
    historico_completo = []
    for mes in todos_meses:
        mes_formatado = formatar_mes(mes)
        dados = df_pivot[df_pivot['mes'] == mes]
        
        if not dados.empty:
            linha = dados.iloc[0]
            historico_completo.append({
                'Mês/Ano': mes_formatado,
                'Sessões': int(linha['Sessões']),
                'Vendas': int(linha['Vendas']),
                'Taxa de Conversão': linha['Taxa de Conversão'],
                'Variação Percentual': linha.get('Variação Percentual', 0)
            })
        else:
            historico_completo.append({
                'Mês/Ano': mes_formatado,
                'Sessões': 0,
                'Vendas': 0,
                'Taxa de Conversão': 0,
                'Variação Percentual': 0
            })
    
    df_historico = pd.DataFrame(historico_completo)
    
    # Calcular totais apenas dos meses com dados
    meses_com_dados = df_pivot[['Sessões', 'Vendas']]
    total_sessoes = int(meses_com_dados['Sessões'].sum())
    total_vendas = int(meses_com_dados['Vendas'].sum())
    taxa_geral = (total_vendas / total_sessoes * 100) if total_sessoes > 0 else 0
    
    # Exibir tabela em ordem cronológica
    st.dataframe(
        df_historico,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Taxa de Conversão": st.column_config.NumberColumn(format="%.1f%%"),
            "Variação Percentual": st.column_config.NumberColumn(format="%.1f%%")
        }
    )
    
    # Totais
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: -10px;">
        <strong>Total Geral:</strong> 
        Sessões: {total_sessoes} | 
        Vendas: {total_vendas} | 
        Taxa: {taxa_geral:.1f}%
    </div>
    """, unsafe_allow_html=True)
    
    # Gráficos - AGORA EM ORDEM CRONOLÓGICA
    st.subheader("Análise Gráfica")
    
    # Preparar dados completos para gráficos em ordem cronológica
    dados_graficos = []
    for mes in todos_meses:
        mes_formatado = mes.strftime('%b/%Y')
        dados = df_pivot[df_pivot['mes'] == mes]
        
        if not dados.empty:
            linha = dados.iloc[0]
            dados_graficos.append({
                'mes': mes,
                'Mes_Formatado': mes_formatado,
                'Sessões': linha['Sessões'],
                'Vendas': linha['Vendas'],
                'Taxa de Conversão': linha['Taxa de Conversão'],
                'Variação Percentual': linha.get('Variação Percentual', 0)
            })
        else:
            dados_graficos.append({
                'mes': mes,
                'Mes_Formatado': mes_formatado,
                'Sessões': 0,
                'Vendas': 0,
                'Taxa de Conversão': 0,
                'Variação Percentual': 0
            })
    
    df_graficos = pd.DataFrame(dados_graficos)
    
    # Criar os 4 gráficos em ordem cronológica
    col1, col2 = st.columns(2)
    
    # Gráfico 1: Sessões
    with col1:
        fig1 = px.bar(
            df_graficos,
            x='Mes_Formatado',
            y='Sessões',
            labels={'Sessões': 'Quantidade', 'Mes_Formatado': 'Mês'},
            title='SESSÕES REALIZADAS',
            color_discrete_sequence=['#FF4F00'],
            text_auto=True
        )
        fig1.update_layout(
            xaxis_title='',
            yaxis_title='Quantidade de Sessões',
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Vendas
    with col2:
        fig2 = px.bar(
            df_graficos,
            x='Mes_Formatado',
            y='Vendas',
            labels={'Vendas': 'Quantidade', 'Mes_Formatado': 'Mês'},
            title='VENDAS CONCLUÍDAS',
            color_discrete_sequence=['#67BCBF'],
            text_auto=True
        )
        fig2.update_layout(
            xaxis_title='',
            yaxis_title='Quantidade de Vendas',
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    # Gráfico 3: Taxa de conversão
    with col3:
        fig3 = px.line(
            df_graficos,
            x='Mes_Formatado',
            y='Taxa de Conversão',
            labels={'Taxa de Conversão': 'Taxa (%)', 'Mes_Formatado': 'Mês'},
            title='TAXA DE CONVERSÃO',
            markers=True,
            color_discrete_sequence=['#FFD700'],
            text=df_graficos['Taxa de Conversão'].apply(lambda x: f"{x}%" if x > 0 else "")
        )
        fig3.update_traces(textposition="top center")
        fig3.update_layout(
            xaxis_title='',
            yaxis_title='Taxa de Conversão (%)',
            yaxis=dict(ticksuffix='%')
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Gráfico 4: Variação percentual
    with col4:
        fig4 = px.bar(
            df_graficos,
            x='Mes_Formatado',
            y='Variação Percentual',
            labels={'Variação Percentual': 'Variação (%)', 'Mes_Formatado': 'Mês'},
            title='VARIAÇÃO PERCENTUAL DA TAXA DE CONVERSÃO',
            color='Variação Percentual',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            range_color=[-100, 100],
            text=df_graficos['Variação Percentual'].apply(lambda x: f"{x:.1f}%" if x != 0 else "")
        )
        fig4.update_layout(
            xaxis_title='',
            yaxis_title='Variação (%)',
            yaxis=dict(ticksuffix='%'),
            coloraxis_showscale=False
        )
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)
    
    # Rodapé
    st.markdown("---")
    st.caption("Painel Embaixadoras © 2023 - Todos os direitos reservados")

# Página principal
def main():
    # Verificar logout
    if "logout" in st.query_params:
        st.session_state.clear()
        st.query_params.clear()
        st.success("Você foi desconectado com sucesso!")
        time.sleep(1)
        st.rerun()
    
    # Verificar autenticação
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        login_screen()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
