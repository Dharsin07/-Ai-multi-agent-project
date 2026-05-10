import streamlit as st
import sys
import os
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from services.working_crew_manager import WorkingCrewManager
from utils.logger import logger

# Configure Streamlit page
st.set_page_config(page_title="TRAVA AI OS - Live", page_icon="🌐", layout="wide", initial_sidebar_state="expanded")

# Inject Custom CSS for dark glassmorphism
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0e;
        color: #f0f0f5;
        font-family: 'Inter', sans-serif;
    }
    .stSidebar {
        background-color: rgba(20, 20, 28, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #fff 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .glass-card {
        background: rgba(20, 20, 28, 0.6);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
    .status-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #06b6d4;
        box-shadow: 0 0 10px #06b6d4;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(6, 182, 212, 0); }
        100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0); }
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## <span class='status-pulse'></span> TRAVA AI OS Live", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### System Status")
    
    # API Status indicators
    api_status = {
        'Groq LLM': bool(os.getenv('GROQ_API_KEY')),
        'Serper Search': bool(os.getenv('SERPER_API_KEY')),
        'OpenWeatherMap': bool(os.getenv('OPENWEATHERMAP_API_KEY'))
    }
    
    for api, status in api_status.items():
        status_color = "✅" if status else "❌"
        st.markdown(f"{status_color} {api}")
    
    st.markdown("---")
    st.info("✨ Ready for travel planning")

# Main Dashboard
st.title("Autonomous Travel Command Center - Live")

# Initialize crew manager
@st.cache_resource
def get_crew_manager():
    return WorkingCrewManager()

crew_manager = get_crew_manager()

# Quick Template Buttons
st.markdown("**Quick Templates:**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🧳 Your Chennai-Bangalore Plan", help="Your specific travel plan"):
        st.session_state.template_request = "Chennai to Bangalore flight booking date May 25, my budget is 15k. May 25 booking for budget-friendly hotel booking for above 4 rating."

with col2:
    if st.button("🌤 Weather Check", help="Quick weather inquiry"):
        st.session_state.template_request = "What's the weather like in Bangalore for May 25?"

with col3:
    if st.button("🔍 General Search", help="Travel research"):
        st.session_state.template_request = "Search for best travel tips for Bangalore visit"

st.markdown("---")

# Universal Input Section
st.markdown("### 🎯 Universal Task Input")
st.markdown("Enter your travel request - AI will process with real-time data")

with st.form("universal_input"):
    user_request = st.text_area(
        "What would you like to accomplish?",
        placeholder="Enter your travel request here...",
        height=120,
        help="The AI will use Groq LLM, Serper Search, and OpenWeatherMap to create your plan"
    )
    
    # Use template request if available
    if hasattr(st.session_state, 'template_request') and st.session_state.template_request:
        user_request = st.session_state.template_request
        del st.session_state.template_request
    
    submit = st.form_submit_button("🚀 Generate Travel Plan with AI", use_container_width=True)

if submit and user_request:
    st.markdown("---")
    st.markdown("### 🤖 AI Processing with Real-time Data")
    
    # Progress tracking
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # Step 1: Extract details
        status_placeholder.info("🔍 Analyzing your request...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        # Step 2: Get weather data
        status_placeholder.info("🌤️ Fetching real-time weather data...")
        progress_bar.progress(40)
        time.sleep(0.5)
        
        # Step 3: Search for travel information
        status_placeholder.info("🔍 Searching web for flights and hotels...")
        progress_bar.progress(60)
        time.sleep(0.5)
        
        # Step 4: Generate AI plan
        status_placeholder.info("🤖 Generating AI-powered travel plan...")
        progress_bar.progress(80)
        
        # Run the actual travel planning
        result = crew_manager.run_travel_planning(user_request)
        
        progress_bar.progress(100)
        
        if result['success']:
            status_placeholder.success("✨ Travel plan generated successfully!")
            
            # Display results
            travel_plan = result['travel_plan']
            travel_details = result['travel_details']
            
            # Travel Details Card
            st.markdown("#### 📋 Trip Overview")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Origin", travel_details['origin'])
            with col2:
                st.metric("Destination", travel_details['destination'])
            with col3:
                st.metric("Date", travel_details['date'])
            with col4:
                st.metric("Budget", travel_details['budget'])
            
            # Weather Information
            if result['weather_data'].get('success'):
                weather = result['weather_data']['current']
                st.markdown("---")
                st.markdown("#### 🌤️ Weather Information")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Temperature", f"{weather['temperature']}°C")
                with col2:
                    st.metric("Feels Like", f"{weather['feels_like']}°C")
                with col3:
                    st.metric("Humidity", f"{weather['humidity']}%")
                with col4:
                    st.metric("Condition", weather['condition'].title())
            
            # Search Results Status
            if result['search_data'].get('success'):
                search = result['search_data']
                st.markdown("---")
                st.markdown("#### 🔍 Data Sources")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.success("✅ Flight Data Found" if search.get('flights') else "⚠️ Flight Data Limited")
                with col2:
                    st.success("✅ Hotel Data Found" if search.get('hotels') else "⚠️ Hotel Data Limited")
                with col3:
                    st.success("✅ Travel Tips Found" if search.get('tips') else "⚠️ Tips Data Limited")
            
            # AI-Generated Travel Plan
            if 'llm_generated_plan' in travel_plan:
                st.markdown("---")
                st.markdown("#### 🤖 AI-Generated Travel Plan")
                st.markdown(f"""
                <div class="glass-card">
                    {travel_plan['llm_generated_plan']}
                </div>
                """, unsafe_allow_html=True)
            
            # Recommendations
            if travel_plan.get('recommendations'):
                st.markdown("---")
                st.markdown("#### 💡 AI Recommendations")
                for i, rec in enumerate(travel_plan['recommendations'], 1):
                    st.markdown(f"{i}. {rec}")
            
            # Budget Information
            budget_info = travel_plan.get('budget_estimates', {})
            if budget_info:
                st.markdown("---")
                st.markdown("#### 💰 Budget Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Estimate", budget_info.get('total_estimate', 'N/A'))
                with col2:
                    st.metric("Flight Cost", budget_info.get('flight_cost', 'N/A'))
            
            # Metadata
            st.markdown("---")
            st.markdown("#### 🔧 System Information")
            metadata = result['metadata']
            st.markdown(f"""
            - **Generated at**: {metadata['generated_at']}
            - **Data Sources**: {', '.join(metadata['data_sources'])}
            - **Processing**: Real-time with AI
            """)
            
        else:
            status_placeholder.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        status_placeholder.error(f"❌ Processing error: {str(e)}")
        st.error("Please try again or check your API configuration")

elif submit and not user_request:
    st.warning("⚠️ Please enter a travel request above.")

# Footer
st.markdown("---")
st.markdown("*Powered by Groq LLM, Serper Search, and OpenWeatherMap*")
