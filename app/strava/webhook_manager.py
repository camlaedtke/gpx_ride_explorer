"""
webhook_manager.py
-----------------
Utility script for managing Strava webhook subscriptions.

This script provides functions to:
1. Create a new webhook subscription
2. View existing webhook subscriptions
3. Delete webhook subscriptions

Usage:
    python -m app.strava.webhook_manager create [ngrok_url]
    python -m app.strava.webhook_manager list
    python -m app.strava.webhook_manager delete [subscription_id]
"""

import requests
import sys
import argparse
from app.config import settings

# Base URL for Strava Push Subscriptions API
API_URL = "https://www.strava.com/api/v3/push_subscriptions"

def get_callback_url(ngrok_url=None):
    """
    Get the callback URL for the webhook.
    In production, this would be your public URL.
    For local development, you can use ngrok to create a tunnel.
    """
    # For production
    # return "https://your-domain.com/strava/webhook"
    
    # For local development with ngrok
    if ngrok_url:
        return f"{ngrok_url}/strava/webhook"
    else:
        try:
            ngrok_url = input("Enter your ngrok URL (e.g., https://abc123.ngrok.io): ")
            return f"{ngrok_url}/strava/webhook"
        except EOFError:
            print("Error: Input was not available. Please provide the ngrok URL as a command-line argument.")
            print("Example: python -m app.strava.webhook_manager create https://abc123.ngrok.io")
            sys.exit(1)

def create_subscription(ngrok_url=None):
    """
    Register a new webhook subscription with Strava.
    """
    callback_url = get_callback_url(ngrok_url)
    
    # The verify token should match what's checked in the webhook endpoint
    verify_token = settings.STRAVA_CLIENT_SECRET
    
    payload = {
        'client_id': settings.STRAVA_CLIENT_ID,
        'client_secret': settings.STRAVA_CLIENT_SECRET,
        'callback_url': callback_url,
        'verify_token': verify_token
    }
    
    print(f"Registering webhook with Strava...")
    print(f"Callback URL: {callback_url}")
    
    response = requests.post(API_URL, data=payload)
    
    if response.status_code == 200 or response.status_code == 201:
        print("Success! Webhook subscription created:")
        print(response.json())
    else:
        print(f"Error creating subscription: {response.status_code}")
        print(response.text)

def list_subscriptions():
    """
    List all active webhook subscriptions.
    """
    params = {
        'client_id': settings.STRAVA_CLIENT_ID,
        'client_secret': settings.STRAVA_CLIENT_SECRET
    }
    
    response = requests.get(API_URL, params=params)
    
    if response.status_code == 200:
        subscriptions = response.json()
        
        if not subscriptions:
            print("No active webhook subscriptions found.")
            return
            
        print(f"Found {len(subscriptions)} webhook subscription(s):")
        for sub in subscriptions:
            print(f"ID: {sub['id']}")
            print(f"Application ID: {sub['application_id']}")
            print(f"Callback URL: {sub['callback_url']}")
            print(f"Created At: {sub['created_at']}")
            print("-" * 40)
    else:
        print(f"Error listing subscriptions: {response.status_code}")
        print(response.text)

def delete_subscription(subscription_id):
    """
    Delete a specific webhook subscription.
    """
    params = {
        'client_id': settings.STRAVA_CLIENT_ID,
        'client_secret': settings.STRAVA_CLIENT_SECRET
    }
    
    delete_url = f"{API_URL}/{subscription_id}"
    response = requests.delete(delete_url, params=params)
    
    if response.status_code == 204:
        print(f"Successfully deleted subscription {subscription_id}")
    else:
        print(f"Error deleting subscription: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage Strava webhook subscriptions")
    parser.add_argument('action', choices=['create', 'list', 'delete'], help='Action to perform')
    parser.add_argument('param', nargs='?', help='URL for create or subscription ID for delete')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_subscription(args.param)  # Pass the ngrok URL if provided
    elif args.action == 'list':
        list_subscriptions()
    elif args.action == 'delete':
        if not args.param:
            print("Error: subscription_id is required for delete action")
            sys.exit(1)
        delete_subscription(args.param)