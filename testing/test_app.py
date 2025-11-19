"""
Prompt Testing Application
Simplified Flask app for testing chatbot prompts with template patients
Run: python testing/test_app.py
Access: http://localhost:5000
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import main app modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import uuid
from datetime import datetime
import logging

# Import from main app
from prompt_templates import get_prompt, get_separated_prompts
from template_patients import get_all_templates, create_patient_session_data

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

azure_openai_client = None
if all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
    try:
        from openai import AzureOpenAI
        azure_openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        logger.info("✅ Azure OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Azure OpenAI client: {str(e)}")
else:
    logger.warning("⚠️ Azure OpenAI configuration incomplete")

def get_ai_response(message, patient_info):
    """Get AI response using Azure OpenAI"""
    if not azure_openai_client:
        return None, "Azure OpenAI client not initialized. Check .env configuration."

    try:
        # Get separated prompts for Azure OpenAI
        system_prompt, user_prompt = get_separated_prompts(message, patient_info)

        logger.info("Sending request to Azure OpenAI...")

        response = azure_openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=2000
        )

        if response and response.choices:
            content = response.choices[0].message.content
            logger.info("✅ Received response from Azure OpenAI")
            return content, None
        else:
            return None, "Empty response from Azure OpenAI"

    except Exception as e:
        logger.error(f"Error getting Azure OpenAI response: {str(e)}", exc_info=True)
        return None, str(e)

app = Flask(__name__,
            template_folder='templates',
            static_folder='../static')  # Reuse main app's static files
app.secret_key = os.getenv('SECRET_KEY', 'testing-secret-key-change-in-production')

@app.route('/')
def index():
    """Main testing interface - select template patient and start chatting"""
    # Initialize session if needed
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['chat_history'] = []

    templates = get_all_templates()
    return render_template('prompt_test.html', templates=templates)

@app.route('/select_patient', methods=['POST'])
def select_patient():
    """Load a template patient into session"""
    data = request.get_json()
    template_id = data.get('template_id')

    patient_data = create_patient_session_data(template_id)
    if not patient_data:
        return jsonify({'success': False, 'error': 'Invalid template ID'}), 400

    # Clear previous chat history
    session['chat_history'] = []

    # Load patient data into session
    session.update(patient_data)

    return jsonify({
        'success': True,
        'patient': patient_data
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with current template patient"""
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'success': False, 'error': 'Empty message'}), 400

    # Check if patient is loaded
    if 'patient_name' not in session:
        return jsonify({'success': False, 'error': 'No patient selected'}), 400

    # Get patient context
    patient_context = {
        'name': session.get('patient_name'),
        'age': session.get('patient_age'),
        'gender': session.get('patient_gender'),
        'operation': session.get('operation'),
        'cfs_score': session.get('cfs_score'),
        'concerns': session.get('concerns'),
        'medical_history': session.get('medical_history', {})
    }

    # Build chat history for context
    chat_history = session.get('chat_history', [])

    # Generate AI response
    try:
        # Get Azure OpenAI response
        ai_response, error = get_ai_response(user_message, patient_context)

        if error:
            return jsonify({
                'success': False,
                'error': f'AI response failed: {error}'
            }), 500

        # Get prompts for preview
        system_prompt, user_prompt = get_separated_prompts(user_message, patient_context)

        # Save to chat history
        chat_history.append({
            'role': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        chat_history.append({
            'role': 'bot',
            'message': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        session['chat_history'] = chat_history

        result = {
            'success': True,
            'response': ai_response,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt
        }
        logger.info(f"Returning response - length: {len(ai_response)} chars")
        logger.info(f"Response preview: {ai_response[:100]}...")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'AI response failed: {str(e)}'
        }), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear chat history but keep current patient"""
    session['chat_history'] = []
    return jsonify({'success': True})

@app.route('/reset', methods=['POST'])
def reset():
    """Reset everything - clear patient and chat history"""
    session.clear()
    session['session_id'] = str(uuid.uuid4())
    session['chat_history'] = []
    return jsonify({'success': True})

@app.route('/get_prompt_preview', methods=['POST'])
def get_prompt_preview():
    """Preview the actual prompt that will be sent to AI"""
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if 'patient_name' not in session:
        return jsonify({'success': False, 'error': 'No patient selected'}), 400

    patient_context = {
        'age': session.get('patient_age'),
        'operation': session.get('operation'),
        'cfs_score': session.get('cfs_score')
    }

    chat_history = session.get('chat_history', [])

    # Get combined prompt
    full_prompt = get_prompt(
        patient_context['age'],
        patient_context['operation'],
        patient_context.get('cfs_score'),
        user_message,
        chat_history
    )

    # Get separated prompts for Azure
    system_prompt, user_prompt = get_separated_prompts(
        patient_context['age'],
        patient_context['operation'],
        patient_context.get('cfs_score'),
        user_message,
        chat_history
    )

    return jsonify({
        'success': True,
        'full_prompt': full_prompt,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Prompt Testing Server Starting...")
    print("=" * 60)
    print(f"Access the testing interface at: http://localhost:5000")
    print(f"Press Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
