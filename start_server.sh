#!/bin/bash
# Start Django server without proxy for Stripe API calls

# Unset proxy environment variables
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy

# Add Stripe to NO_PROXY
export NO_PROXY="${NO_PROXY},api.stripe.com,*.stripe.com"

# Change to project directory
cd /Users/mohammedalhajri/Test_Bank

# Activate virtual environment
source venv/bin/activate

# Start Django server
python manage.py runserver
