# #!/usr/bin/env python3
# """
# Streamlit UI - Beautiful Frontend for PySR Job Management
# Advanced and attractive user interface for symbolic regression
# """

# import streamlit as st
# import requests
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import numpy as np
# import json
# import io
# from datetime import datetime, timedelta
# import time
# from typing import Dict, List, Any, Optional
# import base64

# # Page configuration
# st.set_page_config(
#     page_title="PySR - Symbolic Regression Platform",
#     page_icon="🧮",
#     layout="wide",
#     initial_sidebar_state="expanded",
#     menu_items={
#         'Get Help': 'https://pysr.readthedocs.io/',
#         'Report a bug': 'https://github.com/MilesCranmer/PySR/issues',
#         'About': "# PySR Symbolic Regression Platform\nPowerful symbolic regression with interpretable AI"
#     }
# )

# # Configuration
# APP_SERVER_URL = "http://localhost:8000"
# PYSR_MCP_URL = "http://localhost:8001"

# # Custom CSS for beautiful UI
# st.markdown("""
# <style>
#     /* Import Google Fonts */
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
#     /* Global Styles */
#     .main {
#         font-family: 'Inter', sans-serif;
#     }
    
#     /* Header Styles */
#     .main-header {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 2rem;
#         border-radius: 15px;
#         margin-bottom: 2rem;
#         color: white;
#         text-align: center;
#         box-shadow: 0 10px 30px rgba(0,0,0,0.1);
#     }
    
#     .main-header h1 {
#         font-size: 3rem;
#         font-weight: 700;
#         margin-bottom: 0.5rem;
#         text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
#     }
    
#     .main-header p {
#         font-size: 1.2rem;
#         font-weight: 300;
#         opacity: 0.9;
#     }
    
#     /* Card Styles */
#     .metric-card {
#         background: white;
#         padding: 1.5rem;
#         border-radius: 12px;
#         box-shadow: 0 4px 15px rgba(0,0,0,0.08);
#         border-left: 4px solid #667eea;
#         margin-bottom: 1rem;
#         transition: transform 0.2s ease;
#     }
    
#     .metric-card:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 6px 20px rgba(0,0,0,0.12);
#     }
    
#     .status-card {
#         padding: 1rem;
#         border-radius: 10px;
#         margin: 0.5rem 0;
#         border-left: 4px solid;
#     }
    
#     .status-success {
#         background: linear-gradient(135deg, #d4edda, #c3e6cb);
#         border-left-color: #28a745;
#     }
    
#     .status-warning {
#         background: linear-gradient(135deg, #fff3cd, #ffeeba);
#         border-left-color: #ffc107;
#     }
    
#     .status-error {
#         background: linear-gradient(135deg, #f8d7da, #f5c6cb);
#         border-left-color: #dc3545;
#     }
    
#     .status-info {
#         background: linear-gradient(135deg, #d1ecf1, #bee5eb);
#         border-left-color: #17a2b8;
#     }
    
#     /* Button Styles */
#     .stButton > button {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         border: none;
#         border-radius: 8px;
#         padding: 0.5rem 1rem;
#         font-weight: 500;
#         transition: all 0.2s ease;
#         box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
#     }
    
#     .stButton > button:hover {
#         transform: translateY(-1px);
#         box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
#     }
    
#     /* Sidebar Styles */
#     .css-1d391kg {
#         background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
#     }
    
#     /* Animation Classes */
#     @keyframes fadeIn {
#         from { opacity: 0; transform: translateY(20px); }
#         to { opacity: 1; transform: translateY(0); }
#     }
    
#     .fade-in {
#         animation: fadeIn 0.5s ease-out;
#     }
    
#     /* Data Quality Indicator */
#     .quality-indicator {
#         display: inline-block;
#         width: 12px;
#         height: 12px;
#         border-radius: 50%;
#         margin-right: 8px;
#     }
    
#     .quality-high { background-color: #28a745; }
#     .quality-medium { background-color: #ffc107; }
#     .quality-low { background-color: #dc3545; }
    
#     /* Equation Display */
#     .equation-display {
#         background: linear-gradient(135deg, #f8f9fa, #e9ecef);
#         border: 1px solid #dee2e6;
#         border-radius: 8px;
#         padding: 1rem;
#         margin: 1rem 0;
#         font-family: 'Courier New', monospace;
#         font-size: 1.1rem;
#         text-align: center;
#     }
    
#     /* Progress Bar */
#     .custom-progress {
#         background: #e9ecef;
#         border-radius: 10px;
#         height: 20px;
#         overflow: hidden;
#     }
    
#     .custom-progress-bar {
#         background: linear-gradient(90deg, #667eea, #764ba2);
#         height: 100%;
#         border-radius: 10px;
#         transition: width 0.3s ease;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Initialize session state
# if 'authenticated' not in st.session_state:
#     st.session_state.authenticated = False
# if 'token' not in st.session_state:
#     st.session_state.token = None
# if 'user' not in st.session_state:
#     st.session_state.user = None
# if 'jobs' not in st.session_state:
#     st.session_state.jobs = []
# if 'selected_job' not in st.session_state:
#     st.session_state.selected_job = None

# # Utility Functions
# def make_request(method: str, endpoint: str, data: dict = None, files: dict = None) -> dict:
#     """Make HTTP request to app server"""
#     url = f"{APP_SERVER_URL}{endpoint}"
#     headers = {}
    
#     if st.session_state.token:
#         headers["Authorization"] = f"Bearer {st.session_state.token}"
    
#     try:
#         if method == "GET":
#             response = requests.get(url, headers=headers)
#         elif method == "POST":
#             if files:
#                 response = requests.post(url, headers=headers, data=data, files=files)
#             else:
#                 headers["Content-Type"] = "application/json"
#                 response = requests.post(url, headers=headers, json=data)
#         elif method == "PUT":
#             headers["Content-Type"] = "application/json"
#             response = requests.put(url, headers=headers, json=data)
#         elif method == "DELETE":
#             response = requests.delete(url, headers=headers)
        
#         if response.status_code == 401:
#             st.session_state.authenticated = False
#             st.session_state.token = None
#             st.error("Session expired. Please login again.")
#             st.rerun()
        
#         return response.json()
    
#     except requests.exceptions.ConnectionError:
#         st.error("🚨 Cannot connect to server. Please ensure the App Server is running.")
#         return {"error": "Connection failed"}
#     except Exception as e:
#         st.error(f"Request failed: {str(e)}")
#         return {"error": str(e)}

# def create_status_badge(status: str) -> str:
#     """Create colored status badge"""
#     status_colors = {
#         "created": ("🟡", "#ffc107", "Created"),
#         "running": ("🔵", "#007bff", "Running"),
#         "completed": ("🟢", "#28a745", "Completed"),
#         "failed": ("🔴", "#dc3545", "Failed"),
#         "pending": ("⚪", "#6c757d", "Pending")
#     }
    
#     emoji, color, text = status_colors.get(status.lower(), ("⚫", "#6c757d", status))
#     return f"""<span style="color: {color}; font-weight: 600;">{emoji} {text}</span>"""

