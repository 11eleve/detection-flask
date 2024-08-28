from flask import Flask, make_response, request, jsonify, send_file
from flask_cors import CORS
import mysql.connector, threading
from ultralytics import YOLO


app = Flask(__name__)
CORS(app, supports_credentials=True)
#全局变量
uninumput = 0 #uniapp上传时
lock = threading.Lock()
uninumpush = 0 #web将uniapp信息取出时
webnumput = 1#web将派工单信息存入时
webnumpush = 1#uniapp将信息取出时
words = ''
latitude = ''
longitude = ''#v8
model = YOLO('v8/best.pt')  # 加载模型
model.to('cpu')#设备是cpu


@app.route('/', methods=['GET', 'POST'])
def run():
    host = request.headers.get('Host')  # 获取headers内的host
    print(host)

    return make_response('ok')

#web获取图片信息
@app.route('/getinfo', methods=['GET'])
def getinfo():
    global uninumpush
    print(uninumpush)
    # 获取图片数据，图片等待接入模型
    # 获取字符串数据
    conn = mysql.connector.connect(
        host="localhost",  # 数据库地址
        user="root",  # 数据库用户名
        password="123456",  # 数据库密码
        database="info"  # 数据库名
    )
    cursor = conn.cursor()
    sql = f"SELECT words,longitude,latitude,class FROM uniappinfo WHERE id = %s"
    val = (uninumpush,)
    cursor.execute(sql, val)
    result = cursor.fetchone()
    if result:
        # 将图片路径和字符串数据组合成一个 JSON 对象
        data = {
            'Words': result[0],
            'Longitude': result[1],
            'Latitude': result[2],
            'Class': result[3],
            'msg': 'Suc'
        }
        # 将 JSON 对象作为响应发送给前端
        return jsonify(data)
    else:
        return jsonify({'msg': 'Over'})


#web获取图片，！后面把图片路径改成动态的
@app.route('/getimage', methods=['GET'])
def getimage():
    lock.acquire()
    try:
        global uninumpush
        image = f'./jg/{uninumpush}.jpg'
        # 修改全局变量
        uninumpush += 1
    finally:
        # 释放线程锁
        lock.release()
    return send_file(image, mimetype='image/jpg')


#网页信息入库
@app.route('/pushsql', methods=['POST'])
def pushsql():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="info"
    )
    cursor = conn.cursor()
    longitude = request.form['Longitude']
    latitude = request.form['Latitude']
    print(longitude)
    print(latitude)

    sql = "INSERT INTO location (longitude, latitude) VALUES (%s,%s)"
    data = (longitude, latitude, )
    cursor.execute(sql, data)
    conn.commit()
    cursor.close()
    conn.close()
    response = {'msg': 'True'}
    return jsonify(response)


#网页下发派工单,先将信息保存在数据库
@app.route('/joborder', methods=['POST'])
def joborder():
    global webnumput
    print(webnumput)
    longitude = request.form['Longitude']
    latitude = request.form['Latitude']
    words = request.form['Words']
    wclass = request.form['Class']
    id = webnumput
    # print(loc)
    # print(words)
    # print(wclass)
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="info"
    )
    cursor = conn.cursor()
    sql = "INSERT INTO repair (longitude,latitude, class, words, id) VALUES (%s,%s,%s,%s,%s)"
    data = (longitude, latitude, wclass, words, id, )
    cursor.execute(sql, data)
    conn.commit()
    # 关闭游标和连接
    cursor.close()
    conn.close()
    lock.acquire()
    try:
        # 修改全局变量
        webnumput += 1
    finally:
        # 释放线程锁
        lock.release()
    response = {'msg': 'True'}
    return jsonify(response)

# 网页登陆
@app.route('/weblogin', methods = ['POST'])
def weblogin():
    try:
        conn = mysql.connector.connect(
            host="localhost",  # 数据库地址
            user="root",  # 数据库用户名
            password="123456",  # 数据库密码
            database="info"  # 数据库名
        )
        print("成功连接到数据库！")
    except mysql.connector.Error as err:
        print("数据库连接错误：", err)
    count = request.form['Count']
    password = request.form['Password']
    print(count)
    print(password)
    cursor = conn.cursor()
    sql = f"SELECT password FROM user WHERE count = %s and id = 2"
    val = (count, )
    cursor.execute(sql, val)
    result = cursor.fetchone()
    if result:
        if result[0] == password:
            response = {'status': '200', 'msg': 'True','type' : 'success'}
            return jsonify(response)
    response = {'status': '500', 'msg': 'Flase','type':'error'}
    return jsonify(response)



