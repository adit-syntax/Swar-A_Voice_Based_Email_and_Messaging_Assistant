import streamlit as st
import time
import threading
import re
from utils import voice, auth, db, email_manager, nlu

# --- PAGE CONFIG ---
st.set_page_config(page_title="Swar Voice Assistant", layout="wide", page_icon="🎙️")

# --- CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #121212; color: #e0e0e0; }
        section[data-testid="stSidebar"] { background-color: #1e1e1e; }
        .email-item-box {
            padding: 12px; border-bottom: 1px solid #333; border-radius: 5px;
            margin-bottom: 5px; cursor: pointer; transition: background 0.3s;
        }
        .email-item-box:hover { background-color: #2c2c2c; }
        .chat-bubble { padding: 10px 15px; border-radius: 12px; max-width: 80%; word-wrap: break-word; font-size: 14px; }
        .bubble-user { background-color: #0b93f6; color: white; border-bottom-right-radius: 2px; }
        .bubble-assist { background-color: #333333; color: #e0e0e0; border-bottom-left-radius: 2px; }
        .chat-row { display: flex; width: 100%; margin-bottom: 10px; }
        .chat-row-user { justify-content: flex-end; }
        .chat-row-assist { justify-content: flex-start; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
if 'auth_stage' not in st.session_state: st.session_state.auth_stage = 'init'
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'emails' not in st.session_state: st.session_state.emails = []
if 'selected_email' not in st.session_state: st.session_state.selected_email = None
if 'current_folder' not in st.session_state: st.session_state.current_folder = "Inbox"
if 'compose_mode' not in st.session_state: st.session_state.compose_mode = False
if 'draft' not in st.session_state: st.session_state.draft = {"to": "", "subject": "", "body": ""}
if 'last_fetched_folder' not in st.session_state: st.session_state.last_fetched_folder = None
if 'auto_read' not in st.session_state: st.session_state.auto_read = False
if 'compose_stage' not in st.session_state: st.session_state.compose_stage = 'init'

@st.cache_resource
def init_resources():
    db.init_db()
    HARDCODED_KEY = "REMOVED_API_KEY"
    nlu.configure_genai(HARDCODED_KEY)

init_resources()

def add_chat(sender, message):
    # Force new list assignment for Streamlit state detection
    new_history = st.session_state.chat_history + [{"sender": sender, "message": message}]
    if len(new_history) > 20: 
        new_history = new_history[-20:]
    st.session_state.chat_history = new_history

def speak_and_log(text, log=True, wait=False, chat_placeholder=None):
    if log:
        add_chat("Swar", text)
        if chat_placeholder:
            render_chat_log(chat_placeholder)
            
    voice.speak(text)
    if wait:
        # Estimate duration: approx 2.0s base (engine startup) + 0.1s per char
        # "Welcome..." ~20 chars -> 4.0s total wait
        dur = 2.0 + (len(text) * 0.1)
        time.sleep(dur)

def render_chat_log(placeholder):
    if not placeholder: return
    
    chat_html = ""
    for c in st.session_state.chat_history:
            r = "chat-row-user" if c["sender"]=="User" else "chat-row-assist"
            b = "bubble-user" if c["sender"]=="User" else "bubble-assist"
            chat_html += f'<div class="{r} chat-row"><div class="{b} chat-bubble">{c["message"]}</div></div>'
    
    with placeholder.container():
        st.markdown(f'''
            <div id="chat-container" style="height: 400px; overflow-y: auto; padding: 5px; border: 1px solid #333; border-radius: 5px;">
                {chat_html}
            </div>
            <script>
                // Use a timeout to ensure DOM is ready and force execution
                setTimeout(function() {{
                    var element = document.getElementById("chat-container");
                    if(element) {{ 
                        element.scrollTop = element.scrollHeight;
                        // Double check after a short delay for large image loads or layout shifts
                        setTimeout(function() {{ element.scrollTop = element.scrollHeight; }}, 100);
                    }}
                }}, 50);
            </script>
            ''', unsafe_allow_html=True)

def speak_interruptible(text, chat_placeholder=None):
    """
    Speaks text but listens for 'stop' command simultaneously.
    Supports streaming effect in UI if chat_placeholder is provided.
    """
    # 1. Update Chat Initial
    # If streaming, we start with empty or "Speaking..." then fill it?
    # Better: Start with empty "Swar" message and fill it up?
    # For now, simplistic approach: Add FULL text to session state (hidden?) or 
    # Just add "..." then update it.
    
    # We will use keys in chat history to identify the message? No, just last one.
    
    if chat_placeholder:
        # Start with empty message if we want to stream from 0, 
        # BUT current architecture appends logic. 
        # Let's add the FULL text but maybe use a custom renderer?
        # Simpler: Add full text, but in the Loop, we don't really 'stream' visually unless we re-render portions.
        # Actually, let's just do the "Typewriter" effect:
        # 1. Add "" (empty) to chat history
        add_chat("Swar", "") 
        full_text = text
        chars_per_sec = 15 # Adjust roughly to speech speed
        
    else:
        add_chat("Swar", text)
        
    voice.speak(text)
    
    # Allow process to start (avoid immediate poll=None check failing)
    # And allow streaming loop to run
    start_time = time.time()
    
    # We need a loop that runs WHILE speaking to update the UI
    # voice.is_speaking() checks the process.
    
    # Initial wait for process to spawn
    while not voice.is_speaking():
        if time.time() - start_time > 3.0: break # timed out
        time.sleep(0.1)

    # Main Loop
    last_update = 0
    while voice.is_speaking():
        # --- STREAMING UI UPDATE ---
        if chat_placeholder:
            elapsed = time.time() - start_time
            # Estimate how many chars should be shown
            # This is a visual trick, unrelated to actual audio progress
            # 10 chars per second is slow, 20 is fast.
            # Let's just assume 15 char/s avg
            num_chars = int(elapsed * 20) 
            if num_chars > len(text): num_chars = len(text)
            
            # Update the LAST message in history
            current_show = text[:num_chars] + (" ▌" if num_chars < len(text) else "")
            
            # Direct manipulation of session state last item
            if st.session_state.chat_history and st.session_state.chat_history[-1]["sender"] == "Swar":
                 st.session_state.chat_history[-1]["message"] = current_show
            
            # Re-render periodically (every 0.5s or so to avoid flickering too much?)
            # Actually Streamlit is fast enough for 0.1s updates usually
            if time.time() - last_update > 0.1:
                render_chat_log(chat_placeholder)
                last_update = time.time()
        # ---------------------------

        # Quick check for interruption
        # Lower threshold to catch commands even if TTS is playing
        # Use 1000 - good balance?
        cmd = voice.listen(timeout=0.5, phrase_time_limit=1.5, adjust_noise=False, energy_threshold=1000)
        # print(f"DEBUG: Interrupt Listen Result: '{cmd}'") # Uncomment for debugging
        
        if cmd and ("stop" in cmd.lower() or "cancel" in cmd.lower()):
            # Log the interruption
            add_chat("User", cmd) 
            
            # Finalize the Swar message if interrupted (remove cursor)
            if chat_placeholder and st.session_state.chat_history[-1]["sender"] == "Swar":
                st.session_state.chat_history[-2]["message"] = text[:num_chars] + "..." # -2 because we just added User msg
            
            if chat_placeholder:
                render_chat_log(chat_placeholder)
                
            voice.stop_speaking()
            speak_and_log("Stopped reading.", chat_placeholder=chat_placeholder)
            return True # Interrupted
            
    # Finished Speaking Normally
    if chat_placeholder:
        # Ensure full text is shown at end
        if st.session_state.chat_history and st.session_state.chat_history[-1]["sender"] == "Swar":
             st.session_state.chat_history[-1]["message"] = text
        render_chat_log(chat_placeholder)
        
    return False # Finished normally

def main():
    # Single root placeholder to control the page layout
    root_placeholder = st.empty()
    
    if not st.session_state.logged_in:
        with root_placeholder.container():
            login_flow()
    else:
        with root_placeholder.container():
            dashboard_flow()

# --- AUTH FLOW ---
def login_flow():
    st.title("🔐 Swar - Secure Login")
    col1, col2 = st.columns([2, 1])
    with col1:
        status_box = st.empty()
        camera_box = st.empty()
    with col2:
        st.subheader("Log")
        # Custom scrollable container for Streamlit < 1.30
        # Shared Chat Log Rendering
        chat_placeholder = st.empty()
        render_chat_log(chat_placeholder)

    if st.session_state.auth_stage == 'init':
        status_box.info("Init...")
        time.sleep(1)
        st.session_state.auth_stage = 'scanning'
        st.rerun()

    elif st.session_state.auth_stage == 'scanning':
        status_box.warning("Scanning...")
        import cv2
        cap = cv2.VideoCapture(0)
        start = time.time()
        last_frame = None
        # OPTIMIZATION: Scan for 2.0s and try to identify ON THE FLY
        identified_email = None
        while (time.time() - start) < 2.0:
            ret, frame = cap.read()
            if ret: 
                camera_box.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), width=400)
                
                # Check frame for user immediately - skips waiting
                # Check every few frames to avoid lag
                if int(time.time() * 10) % 2 == 0:
                     _, buffer = cv2.imencode('.jpg', frame)
                     email, score = auth.identify_user_from_frame_bytes(buffer.tobytes())
                     if email:
                         identified_email = email
                         break
            time.sleep(0.05)
        cap.release()
        
        email = identified_email # Use found email
        if email:
            ur = db.get_user_by_email(email)
            if ur:
                g_e = ur[5] if len(ur)>5 else None
                g_p = ur[6] if len(ur)>6 else None
                st.session_state.temp_user = {"name": ur[1], "email": ur[2], "pin": ur[3], "gmail_email": g_e, "gmail_password": g_p}
                st.session_state.temp_user = {"name": ur[1], "email": ur[2], "pin": ur[3], "gmail_email": g_e, "gmail_password": g_p}
                # Use wait=False so we can move to PIN check but keep log updated? 
                # Actually wait=True is fine for login flow as long as we log FIRST.
                speak_and_log(f"Welcome {ur[1]}. PIN?", wait=True, chat_placeholder=chat_placeholder)
                st.session_state.auth_stage = 'pin_check'
                st.rerun()
        else:
            speak_and_log("Unknown face. Register?", wait=True, chat_placeholder=chat_placeholder)
            st.session_state.auth_stage = 'register_name'
            st.rerun()

    elif st.session_state.auth_stage == 'pin_check':
        pin_in = voice.listen(timeout=5)
        if pin_in:
            add_chat("User", pin_in)
            
            # Allow cancellation
            if "stop" in pin_in.lower() or "cancel" in pin_in.lower():
                 speak_and_log("Cancelled login.", wait=True, chat_placeholder=chat_placeholder)
                 st.session_state.auth_stage = 'init'
                 st.rerun()
            
            digits = ''.join(filter(str.isdigit, pin_in))
            if digits == st.session_state.temp_user['pin']:
                st.session_state.user = st.session_state.temp_user
                st.session_state.logged_in = True
                st.session_state.chat_history = []
                speak_and_log("Logged in.", chat_placeholder=chat_placeholder)
                st.rerun()
            else:
                render_chat_log(chat_placeholder) # Update chat with user wrong pin
                speak_and_log("Wrong PIN.", wait=True, chat_placeholder=chat_placeholder)
                st.rerun() # Loop back to listen again
        else:
            time.sleep(1)
            st.rerun()

    elif st.session_state.auth_stage == 'register_name':
        st.session_state.auth_stage = 'init'
        st.rerun()

# --- DASHBOARD FLOW ---
def dashboard_flow():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1144/1144760.png", width=60)
        st.markdown(f"**{st.session_state.user['name']}**")
        st.caption(st.session_state.user.get('gmail_email', 'No Gmail'))
        st.divider()
        
        if st.button("✏️ Compose New", use_container_width=True, type="primary"):
             st.session_state.compose_mode = True
             st.session_state.compose_stage = 'init'
             # speak_and_log("Starting Composer.") # Handled in loop
             st.rerun()
        st.divider()

        folders = ["Inbox", "Sent", "Drafts", "Trash", "Settings"]
        for f in folders:
            btn_type = "secondary"
            if st.session_state.current_folder == f and not st.session_state.compose_mode:
                btn_type = "primary"
            
            if st.button(f, use_container_width=True, type=btn_type):
                st.session_state.current_folder = f
                st.session_state.last_fetched_folder = None
                st.session_state.selected_email = None
                st.session_state.compose_mode = False
                # speak_and_log(f"Opening {f}") # Handled in loop or next rerun
                st.rerun() # Trigger refresh
                
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.auth_stage = 'init'
            st.rerun()

    cur_f = st.session_state.current_folder
    
    # Auto-fetch
    if not st.session_state.compose_mode and cur_f != "Settings" and st.session_state.last_fetched_folder != cur_f:
        g_u = st.session_state.user.get('gmail_email')
        g_p = st.session_state.user.get('gmail_password')
        if g_u and g_p:
            with st.spinner("Fetching..."):
                st.session_state.emails = email_manager.fetch_emails(g_u, g_p, folder=cur_f, limit=10)
                st.session_state.last_fetched_folder = cur_f
    
    if st.session_state.compose_mode:
        render_compose_pane()
    elif cur_f == "Settings":
        render_settings_page()
    else:
        render_email_dashboard()

def render_email_dashboard():
    c1, c2, c3 = st.columns([1.5, 2.5, 1.5])
    
    # We need chat placeholder FIRST to pass to reading
    with c3:
        st.subheader("🎙️ Swar")
        chat_placeholder = st.empty()
        render_chat_log(chat_placeholder)

    with c1:
        st.subheader(f"📬 {st.session_state.current_folder}")
        if st.session_state.emails:
            for i, email in enumerate(st.session_state.emails):
                is_sel = (st.session_state.selected_email == i)
                
                # Layout: separate number from content for clarity
                ec1, ec2 = st.columns([0.5, 4])
                
                with ec1:
                    st.markdown(f"**{i+1}.**")
                with ec2:
                    label = f"{email['sender'][:15]}...: {email['subject'][:20]}..."
                    if st.button(label, key=f"m_{i}", use_container_width=True, type="primary" if is_sel else "secondary"):
                        st.session_state.selected_email = i
                        st.session_state.auto_read = True
                        st.rerun()
        else:
            st.info("No emails.")

    with c2:
        st.subheader("📖 Reader")
        if st.session_state.selected_email is not None:
             if 0 <= st.session_state.selected_email < len(st.session_state.emails):
                 data = st.session_state.emails[st.session_state.selected_email]
                 
                 # LAZY LOAD BODY if missing
                 if not data.get("body"):
                     with st.spinner("Downloading email..."):
                        g_u = st.session_state.user.get('gmail_email')
                        g_p = st.session_state.user.get('gmail_password')
                        if g_u and g_p:
                             # Fetch and cache
                             full_body = email_manager.fetch_email_body(g_u, g_p, st.session_state.current_folder, data['id'])
                             st.session_state.emails[st.session_state.selected_email]['body'] = full_body
                             data['body'] = full_body # Update local ref
                 
                 st.markdown(f"**From**: {data['sender']}")
                 st.markdown(f"**Sub**: {data['subject']}")
                 st.divider()
                 st.write(data['body'])
                 
                 if st.session_state.auto_read:
                     st.session_state.auto_read = False
                     # Strip newlines and excessive whitespace for smoother reading
                     txt = data['body'].replace("\n", " ").strip()
                     # Read full email interruptibly with Sender
                     speak_interruptible(f"From: {data['sender']}. Subject: {data['subject']}. Message: {txt}", chat_placeholder=chat_placeholder)
                     st.rerun() # Refresh UI and restart listener loop after reading
             else:
                 st.warning("Error.")
        else:
            st.info("Say 'Open Email 1'...")

    # Process commands at the bottom
    with c3:
        status_ph = st.empty()
        process_voice_commands(status_ph, chat_placeholder)

def render_compose_pane():
    c1, c2 = st.columns([2, 1])
    
    with c2:
        st.subheader("🎙️ Swar")
        chat_placeholder = st.empty()
        render_chat_log(chat_placeholder)

    with c1:
        st.subheader("✍️ Compose Wizard")
        
        # NOTE: Pass Chat Placeholder to Send Logic?
        # send_current_draft logic is currently blocking. 
        # Refactor send logic to take placeholder if we want "Sending..." logs to appear.
        
        stage = st.session_state.compose_stage
        draft = st.session_state.draft
        st.info(f"Step: {stage.upper()}")
        st.text_input("To", value=draft['to'])
        st.text_input("Subject", value=draft['subject'])
        st.text_area("Body", value=draft['body'])
        if st.button("Send Now"):
             # For button clicks, we can use the placeholder if we pass it
             send_current_draft(chat_placeholder)
            
    with c2:
        # render_assistant_chat_column() # REMOVED
        status_ph = st.empty()
        process_voice_commands(status_ph, chat_placeholder)

def send_current_draft(chat_placeholder=None):
    d = st.session_state.draft
    g_u = st.session_state.user.get('gmail_email')
    g_p = st.session_state.user.get('gmail_password')
    
    if not g_u or not g_p:
        speak_and_log("Error. Missing Gmail Settings.", chat_placeholder=chat_placeholder)
        return

    if not d['to']:
         speak_and_log("Error. No recipient.", chat_placeholder=chat_placeholder)
         return

    speak_and_log("Sending email...", chat_placeholder=chat_placeholder)
    if email_manager.send_email(g_u, g_p, d['to'], d['subject'], d['body']):
         speak_and_log("Sent successfully! Opening Sent folder.", chat_placeholder=chat_placeholder)
         st.session_state.compose_mode = False
         st.session_state.compose_stage = 'init'
         st.session_state.current_folder = "Sent"
         st.session_state.last_fetched_folder = None
         # Reset draft
         st.session_state.draft = {"to": "", "subject": "", "body": ""}
         st.rerun()
    else:
         speak_and_log("Failed to send. Check credentials.", chat_placeholder=chat_placeholder)

def render_settings_page():
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Settings")
        st.info("Use voice commands.")
        g = st.session_state.user.get('gmail_email','')
        p = st.session_state.user.get('gmail_password','')
        st.text_input("Gmail", value=g, disabled=True)
        st.text_input("Pass", value=p, type="password", disabled=True)
    with c2:
        st.subheader("🎙️ Swar")
        chat_placeholder = st.empty()
        render_chat_log(chat_placeholder)
        
        status_ph = st.empty()
        process_voice_commands(status_ph, chat_placeholder)

# Removed render_assistant_chat_column as it's now integrated
# def render_assistant_chat_column(): ...

def process_voice_commands(status_ph, chat_placeholder):
    time.sleep(0.5) # Short buffer to ensure TTS starts before mic opens (fixes audio cutoff)
    
    # Wizard Prompt
    if st.session_state.compose_mode:
        stage = st.session_state.compose_stage
        if stage == 'init':
            st.session_state.compose_stage = 'recipient'
            speak_and_log("Who is the email for?", chat_placeholder=chat_placeholder)
            st.rerun()

    status_ph.markdown("#### 🔴 Listening...", unsafe_allow_html=True)
    
    # -----------------------------------------------
    # CRITICAL: We pass chat_placeholder to render new messages
    # BUT we also want to display inter-turn messages (like 'Listening...')
    # -----------------------------------------------
    cmd = voice.listen(timeout=5)
    
    if cmd:
        add_chat("User", cmd)
        render_chat_log(chat_placeholder) # Immediate update
        
        intent_data = nlu.parse_command(cmd)
        intent = intent_data.get("intent")
        params = intent_data.get("params", {})
        
        if st.session_state.compose_mode:
            # --- GLOBAL INTENT OVERRIDE ---
            # Allow user to switch context (e.g. "Open Inbox") even while composing
            if intent == "navigation":
                f = params.get("folder_name")
                if f:
                    st.session_state.current_folder = f
                    st.session_state.last_fetched_folder = None
                    st.session_state.selected_email = None
                    st.session_state.selected_email = None
                    st.session_state.compose_mode = False
                    speak_and_log(f"Opening {f}", chat_placeholder=chat_placeholder)
                    st.rerun()
                return

            if intent == "stop":
                 voice.stop_speaking()
                 speak_and_log("Stopped.", chat_placeholder=chat_placeholder)
                 st.rerun()
                 return
                 
            if intent == "logout":
                 voice.stop_speaking()
                 st.session_state.logged_in = False
                 st.session_state.auth_stage = "init"
                 speak_and_log("Logged out.", chat_placeholder=chat_placeholder)
                 st.rerun()
                 return

            if intent == "open_email":
                # If user tries to open an email, exit compose and open it
                idx = params.get("index")
                if idx is not None:
                    st.session_state.compose_mode = False
                    st.session_state.selected_email = idx
                    st.session_state.auto_read = True
                    speak_and_log(f"Opening email {idx+1}", chat_placeholder=chat_placeholder)
                    st.rerun()
                return
            # ------------------------------

            stage = st.session_state.compose_stage
            
            # Use parsed intent if available for actions
            val = params.get("value", cmd)
            
            if "cancel" in cmd.lower() or intent == "cancel":
                st.session_state.compose_mode = False
                st.session_state.compose_stage = 'init'
                speak_and_log("Cancelled.", chat_placeholder=chat_placeholder)
                st.rerun()

            elif stage == 'recipient':
                # NLU might already have sanitized it in 'value' if intent was compse_action
                # If not, fall back to basic cleanup
                if intent == "compose_action" and params.get("value"):
                     cln = params.get("value")
                else:
                     cln = cmd.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
                
                st.session_state.draft['to'] = cln
                st.session_state.compose_stage = 'recipient_confirm'
                speak_and_log(f"I heard {cln}. Is this correct?", chat_placeholder=chat_placeholder)
                st.rerun()

            elif stage == 'recipient_confirm':
                if (intent == "confirmation" and params.get("value") == "yes") or \
                   "yes" in cmd.lower() or "correct" in cmd.lower():
                    st.session_state.compose_stage = 'subject'
                    speak_and_log("Great. Subject?", chat_placeholder=chat_placeholder)
                    st.rerun()
                elif (intent == "confirmation" and params.get("value") == "no") or \
                     "no" in cmd.lower() or "wrong" in cmd.lower():
                    st.session_state.draft['to'] = ""
                    st.session_state.compose_stage = 'recipient'
                    speak_and_log("Okay. Who is the email for?", chat_placeholder=chat_placeholder)
                    st.rerun()
                else:
                    speak_and_log("Please say Yes or No.", chat_placeholder=chat_placeholder)
                    st.rerun()

            elif stage == 'subject':
                st.session_state.draft['subject'] = cmd
                st.session_state.compose_stage = 'message'
                speak_and_log("Subject set. Message?", chat_placeholder=chat_placeholder)
                st.rerun()

            elif stage == 'message':
                st.session_state.draft['body'] = cmd
                st.session_state.compose_stage = 'confirm'
                speak_and_log("Message set. Say 'Yes' to send.", chat_placeholder=chat_placeholder)
                st.rerun()
            elif stage == 'confirm':
                if (intent == "confirmation" and params.get("value") == "yes") or \
                   "yes" in cmd.lower() or "send" in cmd.lower():
                    send_current_draft(chat_placeholder)
                else:
                    speak_and_log("Say 'Yes' to send, or 'Cancel'.", chat_placeholder=chat_placeholder)
            return

        # Normal Commands
        if intent == "navigation":
            f = params.get("folder_name")
            if f:
                st.session_state.current_folder = f
                st.session_state.last_fetched_folder = None
                st.session_state.selected_email = None
                st.session_state.compose_mode = False
                speak_and_log(f"Opening {f}", chat_placeholder=chat_placeholder)
                st.rerun()
        elif intent == "open_email":
            idx = params.get("index")
            if idx is not None:
                if 0 <= idx < len(st.session_state.emails):
                    st.session_state.selected_email = idx
                    st.session_state.auto_read = True
                    speak_and_log(f"Opening email {idx+1}", chat_placeholder=chat_placeholder)
                    st.rerun()
                else:
                    speak_and_log("Invalid number.", chat_placeholder=chat_placeholder)
        elif intent == "compose_start":
            st.session_state.compose_mode = True
            st.session_state.compose_stage = 'init'
            speak_and_log("Starting Composer.", chat_placeholder=chat_placeholder)
            st.rerun()
            
        elif intent == "stop":
             voice.stop_speaking()
             speak_and_log("Stopped.", chat_placeholder=chat_placeholder)
             st.rerun()
             
        elif intent == "logout":
             voice.stop_speaking()
             st.session_state.logged_in = False
             st.session_state.auth_stage = "init"
             speak_and_log("Logged out.", chat_placeholder=chat_placeholder)
             st.rerun()

        elif intent == "delete_email":
             target_idx = None
             if params.get('index') is not None:
                 target_idx = params.get('index')
             elif st.session_state.selected_email is not None:
                 target_idx = st.session_state.selected_email
                 
             if target_idx is not None and 0 <= target_idx < len(st.session_state.emails):
                 email_id = st.session_state.emails[target_idx]['id']
                 g_u = st.session_state.user.get('gmail_email')
                 g_p = st.session_state.user.get('gmail_password')
                 
                 success = email_manager.move_to_trash(g_u, g_p, st.session_state.current_folder, email_id)
                 if success:
                     st.session_state.current_folder = "Trash"
                     st.session_state.last_fetched_folder = None
                     st.session_state.selected_email = None # Clear selection to show list
                     speak_and_log(f"Deleted email {target_idx+1}. Opening Trash.", chat_placeholder=chat_placeholder)
                     st.rerun()
                 else:
                     speak_and_log("Failed to delete.", chat_placeholder=chat_placeholder)
                     st.rerun()
             else:
                 speak_and_log("Which email?", chat_placeholder=chat_placeholder)
                 st.rerun()

        elif intent == "read_content":
            # Explicitly read the currently open email
            if st.session_state.selected_email is not None:
                st.session_state.auto_read = True
                st.rerun()
            else:
                 speak_and_log("No email is open to read.", chat_placeholder=chat_placeholder)
                 st.rerun()
        
        else:
            speak_and_log("I didn't understand.", chat_placeholder=chat_placeholder)
            st.rerun()
    else:
        time.sleep(0.5)
        st.rerun()

if __name__ == "__main__":
    main()