# def format_duration(start_time: str, end_time: str = None) -> str:
#     """Format duration between timestamps"""
#     try:
#         start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
#         if end_time:
#             end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
#         else:
#             end = datetime.now()
        
#         duration = end - start
        
#         if duration.days > 0:
#             return f"{duration.days}d {duration.seconds//3600}h"
#         elif duration.seconds >= 3600:
#             return f"{duration.seconds//3600}h {(duration.seconds%3600)//60}m"
#         elif duration.seconds >= 60:
#             return f"{duration.seconds//60}m {duration.seconds%60}s"
#         else:
#             return f"{duration.seconds}s"
#     except:
#         return "Unknown"

# def plot_equation_complexity(equations: List[Dict]) -> go.Figure:
#     """Plot equation complexity vs accuracy"""
#     df = pd.DataFrame(equations)
    
#     fig = go.Figure()
    
#     # Add scatter plot
#     fig.add_trace(go.Scatter(
#         x=df['complexity'],
#         y=df['score'],
#         mode='markers',
#         marker=dict(
#             size=12,
#             color=df['loss'],
#             colorscale='Viridis',
#             colorbar=dict(title="Loss"),
#             line=dict(width=1, color='white')
#         ),
#         text=[f"Equation {i}: {eq}" for i, eq in enumerate(df['equation'])],
#         hovertemplate="<b>Complexity:</b> %{x}<br><b>Score:</b> %{y}<br><b>%{text}</b><extra></extra>",
#         name="Equations"
#     ))
    
#     fig.update_layout(
#         title="Equation Complexity vs Performance",
#         xaxis_title="Complexity",
#         yaxis_title="Score",
#         template="plotly_white",
#         height=500
#     )
    
#     return fig

# def plot_training_progress(job_runs: List[Dict]) -> go.Figure:
#     """Plot training progress over time"""
#     if not job_runs:
#         return go.Figure()
    
#     fig = go.Figure()
    
#     for i, run in enumerate(job_runs):
#         if run['started_at'] and run['completed_at']:
#             start = datetime.fromisoformat(run['started_at'])
#             end = datetime.fromisoformat(run['completed_at'])
#             duration = (end - start).total_seconds()
            
#             color = '#28a745' if run['status'] == 'completed' else '#dc3545'
            
#             fig.add_trace(go.Bar(
#                 x=[f"Run {run['run_number']}"],
#                 y=[duration],
#                 name=f"Run {run['run_number']}",
#                 marker_color=color,
#                 text=f"{duration:.1f}s",
#                 textposition='outside'
#             ))
    
#     fig.update_layout(
#         title="Training Duration by Run",
#         xaxis_title="Job Runs",
#         yaxis_title="Duration (seconds)",
#         template="plotly_white",
#         showlegend=False,
#         height=400
#     )
    
#     return fig

# # Authentication Functions
# def login_page():
#     """Login page"""
#     st.markdown('<div class="main-header"><h1>🧮 PySR Platform</h1><p>Advanced Symbolic Regression with Interpretable AI</p></div>', unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         st.markdown("### 🔐 Authentication")
        
#         tab1, tab2 = st.tabs(["Login", "Register"])
        
#         with tab1:
#             st.markdown("#### Sign In")
#             with st.form("login_form"):
#                 username = st.text_input("Username", placeholder="Enter your username")
#                 password = st.text_input("Password", type="password", placeholder="Enter your password")
#                 login_btn = st.form_submit_button("🚀 Sign In", use_container_width=True)
                
#                 if login_btn:
#                     if username and password:
#                         response = make_request("POST", "/auth/login", {
#                             "username": username,
#                             "password": password
#                         })
                        
#                         if "token" in response:
#                             st.session_state.authenticated = True
#                             st.session_state.token = response["token"]
#                             st.session_state.user = response["user"]
#                             st.success("✅ Login successful!")
#                             time.sleep(1)
#                             st.rerun()
#                         else:
#                             st.error("❌ Invalid credentials")
#                     else:
#                         st.error("⚠️ Please fill in all fields")
        
#         with tab2:
#             st.markdown("#### Create Account")
#             with st.form("register_form"):
#                 reg_username = st.text_input("Username", placeholder="Choose a username")
#                 reg_email = st.text_input("Email", placeholder="Enter your email")
#                 reg_password = st.text_input("Password", type="password", placeholder="Choose a password")
#                 register_btn = st.form_submit_button("📝 Create Account", use_container_width=True)
                
#                 if register_btn:
#                     if reg_username and reg_email and reg_password:
#                         response = make_request("POST", "/auth/register", {
#                             "username": reg_username,
#                             "email": reg_email,
#                             "password": reg_password
#                         })
                        
#                         if "token" in response:
#                             st.session_state.authenticated = True
#                             st.session_state.token = response["token"]
#                             st.session_state.user = response["user"]
#                             st.success("✅ Account created successfully!")
#                             time.sleep(1)
#                             st.rerun()
#                         else:
#                             st.error(f"❌ Registration failed: {response.get('detail', 'Unknown error')}")
#                     else:
#                         st.error("⚠️ Please fill in all fields")

# def dashboard_page():
#     """Main dashboard page"""
#     st.markdown('<div class="main-header"><h1>🧮 PySR Dashboard</h1><p>Symbolic Regression Made Simple</p></div>', unsafe_allow_html=True)
    
#     # Sidebar
#     with st.sidebar:
#         st.markdown(f"### Welcome, {st.session_state.user['username']}! 👋")
#         st.markdown("---")
        
#         # Navigation
#         page = st.selectbox("📍 Navigate", [
#             "🏠 Dashboard",
#             "📊 Jobs",
#             "🔬 Create New Job",
#             "📈 Analytics",
#             "⚙️ Settings"
#         ])
        
#         st.markdown("---")
#         if st.button("🚪 Logout", use_container_width=True):
#             st.session_state.authenticated = False
#             st.session_state.token = None
#             st.session_state.user = None
#             st.rerun()
    
#     # Load jobs
#     jobs_response = make_request("GET", "/jobs")
#     if "jobs" in jobs_response:
#         st.session_state.jobs = jobs_response["jobs"]
    
#     # Route to selected page
#     if page == "🏠 Dashboard":
#         dashboard_overview()
#     elif page == "📊 Jobs":
#         jobs_page()
#     elif page == "🔬 Create New Job":
#         create_job_page()
#     elif page == "📈 Analytics":
#         analytics_page()
#     elif page == "⚙️ Settings":
#         settings_page()

# def dashboard_overview():
#     """Dashboard overview"""
#     jobs = st.session_state.jobs
    
#     # Metrics
#     col1, col2, col3, col4 = st.columns(4)
    
#     total_jobs = len(jobs)
#     completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
#     running_jobs = len([j for j in jobs if j['status'] == 'running'])
#     failed_jobs = len([j for j in jobs if j['status'] == 'failed'])
    
#     with col1:
#         st.metric("📋 Total Jobs", total_jobs, delta=None)
#     with col2:
#         st.metric("✅ Completed", completed_jobs, delta=f"{completed_jobs-failed_jobs:+d}")
#     with col3:
#         st.metric("🔄 Running", running_jobs, delta=None)
#     with col4:
#         st.metric("❌ Failed", failed_jobs, delta=None)
    
