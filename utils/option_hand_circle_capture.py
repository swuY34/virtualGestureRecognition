import cv2
import numpy as np
import math
import os
from datetime import datetime

class HandGestureRecognizer:
    def __init__(self):
        self.latest_crop = None
        self.save_directory = "captures"

        self.gesture_config = {
            'one': {
                'file': './hand_images/one.png',
                'fingers': [0, 1, 0, 0, 0],
            },
            'ok': {
                'file': './hand_images/ok.png',
                'check': self.check_ok_gesture,
            }
        }
        self.valid_gestures = self._load_gesture_images()
        self.gesture_history = []
        self.history_length = 5

        self.hover_counter = 0
        self.hover_frames_threshold = 100

        self.last_tip_positions = None

        self.preview_image = None
        self.show_save_button = False
        self.save_button_rect = None

        self.draw_points = []
        self.preview_stopped = False

    def _load_gesture_images(self):
        valid = {}
        for name, config in self.gesture_config.items():
            img = cv2.imread(config['file'])
            if img is not None:
                valid[name] = {
                    'img': cv2.resize(img, (200, 200)),
                    'config': config
                }
            else:
                print(f"⚠️ 无法加载 {config['file']}")
        return valid

    def angle_between_vectors(self, v1, v2):
        mag1 = np.linalg.norm(v1)
        mag2 = np.linalg.norm(v2)
        if mag1 * mag2 == 0:
            return 0
        return np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (mag1 * mag2), -1.0, 1.0)))

    def get_finger_bending_degree(self, lmList):
        coord = np.array(lmList).T
        p0 = coord[:, 0]
        bending = []
        for i in range(5):
            p1 = coord[:, 1 + 4 * i]
            p2 = coord[:, 2 + 4 * i]
            p3 = coord[:, 3 + 4 * i]
            p4 = coord[:, 4 + 4 * i]
            bend1 = self.angle_between_vectors(p1 - p0, p2 - p1)
            bend2 = self.angle_between_vectors(p4 - p3, p2 - p1)
            bending.append(bend1)
            bending.append(bend2)
        return bending

    def check_ok_gesture(self, lmList):
        thumb_tip = lmList[4][:2]
        index_tip = lmList[8][:2]
        distance = np.linalg.norm(np.array(thumb_tip) - np.array(index_tip))
        return distance < 30

    def _draw_progress_ring(self, frame, center, radius=20, thickness=5):
        cv2.circle(frame, center, radius, (200, 200, 200), thickness)
        progress_ratio = min(self.hover_counter / self.hover_frames_threshold, 1.0)
        if progress_ratio > 0:
            angle = int(360 * progress_ratio)
            cv2.ellipse(frame, center, (radius, radius), -90, 0, angle, (0, 255, 0), thickness)

    def draw_preview_and_save_button(self, frame):
        if self.preview_image is not None:
            h, w = self.preview_image.shape[:2]
            x, y = frame.shape[1] - w - 20, frame.shape[0] - h - 45
            frame[y:y + h, x:x + w] = self.preview_image
            if self.show_save_button and self.save_button_rect:
                bx, by, bw, bh = self.save_button_rect
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), -1)
                text = "Save"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
                text_x = bx + (bw - text_w) // 2
                text_y = by + (bh + text_h) // 2
                cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)
        return frame

    def draw_transparent_lines(self, frame, points, color=(0, 0, 255), thickness=5, alpha=0.7):
        overlay = frame.copy()
        for i in range(1, len(points)):
            cv2.line(overlay, points[i - 1], points[i], color, thickness)
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    def handle_mouse_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.show_save_button and self.save_button_rect:
            bx, by, bw, bh = self.save_button_rect
            if bx <= x <= bx + bw and by <= y <= by + bh:
                if self.latest_crop is not None:
                    os.makedirs(self.save_directory, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(self.save_directory, f"hand_{timestamp}.png")
                    cv2.imwrite(filename, self.latest_crop)
                    print(f"图片已保存为 {filename}")
                    self.latest_crop = None
                    self.save_button_rect = None
                    self.hover_counter = 0
                    self.last_tip_positions = None
                    self.show_save_button = False
                    self.preview_image = None
                    self.draw_points.clear()
                    self.preview_stopped = False

    def recognize(self, frame, hands, raw_frame):
        current_gesture = None

        if hands:
            hand = hands[0]
            lmList = hand["lmList"]

            bending = self.get_finger_bending_degree(lmList)
            threshold = 30
            fingers = [
                int(bending[0] < threshold and bending[1] < threshold),
                int(bending[2] < threshold and bending[3] < threshold),
                int(bending[4] < threshold and bending[5] < threshold),
                int(bending[6] < threshold and bending[7] < threshold),
                int(bending[8] < threshold and bending[9] < threshold),
            ]

            detected_gestures = []
            for name, data in self.valid_gestures.items():
                config = data['config']
                if 'fingers' in config and fingers == config['fingers']:
                    detected_gestures.append(name)
                elif 'check' in config and config['check'](lmList):
                    detected_gestures.append(name)

            self.gesture_history.append(detected_gestures)
            if len(self.gesture_history) > self.history_length:
                self.gesture_history.pop(0)

            all_detected = [g for sublist in self.gesture_history for g in sublist]
            if all_detected:
                current_gesture = max(set(all_detected), key=all_detected.count)

            if current_gesture and current_gesture in self.valid_gestures:
                img_gesture = self.valid_gestures[current_gesture]['img']
                x, y = 50, 100
                frame[y:y + 200, x:x + 200] = img_gesture

            if self.preview_stopped and current_gesture != 'ok':
                pass
            else:
                if current_gesture == 'one':
                    offset_x, offset_y = 20, 20
                    tip_pos_2d = (int(lmList[8][0]) - offset_x, int(lmList[8][1]) - offset_y)

                    moving = True
                    if self.last_tip_positions is not None:
                        dist = math.hypot(tip_pos_2d[0] - self.last_tip_positions[0],
                                          tip_pos_2d[1] - self.last_tip_positions[1])
                        moving = dist >= 10
                    else:
                        moving = False

                    self._draw_progress_ring(frame, tip_pos_2d)

                    if not moving:
                        self.hover_counter += 1
                    else:
                        self.hover_counter = 0
                        self.preview_stopped = False

                    if self.hover_counter >= self.hover_frames_threshold:
                        self.draw_points.clear()
                        self.preview_stopped = True
                        self.show_save_button = True
                        h_frame, w_frame = frame.shape[:2]
                        self.save_button_rect = (w_frame - 220, h_frame - 35, 200, 40)
                        self.hover_counter = 0

                    if not self.preview_stopped:
                        self.draw_points.append(tip_pos_2d)
                        if len(self.draw_points) > 0:
                            x_coords = [p[0] for p in self.draw_points]
                            y_coords = [p[1] for p in self.draw_points]
                            x_min, x_max = max(min(x_coords), 0), min(max(x_coords), frame.shape[1] - 1)
                            y_min, y_max = max(min(y_coords), 0), min(max(y_coords), frame.shape[0] - 1)

                            margin = 10
                            x_min = max(x_min - margin, 0)
                            y_min = max(y_min - margin, 0)
                            x_max = min(x_max + margin, frame.shape[1] - 1)
                            y_max = min(y_max + margin, frame.shape[0] - 1)

                            self.latest_crop = raw_frame[y_min:y_max, x_min:x_max].copy()

                            if self.latest_crop.size != 0:
                                self.preview_image = cv2.resize(self.latest_crop, (200, 200))

                    self.last_tip_positions = tip_pos_2d

                    frame = self.draw_transparent_lines(frame, self.draw_points)

                    if len(self.draw_points) > 0:
                        x_coords = [p[0] for p in self.draw_points]
                        y_coords = [p[1] for p in self.draw_points]
                        x_min, x_max = max(min(x_coords), 0), min(max(x_coords), frame.shape[1] - 1)
                        y_min, y_max = max(min(y_coords), 0), min(max(y_coords), frame.shape[0] - 1)
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                elif current_gesture == 'ok':
                    self.hover_counter = 0
                    self.last_tip_positions = None
                    self.show_save_button = False
                    self.preview_image = None
                    self.draw_points.clear()
                    self.preview_stopped = False

                else:
                    self.hover_counter = 0
                    self.last_tip_positions = None
                    frame = self.draw_transparent_lines(frame, self.draw_points)

                    if len(self.draw_points) > 0:
                        x_coords = [p[0] for p in self.draw_points]
                        y_coords = [p[1] for p in self.draw_points]
                        x_min, x_max = max(min(x_coords), 0), min(max(x_coords), frame.shape[1] - 1)
                        y_min, y_max = max(min(y_coords), 0), min(max(y_coords), frame.shape[0] - 1)
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        frame = self.draw_preview_and_save_button(frame)
        return frame, current_gesture
