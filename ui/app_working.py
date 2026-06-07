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
from services.autonomous_booking_agent import AutonomousBookingAgent
from services.fully_automated_booking_agent import FullyAutomatedBookingAgent
from tools.correct_booking_automation import CorrectBookingAutomation
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

# Initialize crew managers
@st.cache_resource
def get_crew_manager():
    return WorkingCrewManager()

@st.cache_resource
def get_autonomous_agent():
    return AutonomousBookingAgent()

@st.cache_resource
def get_fully_automated_agent():
    return FullyAutomatedBookingAgent()

crew_manager = get_crew_manager()
autonomous_agent = get_autonomous_agent()
fully_automated_agent = get_fully_automated_agent()

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

# Add Chennai-Goa autonomous booking template
col4, col5 = st.columns(2)
with col4:
    if st.button("🚀 Chennai-Goa Auto-Booking", help="Autonomous booking demo"):
        st.session_state.template_request = "Book Chennai to Goa flight for June 10 under 8000"

with col5:
    if st.button("🤖 FULLY AUTO Booking", help="Complete end-to-end automation"):
        st.session_state.template_request = "Book Chennai to Bangalore flight for May 25 under 8000"
        st.session_state.fully_auto_mode = True

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
    
    # Check if fully automated mode is requested
    is_fully_auto = hasattr(st.session_state, 'fully_auto_mode') and st.session_state.fully_auto_mode
    is_booking_request = any(keyword in user_request.lower() for keyword in ['book', 'booking', 'flight', 'hotel'])
    
    if is_fully_auto and is_booking_request:
        st.markdown("### 🤖 FULLY AUTOMATED BOOKING AGENT")
        st.warning("🚀 This will automatically book your flight after AI analysis!")
        
        # Collect passenger info for fully automated booking
        st.markdown("#### 📝 Passenger Information Required")
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", key="auto_first_name")
            phone = st.text_input("Phone Number*", key="auto_phone")
        with col2:
            last_name = st.text_input("Last Name*", key="auto_last_name")
            email = st.text_input("Email*", key="auto_email")
        
        passenger_info_provided = all([first_name, last_name, email, phone])
        
        if not passenger_info_provided:
            st.error("⚠️ Please fill in all passenger information fields for automated booking")
            st.stop()
        
        passenger_info = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone
        }
        
    elif is_booking_request:
        st.markdown("### 🤖 Autonomous AI Booking Agent")
    else:
        st.markdown("### 🤖 AI Processing with Real-time Data")
    
    # Progress tracking
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    try:
        if is_fully_auto and is_booking_request and passenger_info_provided:
            # Use fully automated booking agent
            status_placeholder.info("🔍 Phase 1: LLM Analysis...")
            progress_bar.progress(15)
            time.sleep(0.5)
            
            status_placeholder.info("🎯 Phase 2: Intelligent Flight Selection...")
            progress_bar.progress(35)
            time.sleep(0.5)
            
            status_placeholder.info("🤖 Phase 3: Automatic Booking Execution...")
            progress_bar.progress(55)
            time.sleep(0.5)
            
            status_placeholder.info("📸 Phase 4: Form Filling & Screenshots...")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            status_placeholder.info("💳 Phase 5: Ready for Manual Payment...")
            progress_bar.progress(90)
            
            # Run fully automated booking
            import asyncio
            def run_fully_automated_booking():
                try:
                    loop = asyncio.new_event_loop()
                    task = loop.create_task(fully_automated_agent.process_and_book_automatically(user_request, passenger_info))
                    return loop.run_until_complete(task)
                except Exception as e:
                    return {'success': False, 'error': str(e), 'phase': 'automation_failed'}
            
            result = run_fully_automated_booking()
            progress_bar.progress(100)
            
            # Clear fully auto mode
            if hasattr(st.session_state, 'fully_auto_mode'):
                del st.session_state.fully_auto_mode
                
        elif is_booking_request:
            # Use autonomous booking agent
            status_placeholder.info("🔍 Analyzing travel booking request...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status_placeholder.info("📋 Extracting travel details...")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            status_placeholder.info("🔍 Searching for best options...")
            progress_bar.progress(60)
            time.sleep(0.5)
            
            status_placeholder.info("✈️ Selecting budget-friendly flight...")
            progress_bar.progress(80)
            
            # Run autonomous booking agent
            result = autonomous_agent.process_travel_request(user_request)
            
            progress_bar.progress(100)
        else:
            # Use regular travel planning
            status_placeholder.info("🔍 Analyzing your request...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status_placeholder.info("🌤️ Fetching real-time weather data...")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            status_placeholder.info("🔍 Searching web for flights and hotels...")
            progress_bar.progress(60)
            time.sleep(0.5)
            
            status_placeholder.info("🤖 Generating AI-powered travel plan...")
            progress_bar.progress(80)
            
            # Run the actual travel planning
            result = crew_manager.run_travel_planning(user_request)
            
            progress_bar.progress(100)
        
        if result['success']:
            if is_fully_auto and is_booking_request and passenger_info_provided:
                status_placeholder.success("✨ Fully automated booking completed!")
                
                # Display fully automated booking results
                st.markdown("#### 🎯 Fully Automated Booking Results")
                
                # Phase results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("LLM Analysis", "✅ Complete")
                with col2:
                    st.metric("Flight Selection", "✅ Complete")
                with col3:
                    st.metric("Booking Execution", "✅ Complete")
                
                # Travel Details
                st.markdown("---")
                st.markdown("#### 📋 Travel Details")
                analysis = result.get('analysis', {})
                travel_details = analysis.get('travel_details', {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Source", travel_details.get('source', 'N/A'))
                with col2:
                    st.metric("Destination", travel_details.get('destination', 'N/A'))
                with col3:
                    st.metric("Date", travel_details.get('departure_date', 'N/A'))
                with col4:
                    st.metric("Budget", travel_details.get('budget', 'N/A'))
                
                # Flight Selection Results
                st.markdown("---")
                st.markdown("#### ✈️ Flight Selection Results")
                flight_selection = result.get('flight_selection', {})
                selected_flight = flight_selection.get('selected_flight', {})
                
                if selected_flight.get('success'):
                    st.success(f"✅ Flight selected: {selected_flight.get('reason', 'Best option')}")
                    st.info(f"🔗 Booking URL: {selected_flight.get('booking_url', 'N/A')}")
                else:
                    st.warning("⚠️ Flight selection encountered issues")
                
                # Booking Execution Results
                st.markdown("---")
                st.markdown("#### 🤖 Booking Execution Results")
                booking = result.get('booking', {})
                automation_result = booking.get('automation_result', {})
                
                if automation_result.get('success'):
                    st.success("✅ Booking forms filled successfully!")
                    st.info("📸 Screenshots captured for verification")
                    
                    # Display screenshots if available
                    screenshots = automation_result.get('screenshots', [])
                    if screenshots:
                        st.markdown("#### 📸 Booking Screenshots")
                        for i, screenshot in enumerate(screenshots, 1):
                            try:
                                st.image(screenshot, caption=f"Step {i}: Booking Process")
                            except:
                                st.info(f"Screenshot {i}: {screenshot}")
                else:
                    st.error(f"❌ Booking execution failed: {automation_result.get('error', 'Unknown error')}")
                
                # Final Instructions
                st.markdown("---")
                st.markdown("#### 💳 Next Steps")
                st.success("🎉 Automation completed! Your browser should be open with filled booking forms.")
                st.warning("⚠️ Complete the payment manually to confirm your booking.")
                st.info("📸 Check the screenshots above for verification of filled details.")
                
            elif is_booking_request:
                status_placeholder.success("✨ Autonomous booking agent completed!")
                
                # Display booking results
                travel_details = result['travel_details']
                execution_result = result['execution_result']
                booking_automation = result['booking_automation']
                
                # Travel Details Card
                st.markdown("#### 📋 Travel Details")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Source", travel_details['source'])
                with col2:
                    st.metric("Destination", travel_details['destination'])
                with col3:
                    st.metric("Date", travel_details['departure_date'])
                with col4:
                    st.metric("Budget", travel_details['budget'])
                
                # Selected Options
                st.markdown("---")
                st.markdown("#### ✈️ Selected Flight Option")
                selected_flight = execution_result['selected_options'].get('flight', {})
                if selected_flight.get('success'):
                    st.success(f"✅ Flight selected: {selected_flight.get('reason', 'Best option')}")
                    st.info(f"🔗 Booking URL: {selected_flight.get('booking_url', 'N/A')}")
                
                # Search Results Summary
                st.markdown("---")
                st.markdown("#### 🔍 Search Results")
                search_results = execution_result['search_results']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    flights_found = search_results.get('flights', {}).get('total_results', 0)
                    st.metric("Flights Found", flights_found)
                with col2:
                    hotels_found = search_results.get('hotels', {}).get('total_results', 0)
                    st.metric("Hotels Found", hotels_found)
                with col3:
                    weather_status = search_results.get('weather', {}).get('success', False)
                    st.metric("Weather Available", "✅" if weather_status else "❌")
                
                # Booking Automation Status
                st.markdown("---")
                st.markdown("#### 🤖 Booking Automation Status")
                
                if booking_automation.get('ready'):
                    st.success("✅ Ready for automated form filling")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"🔗 Flight Booking: {booking_automation['flight_booking']['status']}")
                    with col2:
                        st.info(f"🔗 Hotel Booking: {booking_automation['hotel_booking']['status']}")
                    
                    st.warning("⚠️  System will autofill forms and STOP at payment page")
                    st.info("🛡️  Safety: Manual payment confirmation required")
                    
                    # Passenger info needed
                    st.markdown("---")
                    st.markdown("#### 📝 Passenger Information Needed")
                    for field in booking_automation.get('passenger_info_needed', []):
                        st.markdown(f"- {field.replace('_', ' ').title()}")
                    
                    # Browser automation button
                    if st.button("🚀 Start Browser Automation", key="start_browser"):
                        st.info("⚠️  Browser automation will open in a new window")
                        st.warning("Please fill in your passenger details in the form below:")
                        
                        # Simple passenger form
                        with st.form("passenger_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                first_name = st.text_input("First Name")
                                phone = st.text_input("Phone Number")
                            with col2:
                                last_name = st.text_input("Last Name")
                                email = st.text_input("Email")
                            
                            if st.form_submit_button("🤖 Autofill Booking Form"):
                                passenger_info = {
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'email': email,
                                    'phone': phone
                                }
                                
                                st.info("🚀 Starting browser automation...")
                                st.warning("⚠️  Browser will open automatically. Please complete payment manually.")
                                
                                # Run real browser automation
                                try:
                                    # Create sync wrapper for async automation
                                    def run_automation():
                                        try:
                                            loop = asyncio.new_event_loop()
                                            task = loop.create_task(automation.book_chennai_goa_flight(passenger_info))
                                            return loop.run_until_complete(task)
                                        except Exception as e:
                                            return {'success': False, 'error': str(e), 'message': 'Automation failed'}
                                    
                                    automation = CorrectBookingAutomation()
                                    result = run_automation()
                                    
                                    # REAL browser automation runs here
                                    if 'screenshots' in result:
                                        st.markdown("#### 📸 Screenshots Captured")
                                        for i, screenshot in enumerate(result['screenshots'], 1):
                                            st.image(screenshot)
                                            st.markdown(f"{i}. Screenshot")
                                            st.markdown("---")
                                    else:
                                        st.error(f"❌ Automation failed: {result.get('message')}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Browser automation error: {str(e)}")
                                    st.info("Please try again or book manually")
                
                # Task Plan
                st.markdown("---")
                st.markdown("#### 📋 Task Plan")
                task_plan = result['task_plan']
                
                with st.expander("View Task Plan"):
                    st.markdown("**Search Tasks:**")
                    for task in task_plan['search_tasks']:
                        st.markdown(f"- {task}")
                    
                    st.markdown("**Validation Tasks:**")
                    for task in task_plan['validation_tasks']:
                        st.markdown(f"- {task}")
                    
                    st.markdown("**Booking Tasks:**")
                    for task in task_plan['booking_tasks']:
                        st.markdown(f"- {task}")
            
            else:
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
