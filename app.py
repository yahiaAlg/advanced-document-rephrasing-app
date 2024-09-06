import streamlit as st
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
)
import tempfile
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()


# Function to load document based on file type
def load_document(file):
    file_extension = os.path.splitext(file.name)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.read())
        temp_file_path = temp_file.name

    if file_extension == ".pdf":
        loader = PyPDFLoader(temp_file_path)
    elif file_extension == ".md":
        loader = UnstructuredMarkdownLoader(temp_file_path)
    elif file_extension == ".docx":
        loader = Docx2txtLoader(temp_file_path)
    else:  # Assume it's a text file
        loader = TextLoader(temp_file_path)

    document = loader.load()
    os.unlink(temp_file_path)
    return document[0].page_content


# Function to get download link
def get_download_link(text, filename, file_label):
    b64 = base64.b64encode(text.encode()).decode()
    return (
        f'<a href="data:file/txt;base64,{b64}" download="{filename}">{file_label}</a>'
    )


# Streamlit UI
st.set_page_config(page_title="Advanced Document Rephrasing App", layout="wide")

st.title("Advanced Document Rephrasing App")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")

    # LLM Provider selection
    llm_provider = st.selectbox(
        "Select LLM Provider",
        [
            "Google Generative AI (Gemini)",
            "Ollama (Phi-3)",
            "Ollama (LLaMA-3)",
            "Ollama (Mistral)",
            "Ollama (Mixtral)",
            "Ollama (Vicuna)",
        ],
    )

    # API Key input
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter your Google API Key", type="password")
    else:
        st.success("Google API Key loaded from .env file")

    st.caption(
        "API key is required for Google Generative AI. Ollama models run locally."
    )

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("Input")
    tab1, tab2 = st.tabs(["Text Input", "File Upload"])

    with tab1:
        user_input = st.text_area("Enter the text you want to rephrase:", height=300)

    with tab2:
        uploaded_file = st.file_uploader(
            "Choose a file", type=["txt", "pdf", "md", "docx"]
        )
        if uploaded_file is not None:
            user_input = load_document(uploaded_file)
            st.text_area("Extracted text:", value=user_input, height=300)

    rephrase_style = st.selectbox(
        "Choose rephrasing style:",
        ["Formal", "Casual", "Simple", "Academic", "Creative", "Professional"],
    )

    # Additional customization options based on style
    if rephrase_style == "Academic":
        citation_style = st.selectbox(
            "Citation Style", ["APA", "MLA", "Chicago", "Harvard", "IEEE"]
        )
        technical_level = st.selectbox(
            "Technical Level",
            ["Undergraduate", "Graduate", "Doctoral", "Post-doctoral"],
        )
        discipline = st.selectbox(
            "Discipline",
            ["Humanities", "Social Sciences", "Natural Sciences", "Engineering"],
        )
        tone = st.multiselect("Tone", ["Objective", "Analytical", "Critical"])
        voice = st.radio("Voice", ["Active", "Passive", "Balanced"])
    elif rephrase_style == "Formal":
        formality_level = st.slider("Formality Level", 1, 5, 3)
        professionalism = st.selectbox(
            "Professionalism", ["Business", "Legal", "Diplomatic"]
        )
    elif rephrase_style == "Casual":
        informality_level = st.slider("Informality Level", 1, 5, 3)
        include_slang = st.checkbox("Include slang/idioms")
        use_contractions = st.checkbox("Use contractions")
    elif rephrase_style == "Simple":
        reading_level = st.selectbox(
            "Reading Level", ["Elementary", "Middle School", "High School"]
        )
        sentence_structure = st.multiselect(
            "Sentence Structure", ["Simple", "Compound", "Complex"]
        )
    elif rephrase_style == "Creative":
        literary_devices = st.multiselect(
            "Literary Devices",
            ["Metaphors", "Similes", "Personification", "Alliteration"],
        )
        narrative_voice = st.radio(
            "Narrative Voice", ["First-person", "Second-person", "Third-person"]
        )
    elif rephrase_style == "Professional":
        industry_jargon = st.slider("Industry Jargon Level", 1, 5, 3)
        data_focus = st.checkbox("Incorporate data and metrics")
        action_oriented = st.checkbox("Use action-oriented language")

    if st.button("Rephrase"):
        if (llm_provider.startswith("Google") and api_key and user_input) or (
            llm_provider.startswith("Ollama") and user_input
        ):
            # Initialize the LLM
            if llm_provider.startswith("Google"):
                llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
            else:
                model_name = llm_provider.split("(")[1][:-1].lower()
                llm = Ollama(model=model_name)

            # Create a prompt template with style-specific customizations
            template = """
            Rephrase the following text in a {style} style:
            
            {text}
            
            Style-specific customizations:
            {customizations}
            
            Rephrased text:
            """

            # Prepare customizations based on selected style
            if rephrase_style == "Academic":
                customizations = f"Citation Style: {citation_style}, Technical Level: {technical_level}, Discipline: {discipline}, Tone: {', '.join(tone)}, Voice: {voice}"
            elif rephrase_style == "Formal":
                customizations = f"Formality Level: {formality_level}/5, Professionalism: {professionalism}"
            elif rephrase_style == "Casual":
                customizations = f"Informality Level: {informality_level}/5, Include Slang: {include_slang}, Use Contractions: {use_contractions}"
            elif rephrase_style == "Simple":
                customizations = f"Reading Level: {reading_level}, Sentence Structure: {', '.join(sentence_structure)}"
            elif rephrase_style == "Creative":
                customizations = f"Literary Devices: {', '.join(literary_devices)}, Narrative Voice: {narrative_voice}"
            elif rephrase_style == "Professional":
                customizations = f"Industry Jargon Level: {industry_jargon}/5, Data Focus: {data_focus}, Action-Oriented: {action_oriented}"
            else:
                customizations = "No specific customizations"

            prompt = PromptTemplate(
                template=template, input_variables=["style", "text", "customizations"]
            )

            # Create and run the chain
            chain = LLMChain(llm=llm, prompt=prompt)
            with st.spinner("Rephrasing..."):
                result = chain.run(
                    style=rephrase_style, text=user_input, customizations=customizations
                )

            st.session_state.rephrased_text = result
        else:
            st.error("Please provide all required inputs.")