#     st.markdown("---")
    
#     # Recent Jobs
#     st.markdown("### 📈 Recent Jobs")
    
#     if jobs:
#         recent_jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)[:5]
        
#         for job in recent_jobs:
#             with st.container():
#                 col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
#                 with col1:
#                     st.markdown(f"**{job['name']}**")
#                     st.caption(job['description'] or "No description")
                
#                 with col2:
#                     st.markdown(create_status_badge(job['status']), unsafe_allow_html=True)
                
#                 with col3:
#                     created_date = datetime.fromisoformat(job['created_at']).strftime("%Y-%m-%d %H:%M")
#                     st.caption(f"Created: {created_date}")
                
#                 with col4:
#                     if st.button("View", key=f"view_{job['id']}"):
#                         st.session_state.selected_job = job
#                         st.rerun()
                
#                 st.markdown("---")
#     else:
#         st.info("🎯 No jobs yet. Create your first symbolic regression job!")
#         if st.button("🚀 Create First Job", use_container_width=True):
#             st.session_state.page = "🔬 Create New Job"
#             st.rerun()

# def jobs_page():
#     """Jobs management page"""
#     st.markdown("### 📊 Job Management")
    
#     # Filters
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         status_filter = st.selectbox("Filter by Status", ["All", "created", "running", "completed", "failed"])
#     with col2:
#         sort_by = st.selectbox("Sort by", ["Created Date", "Name", "Status"])
#     with col3:
#         sort_order = st.selectbox("Order", ["Descending", "Ascending"])
    
#     # Filter jobs
#     filtered_jobs = st.session_state.jobs
#     if status_filter != "All":
#         filtered_jobs = [j for j in filtered_jobs if j['status'] == status_filter]
    
#     # Sort jobs
#     if sort_by == "Created Date":
#         filtered_jobs.sort(key=lambda x: x['created_at'], reverse=(sort_order == "Descending"))
#     elif sort_by == "Name":
#         filtered_jobs.sort(key=lambda x: x['name'], reverse=(sort_order == "Descending"))
#     elif sort_by == "Status":
#         filtered_jobs.sort(key=lambda x: x['status'], reverse=(sort_order == "Descending"))
    
#     st.markdown("---")
    
#     # Jobs table
#     if filtered_jobs:
#         for job in filtered_jobs:
#             with st.expander(f"📋 {job['name']} - {create_status_badge(job['status'])}", expanded=False):
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.markdown(f"**Description:** {job['description'] or 'No description'}")
#                     st.markdown(f"**Created:** {datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
#                     if job['started_at']:
#                         st.markdown(f"**Started:** {datetime.fromisoformat(job['started_at']).strftime('%Y-%m-%d %H:%M:%S')}")
#                     if job['completed_at']:
#                         st.markdown(f"**Completed:** {datetime.fromisoformat(job['completed_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                
#                 with col2:
#                     if job['file_path']:
#                         st.markdown(f"**Data File:** ✅ Uploaded")
#                     else:
#                         st.markdown(f"**Data File:** ❌ Not uploaded")
                    
#                     if job['result_path']:
#                         st.markdown(f"**Results:** ✅ Available")
#                     else:
#                         st.markdown(f"**Results:** ❌ Not available")
                
#                 # Action buttons
#                 col1, col2, col3, col4, col5 = st.columns(5)
                
#                 with col1:
#                     if st.button("👁️ View", key=f"view_job_{job['id']}"):
#                         view_job_details(job)
                
#                 with col2:
#                     if st.button("✏️ Edit", key=f"edit_job_{job['id']}"):
#                         edit_job(job)
                
#                 with col3:
#                     if job['status'] == 'created' and job['file_path']:
#                         if st.button("🚀 Run", key=f"run_job_{job['id']}"):
#                             submit_job(job['id'])
                
#                 with col4:
#                     if job['status'] == 'completed' and job['result_path']:
#                         if st.button("📊 Results", key=f"results_job_{job['id']}"):
#                             show_job_results(job)
                
#                 with col5:
#                     if st.button("🗑️ Delete", key=f"delete_job_{job['id']}"):
#                         delete_job(job['id'])
#     else:
#         st.info("No jobs found with the selected filters.")

# def create_job_page():
#     """Create new job page"""
#     st.markdown("### 🔬 Create New Symbolic Regression Job")
    
#     with st.form("create_job_form"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             job_name = st.text_input("Job Name *", placeholder="e.g., Stock Price Prediction")
#             job_description = st.text_area("Description", placeholder="Brief description of your regression task...")
        
#         with col2:
#             st.markdown("#### 📊 Data Upload")
#             uploaded_file = st.file_uploader(
#                 "Choose CSV file",
#                 type=['csv'],
#                 help="Upload CSV file with features in columns and target in the last column"
#             )
        
#         st.markdown("#### ⚙️ Model Configuration")
        
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             maxsize = st.slider("Max Equation Size", 5, 50, 20, help="Maximum complexity of equations")
#             niterations = st.slider("Iterations", 10, 1000, 40, help="Number of iterations to run")
#             populations = st.slider("Populations", 1, 20, 8, help="Number of populations")
        
#         with col2:
#             binary_ops = st.multiselect(
#                 "Binary Operators",
#                 ["+", "-", "*", "/", "^", "max", "min"],
#                 default=["+", "-", "*", "/"],
#                 help="Mathematical operations between two variables"
#             )
            
#             unary_ops = st.multiselect(
#                 "Unary Operators", 
#                 ["cos", "sin", "exp", "log", "sqrt", "abs", "inv"],
#                 default=["cos", "sin", "exp"],
#                 help="Mathematical functions of single variables"
#             )
        
#         with col3:
#             parsimony = st.slider("Parsimony", 0.0, 0.1, 0.0032, 0.0001, help="Penalty for complex equations")
#             maxdepth = st.slider("Max Depth", 3, 20, 10, help="Maximum nesting depth")
            
#             model_selection = st.selectbox(
#                 "Model Selection",
#                 ["best", "accuracy", "score"],
#                 help="How to select the best equation"
#             )
        
#         st.markdown("#### 🎯 Advanced Options")
        
#         with st.expander("Advanced Configuration", expanded=False):
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 timeout = st.number_input("Timeout (seconds)", min_value=0, value=0, help="0 = no timeout")
#                 turbo = st.checkbox("Turbo Mode", help="Faster evaluation (experimental)")
#                 warm_start = st.checkbox("Warm Start", help="Continue from previous run")
            
#             with col2:
#                 precision = st.selectbox("Precision", [32, 64], index=0, help="Computation precision")
#                 verbosity = st.slider("Verbosity", 0, 2, 1, help="Output detail level")
        
#         # Submit button
#         submitted = st.form_submit_button("🚀 Create Job", use_container_width=True)
        
#         if submitted:
#             if not job_name:
#                 st.error("⚠️ Please provide a job name")
#             elif not uploaded_file:
#                 st.error("⚠️ Please upload a data file")
#             else:
#                 # Create job configuration
#                 config = {
#                     "model_config": {
#                         "maxsize": maxsize,
#                         "niterations": niterations,
#                         "populations": populations,
#                         "binary_operators": binary_ops,
#                         "unary_operators": unary_ops,
#                         "parsimony": parsimony,
#                         "maxdepth": maxdepth,
#                         "model_selection": model_selection,
#                         "turbo": turbo,
#                         "warm_start": warm_start,
#                         "precision": precision,
#                         "verbosity": verbosity
#                     }
#                 }
                
