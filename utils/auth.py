import cv2
import os
import time
from utils import face_auth
from utils.db import get_all_users_encodings

# No longer need separate FACES_DIR logic as we store BLOBs in DB, 
# but we might use it for debug or temp storage if needed. For now, strict DB usage.

def capture_face():
    """
    Captures a single frame from the webcam.
    Returns: (success, frame_bytes)
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, None
    
    # Warm up camera
    for _ in range(5): # Faster warmup
        ret, frame = cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        # Encode to bytes for processing
        _, buffer = cv2.imencode('.jpg', frame)
        return True, buffer.tobytes()
    
    return False, None

def identify_user_from_camera():
    """
    Captures a frame and attempts to identify against ALL users in DB.
    Returns: email (if found), score
    """
    success, frame_bytes = capture_face()
    if not success:
        return None, 0
        
    users = get_all_users_encodings() # [(email, blob), ...]
    if not users:
        return None, 0
        
    email, score = face_auth.identify_user(frame_bytes, users)
    return email, score

def identify_user_from_frame_bytes(frame_bytes):
    """
    Identifies a user from already captured frame bytes.
    Avoids re-opening the camera.
    """
    users = get_all_users_encodings()
    if not users:
        return None, 0
    return face_auth.identify_user(frame_bytes, users)

def get_face_encoding_from_frame(frame):
    """
    Given a cv2 frame, return the encoding bytes to save.
    """
    _, buffer = cv2.imencode('.jpg', frame)
    return face_auth.get_face_encodings_from_image(buffer.tobytes())
