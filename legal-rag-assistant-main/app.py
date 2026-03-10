import streamlit as st
import os
import tempfile
import time
import json
import fitz  # PyMuPDF for metadata
from datetime import datetime
from dotenv import load_dotenv
from rag_index_builder import build_index_from_pdf
from tools import retrieve_legal_context
from autogen import AssistantAgent, UserProxyAgent

# --- CONFIGURATION & SETUP ---
load_dotenv()

st.set_page_config(
    page_title="LexAI - Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (ENHANCED PROFESSIONAL) ---
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700;800&display=swap');

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: #1e3a8a;
        font-weight: 700 !important;
    }
    
    h1 {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 12px;
        margin-bottom: 1.5rem;
    }

    /* Sidebar Styling - Enhanced Gradient */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e293b 100%);
        color: #f1f5f9;
        box-shadow: 4px 0 15px rgba(0,0,0,0.1);
    }
    
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }

    /* Cards/Containers - Glass Morphism Effect */
    .info-card {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(30, 58, 138, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        box-shadow: 0 12px 48px rgba(30, 58, 138, 0.15);
        transform: translateY(-2px);
    }

    /* Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.9);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* Primary Buttons - White with Black Text */
    .stButton > button {
        background: #ffffff;
        color: #000000 !important;
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background: #000000;
        color: #ffffff !important;
        border-color: #000000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Quick Action Buttons - Same Style */
    div[data-testid="column"] .stButton > button {
        background: #ffffff;
        color: #000000 !important;
        border: 2px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="column"] .stButton > button:hover {
        background: #000000;
        color: #ffffff !important;
        border-color: #000000;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    /* Form Buttons - Ask (White/Black) and Clear (White/Black) */
    form[data-testid="stForm"] div[data-testid="column"]:nth-child(2) .stButton > button,
    form[data-testid="stForm"] div[data-testid="column"]:nth-child(3) .stButton > button {
        background: #fff !important;
        color: #000 !important;
        border: 2px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        font-weight: 600;
        transition: all 0.3s;
    }

    form[data-testid="stForm"] div[data-testid="column"]:nth-child(2) .stButton > button:hover,
    form[data-testid="stForm"] div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        background: #000 !important;
        color: #fff !important;
        border-color: #000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}
    
    form[data-testid="stForm"] div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%);
        box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
        color: #ffffff !important;
    }

    /* Chat Bubbles - Enhanced */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-top: 20px;
    }

    .user-msg {
        align-self: flex-end;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.25);
        font-size: 0.95rem;
        line-height: 1.6;
        animation: slideInRight 0.3s ease;
    }

    .bot-msg {
        align-self: flex-start;
        background: white;
        border: 1px solid #e5e7eb;
        color: #374151;
        padding: 16px 24px;
        border-radius: 18px 18px 18px 4px;
        max-width: 80%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        font-size: 0.95rem;
        line-height: 1.7;
        animation: slideInLeft 0.3s ease;
    }
    
    .bot-msg strong {
        color: #1e3a8a;
        font-weight: 600;
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* File Uploader - Enhanced */
    .stFileUploader {
        padding: 24px;
        background: white;
        border-radius: 12px;
        border: 2px dashed #3b82f6;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #2563eb;
        background: #f0f9ff;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    }

    /* Text Input */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        padding: 12px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* Alerts - Enhanced */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
        padding: 16px;
    }

    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        color: white !important;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #6d28d9 0%, #9333ea 100%);
        box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
        font-weight: 500;
        color: #1e3a8a;
    }

    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px 0;
    }
    
    .status-active {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        color: white;
    }
    
    .status-idle {
        background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
        color: white;
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3b82f6 0%, #1e3a8a 100%);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #2563eb 0%, #1e40af 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- BACKEND LOGIC ---

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

llm_config = {
    "config_list": [
        {
            "api_key": AZURE_OPENAI_API_KEY,
            "base_url": AZURE_OPENAI_ENDPOINT,
            "api_type": "azure",
            "api_version": AZURE_OPENAI_API_VERSION,
            "model": "gpt-4o", 
        }
    ],
    "temperature": 0
}

def is_termination_msg(msg):
    return msg.get("content") and "TERMINATE" in msg["content"]

def run_agent(query):
    legal_assistant = AssistantAgent(
        name="LegalAssistant",
        system_message=(
            "You are a highly capable legal research assistant. Answer user queries strictly by utilizing the 'retrieve_legal_context' tool to find evidence in the provided documents. "
            "Maintain a professional, objective, and precise tone. "
            "After answering, always respond with 'TERMINATE'."
        ),
        llm_config=llm_config,
    )

    user = UserProxyAgent(
        name="User",
        llm_config=False,
        human_input_mode="NEVER",
        is_termination_msg=is_termination_msg,
        code_execution_config={"use_docker": False}
    )

    legal_assistant.register_for_llm(name="retrieve_legal_context", description="Retrieve context from legal documents.")(retrieve_legal_context)
    user.register_for_execution(name="retrieve_legal_context")(retrieve_legal_context)

    chat_result = user.initiate_chat(
        legal_assistant,
        message=query,
        summary_method="reflection_with_llm"
    )

    history = getattr(chat_result, "chat_history", None)
    if history is None:
        return "No chat history found.", []

    for msg in reversed(history):
        if msg.get("role") == "user" and msg.get("name") == "LegalAssistant":
            final_content = msg.get("content", "").replace("TERMINATE", "").strip()
            return final_content, history

    return "Unable to generate a valid response based on the provided context.", history

# --- Helper: Retry with exponential backoff for rate limits ---
def run_agent_with_retry(query, max_retries: int = 5, initial_delay_seconds: float = 3.0):
    """Call run_agent with retries on Azure OpenAI rate limit errors."""
    delay = initial_delay_seconds
    for attempt in range(max_retries):
        try:
            return run_agent(query)
        except Exception as e:
            # Detect Azure OpenAI rate limit error
            msg = str(e)
            if "RateLimitReached" in msg or "429" in msg:
                time.sleep(delay)
                delay *= 2  # exponential backoff
                continue
            # Non-rate-limit errors should be raised
            raise
    # Fallback after exhausting retries
    return (
        "Rate limit reached. Please wait a moment and try again.",
        []
    )

# --- SESSION STATE MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "doc_meta" not in st.session_state:
    st.session_state.doc_meta = {}
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# --- UI LAYOUT ---

# Sidebar: Context & Reset
with st.sidebar:
    st.markdown("### ⚖️ LexAI")
    st.caption("Legal RAG Assistant")
    st.markdown("---")
    st.markdown("### 📋 System Status")
    
    if st.session_state.pdf_processed:
        st.success("✅ Analysis Engine: Ready")
        meta = st.session_state.doc_meta
        with st.expander("📄 Document Details", expanded=True):
            st.markdown(f"""
            **File:** {meta.get("name", "—")}  
            **Pages:** {meta.get("pages", "—")}  
            **Size:** {meta.get("size", "—")}  
            **Indexed:** {meta.get("indexed_time", "—")}
            """)
    else:
        st.warning("⏸️ Analysis Engine: Idle")
        st.caption("Please upload a document to begin.")
        
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("""
    LexAI leverages Retrieval-Augmented Generation (RAG) to provide precise citations and answers from your legal repository.
    """)
    
    st.markdown("---")
    st.markdown("### 🛠️ Actions")
    cols = st.columns(2)
    if cols[0].button("🔄 Reset", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pdf_processed = False
        st.session_state.doc_meta = {}
        st.session_state.last_answer = ""
        st.rerun()
    
    if cols[1].button("📥 Export", use_container_width=True):
        if st.session_state.chat_history:
            export = json.dumps(st.session_state.chat_history, indent=2)
            st.download_button(
                label="Download Chat",
                data=export,
                file_name=f"lexai_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

# Main Content
st.title("⚖️ Legal Document Analysis")
st.markdown("Use AI-powered RAG to review contracts, extract clauses, and summarize obligations efficiently.")

# Tips section
with st.expander("💡 Tips & Best Practices", expanded=False):
    st.markdown("""
    - **Upload a single PDF** containing your legal document
    - **Use Quick Actions** for common analysis tasks
    - **Ask specific questions** for better results
    - **Download answers** for record-keeping and reports
    - **Clear chat** to start fresh analysis
    """)

# Step 1: Upload
if not st.session_state.pdf_processed:
    st.markdown("### Upload Source Document")
    st.markdown("""
    <div class="info-card">
        <p><strong>Instructions:</strong> Upload a PDF legal document (contract, case file, or regulation). The system will index the content for semantic search.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Select PDF File", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_pdf_path = tmp_file.name
        
        # Extract PDF metadata
        try:
            doc = fitz.open(tmp_pdf_path)
            pages = doc.page_count
            size_kb = round(os.path.getsize(tmp_pdf_path) / 1024, 1)
            st.session_state.doc_meta = {
                "name": getattr(uploaded_file, "name", "document.pdf"),
                "pages": pages,
                "size": f"{size_kb} KB",
                "indexed_time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            doc.close()
        except Exception:
            st.session_state.doc_meta = {"name": "document.pdf"}
        
        status_text.text("📖 Parsing document structure...")
        for i in range(30):
            time.sleep(0.01)
            progress_bar.progress(i + 10)
            
        status_text.text("🔍 Building semantic index...")
        build_index_from_pdf(tmp_pdf_path, persist_dir="rag_faiss_store")
        
        for i in range(30, 100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
            
        status_text.success("✅ Indexing complete!")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        st.session_state.pdf_processed = True
        st.rerun()

# Step 2: Chat Interface
else:
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    # Define a helper to set prompt
    def set_prompt(text):
        st.session_state.temp_prompt = text

    if col_q1.button("📑 Summarize"):
        set_prompt("Provide a comprehensive executive summary of this legal document.")
        
    if col_q2.button("⚠️ Risks"):
        set_prompt("List all potential liabilities and risks for the primary party.")
        
    if col_q3.button("📅 Dates"):
        set_prompt("List all critical dates, deadlines, and termination clauses.")
    
    if col_q4.button("📄 Key Clauses"):
        set_prompt("Extract and list key clauses (termination, indemnity, confidentiality, governing law) with brief explanations.")

    st.markdown("---")
    st.subheader("💬 Consultation")

    chat_container = st.container()

    # Input Area at the bottom
    with st.form(key="chat_form", clear_on_submit=True):
        col_in1, col_in2, col_in3 = st.columns([6, 1, 1])
        with col_in1:
            user_input = st.text_input(
                "Enter your query", 
                placeholder="Ex: What is the governing law of this contract?", 
                label_visibility="collapsed"
            )
        with col_in2:
            submit_button = st.form_submit_button("Ask")
        with col_in3:
            clear_button = st.form_submit_button("Clear")

    # Handle clear button
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.last_answer = ""
        st.success("Chat cleared successfully!")
        st.rerun()

    # Handle Logic
    active_prompt = None
    if submit_button and user_input:
        active_prompt = user_input
    elif "temp_prompt" in st.session_state:
        active_prompt = st.session_state.temp_prompt
        del st.session_state.temp_prompt

    if active_prompt:
        st.session_state.chat_history.append({"role": "user", "content": active_prompt})
        
        with st.spinner("🔍 Analyzing legal corpus..."):
            # Use retry wrapper to handle 429s gracefully
            answer, _ = run_agent_with_retry(active_prompt)
            
            if answer.startswith("Rate limit reached"):
                st.warning(answer)
        
        st.session_state.last_answer = answer
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    # Display History
    with chat_container:
        if not st.session_state.chat_history:
            st.info("Session started. Please select a quick action or type a specific query.")
        
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                    <div class="user-msg">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div class="bot-msg">
                        <strong style="color: #0f172a;">LexAI Assistant</strong><br>
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

