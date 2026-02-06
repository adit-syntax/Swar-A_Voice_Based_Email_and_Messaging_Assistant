import cv2  # Import OpenCV for image processing
import numpy as np  # Import NumPy for array operations
import io  # Import IO for byte streams

def get_face_encodings_from_image(image_bytes):
    """
    Detects a face in the image and returns the cropped face image as bytes.
    Uses OpenCV Haar Cascades.
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)  # Create numpy array from buffer
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode array to image

        # Load Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # Load face detector

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)  # Detect faces

        if len(faces) == 0:
            return None  # Return None if no face found

        # Get the largest face
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]  # Sort by area

        # Crop the face
        face_img = img[y:y+h, x:x+w]  # Crop image

        # Resize to standard size (e.g., 200x200) for comparison
        face_img = cv2.resize(face_img, (200, 200))  # Resize

        # Encode back to bytes (jpg) to store in DB
        _, buffer = cv2.imencode('.jpg', face_img)  # Encode as JPG
        return buffer.tobytes()  # Return bytes

    except Exception as e:
        print(f"Error processing face: {e}")  # Log error
        return None

def verify_face(known_face_bytes, check_image_bytes):
    """
    Compares two faces using OpenCV Histogram Comparison.
    """
    try:
        if not known_face_bytes or not check_image_bytes:
            return False, "Missing face data"  # Validate inputs

        # 1. Decode Known Face (Stored as cropped 200x200 JPG)
        known_nparr = np.frombuffer(known_face_bytes, np.uint8)
        known_img = cv2.imdecode(known_nparr, cv2.IMREAD_COLOR)

        if known_img is None:
             return False, "Corrupt stored face signature"

        # 2. Process Check Image (Full Webcam Frame)
        check_nparr = np.frombuffer(check_image_bytes, np.uint8)
        check_full_img = cv2.imdecode(check_nparr, cv2.IMREAD_COLOR)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # Load detector
        gray_check = cv2.cvtColor(check_full_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_check, 1.1, 4)

        if len(faces) == 0:
            return False, "No face detected in camera"

        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]  # Get largest face
        check_face_img = check_full_img[y:y+h, x:x+w]  # Crop
        check_face_img = cv2.resize(check_face_img, (200, 200))  # Resize

        # 3. Compare Histograms (HSV Color Space is robust)
        # Convert to HSV
        hsv_known = cv2.cvtColor(known_img, cv2.COLOR_BGR2HSV)
        hsv_check = cv2.cvtColor(check_face_img, cv2.COLOR_BGR2HSV)

        # Calculate Histograms
        # Using channels [0, 1] (Hue, Saturation)
        hist_known = cv2.calcHist([hsv_known], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist_check = cv2.calcHist([hsv_check], [0, 1], None, [50, 60], [0, 180, 0, 256])

        # Normalize
        cv2.normalize(hist_known, hist_known, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_check, hist_check, 0, 1, cv2.NORM_MINMAX)

        # Compare (Correlation method: 1 is perfect match, 0 is mismatch)
        score = cv2.compareHist(hist_known, hist_check, cv2.HISTCMP_CORREL)

        # Threshold (0.5 to 0.7 is usually good for similar lighting)
        print(f"Face Match Score: {score}")

        if score > 0.5:
            return True, f"Face Verified (Score: {score:.2f})"
        else:
            return False, f"Face Mismatch (Score: {score:.2f})"

    except Exception as e:
        return False, f"Verification Error: {str(e)}"

def identify_user(check_image_bytes, users_list):
    """
    Identifies a user from a list of (email, encoding) tuples.
    Returns (email, score) of the best match if score > threshold, else (None, 0).
    """
    import numpy as np
    import cv2

    best_score = 0
    best_user_email = None

    # Pre-process check image once
    try:
        check_nparr = np.frombuffer(check_image_bytes, np.uint8)
        check_full_img = cv2.imdecode(check_nparr, cv2.IMREAD_COLOR)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray_check = cv2.cvtColor(check_full_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_check, 1.1, 4)

        if len(faces) == 0:
            return None, 0

        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        check_face_img = check_full_img[y:y+h, x:x+w]
        check_face_img = cv2.resize(check_face_img, (200, 200))
        hsv_check = cv2.cvtColor(check_face_img, cv2.COLOR_BGR2HSV)
        hist_check = cv2.calcHist([hsv_check], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist_check, hist_check, 0, 1, cv2.NORM_MINMAX)

        for email, encoding_bytes in users_list:
            if not encoding_bytes: continue

            # Decode known face
            known_nparr = np.frombuffer(encoding_bytes, np.uint8)
            known_img = cv2.imdecode(known_nparr, cv2.IMREAD_COLOR)
            if known_img is None: continue

            hsv_known = cv2.cvtColor(known_img, cv2.COLOR_BGR2HSV)
            hist_known = cv2.calcHist([hsv_known], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist_known, hist_known, 0, 1, cv2.NORM_MINMAX)

            score = cv2.compareHist(hist_known, hist_check, cv2.HISTCMP_CORREL)

            if score > best_score:
                best_score = score
                best_user_email = email

        if best_score > 0.4:
            print(f"DEBUG: Face match result: {best_user_email} with score {best_score}")
            return best_user_email, best_score
        else:
            print(f"DEBUG: No face match. Best score: {best_score}")
            return None, best_score

    except Exception as e:
        print(f"Identify Error: {e}")
        return None, 0
