import cv2
from cvzone.HandTrackingModule import HandDetector
from utils.option_virtual_calculator import VirtualCalculator
from utils.hands_capture import HandsCapture

def open_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    detector = HandDetector(maxHands=1, detectionCon=0.8)
    window_name = '实时视频'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    option1_active = True
    option2_active = False
    stay_timer = 0
    hover_position = None
    hover_option = None
    hover_switch_counter = 0
    HOVER_THRESHOLD = 30

    calculator = VirtualCalculator()
    hands_capture = HandsCapture()

    # 鼠标回调
    def mouse_callback(event, x, y, flags, param):
        hands_capture.handle_mouse_event(event, x, y, flags, param)

    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法获取图像")
            break

        frame = cv2.flip(frame, 1)
        raw_frame = frame.copy()  # 保留未被污染的原始图像

        # 用副本处理 hand UI，防止污染原图
        frame_for_ui = frame.copy()
        hands, frame_for_ui = detector.findHands(frame_for_ui)

        height, width, _ = frame_for_ui.shape
        button_size = int(min(width, height) * 0.075)
        button_spacing = int(button_size * 1.5)

        button1_x_start = int(width * 2 / 3)
        button1_x_end = button1_x_start + button_spacing + button_size
        button1_y = button_spacing - button_size
        button2_x_start = int(width * 2 / 3) + 2 * button_spacing
        button2_x_end = button2_x_start + button_spacing + button_size
        button2_y = button1_y

        color1 = (255, 255, 0) if option1_active else (128, 128, 128)
        color2 = (255, 255, 0) if option2_active else (128, 128, 128)
        cv2.rectangle(frame_for_ui, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(frame_for_ui, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), color1, -1)
        cv2.putText(frame_for_ui, "option1", (button1_x_start + 5, button1_y + int(button_size * 0.7)),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1)

        cv2.rectangle(frame_for_ui, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(frame_for_ui, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), color2, -1)
        cv2.putText(frame_for_ui, "option2", (button2_x_start + 5, button2_y + int(button_size * 0.7)),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1)

        # option1 功能
        if option1_active:
            frame_for_ui = calculator.draw_buttons(frame_for_ui, width, height)
            calculator.draw_display(frame_for_ui)

        # 判断手指是否悬停切换选项
        if hands:
            index_tip = hands[0]["lmList"][8]
            hovering = False

            if option1_active:
                for bx, by, bs in calculator.button_positions:
                    if bx < index_tip[0] < bx + bs and by < index_tip[1] < by + bs:
                        hovering = True
                        hover_position = (index_tip[0], index_tip[1])
                        stay_timer += 1
                        break

            if not hovering:
                stay_timer = 0
                hover_position = None

            if stay_timer >= 30 and hover_position:
                if option1_active and calculator.process_finger_click(*hover_position):
                    print(f"点击触发：{calculator.clicked_button_text}")
                stay_timer = 0

            x, y = index_tip[0], index_tip[1]
            if button1_x_start < x < button1_x_end and button1_y < y < button1_y + button_size:
                if hover_option == "option1":
                    hover_switch_counter += 1
                else:
                    hover_option = "option1"
                    hover_switch_counter = 1
                if hover_switch_counter >= HOVER_THRESHOLD and not option1_active:
                    option1_active = True
                    option2_active = False
                    detector = HandDetector(maxHands=1, detectionCon=0.8)
                    hover_switch_counter = 0
            elif button2_x_start < x < button2_x_end and button2_y < y < button2_y + button_size:
                if hover_option == "option2":
                    hover_switch_counter += 1
                else:
                    hover_option = "option2"
                    hover_switch_counter = 1
                if hover_switch_counter >= HOVER_THRESHOLD and not option2_active:
                    option1_active = False
                    option2_active = True
                    detector = HandDetector(maxHands=2, detectionCon=0.8)
                    hover_switch_counter = 0
            else:
                hover_option = None
                hover_switch_counter = 0

        else:
            stay_timer = 0
            hover_position = None
            hover_option = None
            hover_switch_counter = 0

        # option2 功能，传入未污染的 raw_frame 供截图，UI 绘制在 frame_for_ui 上
        if option2_active:
            frame_for_ui = hands_capture.process_frame(frame_for_ui, hands, raw_frame)

        cv2.imshow(window_name, frame_for_ui)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    open_camera()
