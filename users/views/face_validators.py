import cv2
import numpy as np
import face_recognition

def validate_face_image(img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #blur detection
    blur_score = cv2.Laplacian(gray,cv2.CV_64F).var()
    if blur_score < 100:
        return False, "Face is too blurry. Please try again."
    
    #saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation= hsv[:,:,1].mean()
    if saturation < 30:
        return False, "Image looks washed out. Possible screen replay. Please try again."
    
    #noise check (low->image spoof)
    noise = cv2.Laplacian(gray, cv2.CV_64F).var()
    if noise < 50:
        return False, "Low noise level detected. Suspected spoof."
    

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(img_rgb)

    if len(face_locations) != 1:
        return False, f"Exactly one face required. Found: {len(face_locations)}"

    return True, img