import requests
import logging
import sys
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('ollama-test')

# Load environment variables
load_dotenv()

# Ollama configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma')

def get_ollama_response(prompt, model_name=OLLAMA_MODEL, ollama_url=OLLAMA_URL):
    """Get response from local Ollama server running Gemma model"""
    try:
        # Endpoint for Ollama API
        endpoint = f"{ollama_url}/api/generate"
        
        # Prepare the request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 64,
            "max_tokens": 8192
        }
        
        logger.info(f"Sending request to Ollama API at {ollama_url} for model: {model_name}")
        response = requests.post(endpoint, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            logger.error(f"Ollama API error: Status code {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error in get_ollama_response: {str(e)}", exc_info=True)
        return None

def main():
    # IP address of the computer running Ollama
    remote_ip = input("Enter the IP address of the computer running Ollama (default: localhost): ") or "localhost"
    ollama_url = f"http://{remote_ip}:11434"
    
    # Model name
    model_name = input("Enter the model name (default: gemma): ") or "gemma"
    
    # Test prompt
    test_prompt = input("Enter a test prompt (default: 介紹一下麻醉的風險): ") or "介紹一下麻醉的風險"
    
    logger.info(f"Connecting to Ollama at {ollama_url}")
    logger.info(f"Using model: {model_name}")
    logger.info(f"Test prompt: {test_prompt}")
    
    # Get response
    response = get_ollama_response(test_prompt, model_name=model_name, ollama_url=ollama_url)
    
    if response:
        print("\n===== RESPONSE =====")
        print(response)
        print("====================\n")
        logger.info("Successfully received response from Ollama")
    else:
        logger.error("Failed to get response from Ollama")

if __name__ == "__main__":
    main()
