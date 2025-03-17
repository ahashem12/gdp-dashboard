import streamlit as st
import os
from dotenv import load_dotenv
from slangit_api import SlangitAPI, MultiSpaceProcessor

# Load environment variables
load_dotenv()

# UI Setup
st.set_page_config(layout="wide")

# Custom CSS for containers
st.markdown("""
    <style>
        /* Fix main container padding */
        .block-container {
            padding: 1rem;
        }
        
        /* Style for chat container */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 1rem;
            background-color: white;
        }
        
        /* Make chat messages more compact */
        .stChatMessage {
            padding: 5px !important;
            margin: 5px !important;
        }
        
        /* Custom scrollbar */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]::-webkit-scrollbar {
            width: 5px;
        }
        
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Slangit Multi-Space Chat")
st.caption("🚀 Chat with multiple Slangit spaces simultaneously")

# Initialize session state
if "space_chats" not in st.session_state:
    st.session_state.space_chats = {}
if "conversation_ids" not in st.session_state:
    st.session_state.conversation_ids = {}

# Define space to project name mapping
SPACE_MAPPING = {
    41: "Al Bawader",
    45: "3F Pharma",
    46: "Al Mada"
}

# Available spaces with their names
if "available_spaces" not in st.session_state:
    st.session_state.available_spaces = list(SPACE_MAPPING.keys())

# Initialize Slangit API Utility
def get_slangit_api(space_id):
    return SlangitAPI(
        base_url='https://mvp.slangit.ai/api',
        token=os.getenv("SLANGIT_TOKEN"),
        space_id=space_id
    )

# Create three columns for the chat windows
col1, col2, col3 = st.columns(3)

# Function to create or get conversation for a space
def get_conversation(space_id):
    if space_id not in st.session_state.space_chats:
        project_name = SPACE_MAPPING.get(space_id, f"Space {space_id}")
        st.session_state.space_chats[space_id] = [{"role": "assistant", "content": f"Welcome to {project_name}! How can I help you?"}]
        slangit_api = get_slangit_api(space_id)
        st.session_state.conversation_ids[space_id] = slangit_api.create_conversation()
    return st.session_state.conversation_ids[space_id]

# Function to format space options for dropdown
def format_space_option(space_id):
    return SPACE_MAPPING.get(space_id, f"Space {space_id}")

# Function to handle chat for a specific space
def space_chat(col, window_num):
    with col:
        # Project selection at the top
        space_id = st.selectbox(
            f"Select Project",
            options=st.session_state.available_spaces,
            format_func=format_space_option,
            key=f"space_{window_num}"
        )
        
        # Get or create conversation for this space
        conversation_id = get_conversation(space_id)
        
        # Create a container for the chat interface
        chat_container = st.container()
        
        # Display chat messages in the container
        with chat_container:
            for msg in st.session_state.space_chats[space_id]:
                st.chat_message(msg["role"]).write(msg["content"])
        
        # Chat input at the bottom
        prompt = st.chat_input(f"Chat with {format_space_option(space_id)}", key=f"input_{window_num}")
        
        if prompt:
            # Append user's message
            st.session_state.space_chats[space_id].append({"role": "user", "content": prompt})
            
            with st.spinner("Generating response..."):
                # Get response from Slangit API
                slangit_api = get_slangit_api(space_id)
                response = slangit_api.send_message(conversation_id, prompt)
                
                # Append assistant's response
                st.session_state.space_chats[space_id].append({"role": "assistant", "content": response})
            
            # Force a rerun to update the chat
            st.rerun()

# Create the three chat windows
space_chat(col1, 1)
space_chat(col2, 2)
space_chat(col3, 3)

# Add the multi-space chat at the bottom
st.markdown("---")
st.subheader("💬 Chat with All Selected Spaces")

# Get the selected spaces from all windows
selected_spaces = [
    st.session_state.get(f"space_{i}") 
    for i in range(1, 4)
]

# Show selected projects
st.caption("Selected Projects: " + ", ".join([format_space_option(space_id) for space_id in selected_spaces]))

# Multi-space chat input
if multi_prompt := st.chat_input("Ask all selected spaces", key="multi_space_input"):
    # Process the question for each selected space
    for space_id in selected_spaces:
        conversation_id = get_conversation(space_id)
        
        # Append user's message to each space's chat
        st.session_state.space_chats[space_id].append({"role": "user", "content": multi_prompt})
        
        with st.spinner(f"Getting response from {format_space_option(space_id)}..."):
            # Get response from Slangit API
            slangit_api = get_slangit_api(space_id)
            response = slangit_api.send_message(conversation_id, multi_prompt)
            
            # Append assistant's response
            st.session_state.space_chats[space_id].append({"role": "assistant", "content": response})
    
    # Force a rerun to update all chats
    st.rerun()

