import os
import requests
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

APP_ID = os.getenv("FACEBOOK_APP_ID")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

if not all([APP_ID, APP_SECRET, PAGE_ID]):
    print("?? Error: Missing credentials in .env file.")
    print(f"APP_ID: {APP_ID}")
    print(f"APP_SECRET: {'***' if APP_SECRET else None}")
    print(f"PAGE_ID: {PAGE_ID}")
    exit(1)

# Step 1: Generate Authorization URL
redirect_uri = "https://www.facebook.com/connect/login_success.html"
scope = "pages_manage_posts,pages_read_engagement,public_profile"

auth_url = (
    f"https://www.facebook.com/v24.0/dialog/oauth?"
    f"client_id={APP_ID}&"
    f"redirect_uri={redirect_uri}&"
    f"scope={scope}&"
    f"response_type=token"
)

print("-" * 50)
print("?? STEP 1: AUTHORIZE YOUR APP")
print("-" * 50)
print("1. Copy and paste this URL into your browser:")
print(f"\n{auth_url}\n")
print("2. Log in and click 'Continue' / 'Allow' for your Page.")
print("3. After you click allow, you will be redirected to a blank page.")
print("4. LOOK AT THE URL in your browser's address bar.")
print("5. It will look like: https://www.facebook.com/connect/login_success.html#access_token=ABC...&expires_in=...")
print("6. COPY everything after 'access_token=' until the '&' symbol.")
print("-" * 50)
print("?? STEP 2: PASTE THAT TOKEN BELOW")
print("-" * 50)
