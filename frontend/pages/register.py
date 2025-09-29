import streamlit as st

def show():
    """Display the register page"""
    
    # Center the registration form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# 🌍 Atlas AI Travel Planner")
        st.markdown("### Create your account to start planning amazing trips!")
        
        # Registration form
        with st.form("register_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                register_button = st.form_submit_button("📝 Create Account", use_container_width=True)
            with col_b:
                if st.form_submit_button("🔐 Sign In", use_container_width=True):
                    st.session_state.current_page = "login"
                    st.rerun()
        
        # Handle registration
        if register_button:
            if username and email and password and confirm_password:
                if password == confirm_password:
                    # TODO: Implement actual registration with backend
                    # For now, just set authenticated state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Account created successfully!")
                    st.session_state.current_page = "home"
                    st.rerun()
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill in all fields")
        
        st.markdown("---")
        
        # Link to login page
        col_x, col_y, col_z = st.columns([1, 2, 1])
        with col_y:
            if st.button("Already have an account? Sign in here", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()
        
        st.info("💡 Registration functionality will be implemented to connect with the FastAPI backend.")
