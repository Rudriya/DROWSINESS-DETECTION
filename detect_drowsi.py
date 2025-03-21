# Import necessary packages
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import pygame  # Updated: Using pygame for sound playback

# Function to play alarm sound
def sound_alarm(path):
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(1.0)  # Ensure max volume
    pygame.mixer.music.play()

    # Keep script running until sound finishes playing
    while pygame.mixer.music.get_busy():
        continue  # Keeps looping while sound is playing

# Function to calculate Eye Aspect Ratio (EAR)
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Argument parsing
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor", required=True, help="Path to facial landmark predictor")
ap.add_argument("-a", "--alarm", type=str, default="", help="Path to alarm.WAV file")
ap.add_argument("-w", "--webcam", type=int, default=0, help="Index of webcam on system")
args = vars(ap.parse_args())

# Constants for drowsiness detection
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 48
COUNTER = 0
ALARM_ON = False

# Load facial landmark predictor
print("[INFO] Loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(args["shape_predictor"])
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# Start video stream
print("[INFO] Starting video stream...")
vs = VideoStream(src=args["webcam"]).start()
time.sleep(1.0)

# Main loop
while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in grayscale frame
    rects = detector(gray, 0)

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)

        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)

        ear = (leftEAR + rightEAR) / 2.0

        # Draw contours around the eyes
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        # Check if EAR is below the threshold
        if ear < EYE_AR_THRESH:
            COUNTER += 1

            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                if not ALARM_ON:
                    ALARM_ON = True
                    
                    if args["alarm"] != "":
                        t = Thread(target=sound_alarm, args=(args["alarm"],))
                        t.daemon = True
                        t.start()

                cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            COUNTER = 0
            ALARM_ON = False

        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # Quit if 'q' is pressed
    if key == ord("q"):
        break

# Cleanup
cv2.destroyAllWindows()
vs.stop()