#                 if timeout > 0:
#                     config["model_config"]["timeout_in_seconds"] = timeout
                
#                 # Create job
#                 response = make_request("POST", "/jobs", {
#                     "name": job_name,
#                     "description": job_description,
#                     "config": config
#                 })
                
#                 if "job" in response:
#                     job_id = response["job"]["id"]
#                     st.success(f"✅ Job '{job_name}' created successfully!")
                    
#                     # Upload file
#                     files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
#                     upload_response = make_request("POST", f"/jobs/{job_id}/upload", files=files)
                    
#                     if "message" in upload_response and "successfully" in upload_response["message"]:
#                         st.success("✅ Data file uploaded successfully!")
                        
#                         # Auto-submit job
#                         if st.button("🚀 Submit Job for Execution"):
#                             submit_response = make_request("POST", f"/jobs/{job_id}/submit")
#                             if "message" in submit_response:
#                                 st.success("✅ Job submitted for execution!")
#                                 time.sleep(2)
#                                 st.rerun()
#                     else:
#                         st.error(f"❌ File upload failed: {upload_response.get('detail', 'Unknown error')}")
#                 else:
#                     st.error(f"❌ Job creation failed: {response.get('detail', 'Unknown error')}")

# def view_job_details(job):
#     """View detailed job information"""
#     st.markdown(f"### 📋 Job Details: {job['name']}")
    
#     # Job info
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown(f"**Status:** {create_status_badge(job['status'])}", unsafe_allow_html=True)
#         st.markdown(f"**Created:** {datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    
#     with col2:
#         if job['started_at']:
#             st.markdown(f"**Started:** {datetime.fromisoformat(job['started_at']).strftime('%Y-%m-%d %H:%M:%S')}")
#         if job['completed_at']:
#             st.markdown(f"**Completed:** {datetime.fromisoformat(job['completed_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    
#     with col3:
#         if job['started_at'] and job['completed_at']:
#             duration = format_duration(job['started_at'], job['completed_at'])
#             st.markdown(f"**Duration:** {duration}")
    
#     # Description
#     if job['description']:
#         st.markdown(f"**Description:** {job['description']}")
    
#     # Configuration
#     with st.expander("⚙️ Model Configuration", expanded=False):
#         config = job.get('config', {})
#         if config:
#             st.json(config)
#         else:
#             st.info("No configuration available")
    
#     # Job runs
#     st.markdown("### 🔄 Job Runs")
#     runs_response = make_request("GET", f"/jobs/{job['id']}/runs")
    
#     if "job_runs" in runs_response:
#         runs = runs_response["job_runs"]
        
#         if runs:
#             for run in runs:
#                 with st.expander(f"Run {run['run_number']} - {create_status_badge(run['status'])}", expanded=False):
#                     col1, col2 = st.columns(2)
                    
#                     with col1:
#                         if run['started_at']:
#                             st.markdown(f"**Started:** {datetime.fromisoformat(run['started_at']).strftime('%Y-%m-%d %H:%M:%S')}")
#                         if run['completed_at']:
#                             st.markdown(f"**Completed:** {datetime.fromisoformat(run['completed_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                    
#                     with col2:
#                         if run['started_at'] and run['completed_at']:
#                             duration = format_duration(run['started_at'], run['completed_at'])
#                             st.markdown(f"**Duration:** {duration}")
                    
#                     if run['error_message']:
#                         st.error(f"Error: {run['error_message']}")
                    
#                     if run['result_data']:
#                         st.markdown("**Results:**")
#                         result_data = run['result_data']
#                         if isinstance(result_data, str):
#                             result_data = json.loads(result_data)
                        
#                         if 'equations' in result_data:
#                             equations = result_data['equations']
#                             st.markdown(f"Found {len(equations)} equations")
                            
#                             # Show best equation
#                             if equations:
#                                 best_eq = equations[0]
#                                 st.markdown(f"**Best Equation:** `{best_eq['equation']}`")
#                                 st.markdown(f"**Loss:** {best_eq['loss']:.6f}")
#                                 st.markdown(f"**Complexity:** {best_eq['complexity']}")
#         else:
#             st.info("No runs found for this job")
    
#     # Action buttons
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         if job['status'] == 'created' and job['file_path']:
#             if st.button("🚀 Submit Job"):
#                 submit_job(job['id'])
    
#     with col2:
#         if job['status'] == 'running':
#             if st.button("🔄 Refresh Status"):
#                 st.rerun()
    
#     with col3:
#         if job['status'] == 'completed' and job['result_path']:
#             if st.button("📊 View Results"):
#                 show_job_results(job)
    
#     with col4:
#         if st.button("🗑️ Delete Job"):
#             delete_job(job['id'])

# def show_job_results(job):
#     """Show job results with visualizations"""
#     st.markdown(f"### 📊 Results: {job['name']}")
    
#     # Get latest job run with results
#     runs_response = make_request("GET", f"/jobs/{job['id']}/runs")
    
#     if "job_runs" in runs_response:
#         runs = runs_response["job_runs"]
#         completed_runs = [r for r in runs if r['status'] == 'completed' and r['result_data']]
        
#         if completed_runs:
#             latest_run = completed_runs[-1]  # Get latest completed run
#             result_data = latest_run['result_data']
            
#             if isinstance(result_data, str):
#                 result_data = json.loads(result_data)
            
#             if 'equations' in result_data:
#                 equations = result_data['equations']
                
#                 # Summary metrics
#                 col1, col2, col3, col4 = st.columns(4)
                
#                 with col1:
#                     st.metric("🧮 Total Equations", len(equations))
                
#                 with col2:
#                     best_loss = min(eq['loss'] for eq in equations)
#                     st.metric("🎯 Best Loss", f"{best_loss:.6f}")
                
#                 with col3:
#                     avg_complexity = sum(eq['complexity'] for eq in equations) / len(equations)
#                     st.metric("📊 Avg Complexity", f"{avg_complexity:.1f}")
                
#                 with col4:
#                     best_score = max(eq['score'] for eq in equations)
#                     st.metric("⭐ Best Score", f"{best_score:.4f}")
                
#                 st.markdown("---")
                
#                 # Best equations
#                 st.markdown("### 🏆 Top Equations")
                
#                 # Sort by score (higher is better)
#                 sorted_equations = sorted(equations, key=lambda x: x['score'], reverse=True)
#                 top_equations = sorted_equations[:5]
                
#                 for i, eq in enumerate(top_equations, 1):
#                     with st.container():
#                         st.markdown(f"**#{i} Equation:**")
                        
#                         # Equation display
#                         st.markdown(f"""
#                         <div class="equation-display">
#                             {eq['equation']}
#                         </div>
#                         """, unsafe_allow_html=True)
                        
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Loss", f"{eq['loss']:.6f}")
#                         with col2:
#                             st.metric("Complexity", eq['complexity'])
#                         with col3:
#                             st.metric("Score", f"{eq['score']:.4f}")
                        