with col2:
    st.header("Output")
    if "rephrased_text" in st.session_state:
        st.text_area(
            "Rephrased Text:", value=st.session_state.rephrased_text, height=400
        )

        st.subheader("Download Options")
        col_txt, col_md, col_docx = st.columns(3)
        with col_txt:
            st.markdown(
                get_download_link(
                    st.session_state.rephrased_text,
                    "rephrased_text.txt",
                    "Download as TXT",
                ),
                unsafe_allow_html=True,
            )
        with col_md:
            st.markdown(
                get_download_link(
                    st.session_state.rephrased_text,
                    "rephrased_text.md",
                    "Download as MD",
                ),
                unsafe_allow_html=True,
            )
        with col_docx:
            st.markdown(
                get_download_link(
                    st.session_state.rephrased_text,
                    "rephrased_text.docx",
                    "Download as DOCX",
                ),
                unsafe_allow_html=True,
            )

# Chat interface
st.header("Chat for Customization")
st.markdown(
    """
To customize the rephrasing further, you can use the chat interface below. 
For example, you can type:
- "Customize academic style: Use more hedging language and add a thesis statement."
- "Customize formal style: Increase formality and use more industry-specific terms."
- "Customize casual style: Make it more conversational and include some popular idioms."
"""
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask for specific rephrasing or customization"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if (llm_provider.startswith("Google") and api_key) or llm_provider.startswith(
        "Ollama"
    ):
        if llm_provider.startswith("Google"):
            llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
        else:
            model_name = llm_provider.split("(")[1][:-1].lower()
            llm = Ollama(model=model_name)

        with st.spinner("Generating response..."):
            if prompt.lower().startswith("customize"):
                customization_prompt = f"""
                Customize the rephrasing based on the following specifications:
                
                {prompt}
                
                Apply these customizations to the following text:
                
                {st.session_state.rephrased_text}
                
                Provide the customized text:
                """
                response = llm.invoke(customization_prompt)
                st.session_state.rephrased_text = response  # Update the rephrased text
            else:
                response = llm.invoke(prompt)

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
    else:
        st.error("Please provide necessary inputs to use the chat feature.")

# Footer
st.markdown("---")
st.caption(
    "Powered by LangChain with support for Google Generative AI and Ollama models"
)
