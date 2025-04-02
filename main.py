import requests
import json
import time
import logging
from datetime import datetime

# Configure logging
LOG_FILE = "webhook_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Discord webhook URL
WEBHOOK_URL = "YOUR_WEBHOOK_URL"

# Fortnite API endpoint
API_URL = "https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game/dynamicbackgrounds"

# Path to store the previous image URL
JSON_FILE_PATH = "image_data.json"

def log_message(message, level="info"):
    """Logs message to file and prints to console."""
    if level == "info":
        logging.info(message)
        print(f"[INFO] {message}")
    elif level == "warning":
        logging.warning(message)
        print(f"[WARNING] {message}")
    elif level == "error":
        logging.error(message)
        print(f"[ERROR] {message}")
    elif level == "debug":
        logging.debug(message)
        print(f"[DEBUG] {message}")

def fetch_api_data():
    """Fetch the latest background image URL from the API."""
    try:
        log_message("Fetching data from Fortnite API...", "debug")
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()

        # Extract the first background image URL
        backgrounds = data.get("backgrounds", {}).get("backgrounds", [])
        if backgrounds:
            image_url = backgrounds[0].get("backgroundimage", None)
            if image_url:
                log_message(f"Fetched image URL: {image_url}", "info")
                return image_url

        log_message("No valid background image found in API response!", "warning")
        return None
    except requests.RequestException as e:
        log_message(f"API request failed: {e}", "error")
        return None
    except json.JSONDecodeError:
        log_message("Failed to parse API response as JSON.", "error")
        return None

def load_previous_data():
    """Load previously saved image data from a JSON file."""
    try:
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
            log_message(f"Loaded previous image URL: {data.get('image_url')}", "debug")
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        log_message("No previous data found or JSON file is corrupted.", "warning")
        return None

def save_image_data(image_url):
    """Save the image URL to a JSON file."""
    try:
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump({'image_url': image_url}, file)
        log_message(f"Saved new image URL: {image_url}", "info")
    except Exception as e:
        log_message(f"Error saving image data: {e}", "error")

def send_discord_webhook(image_url):
    """Send a message with the image URL to the Discord webhook without a plain text link."""
    data = {
        "content": "",  # Empty content to avoid sending plain text
        "embeds": [
            {
                "title": "New Fortnite Dynamic Background",
                "description": "A new dynamic background has been added!",
                "image": {"url": image_url},  # Main image
                "thumbnail": {"url": image_url}  # Thumbnail (same as main)
            }
        ]
    }

    try:
        log_message("Sending webhook to Discord...", "debug")
        response = requests.post(WEBHOOK_URL, json=data)

        if response.status_code == 204:
            log_message("Webhook sent successfully!", "info")
        else:
            log_message(f"Failed to send webhook: {response.status_code} - {response.text}", "error")
    except Exception as e:
        log_message(f"Error sending webhook: {e}", "error")

def main():
    """Main function to check the image URL every 60 seconds."""
    log_message("Starting script... Monitoring Fortnite API.", "info")

    while True:
        current_image_url = fetch_api_data()

        if current_image_url:
            previous_data = load_previous_data()

            # If there's no previous data or the image URL has changed
            if not previous_data or previous_data['image_url'] != current_image_url:
                log_message("New image detected! Sending webhook...", "info")
                send_discord_webhook(current_image_url)
                save_image_data(current_image_url)
            else:
                log_message("No change in image URL.", "debug")

        log_message("Sleeping for 60 seconds before next check...", "debug")
        time.sleep(60)

if __name__ == "__main__":
    main()