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
@st.cache_data(ttl=0)  # Cache desativado para testes de atualização
def fetch_data(email):
    response = supabase.table(SUPABASE_TABLE).select("*").eq("email", email).gt("valor", 0).order("mes").execute()
    return pd.DataFrame(response.data)

# Função para formatar o mês (ajustada para lidar com datetime)
def formatar_mes(dt):
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"{meses[dt.month - 1]} {dt.year}"

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
        
        # Calcular a taxa de conversão com tratamento para divisão por zero
        df_pivot['Taxa de Conversão'] = df_pivot.apply(
            lambda row: (row['Vendas'] / row['Sessões']) * 100 if row['Sessões'] > 0 else 0,
            axis=1
        )
        df_pivot['Taxa de Conversão'] = df_pivot['Taxa de Conversão'].round(1)
        
        # Ordenar por mês
        df_pivot = df_pivot.sort_values('mes')
        
        # Calcular variação percentual da taxa de conversão
        df_pivot['Variação Percentual'] = df_pivot['Taxa de Conversão'].pct_change() * 100
        df_pivot['Variação Percentual'] = df_pivot['Variação Percentual'].fillna(0).round(1)
        
        # Lista de meses para seleção
        meses_disponiveis = df_pivot['mes'].unique()
        meses_formatados = [formatar_mes(m) for m in meses_disponiveis]
        meses_dict = dict(zip(meses_formatados, meses_disponiveis))
        
    # Filtro de mês
    col1, col2 = st.columns([0.7, 0.3])
    with col2:
        mes_selecionado = st.selectbox(
            "Selecione o mês:",
            options=meses_formatados,
            index=len(meses_formatados)-1
        )
    
    # Cards de resumo
    st.subheader("Resumo")
    col1, col2, col3 = st.columns(3)
    
    # Filtrar dados para o mês selecionado
    dados_mes = df_pivot[df_pivot['mes'] == meses_dict[mes_selecionado]].iloc[0]
    
    with col1:
        st.metric(
            label="SESSÕES REALIZADAS",
            value=int(dados_mes['Sessões']),
            help=f"Total de sessões em {mes_selecionado}"
        )
    
    with col2:
        st.metric(
            label="VENDAS CONCLUÍDAS",
            value=int(dados_mes['Vendas']),
            help=f"Total de vendas em {mes_selecionado}"
        )
    
    with col3:
        st.metric(
            label="TAXA DE CONVERSÃO",
            value=f"{dados_mes['Taxa de Conversão']}%",
            delta=f"{dados_mes['Variação Percentual']}%" if 'Variação Percentual' in dados_mes else None,
            help=f"Taxa de conversão em {mes_selecionado}"
        )
    
    # Histórico mensal
    st.subheader("Histórico Mensal")
    
    # Formatar a tabela
    df_historico = df_pivot[['mes', 'Sessões', 'Vendas', 'Taxa de Conversão', 'Variação Percentual']].copy()
    df_historico['Mês/Ano'] = df_historico['mes'].apply(formatar_mes)
    df_historico = df_historico[['Mês/Ano', 'Sessões', 'Vendas', 'Taxa de Conversão', 'Variação Percentual']]
    
    # Calcular totais
    total_sessoes = df_historico['Sessões'].sum()
    total_vendas = df_historico['Vendas'].sum()
    taxa_geral = (total_vendas / total_sessoes * 100) if total_sessoes > 0 else 0
    
    # Exibir tabela
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
    
    # Gráficos
    st.subheader("Análise Gráfica")
    
    # Formatar datas para eixo X
    df_pivot['Mes_Formatado'] = df_pivot['mes'].dt.strftime('%b/%Y')
    
    # Criar os 4 gráficos solicitados
    col1, col2 = st.columns(2)
    
    # Gráfico 1: Sessões mês a mês (colunas) com valores nas barras
    with col1:
        fig1 = px.bar(
            df_pivot,
            x='Mes_Formatado',
            y='Sessões',
            labels={'Sessões': 'Quantidade', 'Mes_Formatado': 'Mês'},
            title='SESSÕES REALIZADAS',
            color_discrete_sequence=['#FF4F00'],  # Laranja
            text_auto=True  # Mostra valores nas barras
        )
        fig1.update_layout(
            xaxis_title='',
            yaxis_title='Quantidade de Sessões',
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 2: Vendas mês a mês (colunas) com valores nas barras
    with col2:
        fig2 = px.bar(
            df_pivot,
            x='Mes_Formatado',
            y='Vendas',
            labels={'Vendas': 'Quantidade', 'Mes_Formatado': 'Mês'},
            title='VENDAS CONCLUÍDAS',
            color_discrete_sequence=['#67BCBF'],  # Verde
            text_auto=True  # Mostra valores nas barras
        )
        fig2.update_layout(
            xaxis_title='',
            yaxis_title='Quantidade de Vendas',
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    # Gráfico 3: Taxa de conversão (linha) com valores nos pontos
    with col3:
        fig3 = px.line(
            df_pivot,
            x='Mes_Formatado',
            y='Taxa de Conversão',
            labels={'Taxa de Conversão': 'Taxa (%)', 'Mes_Formatado': 'Mês'},
            title='TAXA DE CONVERSÃO',
            markers=True,
            color_discrete_sequence=['#FFD700'],  # Amarelo
            text=df_pivot['Taxa de Conversão'].apply(lambda x: f"{x}%")  # Adiciona texto aos pontos
        )
        fig3.update_traces(textposition="top center")  # Posiciona o texto
        fig3.update_layout(
            xaxis_title='',
            yaxis_title='Taxa de Conversão (%)',
            yaxis=dict(ticksuffix='%')
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    # Gráfico 4: Variação percentual da taxa (colunas) com valores
    with col4:
        fig4 = px.bar(
            df_pivot,
            x='Mes_Formatado',
            y='Variação Percentual',
            labels={'Variação Percentual': 'Variação (%)', 'Mes_Formatado': 'Mês'},
            title='VARIAÇÃO PERCENTUAL DA TAXA DE CONVERSÃO',
            color='Variação Percentual',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            range_color=[-100, 100],
            text_auto='.1f%'  # Formata os valores com 1 casa decimal
        )
        fig4.update_layout(
            xaxis_title='',
            yaxis_title='Variação (%)',
            yaxis=dict(ticksuffix='%'),
            coloraxis_showscale=False
        )
        fig4.update_traces(
            textposition='outside'
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # Rodapé
    st.markdown("---")
    st.caption("Painel Embaixadoras © 2023 - Todos os direitos reservados")

# Página principal
def main():
    # Verificar logout
    if "logout" in st.query_params:
        st.session_state.clear()
        # Limpar o parâmetro de logout da URL
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
