# virtual_calculator.py

import cv2

class VirtualCalculator:
    def __init__(self):
        self.button_texts = ['7', '8', '9', '+',
                             '4', '5', '6', '-',
                             '1', '2', '3', '*',
                             '.', '0', '=', '/']
        self.button_positions = []
        self.button_size = 60  # 初始默认值，之后会根据窗口大小动态设置
        self.display_text = ""
        self.current_expression = ""
        self.clicked_button_text = None

    def draw_buttons(self, frame, width, height):
        self.button_positions.clear()
        button_spacing = int(self.button_size * 1.5)
        self.button_size = int(min(width, height) * 0.075)

        for row in range(4):
            for col in range(4):
                bx = int(width * 2 / 3) + col * button_spacing
                by = int(height / 3) + row * button_spacing

                cv2.rectangle(frame, (bx, by), (bx + self.button_size, by + self.button_size), (0, 0, 0), 2)
                cv2.rectangle(frame, (bx, by), (bx + self.button_size, by + self.button_size), (128, 128, 128), -1)

                text = self.button_texts[row * 4 + col]
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, 0.6, 1)[0]
                text_x = bx + (self.button_size - text_size[0]) // 2
                text_y = by + (self.button_size + text_size[1]) // 2
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

                self.button_positions.append((bx, by, self.button_size))

        return frame

    def process_finger_click(self, x, y):
        for i, (bx, by, bs) in enumerate(self.button_positions):
            if bx < x < bx + bs and by < y < by + bs:
                self.clicked_button_text = self.button_texts[i]
                self._process_click()
                return True
        return False

    def _process_click(self):
        if self.clicked_button_text == "=":
            try:
                result = str(eval(self.current_expression))
                self.display_text = self.current_expression + "="
                self.result_text = result
            except:
                self.display_text = "Error"
                self.result_text = ""
            self.current_expression = ""
        else:
            self.current_expression += self.clicked_button_text
            self.display_text = self.current_expression

    def draw_display(self, frame):
        cv2.putText(frame, self.display_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if "=" in self.display_text:
            cv2.putText(frame, self.result_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
