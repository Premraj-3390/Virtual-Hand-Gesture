import cv2
import mediapipe as mp
import pyautogui

# Initialize modules
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
screen_width, screen_height = pyautogui.size()

cap = cv2.VideoCapture(0)

index_y = 0

while True:
    success, image = cap.read()
    if not success:
        break

    image = cv2.flip(image, 1)  # Mirror image
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_image)
    hand_landmarks = result.multi_hand_landmarks

    if hand_landmarks:
        for hand in hand_landmarks:
            mp_drawing.draw_landmarks(image, hand, mp_hands.HAND_CONNECTIONS)
            landmarks = hand.landmark

            for id, lm in enumerate(landmarks):
                h, w, c = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)

                if id == 8:  # Index finger tip
                    cv2.circle(image, (cx, cy), 10, (0, 255, 0), cv2.FILLED)
                    index_x = int(screen_width / w * cx)
                    index_y = int(screen_height / h * cy)
                    pyautogui.moveTo(index_x, index_y)

                if id == 4:  # Thumb tip
                    thumb_x, thumb_y = int(screen_width / w * cx), int(screen_height / h * cy)

            # Click Detection: If thumb & index are close
            if abs(index_y - thumb_y) < 50:
                pyautogui.click()
                pyautogui.sleep(0.2)

    cv2.imshow("Virtual Mouse", image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
