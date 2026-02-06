import google.generativeai as genai
import json
import re
import os

# Default fallback if not configured
API_KEY = None

def configure_genai(api_key):
    global API_KEY
    API_KEY = api_key
    genai.configure(api_key=API_KEY)

def parse_command(text):
    """
    Parses natural language text into a structured intent using Gemini Flash.
    Returns dict: {"intent": "str", "params": {}}
    """
    if not text:
        return None

    # Fallback if no API key
    if not API_KEY:
        return regex_fallback(text)

    # OPTIMIZATION: Check regex first for common commands to avoid API latency
    quick_check = regex_fallback(text)
    if quick_check and quick_check.get("intent") != "unknown":
        print(f"NLU (Fast Path): {quick_check}")
        return quick_check

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a voice assistant NLU. valid intents: 
        - navigation (params: folder_name [Inbox, Sent, Trash, Drafts, Settings])
        - open_email (params: index [integer 0-based], target [optional "latest", "first"])
        - read_content (no params)
        - compose_start (no params)
        - compose_action (params: field [recipient, subject, message], value [string - sanitized for email if recipient])
        - confirmation (params: value [yes, no])
        - stop (no params)
        - confirmation (params: value [yes, no])
        - stop (no params)
        - summarize_email (params: index [integer 0-based], target [optional "current"])
        - reply_with_suggestion (params: index [integer 0-based])
        
        Special instructions:
        - If the user is providing an email address (e.g. "john dot doe at gmail dot com"), convert it to strictly "johndoe@gmail.com" format in the 'value' param.
        - If the user says "cancel", map to intent: "cancel".
        
        Map the user phrase to valid intent JSON. 
        User: "{text}"
        JSON:
        """
        
        response = model.generate_content(prompt)
        # Clean response (sometimes contains markdown ```json ... ```)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0]
            
        data = json.loads(raw)
        return data

    except Exception as e:
        print(f"NLU Error: {e}")
        return regex_fallback(text)

def regex_fallback(text):
    text = text.lower()
    if "cancel" in text: return {"intent": "cancel", "params": {}}
    if "inbox" in text: return {"intent": "navigation", "params": {"folder_name": "Inbox"}}
    if "inbox" in text: return {"intent": "navigation", "params": {"folder_name": "Inbox"}}
    
    # "Sent" synonyms (sometimes heard as 'send')
    if "sent" in text or "send" in text or "outbox" in text: 
        return {"intent": "navigation", "params": {"folder_name": "Sent"}}
    
    if "trash" in text or "bin" in text: return {"intent": "navigation", "params": {"folder_name": "Trash"}}
    
    if "draft" in text: return {"intent": "navigation", "params": {"folder_name": "Drafts"}}
    
    if "setting" in text or "config" in text: return {"intent": "navigation", "params": {"folder_name": "Settings"}}
    
    # Read Content explicitly
    if text in ["read", "read it", "read the mail", "read email", "speak"]:
        return {"intent": "read_content", "params": {}}
    
    # Delete Email
    if "delete" in text or "remove" in text or "trash" in text:
        # Check for numeric index "delete email 5"
        nums = re.findall(r'\d+', text)
        if nums:
             return {"intent": "delete_email", "params": {"index": int(nums[0])-1}}
        
        # Check for context "delete this"
        if "this" in text or "it" in text or "current" in text:
             return {"intent": "delete_email", "params": {"target": "current"}}
             
        # Just "delete" usually means current if reading
        return {"intent": "delete_email", "params": {}}
    
    # Open / Read
    
    # Open / Read
    if "open" in text or "read" in text:
        nums = re.findall(r'\d+', text)
        if nums:
            return {"intent": "open_email", "params": {"index": int(nums[0])-1}}
        
        ordinals = {
            "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
            "sixth": 5, "seventh": 6, "eighth": 7, "ninth": 8, "tenth": 9,
            "one": 0, "two": 1, "three": 2, "four": 3, "five": 4
        }
        for word, idx in ordinals.items():
            if word in text:
                return {"intent": "open_email", "params": {"index": idx}}
            
        if "compose" in text: return {"intent": "compose_start", "params": {}}
    if "yes" in text or "send it" in text: return {"intent": "confirmation", "params": {"value": "yes"}}
    if "logout" in text or "sign out" in text: return {"intent": "logout", "params": {}}
    if "stop" in text or "quiet" in text: return {"intent": "stop", "params": {}}

    # Summarize
    if "summarize" in text or "summary" in text or "short" in text:
        nums = re.findall(r'\d+', text)
        if nums:
             return {"intent": "summarize_email", "params": {"index": int(nums[0])-1}}
        
        ordinals = {
            "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
            "sixth": 5, "seventh": 6, "eighth": 7, "ninth": 8, "tenth": 9,
            "one": 0, "two": 1, "three": 2, "four": 3, "five": 4
        }
        for word, idx in ordinals.items():
            if word in text:
                return {"intent": "summarize_email", "params": {"index": idx}}
                
        # If open, summarize active
        return {"intent": "summarize_email", "params": {"target": "current"}}
        
    # Suggested Replies
    if "reply with" in text or "option" in text:
        nums = re.findall(r'\d+', text)
        if nums:
             return {"intent": "reply_with_suggestion", "params": {"index": int(nums[0])-1}}
        if "one" in text: return {"intent": "reply_with_suggestion", "params": {"index": 0}}
        if "two" in text: return {"intent": "reply_with_suggestion", "params": {"index": 1}}
        if "three" in text: return {"intent": "reply_with_suggestion", "params": {"index": 2}}
    
    return {"intent": "unknown", "params": {}}

def summarize_email_content(text):
    """
    Summarizes the provided text using Gemini Flash.
    """
    if not text: return "No content to summarize."
    if not API_KEY: return "AI key missing. Cannot summarize."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Summarize the following email content in 2 sentences, capturing the main point and any action items:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.replace("\n", " ")
    except Exception as e:
        print(f"Summary Error: {e}")
        return "Failed to generate summary."

def generate_suggested_replies(text):
    """
    Generates 3 short suggested replies for the given email text.
    Returns list of strings.
    """
    if not text: return []
    if not API_KEY: return []
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Read the following email and generate 3 short, polite, and distinct suggested replies (under 10 words each). 
        Return them as a JSON list of strings, e.g. ["Yes, sure.", "No thanks.", "I will check."]
        
        Email: {text}
        
        JSON:
        """
        response = model.generate_content(prompt)
        raw = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        if isinstance(data, list):
            return data[:3]
        return []
    except Exception as e:
        print(f"Suggest Reply Error: {e}")
        return []
