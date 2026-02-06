# Swar - Hands-Free Voice Assistant
**Project State**: Completed
**Tech Stack**: Streamlit, DeepFace, SpeechRecognition, Gmail API

## Overview
Swar is a fully strictly hands-free email and messaging assistant. It uses Face Recognition for secure, touch-free login and Voice Commands for navigating and managing emails.

## 🚀 How to Run

### 1. Prerequisites
- **Python 3.10+**
- **Webcam**
- **Microphone**

### 2. Installation
Open your terminal in this directory:
```bash
# Create virtual environment (Optional)
python -m venv .venv
.venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Running the App
```bash
streamlit run app.py
```

## 🎙️ Hands-Free Usage Guide

### 1. Login
- **Scanning**: Look at the camera. The "Live Preview" will show you are being scanned.
- **PIN**: If recognized, say your 4-digit PIN (e.g., "One Two Three Four").
- **Register**: If not recognized, say "Yes" to register. Follow voice prompts for Name, Email, and PIN.

### 2. Inbox Dashboard
Wait for the "Listening" status.
- **"Refresh"**: Load emails.
- **"Read Email One"**: Open the first email.
- **"Next" / "Previous"**: Navigate list.
- **"Read Body"**: Listen to email content.
- **"Reply"**: Reply to the open email.
- **"Logout"**: Return to login.

### 3. Creating Emails
- **"Compose"**: Start a new email.
- **"Set Recipient"**: Say the address.
- **"Dictate Body"**: Speak the message.
- **"Send"**: Send it.
