---
title: I Built a Turkey Deal Finder with APIs, Local AI, and Zero Dollars
date: 2026-03-10
layout: photo
categories:
  - Hobbies
image: https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1600&q=80
draft: false
description: Bought 15 turkeys for about $100!
---

When turkey prices started fluctuating wildly this season, I decided to stop manually checking three different Fred Meyer stores and build something smarter. What started as a simple web scraping project evolved into a full-stack price monitoring system powered by APIs and local AI.

## The Scraping Dead End

The initial plan was straightforward: scrape Fred Meyer's website for turkey prices. But modern e-commerce sites aren't scraper-friendly—I quickly hit Cloudflare protection, bot detection, and JavaScript-rendered content that returned nothing but empty HTML.

That's when I discovered Kroger's official Partner API. Fred Meyer is owned by Kroger, so their API provides real-time product data, pricing, and store locations—no scraping required. After registering a free developer account and switching to Production mode (the Certification environment doesn't work), I had clean access to everything I needed.

💡 Gotcha: Kroger's Certification/sandbox environment is essentially broken. Don't waste time debugging it—go straight to Production mode. The free tier rate limits are generous enough for personal projects.

## How It All Fits Together

Before diving into the code, here's the 30,000-foot view. The system has five moving parts, and they're all stitched together by a Python script reading from a single config file:

System Architecture:

- config.yaml → Stores, thresholds, and settings
    
- Python App → Orchestrates everything:
    
- Kroger API — Product search, prices & locations
    
- LM Studio — Analyzes pricing data, identifies deals
    
- SMS Gateway — Sends deal alerts
    
- JSON Files — Stores raw data for tracking
    

## Pulling Prices from the Kroger API

The app searches three local stores simultaneously, pulling current turkey prices through the API. The Kroger API uses OAuth2, so you'll need to grab a token first, then hit the product search endpoint with your store's location ID:

# Authenticate with Kroger API

import requests

from base64 import b64encode

  

credentials = b64encode(f"{client_id}:{client_secret}".encode()).decode()

  

token_resp = requests.post(

    "https://api.kroger.com/v1/connect/oauth2/token",

    headers={"Authorization": f"Basic {credentials}"},

    data={"grant_type": "client_credentials", "scope": "product.compact"}

)

access_token = token_resp.json()["access_token"]

  

# Search for turkeys at a specific store

products = requests.get(

    "https://api.kroger.com/v1/products",

    headers={"Authorization": f"Bearer {access_token}"},

    params={

        "filter.term": "whole frozen turkey",

        "filter.locationId": store_id,

        "filter.limit": 20

    }

)

  

## The AI Layer: Local LLM Analysis

Here's where it gets interesting: instead of manually comparing dozens of products across locations, I integrated LM Studio—a local LLM running on my network. The AI analyzes all the pricing data and finds turkeys below a configurable threshold (currently set to $1.00/lb). If it finds deals, it responds with a formatted list by store. If not: "No Cheap Turkeys Yet!"

Since LM Studio exposes an OpenAI-compatible API, integration is dead simple:

# Send pricing data to local LLM for analysis

response = requests.post(

    "http://192.168.1.100:1234/v1/chat/completions",

    json={

        "model": "local-model",

        "messages": [

            {"role": "system", "content": "You are a price analyst..."},

            {"role": "user", "content": f"""

                Analyze these turkey prices. Find any below

                ${threshold}/lb. Group results by store.

                Data: {json.dumps(all_prices)}"""}

        ]

    }

)

  

analysis = response.json()["choices"][0]["message"]["content"]

  

This keeps the signal-to-noise ratio high—I only get alerts when there's actually something worth buying.

## Free SMS Notifications (Seriously, Free)

For notifications, I went with the simplest solution that actually works: email-to-SMS gateway. Every carrier has one (T-Mobile's is phonenumber@tmomail.net), and it's completely free. Using Python's built-in smtplib with a Gmail App Password, the system sends me a text whenever deals appear.

import smtplib

from email.mime.text import MIMEText

  

def send_sms(message, phone, carrier_gateway, gmail_user, gmail_app_pw):

    msg = MIMEText(message)

    msg["To"] = f"{phone}@{carrier_gateway}"

    msg["From"] = gmail_user

  

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(gmail_user, gmail_app_pw)

        server.send_message(msg)

  

# That's it. ~50 lines total for the whole notification system.

# No Twilio fees. No third-party services. Just SMTP.

  

## One Config File to Rule Them All

Everything is configurable through a single YAML file: which stores to check, what price threshold triggers alerts, search terms, and notification settings. The app runs on-demand, but I could easily cron it to check daily.

# config.yaml

kroger_api:

  client_id: "your-client-id"

  client_secret: "your-client-secret"

  

stores:

  - name: "Fred Meyer - Woodinville"

    location_id: "70100153"

  - name: "Fred Meyer - Bothell"

    location_id: "70100097"

  - name: "Fred Meyer - Kirkland"

    location_id: "70100112"

  

search:

  term: "whole frozen turkey"

  price_threshold: 1.00  # dollars per pound

  

notifications:

  phone: "5551234567"

  carrier_gateway: "tmomail.net"

  gmail_user: "your-email@gmail.com"

  

All the data gets saved to JSON files, so I can track price trends over time or feed them into other analyses. Total cost? Zero dollars—just API rate limits and my local LM Studio instance doing the AI work.

## Beyond Turkeys

The best part? This approach works for any Kroger-owned store and any product. Change the search term from "whole frozen turkey" to "ribeye steak" or "tillamook cheese", adjust the price threshold, and you've got a universal deal finder.

Sometimes the best solutions aren't the most complex—they're the ones that combine the right APIs, a bit of AI, and some creative problem-solving.