#                         st.markdown("---")
                
#                 # Visualizations
#                 st.markdown("### 📈 Analysis")
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     # Complexity vs Performance
#                     fig = plot_equation_complexity(equations)
#                     st.plotly_chart(fig, use_container_width=True)
                
#                 with col2:
#                     # Loss distribution
#                     losses = [eq['loss'] for eq in equations]
#                     fig = px.histogram(
#                         x=losses,
#                         bins=20,
#                         title="Loss Distribution",
#                         labels={'x': 'Loss', 'y': 'Count'},
#                         template="plotly_white"
#                     )
#                     st.plotly_chart(fig, use_container_width=True)
                
#                 # Equation table
#                 st.markdown("### 📋 All Equations")
                
#                 df = pd.DataFrame(equations)
#                 df = df[['equation', 'loss', 'complexity', 'score']].round(6)
#                 df.index = df.index + 1  # Start from 1
                
#                 st.dataframe(
#                     df,
#                     use_container_width=True,
#                     column_config={
#                         "equation": "Equation",
#                         "loss": st.column_config.NumberColumn("Loss", format="%.6f"),
#                         "complexity": "Complexity",
#                         "score": st.column_config.NumberColumn("Score", format="%.4f")
#                     }
#                 )
                
#                 # Download results
#                 st.markdown("### 💾 Download Results")
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     # CSV download
#                     csv = df.to_csv(index=False)
#                     st.download_button(
#                         label="📄 Download CSV",
#                         data=csv,
#                         file_name=f"{job['name']}_results.csv",
#                         mime="text/csv"
#                     )
                
#                 with col2:
#                     # JSON download
#                     json_data = json.dumps(result_data, indent=2)
#                     st.download_button(
#                         label="📋 Download JSON",
#                         data=json_data,
#                         file_name=f"{job['name']}_results.json",
#                         mime="application/json"
#                     )
#         else:
#             st.warning("No completed runs with results found.")
#     else:
#         st.error("Failed to load job runs.")

# def submit_job(job_id):
#     """Submit job for execution"""
#     response = make_request("POST", f"/jobs/{job_id}/submit")
    
#     if "message" in response and "successfully" in response["message"]:
#         st.success("✅ Job submitted successfully!")
        
#         # Show progress monitoring
#         st.markdown("### 🔄 Monitoring Job Progress")
        
#         progress_placeholder = st.empty()
#         status_placeholder = st.empty()
        
#         # Monitor job status
#         for i in range(60):  # Monitor for up to 5 minutes
#             time.sleep(5)
            
#             status_response = make_request("GET", f"/jobs/{job_id}/status")
            
#             if "status" in status_response:
#                 status = status_response["status"]
                
#                 with status_placeholder.container():
#                     st.markdown(f"**Current Status:** {create_status_badge(status)}", unsafe_allow_html=True)
                
#                 if status in ['completed', 'failed']:
#                     break
                
#                 # Update progress bar
#                 progress = min((i + 1) * 100 / 60, 95)  # Don't go to 100% until complete
#                 with progress_placeholder.container():
#                     st.progress(progress / 100)
#                     st.caption(f"Monitoring... ({progress:.0f}%)")
        
#         st.rerun()
#     else:
#         st.error(f"❌ Job submission failed: {response.get('detail', 'Unknown error')}")

# def delete_job(job_id):
#     """Delete a job"""
#     if st.button("⚠️ Confirm Delete", key=f"confirm_delete_{job_id}"):
#         response = make_request("DELETE", f"/jobs/{job_id}")
        
#         if "message" in response and "successfully" in response["message"]:
#             st.success("✅ Job deleted successfully!")
#             time.sleep(1)
#             st.rerun()
#         else:
#             st.error(f"❌ Job deletion failed: {response.get('detail', 'Unknown error')}")

# def edit_job(job):
#     """Edit job configuration"""
#     st.markdown(f"### ✏️ Edit Job: {job['name']}")
    
#     with st.form(f"edit_job_{job['id']}"):
#         new_name = st.text_input("Job Name", value=job['name'])
#         new_description = st.text_area("Description", value=job['description'] or "")
        
#         # Configuration editing
#         config = job.get('config', {})
#         model_config = config.get('model_config', {})
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             maxsize = st.slider("Max Equation Size", 5, 50, model_config.get('maxsize', 20))
#             niterations = st.slider("Iterations", 10, 1000, model_config.get('niterations', 40))
        
#         with col2:
#             parsimony = st.slider("Parsimony", 0.0, 0.1, model_config.get('parsimony', 0.0032), 0.0001)
#             maxdepth = st.slider("Max Depth", 3, 20, model_config.get('maxdepth', 10))
        
#         submitted = st.form_submit_button("💾 Update Job")
        
#         if submitted:
#             updated_config = {
#                 "model_config": {
#                     **model_config,
#                     "maxsize": maxsize,
#                     "niterations": niterations,
#                     "parsimony": parsimony,
#                     "maxdepth": maxdepth
#                 }
#             }
            
#             response = make_request("PUT", f"/jobs/{job['id']}", {
#                 "name": new_name,
#                 "description": new_description,
#                 "config": updated_config
#             })
            
#             if "message" in response and "successfully" in response["message"]:
#                 st.success("✅ Job updated successfully!")
#                 time.sleep(1)
#                 st.rerun()
#             else:
#                 st.error(f"❌ Job update failed: {response.get('detail', 'Unknown error')}")

# def analytics_page():
#     """Analytics and insights page"""
#     st.markdown("### 📈 Analytics & Insights")
    
#     jobs = st.session_state.jobs
    
#     if not jobs:
#         st.info("📊 No data available for analytics. Create some jobs first!")
#         return
    
#     # Time series analysis
#     st.markdown("#### 📅 Job Creation Timeline")
    
#     df_jobs = pd.DataFrame(jobs)
#     df_jobs['created_date'] = pd.to_datetime(df_jobs['created_at']).dt.date
    
#     job_counts = df_jobs.groupby(['created_date', 'status']).size().reset_index(name='count')
    
#     fig = px.bar(
#         job_counts,
#         x='created_date',
#         y='count',
#         color='status',
#         title="Jobs Created Over Time",
#         template="plotly_white"
#     )
#     st.plotly_chart(fig, use_container_width=True)
    
#     # Success rate analysis
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.markdown("#### 📊 Job Status Distribution")
#         status_counts = df_jobs['status'].value_counts()
#         fig = px.pie(values=status_counts.values, names=status_counts.index, title="Job Status Distribution")
#         st.plotly_chart(fig, use_container_width=True)
    
#     with col2:
#         st.markdown("#### ⏱️ Average Execution Time")
#         completed_jobs = [j for j in jobs if j['started_at'] and j['completed_at']]
        
#         if completed_jobs:
#             durations = []
#             names = []
            
#             for job in completed_jobs:
#                 start = datetime.fromisoformat(job['started_at'])
#                 end = datetime.fromisoformat(job['completed_at'])
#                 duration = (end - start).total_seconds()
#                 durations.append(duration)
#                 names.append(job['name'][:20] + "..." if len(job['name']) > 20 else job['name'])
            
