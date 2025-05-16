
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector

def open_camera():
    # 创建VideoCapture对象，0表示默认摄像头
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    # 设置窗口名称和大小
    window_name = '实时视频'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

    # 初始化手势检测器
    detector = HandDetector(maxHands=1, detectionCon=0.8)

    # 修改按钮上的文字，按照需求排列
    button_texts = ['7', '8', '9', '+', '4', '5', '6', '-', '1', '2', '3', '*', '.', '0', '=', '/']

    # 初始化全局变量
    global mouse_click, button_positions, button_size, stay_timer, clicked_button_text, button_clicked, display_text, current_expression, option1_active, option2_active
    mouse_click = False
    button_positions = []  # 存储所有按钮的位置信息
    button_size = None
    stay_timer = 0  # 新增计时器变量
    clicked_button_text = None  # 新增变量用于存储被点击的按钮文本
    button_clicked = False  # 初始化按钮点击状态
    display_text = ""  # 新增变量用于保存按钮上的字符
    current_expression = ""  # 新增变量用于存储当前输入的表达式
    option1_active = True  # 默认激活 option1
    option2_active = False  # 默认不激活 option2

    def mouse_callback(event, x, y, flags, param):
        global mouse_click, button_positions, button_size, stay_timer, option1_active, option2_active
        if event == cv2.EVENT_LBUTTONDOWN:
            for pos in button_positions:
                bx, by, bs = pos
                if bx < x < bx + bs and by < y < by + bs:
                    if option1_active:  # 只有在 option1 激活时，点击按钮的操作才生效
                        mouse_click = True
                        stay_timer = 0  # 点击按钮时重置计时器
            # 检查是否点击了 option1 或 option2
            if button1_x_start < x < button1_x_end and button1_y < y < button1_y + button_size:
                option1_active = True  # 激活 option1
                option2_active = False  # 取消激活 option2
            elif button2_x_start < x < button2_x_end and button2_y < y < button2_y + button_size:
                option1_active = False  # 取消激活 option1
                option2_active = True  # 激活 option2

    while True:
        # 读取一帧图像
        ret, frame = cap.read()

        if not ret:
            print("无法获取图像")
            break

        # 对图像进行水平镜像处理
        mirrored_frame = cv2.flip(frame, 1)

        # 检测手势
        hands, mirrored_frame = detector.findHands(mirrored_frame)

        # 获取图像尺寸
        height, width, _ = mirrored_frame.shape

        # 计算按钮大小和间距
        button_size = int(min(width, height) * 0.075)  # 按钮大小为图像最小边的7.5%
        button_spacing = int(button_size * 1.5)  # 按钮间距为按钮大小的1.5倍

        # 清空按钮位置列表
        button_positions.clear()

        # 绘制4x4按钮矩阵（仅在 option1 激活时绘制）
        if option1_active:
            for row in range(4):
                for col in range(4):
                    button_x = int(width * 2 / 3) + col * button_spacing  # 基准位置 + 列偏移
                    button_y = int(height / 3) + row * button_spacing  # 基准位置 + 行偏移

                    # 绘制按钮矩形
                    cv2.rectangle(mirrored_frame, (button_x, button_y), (button_x + button_size, button_y + button_size), (0, 0, 0), 2)
                    cv2.rectangle(mirrored_frame, (button_x, button_y), (button_x + button_size, button_y + button_size), (128, 128, 128), -1)

                    # 在按钮上添加文本
                    text = button_texts[row * 4 + col]  # 获取当前按钮的文本
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_TRIPLEX, 0.6, 1)[0]  # 获取文本尺寸
                    text_x = button_x + int((button_size - text_size[0]) / 2)  # 文本 x 轴居中
                    text_y = button_y + int((button_size + text_size[1]) / 2)  # 文本 y 轴居中
                    cv2.putText(mirrored_frame, text, (text_x, text_y), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

                    # 存储按钮位置信息
                    button_positions.append((button_x, button_y, button_size))

        # 添加右上角两个按钮
        # 第一个按钮：宽度为按钮矩阵中第一个按钮的x起点，到第二个按钮终点，高就是按钮矩阵中一个按钮的高度
        button1_x_start = int(width * 2 / 3)
        button1_x_end = button1_x_start + button_spacing + button_size
        button1_y = button_spacing - button_size  # 将按钮位置移到按钮矩阵上方
        button_color = (255, 255, 0) if option1_active else (128, 128, 128)  # 根据激活状态设置颜色
        cv2.rectangle(mirrored_frame, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(mirrored_frame, (button1_x_start, button1_y), (button1_x_end, button1_y + button_size), button_color, -1)
        cv2.putText(mirrored_frame, "option1", (button1_x_start + 5, button1_y + int(button_size * 0.7)), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

        # 第二个按钮：宽度为按钮矩阵中第３个按钮的x起点，到第４个按钮终点，高就是按钮矩阵中一个按钮的高度
        button2_x_start = int(width * 2 / 3) + 2 * button_spacing
        button2_x_end = int(width * 2 / 3) + 3 * button_spacing + button_size
        button2_y = button_spacing - button_size  # 将按钮位置移到按钮矩阵上方
        button_color = (255, 255, 0) if option2_active else (128, 128, 128)  # 根据激活状态设置颜色
        cv2.rectangle(mirrored_frame, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), (0, 0, 0), 2)
        cv2.rectangle(mirrored_frame, (button2_x_start, button2_y), (button2_x_end, button2_y + button_size), button_color, -1)
        cv2.putText(mirrored_frame, "option2", (button2_x_start + 5, button2_y + int(button_size * 0.7)), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

        # 注册鼠标回调函数
        cv2.setMouseCallback(window_name, mouse_callback)

        # 判断手指是否停留在按钮上（仅在 option1 激活时生效）
        if hands and option1_active:
            hand = hands[0]
            lmList = hand["lmList"]  # 获取手部关键点列表
            index_finger_tip = lmList[8]  # 获取食指指尖的关键点
            button_clicked = False  # 标记是否有按钮被点击
            for pos in button_positions:
                bx, by, bs = pos
                if bx < index_finger_tip[0] < bx + bs and by < index_finger_tip[1] < by + bs:
                    stay_timer += 1  # 手指停留在按钮上时计时
                    if stay_timer >= 30:  # 1.5秒后触发点击事件（假设帧率为20fps）
                        clicked_button_text = button_texts[button_positions.index(pos)]  # 获取被点击的按钮文本
                        if clicked_button_text == "=":
                            try:
                                result_text = str(eval(current_expression))
                                display_text = current_expression + "="  # 更新显示文本
                            except:
                                display_text = "Error"  # 如果表达式无效，显示错误
                            current_expression = ""  # 重置表达式
                        else:
                            current_expression += clicked_button_text  # 将点击的按钮文本添加到表达式中
                            display_text = current_expression  # 更新显示文本
                        button_clicked = True  # 标记按钮被点击
                        stay_timer = 0  # 重置计时器
                    break
            else:
                stay_timer = 0  # 手指离开按钮时重置计时器

        # 如果检测到按钮被点击
        if button_clicked:
            print(f"按钮被点击，显示文字: {clicked_button_text}")
            button_clicked = False  # 重置点击状态

        # 如果检测到鼠标点击按钮
        if mouse_click:
            print(f"按钮被点击，显示文字: {text}")
            mouse_click = False  # 重置点击状态

        # 在图像区域显示保存的字符（仅在 option1 激活时显示）
        if option1_active:
            cv2.putText(mirrored_frame, display_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 如果有运算结果，将其显示在第二行并使用绿色字体（仅在 option1 激活时显示）
        if option1_active and "=" in display_text:
            cv2.putText(mirrored_frame, result_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 显示镜像后的图像
        cv2.imshow(window_name, mirrored_frame)

        # 按下'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    open_camera()