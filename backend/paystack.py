"""
PAYSTACK PAYMENT INTEGRATION for F and B Poultry Farm Limited
============================================================
This module handles all Paystack API interactions:
- Initialize payments
- Verify payments
- Handle webhooks
- Get payment history

How to use:
1. Set your Paystack keys in .env file
2. Import functions from this module
3. Call initialize_payment() to start a payment
4. Call verify_payment() to check payment status
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paystack API base URL
PAYSTACK_BASE_URL = "https://api.paystack.co"

# Get API keys from environment variables
# These will be set in the .env file
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_placeholder_key')
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_placeholder_key')


def get_headers():
    """Get headers for Paystack API requests"""
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }


def initialize_payment(email, amount, reference, callback_url=None, metadata=None):
    """
    Initialize a payment on Paystack
    
    Args:
        email (str): Customer's email address
        amount (int): Amount in GHS pesewas (multiply by 100)
        reference (str): Unique transaction reference
        callback_url (str): URL to redirect after payment
        metadata (dict): Additional data to store with payment
    
    Returns:
        dict: Response from Paystack API
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
    
    # Build the request payload
    payload = {
        "email": email,
        "amount": int(amount * 100),  # Convert to pesewas (Paystack uses smallest unit)
        "reference": reference,
        "currency": "GHS",
        "callback_url": callback_url or "https://fandpoultryfam.fly.dev/pages/success.html",
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)
        result = response.json()
        
        if result.get('status'):
            return {
                'status': True,
                'message': 'Payment initialized successfully',
                'data': result['data']
            }
        else:
            return {
                'status': False,
                'message': result.get('message', 'Failed to initialize payment'),
                'data': None
            }
    except Exception as e:
        return {
            'status': False,
            'message': f'Error: {str(e)}',
            'data': None
        }


def verify_payment(reference):
    """
    Verify a payment on Paystack
    
    Args:
        reference (str): Transaction reference to verify
    
    Returns:
        dict: Payment verification result
    """
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        result = response.json()
        
        if result.get('status'):
            data = result['data']
            return {
                'status': True,
                'message': 'Payment verified',
                'data': {
                    'reference': data.get('reference'),
                    'amount': data.get('amount') / 100,  # Convert back to cedis
                    'currency': data.get('currency'),
                    'status': data.get('status'),
                    'paid_at': data.get('paid_at'),
                    'channel': data.get('channel'),
                    'customer_email': data.get('customer', {}).get('email'),
                    'metadata': data.get('metadata', {})
                }
            }
        else:
            return {
                'status': False,
                'message': result.get('message', 'Payment not found'),
                'data': None
            }
    except Exception as e:
        return {
            'status': False,
            'message': f'Error: {str(e)}',
            'data': None
        }


def handle_webhook(payload, signature):
    """
    Handle Paystack webhook events
    
    Args:
        payload (dict): The webhook payload
        signature (str): The signature from Paystack
    
    Returns:
        dict: Processing result
    """
    # In production, verify the signature
    # For now, we'll just process the event
    
    event = payload.get('event')
    
    if event == 'charge.success':
        data = payload.get('data', {})
        return {
            'status': True,
            'event': event,
            'reference': data.get('reference'),
            'amount': data.get('amount', 0) / 100,
            'message': 'Payment successful'
        }
    elif event == 'charge.failed':
        data = payload.get('data', {})
        return {
            'status': False,
            'event': event,
            'reference': data.get('reference'),
            'message': 'Payment failed'
        }
    else:
        return {
            'status': False,
            'event': event,
            'message': 'Unhandled event type'
        }


def get_payment_history(email=None, limit=50):
    """
    Get payment history from Paystack
    
    Args:
        email (str): Filter by customer email
        limit (int): Number of records to return
    
    Returns:
        dict: Payment history
    """
    url = f"{PAYSTACK_BASE_URL}/transaction?limit={limit}"
    
    if email:
        url += f"&customer={email}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        result = response.json()
        
        if result.get('status'):
            return {
                'status': True,
                'data': result['data']
            }
        else:
            return {
                'status': False,
                'message': result.get('message', 'Failed to get payment history'),
                'data': []
            }
    except Exception as e:
        return {
            'status': False,
            'message': f'Error: {str(e)}',
            'data': []
        }


def create_payment_reference(order_id, amount, customer_email):
    """
    Create a unique payment reference
    
    Args:
        order_id (int): The order ID
        amount (float): The amount to pay
        customer_email (str): Customer's email
    
    Returns:
        str: Unique reference string
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"FAND-B-{order_id}-{timestamp}"