#             fig = px.bar(x=names, y=durations, title="Job Execution Times (seconds)")
#             fig.update_xaxis(tickangle=45)
#             st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.info("No completed jobs to analyze")
    
#     # Performance insights
#     st.markdown("#### 🎯 Performance Insights")
    
#     insights = []
    
#     # Calculate insights
#     total_jobs = len(jobs)
#     completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
#     failed_jobs = len([j for j in jobs if j['status'] == 'failed'])
    
#     if total_jobs > 0:
#         success_rate = completed_jobs / total_jobs * 100
#         insights.append(f"📈 Success Rate: {success_rate:.1f}%")
        
#         if success_rate < 50:
#             insights.append("⚠️ Low success rate detected. Consider reviewing job configurations.")
#         elif success_rate > 80:
#             insights.append("🎉 Excellent success rate! Your configurations are working well.")
    
#     if completed_jobs > 0 and len([j for j in jobs if j['started_at'] and j['completed_at']]) > 0:
#         avg_duration = sum(
#             (datetime.fromisoformat(j['completed_at']) - datetime.fromisoformat(j['started_at'])).total_seconds()
#             for j in jobs if j['started_at'] and j['completed_at']
#         ) / len([j for j in jobs if j['started_at'] and j['completed_at']])
        
#         insights.append(f"⏱️ Average Duration: {avg_duration/60:.1f} minutes")
        
#         if avg_duration > 1800:  # 30 minutes
#             insights.append("🐌 Long execution times detected. Consider reducing iteration count or complexity.")
    
#     for insight in insights:
#         st.info(insight)

# def settings_page():
#     """Settings and configuration page"""
#     st.markdown("### ⚙️ Settings")
    
#     # User settings
#     st.markdown("#### 👤 User Profile")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.text_input("Username", value=st.session_state.user['username'], disabled=True)
#         st.text_input("Email", value=st.session_state.user['email'], disabled=True)
    
#     with col2:
#         st.text_input("User ID", value=st.session_state.user['id'], disabled=True)
#         created_date = datetime.fromisoformat(st.session_state.user['created_at']).strftime('%Y-%m-%d')
#         st.text_input("Member Since", value=created_date, disabled=True)
    
#     st.markdown("---")
    
#     # Server settings
#     st.markdown("#### 🖥️ Server Configuration")
    
#     # Health check
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("🔍 Check App Server Status"):
#             try:
#                 response = requests.get(f"{APP_SERVER_URL}/health", timeout=5)
#                 if response.status_code == 200:
#                     health_data = response.json()
#                     st.success("✅ App Server is healthy")
#                     st.json(health_data)
#                 else:
#                     st.error(f"❌ App Server unhealthy (HTTP {response.status_code})")
#             except:
#                 st.error("❌ Cannot connect to App Server")
    
#     with col2:
#         if st.button("🔍 Check PySR MCP Server Status"):
#             try:
#                 response = requests.get(f"{PYSR_MCP_URL.replace('/pysr', '/health')}", timeout=5)
#                 if response.status_code == 200:
#                     health_data = response.json()
#                     st.success("✅ PySR MCP Server is healthy")
#                     st.json(health_data)
#                 else:
#                     st.error(f"❌ PySR MCP Server unhealthy (HTTP {response.status_code})")
#             except:
#                 st.error("❌ Cannot connect to PySR MCP Server")
    
#     st.markdown("---")
    
#     # Data management
#     st.markdown("#### 💾 Data Management")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("🔄 Refresh Job Data"):
#             st.session_state.jobs = []
#             st.rerun()
    
#     with col2:
#         if st.button("📊 Export All Jobs"):
#             if st.session_state.jobs:
#                 df = pd.DataFrame(st.session_state.jobs)
#                 csv = df.to_csv(index=False)
#                 st.download_button(
#                     label="📄 Download Jobs CSV",
#                     data=csv,
#                     file_name="pysr_jobs_export.csv",
#                     mime="text/csv"
#                 )
#             else:
#                 st.info("No jobs to export")
    
#     st.markdown("---")
    
#     # Danger zone
#     st.markdown("#### ⚠️ Danger Zone")
#     st.warning("These actions cannot be undone!")
    
#     if st.button("🗑️ Delete All Jobs", type="secondary"):
#         if st.button("⚠️ Confirm Delete All Jobs"):
#             # Note: This would require a batch delete endpoint
#             st.error("Batch delete not implemented yet")

