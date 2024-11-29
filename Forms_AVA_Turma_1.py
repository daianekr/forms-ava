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

USER_CREDENTIALS = st.secrets["USER_CREDENTIALS"]

st.set_page_config(
    page_title="Mobilize<>Ifood",
    page_icon="📑",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Formulário das Parças do Programa *Meu Diploma*"
    }
)

conn1 = st.connection("gsheets1", type=GSheetsConnection)

df1 = conn1.read(
    worksheet="dados-brutos",
    ttl="10m"
)

df2 = conn1.read(
    worksheet="respostas",
    ttl="10m"
)

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

    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

    with st.form("meu_forms"):
        st.write("Formulário de checagem de informações dos alunos")
        cpf_input = st.text_input("Digite o CPF:")
        submitted = st.form_submit_button("Confirma")

        if submitted:
            user_info = df1[df1['CPF_ALUNO'] == cpf_input] 

            if not user_info.empty:
                st.write("Informações do aluno com CPF:", cpf_input)
                st.markdown("- Nome: " + formatar_nome(user_info['Nome do Aluno'].values[0]))
                st.markdown("- Já frequentou aula presencial? Se sim, qual? " + user_info['Já frenquentou alguma aula presencial? Se sim, qual?'].values[0])

            else:
                st.write("Nenhum aluno encontrado com o CPF:", cpf_input)
                st.session_state.user_info = None
    with st.form("meu_forms2", clear_on_submit=True):
        st.write("Formulário para escrever as informações de atendimento dos alunos")

        text_2 = st.selectbox("Motivo da Mensagem:", options=['Resposta a uma campanha', 'Resposta a uma parça', 'Contato por conta própria', 'Registro de disparo'])
        text_3 = st.selectbox("Campanha atrelada:", options=['Não', 'Campanha 1', 'Campanha 2', 'Campanha 3', 'Campanha 4'])
        frequentou_aula = st.selectbox("Frequentou aula presencial?", options=['Sim', 'Não'])

        if frequentou_aula == 'Sim':
            quantas_vezes = st.selectbox("Quantas vezes?", options=[' ', '1x', '2x', '3x ou mais'])

        text_6 = st.selectbox("Comentários:", options=["Dúvidas sobre o curso", " Dúvidas sobre a gamificação", "Dúvidas e comentários sobre as aulas", "Problemas de cadastro", "Dificuldades financeiras", "Problemas pessoais ou de saúde"])
        
        text_8 = st.text_input("Observações do atendimento:")
        text_7 = st.text_input("Detalhes sobre o Aluno:")
        text_9 = st.text_input("Precisa encaminhar esse caso?", help="Este campo é obrigatório para submissão.")
        
        if not text_9: 
            st.error("Por favor, preencha o campo 'Precisa encaminhar esse caso?'.")
        if st.form_submit_button("Submeter Resposta"):
            if not text_9: 
                st.error("Por favor, preencha o campo 'Precisa encaminhar esse caso?' para submeter o formulário.")
            else:
                with st.spinner('Gravando dados, por favor aguarde...'):
                    if st.session_state.user_info is not None:
                        user_info = st.session_state.user_info

                        new_row = {
                            'Nome': formatar_nome(user_info['Nome'].values[0]),
                            'CPF': user_info['CPF'].values[0],
                            'Motivo da Mensagem:': text_2,
                            'Campanha atrelada:': text_3,
                            'Frequentou aula presencial?': frequentou_aula,
                            'Quantas vezes?': quantas_vezes if frequentou_aula == 'Sim' else '',
                            'Comentários': text_6,
                            'Detalhes do Aluno': text_7,
                            'Observações do atendimento': text_8,
                            'Precisa encaminhar esse caso?': text_9,  
                            'Quem atendeu?': st.session_state.username,  
                            'extract_at' : (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")}
                        
                        df2 = df2._append(new_row, ignore_index=True)

                        conn1.update(
                            worksheet="teste-turma-2-rds",
                            data=df2
                        )
                        st.cache_data.clear()
                        st.rerun()
                        st.success("Informações atualizadas com sucesso!")
                    else:
                        st.error("Nenhuma informação de CPF encontrada. Verifique antes de submeter.")
else:
    st.write("Por favor, faça login para acessar o app teste.")