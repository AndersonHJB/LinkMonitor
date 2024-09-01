from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from datetime import datetime
import threading

app = Flask(__name__)


# 初始化数据库
def init_db():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, 
                  url TEXT, 
                  status TEXT, 
                  last_checked TEXT)''')
    conn.commit()
    conn.close()


# 检查链接状态
def check_link(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return 'UP'
        else:
            return 'DOWN'
    except requests.exceptions.RequestException:
        return 'DOWN'


# 更新链接状态
def update_link_status():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute("SELECT id, url FROM links")
    links = c.fetchall()
    for link_id, url in links:
        status = check_link(url)
        c.execute("UPDATE links SET status = ?, last_checked = ? WHERE id = ?",
                  (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), link_id))
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute("SELECT name, url, status, last_checked FROM links")
    links = c.fetchall()
    conn.close()
    return render_template('index.html', links=links)


@app.route('/add', methods=['POST'])
def add_link():
    name = request.form['name']
    url = request.form['url']
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute("INSERT INTO links (name, url, status, last_checked) VALUES (?, ?, ?, ?)",
              (name, url, 'UNKNOWN', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# 定义一个间隔时间（例如，每10分钟执行一次检测）
INTERVAL = 3  # 秒


def periodic_check():
    update_link_status()  # 执行检测函数
    threading.Timer(INTERVAL, periodic_check).start()  # 设置定时器，递归调用自身


if __name__ == '__main__':
    init_db()
    periodic_check()  # 启动应用时，开始定时检测
    app.run(debug=True)
