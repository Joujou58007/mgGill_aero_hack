import cv2
import numpy as np

# Open webcam (keep your index)
cap = cv2.VideoCapture(2)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # === 1. Pre-processing: smoothing + contrast boost (kills sensor noise & boosts LEDs) ===
    # Small Gaussian blur on the original frame (better than blurring binary mask)
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    # Optional but very effective: CLAHE on Value channel only (increases LED contrast without amplifying noise)
    hsv_temp = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    hsv_temp[:, :, 2] = clahe.apply(hsv_temp[:, :, 2])
    hsv = hsv_temp  # reuse the enhanced HSV

    # === 2. Targeted HSV masks for each color (core noise killer) ===
    # Green (tune these if your LEDs are a different shade)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # Blue
    lower_blue = np.array([95, 50, 50])
    upper_blue = np.array([135, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # White (low saturation + very high value — ignores colored ambient light)
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 40, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # === 3. Morphological cleanup on EVERY mask (removes tiny noise specks & fills holes) ===
    kernel = np.ones((5, 5), np.uint8)
    for mask in (mask_green, mask_blue):
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)   # remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)  # fill small holes inside LED

    # === 4. Combined mask just for visualisation (like your original) ===
    combined_mask = cv2.bitwise_or(mask_green, mask_blue)
    # combined_mask = cv2.bitwise_or(combined_mask, mask_white)

    # === 5. Helper to process each mask with strong blob filtering ===
    def detect_leds(mask, color_name, bgr_color, frame):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50:                      # ignore tiny noise blobs
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.65:             # LEDs are almost perfectly round
                continue

            (x, y), radius = cv2.minEnclosingCircle(cnt)
            if radius < 4:                     # too small to be a real LED
                continue

            center = (int(x), int(y))
            radius = int(radius)

            cv2.circle(frame, center, radius, bgr_color, 2)
            cv2.putText(frame, f"{color_name} LED", (center[0] + 15, center[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)

    # Run detection for all three colors
    detect_leds(mask_green, "Green", (0, 255, 0), frame)
    detect_leds(mask_blue,  "Blue",  (255, 0, 0), frame)
    # detect_leds(mask_white, "White", (255, 255, 255), frame)

    # === Show results ===
    cv2.imshow("Frame (detections)", frame)
    cv2.imshow("Combined Mask (clean)", combined_mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()