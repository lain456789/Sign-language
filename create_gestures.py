import cv2
import numpy as np
import os
import sqlite3
import pickle
from PIL import Image


def get_hand_hist():
    with open("hist", "rb") as f:
        hist = pickle.load(f)
    return hist


def initialize_camera():
    """初始化摄像头"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头")
        exit(1)
    return cap


def setup_database():
    """设置手势数据库"""
    conn = sqlite3.connect('gesture_db.db')
    cursor = conn.cursor()
    # 使用gesture作为表名，g_id和g_name作为字段名
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gesture (
            g_id INTEGER PRIMARY KEY, 
            g_name TEXT
        )
    ''')
    return conn, cursor


def load_hand_histogram():
    """加载手部直方图数据"""
    try:
        with open('hist', 'rb') as f:
            hist = pickle.load(f)
        return hist
    except FileNotFoundError:
        print("错误：未找到 hist 文件，请先运行 set_hand_histogram.py")
        exit(1)


def modify_gesture():
    """修改手势数据库中的记录"""
    conn, cursor = setup_database()

    # 显示当前所有手势
    cursor.execute("SELECT g_id, g_name FROM gesture")
    gestures = cursor.fetchall()
    print("\n当前手势列表:")
    for g_id, g_name in gestures:
        print(f"ID: {g_id}, 名称: {g_name}")

    # 获取用户输入
    gesture_id = int(input("\n输入要修改的手势ID: "))
    new_name = input("输入新的手势名称: ")

    # 检查手势是否存在
    cursor.execute("SELECT g_name FROM gesture WHERE g_id = ?", (gesture_id,))
    if not cursor.fetchone():
        print(f"错误: 手势ID {gesture_id} 不存在")
        conn.close()
        return

    # 更新手势名称
    cursor.execute("UPDATE gesture SET g_name = ? WHERE g_id = ?", (new_name, gesture_id))
    conn.commit()
    conn.close()
    print(f"手势ID {gesture_id} 的名称已更新为: {new_name}")


def capture_gesture_samples(gesture_id, gesture_name):
    """采集手势样本"""
    cap = initialize_camera()
    conn, cursor = setup_database()

    # 检查手势是否已存在
    cursor.execute('SELECT g_name FROM gesture WHERE g_id = ?', (gesture_id,))
    result = cursor.fetchone()
    if result:
        choice = input(f"手势ID {gesture_id} 已存在(名称: {result[0]})。要更新吗? (y/n): ")
        if choice.lower() == 'y':
            cursor.execute('UPDATE gesture SET g_name = ? WHERE g_id = ?', (gesture_name, gesture_id))
        else:
            gesture_name = result[0]
    else:
        cursor.execute('INSERT INTO gesture (g_id, g_name) VALUES (?, ?)', (gesture_id, gesture_name))
    conn.commit()

    # 创建存储目录
    os.makedirs(f'gestures/{gesture_id}', exist_ok=True)

    # 加载手部直方图
    hist = load_hand_histogram()

    total_samples = 1200
    current_count = len(os.listdir(f'gestures/{gesture_id}')) + 1
    is_capturing = False

    print(f"\n开始采集手势 {gesture_id}({gesture_name}) 的样本")
    print("操作指南:")
    print("1. 将手部放在检测区域内")
    print("2. 按 'c' 开始/暂停采集")
    print("3. 按 'q' 退出采集")

    while current_count <= total_samples:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 手部检测
        back_proj = cv2.calcBackProject([hsv], [0, 1], hist, [0, 180, 0, 256], 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        cv2.filter2D(back_proj, -1, kernel, back_proj)
        _, thresh = cv2.threshold(back_proj, 150, 255, cv2.THRESH_BINARY)

        # 轮廓检测
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 显示采集状态
        status_frame = frame.copy()
        cv2.putText(status_frame, f"已采集: {current_count - 1}/{total_samples}", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.rectangle(status_frame, (300, 100), (600, 400), (0, 255, 0), 2)

        if contours and len(contours) > 0:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(status_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            if is_capturing:
                hand_roi = thresh[y:y + h, x:x + w]
                if hand_roi.size > 0:
                    hand_roi = cv2.resize(hand_roi, (50, 50))
                    cv2.imwrite(f'gestures/{gesture_id}/{current_count}.jpg', hand_roi)
                    current_count += 1

        cv2.imshow(f"手势采集 - {gesture_name}", status_frame)

        key = cv2.waitKey(1)
        if key == ord('c'):
            is_capturing = not is_capturing
            print("采集状态:", "进行中" if is_capturing else "已暂停")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    print(f"\n手势 {gesture_id}({gesture_name}) 采集完成！")


if __name__ == "__main__":
    print("1. 采集新手势样本")
    print("2. 修改已有手势")
    choice = input("请选择操作 (1/2): ")

    if choice == '1':
        gesture_id = int(input("输入手势编号 (g_id): "))
        gesture_name = input("输入手势名称 (g_name): ")
        capture_gesture_samples(gesture_id, gesture_name)
    elif choice == '2':
        modify_gesture()
    else:
        print("无效选择")