# Import the required libraries
import numpy as np
import cv2
import time
import datetime
from collections import deque
from twilio.rest import Client


def is_person_present(frame, thresh=1100):
    
    global foog
    
    # Apply background subtraction
    fgmask = foog.apply(frame)

    # Get rid of the shadows
    ret, fgmask = cv2.threshold(fgmask, 250, 255, cv2.THRESH_BINARY)

    # Apply some morphological operations to make sure you have a good mask
    fgmask = cv2.dilate(fgmask,None,iterations = 4)

    # Detect contours in the frame
    contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
     
    # Check if there was a contour and the area is somewhat higher than some threshold so we know its a person and not noise
    if contours and cv2.contourArea(max(contours, key = cv2.contourArea)) > thresh:
            
            # Get the max contour
            cnt = max(contours, key = cv2.contourArea)

            # Draw a bounding box around the person and label it as person detected
            x,y,w,h = cv2.boundingRect(cnt)
            cv2.rectangle(frame,(x ,y),(x+w,y+h),(0,0,255),2)
            cv2.putText(frame,'Person Detected',(x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1, cv2.LINE_AA)
            
            return True, frame
        
        
    # Otherwise report there was no one present
    else:
        return False, frame


def send_message(body, info_dict):

    # Your Account SID from twilio.com/console
    account_sid = info_dict['account_sid']

    # Your Auth Token from twilio.com/console
    auth_token  = info_dict['auth_token']


    client = Client(account_sid, auth_token)

    message = client.messages.create( to = info_dict['your_num'], from_ = info_dict['trial_num'], body= body)


#time.sleep(15)

# Set Window normal so we can resize it
cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

# This is a test video
cap = cv2.VideoCapture('Sample1.mp4')

# Read the video steram from the camera
#cap = cv2.VideoCapture('http://192.168.43.1:8080/video')

# Get width and height of the frame
width = int(cap.get(3))
height = int(cap.get(4))

# Read and store the credentials information in a dict
with open('credentials.txt', 'r') as myfile:
  data = myfile.read()

info_dict = eval(data)

# Initialize the background Subtractor
foog = cv2.createBackgroundSubtractorMOG2( detectShadows = True, varThreshold = 100, history = 2000)

# Status is True when person is present and False when the person is not present.
status = False

# After the person disapears from view, wait atleast 7 seconds before making the status False
patience = 7

# We don't consider an initial detection unless its detected 15 times, this gets rid of false positives
detection_thresh = 15

# Initial time for calculating if patience time is up
initial_time = None

# We are creating a deque object of length detection_thresh and will store individual detection statuses here
de = deque([False] * detection_thresh, maxlen=detection_thresh)

# Initialize these variables for calculating FPS
fps = 0 
frame_counter = 0
start_time = time.time()


while(True):
    
    ret, frame = cap.read()
    if not ret:
        break 
            
    # This function will return a boolean variable telling if someone was present or not, it will also draw boxes if it 
    # finds someone
    detected, annotated_image = is_person_present(frame)  
    
    # Register the current detection status on our deque object
    de.appendleft(detected)
     
    # If we have consectutively detected a person 15 times then we are sure that soemone is present    
    # We also make this is the first time that this person has been detected so we only initialize the videowriter once
    if sum(de) == detection_thresh and not status:                       
            status = True
            entry_time = datetime.datetime.now().strftime("%A, %I-%M-%S %p %d %B %Y")
            out = cv2.VideoWriter('outputs/{}.mp4'.format(entry_time), cv2.VideoWriter_fourcc(*'XVID'), 15.0, (width, height))

    # If status is True but the person is not in the current frame
    if status and not detected:
        
        # Restart the patience timer only if the person has not been detected for a few frames so we are sure it was'nt a 
        # False positive
        if sum(de) > (detection_thresh/2): 
            
            if initial_time is None:
                initial_time = time.time()
            
        elif initial_time is not None:        
            
            # If the patience has run out and the person is still not detected then set the status to False
            # Also save the video by releasing the video writer and send a text message.
            if  time.time() - initial_time >= patience:
                status = False
                exit_time = datetime.datetime.now().strftime("%A, %I:%M:%S %p %d %B %Y")
                out.release()
                initial_time = None
            
                body = "Alert: \n A Person Entered the Room at {} \n Left the room at {}".format(entry_time, exit_time)
                send_message(body, info_dict)
    
    # If significant amount of detections (more than half of detection_thresh) has occured then we reset the Initial Time.
    elif status and sum(de) > (detection_thresh/2):
        initial_time = None
    
    # Get the current time in the required format
    current_time = datetime.datetime.now().strftime("%A, %I:%M:%S %p %d %B %Y")

    # Display the FPS
    cv2.putText(annotated_image, 'FPS: {:.2f}'.format(fps), (1500, 20), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 40, 155),2)
    
    # Display Time
    cv2.putText(annotated_image, current_time, (310, 20), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 255),2)    
    
    # Display the Room Status
    cv2.putText(annotated_image, 'Room Occupied: {}'.format(str(status)), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                (200, 10, 150),2)

    # Show the patience Value
    if initial_time is None:
        text = 'Patience: {}'.format(patience)
    else: 
        text = 'Patience: {:.2f}'.format(max(0, patience - (time.time() - initial_time)))
        
    cv2.putText(annotated_image, text, (1000, 20), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 40, 155) , 2)   

    # If status is true save the frame
    if status:
        out.write(annotated_image)
 
    # Show the Frame
    cv2.imshow('frame',frame)
    
    # Calculate the Average FPS
    frame_counter += 1
    fps = (frame_counter / (time.time() - start_time))
    
    
    # Exit if q is pressed.
    if cv2.waitKey(30) == ord('q'):
        break

# Release Capture and destroy windows
cap.release()
cv2.destroyAllWindows()
out.release()