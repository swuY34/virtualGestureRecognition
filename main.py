import cv2
from cvzone.HandTrackingModule import HandDetector
from utils.option_virtual_calculator import VirtualCalculator

def open_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    detector = HandDetector(maxHands=1, detectionCon=0.8)
    window_name = '实时视频'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    # 初始化状态
    option1_active = True
    option2_active = False
    stay_timer = 0
    hover_position = None

    # 当前 detector 配置
    current_max_hands = 1

    # 悬停切换相关
    hover_option = None  # "option1" 或 "option2" 或 None
    hover_switch_counter = 0
    HOVER_THRESHOLD = 30  # 停留30帧触发切换（大约1秒）

    # 模块初始化
    calculator = VirtualCalculator()

    def mouse_callback(event, x, y, flags, param):
        nonlocal option1_active, option2_active, detector, current_max_hands
        if event == cv2.EVENT_LBUTTONDOWN:
            if button1_x_start < x < button1_x_end and button1_y < y < button1_y + button_size:
                if not option1_active:
                    option1_active = True
                    option2_active = False
                    detector = HandDetector(maxHands=1, detectionCon=0.8)
                    current_max_hands = 1
            elif button2_x_start < x < button2_x_end and button2_y < y < button2_y + button_size:
                if not option2_active:
                    option1_active = False
                    option2_active = True
                    detector = HandDetector(maxHands=2, detectionCon=0.8)
                    current_max_hands = 2

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法获取图像")
            break

        frame = cv2.flip(frame, 1)
        hands, frame = detector.findHands(frame)
        height, width, _ = frame.shape
        button_size = int(min(width, height) * 0.075)
        button_spacing = int(button_size * 1.5)

        # 选项按钮区域
        button1_x_start = int(width * 2 / 3)
        button1_x_end = button1_x_start + button_spacing + button_size
        button1_y = button_spacing - button_size
        button2_x_start = int(width * 2 / 3) + 2 * button_spacing
        button2_x_end = button2_x_start + button_spacing + button_size
        button2_y = button1_y

        # 绘制选项按钮
        color1 = (255, 255, 0) if option1_active else (128, 128, 128)
        color2 = (255, 255, 0) if option2_active else (128, 128, 128)
        cv2.rectangle(frame, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(frame, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), color1, -1)
        cv2.putText(frame, "option1", (button1_x_start + 5, button1_y + int(button_size * 0.7)),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1)

        cv2.rectangle(frame, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(frame, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), color2, -1)
        cv2.putText(frame, "option2", (button2_x_start + 5, button2_y + int(button_size * 0.7)),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1)

        # 显示功能区域
        if option1_active:
            frame = calculator.draw_buttons(frame, width, height)
            calculator.draw_display(frame)

        # 手势识别逻辑（统一处理）
        if hands:
            index_tip = hands[0]["lmList"][8]
            hovering = False

            # 计算器按钮悬停判断
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

            # 修改后：任意一只手指尖悬停即可切换 option
            hover_detected = False
            for hand in hands:
                tip = hand["lmList"][8]
                x, y = tip[0], tip[1]
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
                        current_max_hands = 1
                        hover_switch_counter = 0
                    hover_detected = True
                    break
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
                        current_max_hands = 2
                        hover_switch_counter = 0
                    hover_detected = True
                    break

            if not hover_detected:
                hover_option = None
                hover_switch_counter = 0

        else:
            stay_timer = 0
            hover_position = None
            hover_option = None
            hover_switch_counter = 0

        cv2.setMouseCallback(window_name, mouse_callback)
        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    open_camera()
