from atproto import Client
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    client = Client()
    try:
        client.login(
            os.getenv('BLUESKY_HANDLE'),
            os.getenv('BLUESKY_PASSWORD')
        )
        print("Successfully connected to Bluesky!")
        
        # Test post
        client.send_post(text="Hello world! I'm a bot testing my connection. 🤖")
        print("Successfully posted to Bluesky!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()