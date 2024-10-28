import os

import streamlit as st

# Importações adicionais
import yaml
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage  # Importar o tipo de mensagem
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a chave da API
openai_api_key = os.getenv("OPENAI_API_KEY")

# Verificar se a chave da API está configurada
if not openai_api_key:
    st.error("Por favor, configure sua chave da API da OpenAI.")
    st.stop()

# Configurar a página do Streamlit
st.set_page_config(page_title="BeBel")

# ------------------- AUTENTICAÇÃO -------------------

# Carregar as configurações de autenticação do arquivo auth.yaml
with open("./auth.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Inicializar o autenticador (remover preauthorized da inicialização)
authenticator = Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login()


if st.session_state.get("authentication_status"):
    # Botão de logout
    authenticator.logout("Logout", "sidebar")

    # ------------------- APLICAÇÃO PRINCIPAL -------------------

    st.title("📄 BeBel")

    # Carregar o arquivo PDF
    uploaded_file = st.file_uploader("Faça upload do PDF", type="pdf")

    if uploaded_file is not None:
        # Ler o PDF
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Dividir o texto em partes menores
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        # Configurar o modelo OpenAI
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0.5, openai_api_key=openai_api_key
        )

        # Definir o prompt padrão
        default_prompt = "Por favor, forneça um resumo abrangente e explicativo dos principais pontos do texto a seguir. Concentre-se em destacar as seções essenciais, os objetivos principais e os conceitos-chave abordados ao longo do texto. Além disso, apresente uma visão geral dos tópicos discutidos, abordando os conceitos de maneira clara e objetiva, facilitando a compreensão dos temas para quem busca uma síntese geral do conteúdo."

        # Campo para o usuário modificar o prompt
        user_prompt = st.text_area(
            "Modifique o prompt se desejar:", value=default_prompt, height=100
        )

        # Dentro do botão para gerar o resumo
        if st.button("Gerar Resumo"):
            resultados = []
            with st.spinner("Gerando resumo..."):
                for chunk in chunks:
                    prompt_message = [HumanMessage(content=f"{user_prompt}\n\n{chunk}")]
                    response = llm(prompt_message)  # Chama o modelo de chat
                    resultados.append(response.content)  # Acessa o conteúdo diretamente

            # Mostrar o resumo
            st.subheader("Resumo:")
            for idx, resultado in enumerate(resultados):
                st.write(f"**Parte {idx+1}:**\n{resultado}\n")

elif st.session_state.get("authentication_status") is False:
    st.error("Nome de usuário/senha incorretos")
elif st.session_state.get("authentication_status") is None:
    st.warning("Por favor, insira seu nome de usuário e senha")
