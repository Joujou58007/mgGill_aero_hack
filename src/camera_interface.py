import cv2
import numpy as np

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(2)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define green color range (tune if needed)
    lower_green = np.array([40, 70, 70])
    upper_green = np.array([80, 255, 255])

    # Create mask for green pixels
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Remove noise
    mask = cv2.GaussianBlur(mask, (9, 9), 0)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)

        # Ignore very small areas
        if area < 50: 
            continue
        
        (x, y), radius = cv2.minEnclosingCircle(cnt)

        if radius < 3:
            continue
        
        center = (int(x), int(y))
        radius = int(radius)

        # Draw circle around LED
        cv2.circle(frame, center, radius, (0, 255, 0), 2)
        cv2.putText(frame, "Green LED", (center[0]+10, center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    # Press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()