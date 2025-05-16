import cv2
import math
import os
from datetime import datetime

class HandsCapture:
    def __init__(self, min_distance=30, hover_frames_threshold=100):
        self.min_distance = min_distance
        self.hover_frames_threshold = hover_frames_threshold
        self.tip_hover_pos_dict = {}
        self.tip_hover_counter = 0
        self.capture_done = False

        self.preview_image = None
        self.latest_crop = None  # 原图截图用于保存
        self.show_save_button = False
        self.save_button_rect = None
        self.last_captured_rect = None

        self.save_directory = "captures"

    def draw_rectangle_around_fingertips(self, frame, index_tips):
        if len(index_tips) < 2:
            return frame
        pt1 = (int(index_tips[0][0]), int(index_tips[0][1]))
        pt2 = (int(index_tips[1][0]), int(index_tips[1][1]))
        distance = math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])
        if distance < self.min_distance:
            return frame
        x_min = max(0, min(pt1[0], pt2[0]) - 10)
        y_min = max(0, min(pt1[1], pt2[1]) - 10)
        x_max = min(frame.shape[1], max(pt1[0], pt2[0]) + 10)
        y_max = min(frame.shape[0], max(pt1[1], pt2[1]) + 10)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        return frame

    def update_and_draw_progress(self, frame, index_tips, raw_frame):
        if len(index_tips) < 2:
            return frame, None, False

        moving = False
        for i, tip in enumerate(index_tips[:2]):
            x, y = tip[:2]
            if i not in self.tip_hover_pos_dict:
                self.tip_hover_pos_dict[i] = (x, y)
            else:
                dist = math.hypot(x - self.tip_hover_pos_dict[i][0], y - self.tip_hover_pos_dict[i][1])
                if dist >= 10:
                    moving = True
                self.tip_hover_pos_dict[i] = (x, y)

        if moving:
            self.tip_hover_counter = 0
            self.capture_done = False
        elif not self.capture_done:
            self.tip_hover_counter += 1

        progress_ratio = min(self.tip_hover_counter / self.hover_frames_threshold, 1.0)

        # 绘制进度环
        radius = 20
        thickness = 5
        for tip in index_tips[:2]:
            center = (int(tip[0]), int(tip[1]))
            cv2.circle(frame, center, radius, (200, 200, 200), thickness)
            angle = int(360 * progress_ratio)
            cv2.ellipse(frame, center, (radius, radius), -90, 0, angle, (0, 255, 0), thickness)

        progress_full = False
        rect_coords = None
        if progress_ratio >= 1.0 and not self.capture_done:
            pt1 = (int(index_tips[0][0]), int(index_tips[0][1]))
            pt2 = (int(index_tips[1][0]), int(index_tips[1][1]))
            x_min = max(0, min(pt1[0], pt2[0]) - 10)
            y_min = max(0, min(pt1[1], pt2[1]) - 10)
            x_max = min(raw_frame.shape[1], max(pt1[0], pt2[0]) + 10)
            y_max = min(raw_frame.shape[0], max(pt1[1], pt2[1]) + 10)

            # 原始尺寸截图
            self.latest_crop = raw_frame[y_min:y_max, x_min:x_max].copy()

            # 创建预览图（缩略图）
            self.preview_image = cv2.resize(self.latest_crop, (150, 150))

            self.capture_done = True
            self.show_save_button = True
            self.save_button_rect = (frame.shape[1] - 170, frame.shape[0] - 35, 150, 25)
            self.last_captured_rect = (x_min, y_min, x_max, y_max)
            progress_full = True
            rect_coords = self.last_captured_rect

        return frame, rect_coords, progress_full

    def draw_preview_and_save_button(self, frame):
        if self.preview_image is not None:
            h, w = self.preview_image.shape[:2]
            x, y = frame.shape[1] - w - 20, frame.shape[0] - h - 45
            frame[y:y + h, x:x + w] = self.preview_image
            if self.show_save_button and self.save_button_rect:
                bx, by, bw, bh = self.save_button_rect
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), -1)
                cv2.putText(frame, "Save", (bx + 50, by + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        return frame

    def reset_progress(self):
        self.tip_hover_pos_dict = {}
        self.tip_hover_counter = 0
        self.capture_done = False
        self.show_save_button = False
        self.preview_image = None
        self.latest_crop = None
        self.save_button_rect = None
        self.last_captured_rect = None

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
                    self.show_save_button = False
                    self.capture_done = False
                    self.preview_image = None
                    self.latest_crop = None
                    self.save_button_rect = None

    def reset_state(self):
        pass  # 可根据需求决定是否清除预览图等

    def process_frame(self, frame, hands, raw_frame):
        index_tips = []
        for hand in hands:
            if "lmList" in hand and len(hand["lmList"]) > 8:
                index_tips.append(hand["lmList"][8])

        frame = self.draw_rectangle_around_fingertips(frame, index_tips)
        frame, rect_coords, progress_full = self.update_and_draw_progress(frame, index_tips, raw_frame)
        frame = self.draw_preview_and_save_button(frame)
        return frame
