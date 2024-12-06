import pandas as pd
import numpy as np
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype
from streamlit_gsheets import GSheetsConnection
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px 
from datetime import datetime, timedelta
import random
import string
import time

USER_CREDENTIALS = st.secrets["USER_CREDENTIALS"]

st.set_page_config(
    page_title="Mobilize<>Ifood",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Formulário das Parças do Programa *Meu Diploma*"
    }
)

conn2 = st.connection("gsheets2", type=GSheetsConnection)
@st.cache_data(ttl=600)
def get_data(worksheet_name):
    return conn2.read(worksheet=worksheet_name, ttl="10m")

df1 = get_data("turma1-ava")
df2 = get_data("respostas-turma1-ava")


# conn2 = st.connection("gsheets2", type=GSheetsConnection)


# df1 = conn2.read(
#     worksheet="turma1-ava",
#     ttl="10m"
# )

# df2 = conn2.read(
#     worksheet="respostas-turma1-ava",
#     ttl="10m"
# )

df1['CPF_ALUNO'] = df1['CPF_ALUNO'].apply(lambda x: str(int(x)) if isinstance(x, float) and not pd.isna(x) else str(x)).str.strip()

def formatar_nome(nome):
    partes = nome.split()
    partes_formatadas = [parte.capitalize() for parte in partes]
    return ' '.join(partes_formatadas)


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Login")

    username = st.text_input("Nome")
    password = st.text_input("Senha", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username  
            st.success(f"Você está logada(o) como {username}")
            return True
        else:
            st.error("Nome ou Senha incorretos")

    return False

if check_password():

    st.title("Formulário das Parças")
    st.markdown("Preenchimento dos dados dos alunos matriculados no AVA da Turma 1. ")

    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

    with st.form("meu_forms"):
        st.markdown("### Formulário de checagem de informações dos alunos")
        cpf_input = st.text_input("Digite o CPF:")
        submitted = st.form_submit_button("Confirma")

        if submitted:
            user_info = df1[df1['CPF_ALUNO'] == cpf_input] 

            if not user_info.empty:
                st.write("**Informações do aluno com CPF:**", cpf_input)
                st.markdown("* **Nome:** " + formatar_nome(user_info['Nome do Aluno'].values[0]))
                st.markdown("* **Já frequentou aula presencial? Se sim, qual?** " + user_info['Já frequentou aula presencial? Se sim, qual?'].values[0])
                st.session_state.user_info = user_info  
            else:
                st.write("Nenhum aluno encontrado com o CPF:", cpf_input)
                st.session_state.user_info = None  

    with st.form("meu_forms2", clear_on_submit=True):
        st.markdown("### Formulário para escrever as informações de atendimento dos alunos")

        text_2 = st.selectbox("Motivo da Mensagem:", options=['Resposta a uma campanha', 'Resposta a uma parça', 'Contato por conta própria', 'Registro de disparo'])
        text_3 = st.selectbox("Campanha atrelada:", options=['Não', 'Campanha 1', 'Campanha 2', 'Campanha 3', 'Campanha 4'])
        frequentou_aula = st.selectbox("Já acessou o AVA?", options=['Sim', 'Não'])

        if frequentou_aula == 'Sim':
            quantas_vezes = st.selectbox("Quantas vezes?", options=[' ', '1x', '2x', '3x ou mais'])

        text_6 = st.selectbox("Comentários:", options=["Dúvidas sobre o curso", " Dúvidas sobre a gamificação", "Dúvidas e comentários sobre as aulas", "Problemas de cadastro", "Dificuldades financeiras", "Problemas pessoais ou de saúde"])
        
        text_8 = st.text_input("Detalhes do atendimento:")
        text_9 = st.text_input("Precisa encaminhar esse caso?", help="Este campo é obrigatório para submissão.")
        
        if not text_9: 
            st.error("Por favor, preencha o campo 'Precisa encaminhar esse caso?'.")
        if st.form_submit_button("Submeter Resposta"):
            if st.session_state.user_info is None:
                st.error("Nenhuma informação de CPF encontrada. Verifique antes de submeter.")
            elif not text_9:
                st.error("Por favor, preencha o campo 'Precisa encaminhar esse caso?'.")
            else:
                st.write("Preparando dados para salvar...") 
                with st.spinner('Gravando dados, por favor aguarde...'):
                    try:
                        user_info = st.session_state.user_info
                        new_row = {
                            'Nome': formatar_nome(user_info['Nome do Aluno'].values[0]),
                            'CPF': user_info['CPF_ALUNO'].values[0],
                            'Motivo da Mensagem:': text_2,
                            'Campanha atrelada:': text_3,
                            'Frequentou aula presencial?': frequentou_aula,
                            'Quantas vezes?': quantas_vezes if frequentou_aula == 'Sim' else '',
                            'Comentários': text_6,
                            'Detalhes do atendimento:': text_8,
                            'Precisa encaminhar esse caso?': text_9,
                            'Quem atendeu?': st.session_state.username,
                            'extract_at': (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                        }

                        st.write("Novo registro criado!")  

                        df2 = df2._append(new_row, ignore_index=True)
                        conn2.update(
                            worksheet="respostas-turma1-ava",
                            data=df2
                        )

                        st.write("Atualizando Google Sheets...")  
                        st.toast("Informações atualizadas com sucesso!", duration=5)
                        time.sleep(5)
                        st.session_state.pop("user_info", None)
                        st.cache_data.clear()
                        st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao gravar os dados: {e}")
                        st.write("Erro detalhado:", e)

else:
    st.write("Por favor, faça login para acessar o app teste.")