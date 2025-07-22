import sqlite3
conn = sqlite3.connect("gesture_db.db")
cursor = conn.cursor()

# 查看表结构
cursor.execute("PRAGMA table_info(gestures)")
columns = [col[1] for col in cursor.fetchall()]  # 提取所有列名
print("表中的列名：", columns)  # 例如输出：['id', 'gesture_type', 'data']

conn.close()
# 连接到数据库
conn = sqlite3.connect("gesture_db.db")
cursor = conn.cursor()

# 示例：更新表中的数据（假设表名为 gestures）
#cursor.execute("INSERT INTO gesture (g_id, g_name) VALUES (?, ?)", (0, "I love you"))
cursor.execute("DELETE FROM gesture WHERE g_name = ?",("1"))
# 提交更改并关闭连接
conn.commit()
conn.close()

#复制表格
# # 连接数据库
# conn = sqlite3.connect('gesture_db.db')
# cursor = conn.cursor()
#
# # 复制表格内容（结构相同）
# try:
#     cursor.execute("INSERT INTO gestures SELECT * FROM gesture")
#     conn.commit()  # 提交事务
#     print("数据复制成功！")
# except sqlite3.Error as e:
#     print(f"错误：{e}")
#
# # 关闭连接
# conn.close()

import sqlite3
from tabulate import tabulate

def print_db_contents(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        print(f"\n表名: {table_name}")

        # 获取列名
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # 获取数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # 打印表格
        print(tabulate(rows, headers=columns, tablefmt="grid"))

    conn.close()


# 调用示例
print_db_contents("gesture_db.db")