import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
import threading
import time
import numpy as np

# Disable PyAutoGUI fail-safe (optional, remove if you want it back)
pyautogui.FAILSAFE = False

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# GUI Setup
root = tk.Tk()
root.title("Virtual Mouse App")
root.geometry("420x400")
root.resizable(False, False)

running = False
sensitivity = tk.DoubleVar(value=2.0)
status_text = tk.StringVar(value="Status: Stopped")

# Gesture state
last_click_time = 0
click_cooldown = 0.3  # seconds between clicks

def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def run_virtual_mouse():
    global running, last_click_time

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    screen_w, screen_h = pyautogui.size()
    prev_x, prev_y = screen_w // 2, screen_h // 2
    smooth_factor = 5  # higher = smoother but laggier

    status_text.set("Status:Running..")

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        gesture = "Move"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                lm = hand_landmarks.landmark

                # Key points
                index_tip = (lm[8].x * w, lm[8].y * h)
                thumb_tip = (lm[4].x * w, lm[4].y * h)
                middle_tip = (lm[12].x * w, lm[12].y * h)
                ring_tip = (lm[16].x * w, lm[16].y * h)
                wrist = (lm[0].x * w, lm[0].y * h)

                # Smooth cursor movement (index finger tip)
                cursor_x = lm[8].x * screen_w
                cursor_y = lm[8].y * screen_h

                # Apply sensitivity
                sens = sensitivity.get()
                dx = (cursor_x - prev_x) * sens
                dy = (cursor_y - prev_y) * sens

                new_x = prev_x + dx / smooth_factor
                new_y = prev_y + dy / smooth_factor

                new_x = np.clip(new_x, 0, screen_w - 1)
                new_y = np.clip(new_y, 0, screen_h - 1)

                pyautogui.moveTo(new_x, new_y)
                prev_x, prev_y = new_x, new_y

                # Gesture detection
                index_thumb_dist = distance(index_tip, thumb_tip)
                index_middle_dist = distance(index_tip, middle_tip)

                # Left Click (Index + Thumb close)
                if index_thumb_dist < 40:
                    current_time = time.time()
                    if current_time - last_click_time > click_cooldown:
                        pyautogui.click()
                        last_click_time = current_time
                        gesture = "Left Click 👆"
                    # Hold for drag
                    pyautogui.mouseDown(button='left')

                else:
                    pyautogui.mouseUp(button='left')

                # Double Click (two quick pinches)
                # (handled by time check above)

                # Right Click (Index + Middle close)
                if index_middle_dist < 50 and index_thumb_dist > 50:
                    current_time = time.time()
                    if current_time - last_click_time > click_cooldown:
                        pyautogui.rightClick()
                        last_click_time = current_time
                        gesture = "Right Click 👌"

                # Scroll (Index + Middle + Ring raised, thumb down)
                fingers_up = sum([
                    lm[8].y < lm[6].y,   # index
                    lm[12].y < lm[10].y, # middle
                    lm[16].y < lm[14].y, # ring
                ])

                if fingers_up >= 3 and lm[4].y > lm[3].y:  # thumb down
                    pyautogui.scroll(40)
                    gesture = "Scroll Up ☝"
                elif fingers_up >= 3 and lm[4].y < lm[3].y:  # thumb up
                    pyautogui.scroll(-40)
                    gesture = "Scroll Down ☝"

        else:
            pyautogui.mouseUp()  # safety

        cv2.putText(frame, f"Gesture: {gesture}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'Q' to quit", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Advanced Virtual Mouse - Move: Index | Click: Pinch | Right: Index+Middle | Scroll: 3 Fingers", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    pyautogui.mouseUp()
    status_text.set("Status:Stopped.")
    running = False


def start_mouse():
    global running
    if not running:
        running = True
        threading.Thread(target=run_virtual_mouse, daemon=True).start()

def stop_mouse():
    global running
    running = False


# GUI Layout
ttk.Label(root, text="Virtual Mouse App", font=("Helvetica", 18, "bold")).pack(pady=15)

ttk.Label(root, text="Hand Gestures:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=30)
ttk.Label(root, text="• Move cursor → Index finger", foreground="gray").pack(anchor="w", padx=40)
ttk.Label(root, text="• Left click / Drag → Thumb + Index pinch", foreground="gray").pack(anchor="w", padx=40)
ttk.Label(root, text="• Right click → Index + Middle close", foreground="gray").pack(anchor="w", padx=40)
ttk.Label(root, text="• Scroll → 3 fingers up/down", foreground="gray").pack(anchor="w", padx=40)

ttk.Separator(root, orient="horizontal").pack(fill="x", pady=15, padx=20)

ttk.Label(root, text="Sensitivity").pack()
ttk.Scale(root, from_=0.5, to=4.0, orient="horizontal", variable=sensitivity).pack(padx=50, fill="x")

ttk.Button(root, text="▶ Start Virtual Mouse", command=start_mouse, style="Accent.TButton").pack(pady=12)
ttk.Button(root, text="⏹ Stop", command=stop_mouse).pack(pady=5)

ttk.Label(root, textvariable=status_text, font=("Helvetica", 11, "bold"), foreground="blue").pack(pady=10)

root.mainloop()