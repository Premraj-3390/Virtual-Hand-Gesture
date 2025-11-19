import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
import threading

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

root = tk.Tk()
root.title("Virtual Mouse Controller")
root.geometry("400x300")
root.resizable(False, False)

running = False  
sensitivity = tk.DoubleVar(value=1.5)
status_text = tk.StringVar(value="Status: Idle")

def run_virtual_mouse():
    global running
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    screen_w, screen_h = pyautogui.size()

    prev_x, prev_y = 0, 0
    smooth_factor = 4

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        hand_landmarks = result.multi_hand_landmarks

        if hand_landmarks:
            for hand in hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                lm = hand.landmark

                h, w, _ = frame.shape
                index_x = int(lm[8].x * w)
                index_y = int(lm[8].y * h)
                thumb_x = int(lm[4].x * w)
                thumb_y = int(lm[4].y * h)

                move_x = int(screen_w / w * index_x)
                move_y = int(screen_h / h * index_y)

                curr_x = prev_x + (move_x - prev_x) / smooth_factor
                curr_y = prev_y + (move_y - prev_y) / smooth_factor
                pyautogui.moveTo(curr_x, curr_y)

                prev_x, prev_y = curr_x, curr_y

                if abs(index_y - thumb_y) < 40:
                    pyautogui.click()
                    pyautogui.sleep(0.2)

        cv2.imshow("Virtual Mouse", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    status_text.set("Status: Stopped")
    running = False

def start_mouse():
    global running
    if not running:
        running = True
        status_text.set("Status: Running")
        threading.Thread(target=run_virtual_mouse, daemon=True).start()

def stop_mouse():
    global running
    running = False
    status_text.set("Status: Stopped")

ttk.Label(root, text="Virtual Mouse", font=("Helvetica", 16, "bold")).pack(pady=10)

ttk.Label(root, text="Sensitivity").pack()
ttk.Scale(root, from_=1, to=3, orient="horizontal", variable=sensitivity).pack(pady=5)

ttk.Button(root, text="▶ Start", command=start_mouse).pack(pady=10)
ttk.Button(root, text="⏹ Stop", command=stop_mouse).pack(pady=5)

ttk.Label(root, textvariable=status_text, font=("Helvetica", 10)).pack(pady=10)
ttk.Label(root, text="Press 'Q' in the video window to exit camera", foreground="gray").pack(pady=10)

root.mainloop()