# # Main App Logic
# def main():
#     """Main application logic"""
#     if not st.session_state.authenticated:
#         login_page()
#     else:
#         dashboard_page()

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Streamlit UI - Beautiful Frontend for PySR Job Management
Fixed version with better error handling and fallbacks
"""

import streamlit as st
import sys
import os

# Try to import required packages with fallbacks
try:
    import requests
except ImportError:
    st.error("requests package not found. Please install with: pip install requests")
    st.stop()

try:
    import pandas as pd
except ImportError:
    st.error("pandas package not found. Please install with: pip install pandas")
    st.stop()

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    st.warning("Plotly not available. Visualizations will be limited.")
    PLOTLY_AVAILABLE = False

try:
    import numpy as np
except ImportError:
    st.error("numpy package not found. Please install with: pip install numpy")
    st.stop()

import json
import io
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="PySR - Symbolic Regression Platform",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://pysr.readthedocs.io/',
        'Report a bug': 'https://github.com/MilesCranmer/PySR/issues',
        'About': "# PySR Symbolic Regression Platform\nPowerful symbolic regression with interpretable AI"
    }
)

# Configuration
APP_SERVER_URL = "http://localhost:8000"
PYSR_MCP_URL = "http://localhost:8001"

# Test server connections on startup
def test_server_connections():
    """Test if servers are running"""
    servers_status = {}
    
    # Test App Server
    try:
        response = requests.get(f"{APP_SERVER_URL}/health", timeout=2)
        servers_status["app_server"] = response.status_code == 200
    except:
        servers_status["app_server"] = False
    
    # Test PySR MCP Server
    try:
        response = requests.get(f"{PYSR_MCP_URL.replace('/pysr', '/health')}", timeout=2)
        servers_status["pysr_server"] = response.status_code == 200
    except:
        servers_status["pysr_server"] = False
    
    return servers_status

# Custom CSS for beautiful UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .status-success { color: #28a745; font-weight: 600; }
    .status-warning { color: #ffc107; font-weight: 600; }
    .status-error { color: #dc3545; font-weight: 600; }
    .status-info { color: #17a2b8; font-weight: 600; }
    
    .equation-display {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
        font-size: 1.1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'servers_checked' not in st.session_state:
    st.session_state.servers_checked = False

# Utility Functions
def make_request(method: str, endpoint: str, data: dict = None, files: dict = None) -> dict:
    """Make HTTP request to app server"""
    url = f"{APP_SERVER_URL}{endpoint}"
    headers = {}
    
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code == 401:
            st.session_state.authenticated = False
            st.session_state.token = None
            st.error("Session expired. Please login again.")
            st.rerun()
        
        return response.json()
    
    except requests.exceptions.ConnectionError:
        st.error("🚨 Cannot connect to server. Please ensure the App Server is running on port 8000.")
        return {"error": "Connection failed"}
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Server may be overloaded.")
        return {"error": "Timeout"}
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return {"error": str(e)}

def create_status_badge(status: str) -> str:
    """Create colored status badge"""
    status_colors = {
        "created": ("🟡", "status-warning", "Created"),
        "running": ("🔵", "status-info", "Running"),
        "completed": ("🟢", "status-success", "Completed"),
        "failed": ("🔴", "status-error", "Failed"),
        "pending": ("⚪", "status-info", "Pending")
    }
    
    emoji, css_class, text = status_colors.get(status.lower(), ("⚫", "status-info", status))
    return f"""<span class="{css_class}">{emoji} {text}</span>"""

def plot_simple_chart(data: List[Dict], x_field: str, y_field: str, title: str):
    """Create simple chart with fallback"""
    if not PLOTLY_AVAILABLE:
        df = pd.DataFrame(data)
        st.line_chart(df.set_index(x_field)[y_field])
        return
    
    df = pd.DataFrame(data)
    fig = px.line(df, x=x_field, y=y_field, title=title)
    st.plotly_chart(fig, use_container_width=True)

# Check servers on first run
def check_servers():
    """Check server status and show warnings"""
    if not st.session_state.servers_checked:
        with st.spinner("Checking server connections..."):
            servers_status = test_server_connections()
            
            if not servers_status["app_server"]:
                st.error("❌ App Server (port 8000) is not responding. Please start it with: `python app_server.py`")
            
            if not servers_status["pysr_server"]:
                st.warning("⚠️ PySR MCP Server (port 8001) is not responding. Some features may be limited.")
            
            if servers_status["app_server"]:
                st.success("✅ App Server is running")
            
        st.session_state.servers_checked = True

# Authentication Functions
def login_page():
    """Login page"""
    st.markdown('<div class="main-header"><h1>🧮 PySR Platform</h1><p>Advanced Symbolic Regression with Interpretable AI</p></div>', unsafe_allow_html=True)
    
    # Check servers
    check_servers()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Authentication")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("#### Sign In")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("🚀 Sign In", use_container_width=True)
                
                if login_btn:
                    if username and password:
                        with st.spinner("Signing in..."):
                            response = make_request("POST", "/auth/login", {
                                "username": username,
                                "password": password
                            })
                            
                            if "token" in response:
                                st.session_state.authenticated = True
                                st.session_state.token = response["token"]
                                st.session_state.user = response["user"]
                                st.success("✅ Login successful!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Invalid credentials or server error")
                    else:
                        st.error("⚠️ Please fill in all fields")
        
        with tab2:
            st.markdown("#### Create Account")
            with st.form("register_form"):
                reg_username = st.text_input("Username", placeholder="Choose a username")
                reg_email = st.text_input("Email", placeholder="Enter your email")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a password")
                register_btn = st.form_submit_button("📝 Create Account", use_container_width=True)
                
                if register_btn:
                    if reg_username and reg_email and reg_password:
                        with st.spinner("Creating account..."):
                            response = make_request("POST", "/auth/register", {
                                "username": reg_username,
                                "email": reg_email,
                                "password": reg_password
                            })
                            
                            if "token" in response:
                                st.session_state.authenticated = True
                                st.session_state.token = response["token"]
                                st.session_state.user = response["user"]
                                st.success("✅ Account created successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Registration failed: {response.get('detail', 'Unknown error')}")
                    else:
                        st.error("⚠️ Please fill in all fields")

def dashboard_page():
    """Main dashboard page"""
    st.markdown('<div class="main-header"><h1>🧮 PySR Dashboard</h1><p>Symbolic Regression Made Simple</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.user['username']}! 👋")
        st.markdown("---")
        
        # Navigation
        page = st.selectbox("📍 Navigate", [
            "🏠 Dashboard",
            "📊 Jobs",
            "🔬 Create New Job",
            "⚙️ Settings"
        ])
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
    
    # Load jobs
    with st.spinner("Loading jobs..."):
        jobs_response = make_request("GET", "/jobs")
        if "jobs" in jobs_response:
            st.session_state.jobs = jobs_response["jobs"]
        elif jobs_response.get("error") != "Connection failed":
            st.warning("Unable to load jobs from server")
    
    # Route to selected page
    if page == "🏠 Dashboard":
        dashboard_overview()
    elif page == "📊 Jobs":
        jobs_page()
    elif page == "🔬 Create New Job":
        create_job_page()
    elif page == "⚙️ Settings":
        settings_page()

def dashboard_overview():
    """Dashboard overview"""
    jobs = st.session_state.jobs
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j['status'] == 'completed'])
    running_jobs = len([j for j in jobs if j['status'] == 'running'])
    failed_jobs = len([j for j in jobs if j['status'] == 'failed'])
    
    with col1:
        st.metric("📋 Total Jobs", total_jobs)
    with col2:
        st.metric("✅ Completed", completed_jobs)
    with col3:
        st.metric("🔄 Running", running_jobs)
    with col4:
        st.metric("❌ Failed", failed_jobs)
    
    st.markdown("---")
    
    # Recent Jobs
    st.markdown("### 📈 Recent Jobs")
    
    if jobs:
        recent_jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)[:5]
        
        for i, job in enumerate(recent_jobs):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{job['name']}**")
                st.caption(job['description'] or "No description")
            
            with col2:
                st.markdown(create_status_badge(job['status']), unsafe_allow_html=True)
            
            with col3:
                try:
                    created_date = datetime.fromisoformat(job['created_at']).strftime("%Y-%m-%d %H:%M")
                    st.caption(f"Created: {created_date}")
                except:
                    st.caption("Created: Unknown")
            
            with col4:
                if st.button("View", key=f"view_{i}_{job['id']}"):
                    st.session_state.selected_job = job
                    st.rerun()
            
            st.divider()
    else:
        st.info("🎯 No jobs yet. Create your first symbolic regression job!")
        if st.button("🚀 Create First Job", use_container_width=True):
            # Switch to create job page
            st.rerun()

def jobs_page():
    """Jobs management page"""
    st.markdown("### 📊 Job Management")
    
    jobs = st.session_state.jobs
    
    if not jobs:
        st.info("No jobs found. Create your first job!")
        if st.button("🚀 Create New Job"):
            st.rerun()
        return
    
    # Simple job listing
    for i, job in enumerate(jobs):
        with st.expander(f"📋 {job['name']} - {job['status']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Description:** {job['description'] or 'No description'}")
                try:
                    created_date = datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                    st.markdown(f"**Created:** {created_date}")
                except:
                    st.markdown("**Created:** Unknown")
            
            with col2:
                st.markdown(f"**Status:** {create_status_badge(job['status'])}", unsafe_allow_html=True)
                
                if job['file_path']:
                    st.markdown("**Data File:** ✅ Uploaded")
                else:
                    st.markdown("**Data File:** ❌ Not uploaded")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ View Details", key=f"view_details_{i}"):
                    view_job_details(job)
            
            with col2:
                if job['status'] == 'created' and job['file_path']:
                    if st.button("🚀 Run Job", key=f"run_{i}"):
                        submit_job(job['id'])
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{i}"):
                    if st.button(f"⚠️ Confirm Delete {job['name']}", key=f"confirm_{i}"):
                        delete_job(job['id'])

def create_job_page():
    """Create new job page"""
    st.markdown("### 🔬 Create New Symbolic Regression Job")
    
    with st.form("create_job_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_name = st.text_input("Job Name *", placeholder="e.g., Stock Price Prediction")
            job_description = st.text_area("Description", placeholder="Brief description of your regression task...")
        
        with col2:
            st.markdown("#### 📊 Data Upload")
            uploaded_file = st.file_uploader(
                "Choose CSV file",
                type=['csv'],
                help="Upload CSV file with features in columns and target in the last column"
            )
        
        st.markdown("#### ⚙️ Model Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            maxsize = st.slider("Max Equation Size", 5, 50, 20)
            niterations = st.slider("Iterations", 10, 200, 40)
        
        with col2:
            binary_ops = st.multiselect(
                "Binary Operators",
                ["+", "-", "*", "/"],
                default=["+", "-", "*", "/"]
            )
            
            unary_ops = st.multiselect(
                "Unary Operators", 
                ["cos", "sin", "exp", "log"],
                default=["cos", "sin"]
            )
        
        with col3:
            parsimony = st.slider("Parsimony", 0.0, 0.01, 0.0032, 0.0001)
            maxdepth = st.slider("Max Depth", 3, 15, 8)
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Job", use_container_width=True)
        
        if submitted:
            if not job_name:
                st.error("⚠️ Please provide a job name")
            elif not uploaded_file:
                st.error("⚠️ Please upload a data file")
            else:
                create_job_with_data(job_name, job_description, uploaded_file, {
                    "maxsize": maxsize,
                    "niterations": niterations,
                    "binary_operators": binary_ops,
                    "unary_operators": unary_ops,
                    "parsimony": parsimony,
                    "maxdepth": maxdepth
                })

def create_job_with_data(job_name, job_description, uploaded_file, config):
    """Create job with uploaded data"""
    with st.spinner("Creating job..."):
        # Create job configuration
        job_config = {
            "model_config": config
        }
        
        # Create job
        response = make_request("POST", "/jobs", {
            "name": job_name,
            "description": job_description,
            "config": job_config
        })
        
        if "job" in response:
            job_id = response["job"]["id"]
            st.success(f"✅ Job '{job_name}' created successfully!")
            
            # Upload file
            with st.spinner("Uploading data file..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                upload_response = make_request("POST", f"/jobs/{job_id}/upload", files=files)
                
                if "message" in upload_response and "successfully" in upload_response.get("message", ""):
                    st.success("✅ Data file uploaded successfully!")
                    
                    # Option to submit job immediately
                    if st.button("🚀 Submit Job for Execution"):
                        submit_job(job_id)
                else:
                    st.error(f"❌ File upload failed: {upload_response.get('detail', 'Unknown error')}")
        else:
            st.error(f"❌ Job creation failed: {response.get('detail', 'Unknown error')}")

def view_job_details(job):
    """View detailed job information"""
    st.markdown(f"### 📋 Job Details: {job['name']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Status:** {create_status_badge(job['status'])}", unsafe_allow_html=True)
        try:
            created_date = datetime.fromisoformat(job['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            st.markdown(f"**Created:** {created_date}")
        except:
            st.markdown("**Created:** Unknown")
    
    with col2:
        if job.get('started_at'):
            try:
                started_date = datetime.fromisoformat(job['started_at']).strftime('%Y-%m-%d %H:%M:%S')
                st.markdown(f"**Started:** {started_date}")
            except:
                pass
        
        if job.get('completed_at'):
            try:
                completed_date = datetime.fromisoformat(job['completed_at']).strftime('%Y-%m-%d %H:%M:%S')
                st.markdown(f"**Completed:** {completed_date}")
            except:
                pass
    
    if job['description']:
        st.markdown(f"**Description:** {job['description']}")
    
    # Configuration
    if job.get('config'):
        with st.expander("⚙️ Model Configuration", expanded=False):
            st.json(job['config'])

def submit_job(job_id):
    """Submit job for execution"""
    with st.spinner("Submitting job..."):
        response = make_request("POST", f"/jobs/{job_id}/submit")
        
        if "message" in response and "successfully" in response.get("message", ""):
            st.success("✅ Job submitted successfully!")
            
            # Simple progress indicator
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(10):
                progress_bar.progress((i + 1) * 10)
                status_text.text(f"Monitoring job progress... {(i + 1) * 10}%")
                time.sleep(2)
                
                # Check status
                status_response = make_request("GET", f"/jobs/{job_id}/status")
                if "status" in status_response:
                    current_status = status_response["status"]
                    status_text.text(f"Current Status: {current_status}")
                    
                    if current_status in ['completed', 'failed']:
                        break
            
            st.rerun()
        else:
            st.error(f"❌ Job submission failed: {response.get('detail', 'Unknown error')}")

def delete_job(job_id):
    """Delete a job"""
    with st.spinner("Deleting job..."):
        response = make_request("DELETE", f"/jobs/{job_id}")
        
        if "message" in response and "successfully" in response.get("message", ""):
            st.success("✅ Job deleted successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"❌ Job deletion failed: {response.get('detail', 'Unknown error')}")

def settings_page():
    """Settings and configuration page"""
    st.markdown("### ⚙️ Settings")
    
    # User settings
    st.markdown("#### 👤 User Profile")
    
    if st.session_state.user:
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Username", value=st.session_state.user.get('username', 'Unknown'), disabled=True)
            st.text_input("Email", value=st.session_state.user.get('email', 'Unknown'), disabled=True)
        
        with col2:
            st.text_input("User ID", value=st.session_state.user.get('id', 'Unknown'), disabled=True)
            try:
                created_date = datetime.fromisoformat(st.session_state.user['created_at']).strftime('%Y-%m-%d')
                st.text_input("Member Since", value=created_date, disabled=True)
            except:
                st.text_input("Member Since", value="Unknown", disabled=True)
    
    st.markdown("---")
    
    # Server health checks
    st.markdown("#### 🖥️ Server Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Check App Server"):
            try:
                response = requests.get(f"{APP_SERVER_URL}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ App Server is healthy")
                    st.json(response.json())
                else:
                    st.error(f"❌ App Server returned HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to App Server: {str(e)}")
    
    with col2:
        if st.button("🔍 Check PySR Server"):
            try:
                response = requests.get(f"{PYSR_MCP_URL.replace('/pysr', '/health')}", timeout=5)
                if response.status_code == 200:
                    st.success("✅ PySR MCP Server is healthy")
                    st.json(response.json())
                else:
                    st.error(f"❌ PySR Server returned HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to PySR Server: {str(e)}")

# Main App Logic
def main():
    """Main application logic"""
    try:
        if not st.session_state.authenticated:
            login_page()
        else:
            dashboard_page()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.markdown("### Troubleshooting:")
        st.markdown("1. Make sure App Server is running on port 8000")
        st.markdown("2. Check if all required packages are installed")
        st.markdown("3. Restart Streamlit with: `streamlit run streamlit_ui_fixed.py`")

if __name__ == "__main__":
    main()