from ultralytics import YOLO

# Load the model
model = YOLO('best.pt')  # 加载模型
model.to('cpu')#设备是cpu
# model.to('0') #设备是cuda
# Predict with the model
img=[]#多图像数组
img.append('well0_0224.jpg')
img.append('well0_0002.jpg')#多图片加载
results = model(img)  # 预测


# Process results list
for i,result in enumerate(results):
    print(i)  # i是索引
    if(len(result.boxes)==0):
        print('没有检测到')
    else:
        boxes = result.boxes  # 目标检测的结果
        names = result.names  # 5个类别的索引名 其实可以自己写出来放在外面
        for box in boxes:  # 单独图片每个盒子的检测信息
            class_index = int(box.cls.item())
            class_name = names[class_index]
            print(class_name, box.conf.item())
        # 根据图像的原名字 加_result保存
    img_file = img[i]
    file_name = img_file.split('.')[0]
    result.save(filename=f'{file_name}_result.jpg')


