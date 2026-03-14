import cv2
import numpy as np

cap = cv2.VideoCapture(2)

# Morphological kernel
kernel = np.ones((5, 5), np.uint8)

kernel_open  = np.ones((3, 3), np.uint8)  # smaller = less aggressive noise removal
kernel_close = np.ones((7, 7), np.uint8)  # larger = better fills bloom holes

def process_led_mask(hsv, lower, upper):
    mask = cv2.inRange(hsv, lower, upper)

    _, value_mask = cv2.threshold(hsv[:, :, 2], 180, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_and(mask, value_mask)

    # Smaller open kernel — won't erase tiny LED blobs
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel_open)
    # Larger close kernel — fills gaps from bloom desaturation
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    return mask

def find_leds(mask, min_area=50, min_radius=3, min_circularity=0.6):
    """Find circular blobs in mask that look like LEDs."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    leds = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity < min_circularity:
            continue

        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if radius < min_radius:
            continue

        leds.append((int(x), int(y), int(radius)))
    return leds


def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv_pixel = param[y, x]
        print(f"HSV at ({x},{y}): H={hsv_pixel[0]}, S={hsv_pixel[1]}, V={hsv_pixel[2]}")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- Green LED ---
    # Wide hue range (35–90) catches yellow-green bloom + pure green
    # Low saturation floor (40) handles overexposed/washed-out LED center
    # High value floor (170) ensures we only pick up bright LED light
    green_lower = np.array([40, 30, 180])   # H-10, S floor below 60, V floor
    green_upper = np.array([70, 255, 255])  # H+10, full S and V ceiling
    green_mask = process_led_mask(hsv, green_lower, green_upper)

    # --- Blue LED (adjust range to your drone's blue) ---
    blue_lower = np.array([100, 80, 170])
    blue_upper = np.array([130, 255, 255])
    blue_mask = process_led_mask(hsv, blue_lower, blue_upper)

    # Draw detections
    for (x, y, r) in find_leds(green_mask):
        cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
        cv2.putText(frame, "Green LED", (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    for (x, y, r) in find_leds(blue_mask):
        cv2.circle(frame, (x, y), r, (255, 100, 0), 2)
        cv2.putText(frame, "Blue LED", (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("Green Mask", green_mask)
    cv2.imshow("Blue Mask", blue_mask)
    
    # cv2.imshow("Frame", frame)
    # cv2.setMouseCallback("Frame", mouse_callback, hsv)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()