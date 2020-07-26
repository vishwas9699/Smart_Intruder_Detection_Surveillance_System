# Smart_Intruder_Detection_Surveillance_System

I build a robust Intruder Detection surveillance system on top of that, this will record video samples whenever someone enters your room and will also send you alert messages via Twilio API.

## 4 major steps are being performed 
* Step 1: We’re Extracting moving objects with Background Subtraction and getting rid of the shadows
* Step 2: Applying morphological operations to improve the background subtraction mask
* Step 3: Then we’re detecting Contours and making sure you’re not detecting noise by filtering small contours
* Step 4: Finally we’re computing a bounding box over the max contour, drawing the box, and displaying the image.

### SMS alert via Twilio API
<img src="https://github.com/vishwas9699/Smart_Intruder_Detection_Surveillance_System/blob/master/SMS%20alert.png">
