import imaplib
import smtplib
import email
from email.header import decode_header
import os

import imaplib
import smtplib
import email
from email.header import decode_header
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"

def connect_imap(email_account, password):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(email_account, password)
        return mail
    except Exception as e:
        print(f"IMAP Connection Error: {e}")
        return None

# Gmail IMAP Folder Mapping
GMAIL_FOLDERS = {
    "Inbox": "INBOX",
    "Sent": "[Gmail]/Sent Mail",
    "Drafts": "[Gmail]/Drafts",
    "Trash": "[Gmail]/Trash",
    "Starred": "[Gmail]/Starred"
}

def fetch_emails(email_account, password, folder="Inbox", limit=10):
    """
    Fetches the top 'limit' emails from the specified 'folder' (Human readable).
    """
    if not email_account or not password:
         print("Missing credentials")
         return []
         
    mail = connect_imap(email_account, password)
    if not mail:
        return []

    try:
        # Map human folder to IMAP folder
        imap_folder = GMAIL_FOLDERS.get(folder, folder)
        
        # Robust folder selection
        target_folder = imap_folder
        
        if folder == "Sent":
             candidates = ["\"[Gmail]/Sent Mail\"", "\"[Gmail]/Sent\"", "Sent", "\"Sent Items\""]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK":
                     target_folder = c
                     break
        elif folder == "Trash":
             candidates = ["\"[Gmail]/Trash\"", "\"[Gmail]/Bin\"", "Trash", "Bin"]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK":
                     target_folder = c
                     break
        else:
             # Default select
             status, _ = mail.select(imap_folder)
             target_folder = imap_folder
        
        if status != "OK":
            print(f"Failed to select folder: {imap_folder}")
            return []
            
        # Search for all emails
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return []

        email_ids = messages[0].split()
        # Get latest first
        latest_email_ids = email_ids[-limit:]
        latest_email_ids.reverse()

        email_list = []

        if not latest_email_ids:
            mail.logout()
            return []

        email_list = []

        for e_id in latest_email_ids:
            # OPTIMIZATION: Fetch HEADERS only. fast.
            res, msg_data = mail.fetch(e_id, "(RFC822.HEADER)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Subject
                    subject, encoding = decode_header(msg["Subject"])[0] if msg["Subject"] else (None, None)
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    if not subject: subject = "(No Subject)"
                    
                    # Decode Sender
                    sender = msg.get("From", "Unknown")
                    date = msg.get("Date", "")
                    
                    email_list.append({
                        "id": e_id.decode(),
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "body": "", # Lazy load this later
                        "snippet": ""
                    })
        
        mail.logout()
        return email_list

    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def fetch_email_body(email_account, password, folder, email_id):
    """
    Lazily fetches the body of a specific email.
    """
    if not email_account or not password: return "Error: No creds"
    
    mail = connect_imap(email_account, password)
    if not mail: return "Error: Connect failed"
    
    try:
        imap_folder = GMAIL_FOLDERS.get(folder, folder)
        # We must select the folder again
        # Logic for Sent/Trash robustness
        target_folder = imap_folder
        if folder == "Sent":
             candidates = ["\"[Gmail]/Sent Mail\"", "\"[Gmail]/Sent\"", "Sent", "\"Sent Items\""]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK": break
        elif folder == "Trash":
             candidates = ["\"[Gmail]/Trash\"", "\"[Gmail]/Bin\"", "Trash", "Bin"]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK": break
        else:
             mail.select(imap_folder)
             
        # Fetch body
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        
        body = "Error reading body."
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                # Extract body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        try:
                            body_part = part.get_payload(decode=True)
                            if body_part and content_type == "text/plain":
                                body = body_part.decode("utf-8", errors="ignore")
                                break
                        except: pass
                else:
                    body_part = msg.get_payload(decode=True)
                    if body_part:
                        body = body_part.decode("utf-8", errors="ignore")
        
        mail.logout()
        return body
    except Exception as e:
        print(f"Body Fetch Error: {e}")
        return f"Error: {e}"

def move_to_trash(email_account, password, current_folder, email_id):
    """
    Moves an email to the Trash folder (Copy + Delete).
    """
    if not email_account or not password: return False

    mail = connect_imap(email_account, password)
    if not mail: return False

    try:
        # Select source folder
        imap_folder = GMAIL_FOLDERS.get(current_folder, current_folder)
        
        # Robust folder selection (borrowed from fetch logic)
        if current_folder == "Sent":
             candidates = ["\"[Gmail]/Sent Mail\"", "\"[Gmail]/Sent\"", "Sent", "\"Sent Items\""]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK": break
        elif current_folder == "Trash":
             candidates = ["\"[Gmail]/Trash\"", "\"[Gmail]/Bin\"", "Trash", "Bin"]
             for c in candidates:
                 status, _ = mail.select(c)
                 if status == "OK": break
        else:
             mail.select(imap_folder)

        # Determine Trash folder path
        trash_folder = GMAIL_FOLDERS["Trash"]
        # Verify Trash folder name on server (Bin vs Trash)
        candidates = ["\"[Gmail]/Trash\"", "\"[Gmail]/Bin\""]
        target_trash = trash_folder
        
        # Check which trash folder exists if standard fails (improving robustness)
        # For simplicity, we try the standard map first.
        
        # COPY to Trash
        res = mail.copy(email_id, trash_folder)
        if res[0] != 'OK':
            # Try 'Bin' if 'Trash' failed
            res = mail.copy(email_id, "\"[Gmail]/Bin\"")
            
        if res[0] == 'OK':
            # Mark as deleted in source
            mail.store(email_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
            return True
        else:
            print(f"Copy to trash failed: {res}")
            mail.logout()
            return False

    except Exception as e:
        print(f"Delete Error: {e}")
        return False

    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def send_email(email_account, password, to_email, subject, body):
    if not email_account or not password:
        return False
        
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(email_account, password)
        
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(email_account, to_email, message)
        server.quit()
        return True
    except Exception as e:
        print(f"Send Error: {e}")
        return False
