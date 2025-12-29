
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants from backend/scrapers/camera.py
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

URL = "https://documenti.camera.it/apps/commonServices/getDocumento.ashx?idLegislatura=19&sezione=assemblea&tipoDoc=elenco&annomese=2025,12"

def test_url():
    print(f"Testing URL: {URL}")
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print("Sending request...")
        response = requests.get(URL, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        
        if response.status_code == 200:
            print("\nSUCCESS! Content snippet:")
            print(response.text[:500])
        else:
            print(f"\nFAILED. Response content:")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_url()
