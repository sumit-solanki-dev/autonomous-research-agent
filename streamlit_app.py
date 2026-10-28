import streamlit as st
import os
from dotenv import load_dotenv
from app.graph import create_research_graph

# ── Load API keys: Streamlit Secrets (cloud) first, then .env (local) ──────
load_dotenv(override=True)

# Streamlit Community Cloud stores secrets in st.secrets
for key in ("GEMINI_API_KEY", "TAVILY_API_KEY"):
    if key in st.secrets and not os.environ.get(key):
        os.environ[key] = st.secrets[key]

st.set_page_config(
    page_title="Autonomous Research AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🔬 Autonomous Research AI")
st.caption("Powered by Google Gemini · Tavily · LangGraph")

# Check for API keys
gemini_key = os.environ.get("GEMINI_API_KEY")
tavily_key = os.environ.get("TAVILY_API_KEY")

if not gemini_key or not tavily_key:
    st.error(
        "Missing API Keys. Configure GEMINI_API_KEY and TAVILY_API_KEY "
        "in Streamlit Secrets (cloud) or .env file (local)."
    )
    st.stop()

import sqlite3
import json

# Initialize top-level cache for instant 5-second loads
def init_app_cache():
    with sqlite3.connect(".report_cache.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reports 
                        (query TEXT PRIMARY KEY, final_report TEXT, md_path TEXT, pdf_path TEXT)''')
init_app_cache()

query = st.text_area("What would you like me to research?", height=100)

if st.button("Start Research"):
    if not query.strip():
        st.warning("Please enter a research question.")
    else:
        st.write("### Research Progress")
        
        # Check cache first
        cached_result = None
        with sqlite3.connect(".report_cache.db") as conn:
            cursor = conn.execute("SELECT final_report, md_path, pdf_path FROM reports WHERE query=?", (query.strip(),))
            cached_result = cursor.fetchone()
            
        final_report = ""
        md_path = ""
        pdf_path = ""
        
        if cached_result:
            st.success("⚡ Cache Hit! Loading previous research instantly...")
            final_report, md_path, pdf_path = cached_result
        else:
            graph = create_research_graph()
            
            initial_state = {
                "research_question": query,
                "research_tasks": [],
                "search_queries": [],
                "sources": [],
                "summaries": [],
                "fact_checks": [],
                "conflicts": [],
                "errors": []
            }
        
            try:
                with st.status("🧠 Autonomous Research in Progress...", expanded=True) as status:
                    events = graph.stream(initial_state)
                    
                    for event in events:
                        for node_name, node_state in event.items():
                            if node_state.get("errors"):
                                for error in node_state["errors"]:
                                    st.error(error)
                                st.stop()
                            
                            if node_name == "planner":
                                st.write("✓ Analyzed research objective and mapped out sub-topics...")
                            elif node_name == "execute_research_task":
                                st.write("✓ Searched the web and extracted relevant sources...")
                            elif node_name == "summarizer":
                                st.write("✓ Summarized key findings across all sources...")
                            elif node_name == "fact_checker":
                                st.write("✓ Cross-referenced claims and resolved conflicts...")
                            elif node_name == "report_writer":
                                st.write("✓ Drafted the final markdown report...")
                                final_report = node_state.get("final_report", "")
                                md_path = node_state.get("markdown_report", "")
                                pdf_path = node_state.get("pdf_path", "")

                    status.update(label="✅ Research Completed Successfully!", state="complete", expanded=False)

                    # Save to cache: store markdown content AND pdf bytes directly
                    pdf_bytes = b""
                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pf:
                            pdf_bytes = pf.read()
                    with sqlite3.connect(".report_cache.db") as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO reports (query, final_report, md_path, pdf_path) VALUES (?, ?, ?, ?)",
                            (query.strip(), final_report, md_path, pdf_path)
                        )
            except Exception as e:
                st.error(f"An error occurred during execution: {e}")
                st.stop()
                
        # The following runs for both fresh generations AND cache hits
        st.write("---")
        st.write("### Final Report")
        st.markdown(final_report)
        
        st.write("---")
        col1, col2 = st.columns(2)

        with col1:
            # Serve markdown directly from the report string (works on cloud)
            if final_report:
                import re, datetime
                safe_name = re.sub(r'[^\w]', '_', query.strip())[:40]
                fname = f"research_{safe_name}_{datetime.datetime.now().strftime('%Y%m%d')}.md"
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=final_report,
                    file_name=fname,
                    mime="text/markdown"
                )

        with col2:
            # Try local file first; fall back to re-generating PDF bytes in memory
            pdf_data = None
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
            elif final_report:
                # Regenerate PDF bytes in memory for cloud (ephemeral fs)
                import tempfile
                from app.tools.pdf_generator import generate_pdf_from_md
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name
                generate_pdf_from_md(final_report, tmp_path)
                if os.path.exists(tmp_path):
                    with open(tmp_path, "rb") as f:
                        pdf_data = f.read()
                    os.unlink(tmp_path)
            if pdf_data:
                import re, datetime
                safe_name = re.sub(r'[^\w]', '_', query.strip())[:40]
                fname = f"research_{safe_name}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=fname,
                    mime="application/pdf"
                )