# uniapp上传信息
@app.route('/uniappinfo', methods=['POST'])
def uniappinfo():
    global uninumput
    global words
    global longitude
    global latitude
    print(uninumput)
    id = uninumput
    data = request.get_json()
    words = data.get('Words')  # 获取上传的文本数据
    longitude = data.get('Longitude')
    latitude = data.get('Latitude')
    print(words)
    print(longitude)
    return jsonify({'msg': 'True'})


#uniapp上传图片
@app.route('/uniappimage', methods=['POST'])
def uniappimage():
    global uninumput
    print(uninumput)
    global longitude
    global latitude
    global words
    try:
        conn = mysql.connector.connect(
            host="localhost",  # 数据库地址
            user="root",  # 数据库用户名
            password="123456",  # 数据库密码
            database="info"  # 数据库名
        )
        print("成功连接到数据库！")
    except mysql.connector.Error as err:
        print("数据库连接错误：", err)
    cursor = conn.cursor()
    img = []
    # 获取上传的图片文件
    image = request.files['Image']
    image.save(f'./image/{uninumput}.jpg')
    image = f'./image/{uninumput}.jpg'
    img.append(image)
    results = model(img)  # 预测
    # Process results list
    data = {
        'msg' : "True",
    }
    for i, result in enumerate(results):
        print(i)  # i是索引
        print(len(result.boxes))
        if len(result.boxes) == 0:
            print('没有检测到')
            data['msg'] = 'False'
            return jsonify(data)
        else:
            boxes = result.boxes  # 目标检测的结果
            names = result.names  # 5个类别的索引名 其实可以自己写出来放在外面
            for box in boxes:  # 单独图片每个盒子的检测信息
                class_index = int(box.cls.item())
                class_name = names[class_index]
                print(class_name, box.conf.item())
                sql = "INSERT INTO uniappinfo (words, longitude, latitude, class, id) VALUES (%s, %s, %s, %s, %s)"
                val = (words, longitude, latitude, class_name, uninumput,)
                cursor.execute(sql, val)
                # 修改全局变量
                result.save(filename=f'./jg/{uninumput}.jpg')
                uninumput += 1
                conn.commit()
                # 关闭游标和连接
                cursor.close()
                conn.close()
            # 根据图像的原名字 加_result保存
        # file_name = img_file.split('.')[0]
    # 返回上传成功的消息
    return jsonify(data)

#uniapp登陆
@app.route('/uniapplogin', methods = ['POST'])
def uniapplogin():
    try:
        conn = mysql.connector.connect(
            host="localhost",  # 数据库地址
            user="root",  # 数据库用户名
            password="123456",  # 数据库密码
            database="info"  # 数据库名
        )
        print("成功连接到数据库！")
    except mysql.connector.Error as err:
        print("数据库连接错误：", err)
    data = request.get_json()
    count = data.get('Count')
    password = data.get('Password')
    print(count)
    print(password)
    cursor = conn.cursor()
    sql = f"SELECT password,id FROM user WHERE count = %s"
    val = (count, )
    cursor.execute(sql, val)
    result = cursor.fetchone()
    if result:
        if result[0] == password:
            if result[1] == '0':
                response = {'code': '200', 'msg': 'Check'}
                print(response)
                return jsonify(response)
            elif result[1] == '1':
                response = {'code': '200', 'msg': 'Repair'}
                return jsonify(response)
    response = {'code': '500', 'msg': 'Flase'}
    return jsonify(response)

#repair获取信息
@app.route('/unigetdata', methods = ['GET'])
def unigetdata():
    lock.acquire()
    try:
        global webnumpush
        print(webnumpush)
        id = webnumpush
        conn = mysql.connector.connect(
            host="localhost",  # 数据库地址
            user="root",  # 数据库用户名
            password="123456",  # 数据库密码
            database="info"  # 数据库名
        )
        cursor = conn.cursor()
        sql = f"SELECT longitude, latitude, class, words FROM repair WHERE id = %s"
        val = (id,)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        if result == None:
            return jsonify({'msg': 'Over'})
            # 修改全局变量
        webnumpush += 1
    finally:
        # 释放线程锁
        lock.release()
    return jsonify({'msg' : 'True', 'Longitude' : result[0], 'Latitude' : result[1], 'Class' : result[2], 'Words':result[3]})


if __name__ == '__main__':
    app.run(host='192.168.0.105')

