from picamera2 import Picamera2

picam2 = Picamera2()
picam2.start()  # Must start the camera (even without preview)
picam2.capture_file("test_picam2.jpg")  # Capture
picam2.stop()
print("Photo saved as test_picam2.jpg")