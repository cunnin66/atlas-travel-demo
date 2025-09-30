import streamlit as st
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.navigation import check_authentication, render_navigation

def show():
    """Display the knowledge base page"""
    
    # Check authentication - redirect to login if not authenticated
    if not check_authentication():
        return

    # Render navigation bar
    render_navigation()

    st.title("📚 Knowledge Base")

    st.write("TODO: Build this page.")

    st.markdown("""
    This page will provide:
    - Upload and manage travel documents
    - Browse knowledge base articles
    - Search through travel information
    - File ingestion for PDFs, documents, and web content
    - Vector search capabilities
    - Knowledge base analytics
    """)
