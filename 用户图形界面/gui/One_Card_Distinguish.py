# -*- coding:utf-8 -*-
import shutil
import tkinter.filedialog
from tkinter import *
from PIL import Image,ImageTk
from tkinter.filedialog import askopenfilename


import argparse
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from PIL import Image
from lib.config import config as cfg
from lib.utils.nms_wrapper import nms
from lib.utils.test import im_detect
#from nets.resnet_v1 import resnetv1
from lib.nets.vgg16 import vgg16
from lib.lib.nets.vgg16 import vgg8
from lib.utils.timer import Timer

# 创建tkinter主窗口
root = tkinter.Tk()
root.title('石家庄铁道大学--打不倒的小强队')

# 指定主窗口位置与大小
w, h = root.maxsize()
root.state("zoomed")
root.geometry("{}x{}".format(w, h))   # width x height + widthoffset + heightoffset

# 不允许改变窗口大小
root.resizable(True, True)
root.focusmodel()


## 读取图像，解决imread不能读取中文路径的问题
def cv_imread(filePath):
    cv_img=cv2.imdecode(np.fromfile(filePath,dtype=np.uint8),-1)
    ## imdecode读取的是rgb，如果后续需要opencv处理的话，需要转换成bgr，转换后图片颜色会变化
    ##cv_img=cv2.cvtColor(cv_img,cv2.COLOR_RGB2BGR)
    return cv_img

#获取输入的标注内容
def getstr():
    words = '123'
    if words != '':
        input_valueText.insert(0,words)


#打开图片文件并显示
def choosepic():
    filelist = []
    rootdir = r"images/"  # 选取删除文件夹的路径,最终结果删除img文件夹
    filelist = os.listdir(rootdir)  # 列出该目录下的所有文件名
    for f in filelist:
        filepath = os.path.join(rootdir, f)  # 将文件名映射成绝对路劲
        if os.path.isfile(filepath):  # 判断该文件是否为文件或者文件夹
            os.remove(filepath)  # 若为文件，则直接删除
            # print(str(filepath) + " removed!")
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath, True)  # 若为文件夹，则删除该文件夹及文件夹内所有文件
            # print("dir " + str(filepath) + " removed!")
    # shutil.rmtree(rootdir, True)  # 最后删除img总文件夹
    print("删除成功")
    path_ = askopenfilename()
    #path.set(path_)
    img_open = Image.open(path_)
    img_open = img_open.resize((400, 300),Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img_open)
    image_label.config(image=img)
    image_label.image = img  # keep a reference
    def gui(path):

        CLASSES = ('__background__', 'lb')
        NETS = {'vgg16': ('vgg16_faster_rcnn_iter_70000.ckpt',), 'res101': ('res101_faster_rcnn_iter_110000.ckpt',)}
        DATASETS = {'pascal_voc': ('voc_2007_trainval',), 'pascal_voc_0712': ('voc_2007_trainval+voc_2012_trainval',)}

        # ***************************************    第一步：进行银行卡定位处理   position    **********************************
        def position(path, filename):
            print("正在进行定位处理")

            # 第一步
            def vis_detections(im, class_name, dets, thresh=0.5):
                """Draw detected bounding boxes."""
                inds = np.where(dets[:, -1] >= thresh)[0]
                if len(inds) == 0:
                    return
                im = im[:, :, (2, 1, 0)]
                fig, ax = plt.subplots(figsize=(12, 12))
                ax.imshow(im, aspect='equal')
                sco = []
                for i in inds:
                    score = dets[i, -1]
                    sco.append(score)
                maxscore = max(sco)  # 成绩最大值
                for i in inds:
                    score = dets[i, -1]
                    if score == maxscore:
                        bbox = dets[i, :4]
                        img = cv2.imread(path)
                        sp = img.shape
                        width = sp[1]
                        if bbox[0] > 50 and bbox[2] + 50 < width:
                            cropped = img[int(bbox[1]):int(bbox[3]),
                                      int(bbox[0] - 50):int(bbox[2]) + 50]  # 裁剪坐标为[y0:y1, x0:x1]
                        if bbox[0] < 50 and bbox[2] + 50 < width:
                            cropped = img[int(bbox[1]):int(bbox[3]),
                                      int(bbox[0]):int(bbox[2]) + 50]  # 裁剪坐标为[y0:y1, x0:x1]
                        if bbox[0] > 50 and bbox[2] + 50 > width:
                            cropped = img[int(bbox[1]):int(bbox[3]),
                                      int(bbox[0] - 50):int(bbox[2])]  # 裁剪坐标为[y0:y1, x0:x1]
                        if bbox[0] < 50 and bbox[2] + 50 > width:
                            cropped = img[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]  # 裁剪坐标为[y0:y1, x0:x1]
                        path1 = 'images/position/'  # 存定位图片地址
                        if not os.path.exists(path1):
                            os.makedirs(path1)
                        # 重定义图片的大小
                        cv2.imwrite(path1 + filename, cropped)
                        # 定位框体显示
                        if bbox[0] > 50 and bbox[2] + 50 < width:
                            ax.add_patch(plt.Rectangle((bbox[0] - 50, bbox[1]),
                                                       bbox[2] - bbox[0] + 100,
                                                       bbox[3] - bbox[1], fill=False,
                                                       edgecolor='red', linewidth=3.5))
                        if bbox[0] < 50 and bbox[2] + 50 < width:
                            ax.add_patch(plt.Rectangle((bbox[0], bbox[1]),
                                                       bbox[2] - bbox[0] + 50,
                                                       bbox[3] - bbox[1], fill=False,
                                                       edgecolor='red', linewidth=3.5))
                        if bbox[0] > 50 and bbox[2] + 50 > width:
                            ax.add_patch(plt.Rectangle((bbox[0] - 50, bbox[1]),
                                                       bbox[2] - bbox[0] + 50,
                                                       bbox[3] - bbox[1], fill=False,
                                                       edgecolor='red', linewidth=3.5))
                        if bbox[0] < 50 and bbox[2] + 50 > width:
                            ax.add_patch(plt.Rectangle((bbox[0], bbox[1]),
                                                       bbox[2] - bbox[0],
                                                       bbox[3] - bbox[1], fill=False,
                                                       edgecolor='red', linewidth=3.5))
                        #     每个框的成绩输出
                        # ax.text(bbox[0], bbox[1] - 2,
                        #         '{:s} {:.3f}'.format(class_name, score),
                        #         bbox=dict(facecolor='blue', alpha=0.5),
                        #         fontsize=14, color='white')
                        ax.set_title(('{} detections with '
                                      'p({} | box) >= {:.1f}').format(class_name, class_name, thresh),
                                     fontsize=14)
                plt.axis('off')
                plt.tight_layout()
                plt.draw()

            def demo_posiotion(sess, net,path):
                """Detect object classes in an image using pre-computed object proposals."""

                # Load the demo image
                im_file = path.encode('utf8')
                # im = cv2.imread(im_file)
                im = cv_imread(im_file)
                scores, boxes = im_detect(sess, net, im)
                # Visualize detections for each class
                CONF_THRESH = 0.1
                NMS_THRESH = 0.1
                for cls_ind, cls in enumerate(CLASSES[1:]):
                    cls_ind += 1  # because we skipped background
                    cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
                    cls_scores = scores[:, cls_ind]
                    # print(cls_scores)#一个300个数的数组
                    # np.newaxis增加维度  np.hstack将数组拼接在一起
                    dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(np.float32)
                    keep = nms(dets, NMS_THRESH)
                    dets = dets[keep, :]

                    vis_detections(im, cls, dets, thresh=CONF_THRESH)

            def parse_args():
                """Parse input arguments."""
                parser = argparse.ArgumentParser(description='Tensorflow Faster R-CNN demo')
                parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16 res101]',
                                    choices=NETS.keys(), default='vgg16')
                parser.add_argument('--dataset', dest='dataset', help='Trained dataset [pascal_voc pascal_voc_0712]',
                                    choices=DATASETS.keys(), default='pascal_voc')
                args = parser.parse_args()

                return args

            args = parse_args()
            demonet = args.demo_net
            dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tfmodel = dir_path+r'/..\demo\lib\models\model_position/vgg16_faster_rcnn_iter_8000.ckpt'
            # 路径异常提醒
            if not os.path.isfile(tfmodel + '.meta'):
                raise IOError(('{:s} not found.\nDid you download the proper networks from '
                               'our server and place them properly?').format(tfmodel + '.meta'))
            tfconfig = tf.ConfigProto(allow_soft_placement=True)
            tfconfig.gpu_options.allow_growth = True
            sess = tf.Session(config=tfconfig)
            if demonet == 'vgg16':
                net = vgg16(batch_size=1)
            else:
                raise NotImplementedError
            net.create_architecture(sess, "TEST", 2,
                                    tag='default', anchor_scales=[8, 16, 32])
            saver = tf.train.Saver()
            saver.restore(sess, tfmodel)
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('Demo for ' + path)
            demo_posiotion(sess, net, path)
            plt.savefig("images/" + filename)
            plt.show()

        # ***************************************     第二步：定位图片进行切割成单位数字图片   cut   ***************************

        def cut(filename):
            print("正在分位处理")

            def vis_detections(im, class_name, dets, thresh=0.5):
                """Draw detected bounding boxes."""
                inds = np.where(dets[:, -1] >= thresh)[0]
                if len(inds) == 0:
                    return
                im = im[:, :, (2, 1, 0)]
                fig, ax = plt.subplots(figsize=(12, 12))
                ax.imshow(im, aspect='equal')
                position = []

                for i in inds:
                    score = dets[i, -1]
                    if score > 0.97:
                        bbox = dets[i, :4]
                        position.append(bbox[0])  # 将多个box的左下角坐标放入数组中
                        img = cv2.imread("images/position/" + filename)
                        # img = cv2.imdecode(np.fromfile(r"images/position/" + filename, dtype=np.uint8), 1)

                        cropped = img[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]  # 裁剪坐标为[y0:y1, x0:x1]
                        targetPath =  'images/cut/' + filename.split('.')[0]
                        if not os.path.exists(targetPath):
                            os.makedirs(targetPath)
                        # 重定义图片的大小
                        res = cv2.resize(cropped, (224, 224), interpolation=cv2.INTER_CUBIC)  # dsize=（2*width,2*height）
                        cv2.imwrite(targetPath + '/' + str(int(bbox[0])) + '.jpg', res)

                        # cv2.imencode(".jpg", res)[1].tofile(targetPath + '/')

                        ax.add_patch(plt.Rectangle((bbox[0], bbox[1]),
                                                   bbox[2] - bbox[0],
                                                   bbox[3] - bbox[1], fill=False,
                                                   edgecolor='red', linewidth=3.5)
                                     )
                        # 显示成绩
                        # ax.text(bbox[0], bbox[1] - 2,
                        #         '{:s} {:.3f}'.format(class_name, score),
                        #         bbox=dict(facecolor='blue', alpha=0.5),
                        #         fontsize=14, color='white')
                        ax.set_title(('{} detections with '
                                      'p({} | box) >= {:.1f}').format(class_name, class_name, thresh),
                                     fontsize=14)
                plt.axis('off')
                plt.tight_layout()
                plt.draw()

            def demo(sess, net, image_name):
                dir_path = os.path.dirname(os.path.abspath(__file__))
                im_file = dir_path+r'/images/position/'+image_name
                if not os.path.exists(dir_path+r'/images/position/'):
                    os.makedirs(dir_path+r'/images/position/')
                im = cv_imread(im_file)
                # Detect all object classes and regress object bounds
                scores, boxes = im_detect(sess, net, im)

                # Visualize detections for each class
                CONF_THRESH = 0.1
                NMS_THRESH = 0.1
                for cls_ind, cls in enumerate(CLASSES[1:]):
                    cls_ind += 1  # because we skipped background
                    cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
                    cls_scores = scores[:, cls_ind]
                    dets = np.hstack((cls_boxes, cls_scores[:, np.newaxis])).astype(np.float32)
                    keep = nms(dets, NMS_THRESH)
                    dets = dets[keep, :]

                    vis_detections(im, cls, dets, thresh=CONF_THRESH)

            def parse_args():
                """Parse input arguments."""
                parser = argparse.ArgumentParser(description='Tensorflow Faster R-CNN demo')
                parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16 res101]',
                                    choices=NETS.keys(), default='vgg16')
                parser.add_argument('--dataset', dest='dataset', help='Trained dataset [pascal_voc pascal_voc_0712]',
                                    choices=DATASETS.keys(), default='pascal_voc')
                args = parser.parse_args()
                return args

            args = parse_args()
            demonet = args.demo_net
            dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            tfmodel = dir_path+r'/../demo/lib/models/model_cut/vgg16_faster_rcnn_iter_8000.ckpt'
            # 路径异常提醒
            if not os.path.isfile(tfmodel + '.meta'):
                raise IOError(('{:s} not found.\nDid you download the proper networks from '
                               'our server and place them properly?').format(tfmodel + '.meta'))
            tfconfig = tf.ConfigProto(allow_soft_placement=True)
            tfconfig.gpu_options.allow_growth = True
            sess = tf.Session(config=tfconfig)
            if demonet == 'vgg16':
                net = vgg8(batch_size=1)
            else:
                raise NotImplementedError
            net.create_architecture(sess, "TEST", 2,
                                    tag='default', anchor_scales=[8, 16, 32])
            saver = tf.train.Saver()
            saver.restore(sess, tfmodel)
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            # print('Demo for test_result/position/{}'.format(filename))
            demo(sess, net, filename)
            plt.show()

        # ***************************************     第三步： 对分位的数字转化格式    convert    ******************************
        def converet(filename):
            import tensorflow as tf
            import os
            import random
            import math
            import sys
            from PIL import Image
            import numpy as np
            # 随机种子
            _RANDOM_SEED = 0
            # 数据集路径
            DATASET_DIR = "images/cut/" + filename.split('.')[0] + '/'
            # tfrecord文件存放路径
            TFRECORD_DIR = "images/tfrecords/"
            if not os.path.exists(TFRECORD_DIR):
                os.makedirs(TFRECORD_DIR)

            # 获取所有图片
            def _get_filenames_and_classes(dataset_dir):
                photo_filenames = []
                img_list = os.listdir(dataset_dir)
                img_list.sort()
                img_list.sort(key=lambda x: int(x[:-4]))  ##文件名按数字排序
                img_nums = len(img_list)
                for i in range(img_nums):
                    img_name = dataset_dir + img_list[i]
                    photo_filenames.append(img_name)
                return photo_filenames

            def int64_feature(values):
                if not isinstance(values, (tuple, list)):
                    values = [values]
                return tf.train.Feature(int64_list=tf.train.Int64List(value=values))

            def bytes_feature(values):
                return tf.train.Feature(bytes_list=tf.train.BytesList(value=[values]))

            def image_to_tfexample(image_data, label0):
                # Abstract base class for protocol messages.
                return tf.train.Example(features=tf.train.Features(feature={
                    'image': bytes_feature(image_data),
                    'label0': int64_feature(label0),
                }))

            # 把数据转为TFRecord格式
            def _convert_dataset(filename, filenames, tfset_dir):
                with tf.Session() as sess:
                    # 定义tfrecord文件的路径+名字
                    output_filename = os.path.join(tfset_dir, filename.split('.')[0] + '.tfrecords')
                    with tf.python_io.TFRecordWriter(output_filename) as tfrecord_writer:
                        names = []
                        for img_name in enumerate(filenames):
                            name = str(img_name).split('/')[-1]
                            name = str(name).split('.')[0]
                            names.append(int(name))
                        names.sort()
                        for i, name in enumerate(names):
                            names[i] = 'images/cut/' + filename.split('.')[0] + '/' + str(name) + '.jpg'
                        for i, name in enumerate(names):
                            try:
                                # sys.stdout.write('\r>> Converting image %d/%d' % (i + 1, len(filenames)))
                                sys.stdout.flush()
                                # 读取图片
                                image_data = Image.open(name)
                                # 根据模型的结构resize
                                # image_data = image_data.resize((224, 224))
                                # 灰度化
                                image_data = np.array(image_data.convert('L'))
                                # 将图片转化为bytes
                                image_data = image_data.tobytes()
                                # 获取label
                                labels = name.split('/')[-1]
                                label = int(labels.split('.')[0])
                                # print(label)
                                example = image_to_tfexample(image_data, label)
                                tfrecord_writer.write(example.SerializeToString())
                            except IOError as e:
                                print('Could not read:', name)
                                print('Error:', e)
                                print('Skip it\n')
                sys.stdout.write('\n')
                sys.stdout.flush()

            # 获得所有图片
            photo_filenames = _get_filenames_and_classes(DATASET_DIR)
            # 把数据切分为训练集和测试集,并打乱
            # random.seed(_RANDOM_SEED)
            # random.shuffle(photo_filenames)
            testing_filenames = photo_filenames[:]

            # 数据转换
            _convert_dataset(filename, testing_filenames, TFRECORD_DIR)
            # print('生成tfcecord文件')

        # ***************************************     第四步：  对分为图片进行数据预测    forecast   ***************************
        def distinguish(filename):
            import os
            import tensorflow as tf
            from PIL import Image
            from lib.nets2 import nets_factory
            import numpy as np
            import matplotlib.pyplot as plt
            # 不同字符数量
            CHAR_SET_LEN = 10
            # 批次
            dir = 'images/cut/' + filename.split('.')[0]
            BATCH_SIZE = s = len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])
            # tfrecord文件存放路径
            TFRECORD_FILE = "images/tfrecords/" + filename.split('.')[0] + '.tfrecords'
            # placeholder
            x = tf.placeholder(tf.float32, [None, 224, 224])

            os.environ["CUDA_VISIBLE_DEVICES"] = '0'  # 指定第一块GPU可用
            config = tf.ConfigProto()
            config.gpu_options.per_process_gpu_memory_fraction = 0.5  # 程序最多只能占用指定gpu50%的显存
            config.gpu_options.allow_growth = True  # 程序按需申请内存
            sess = tf.Session(config=config)

            # 从tfrecord读出数据
            def read_and_decode(filename):
                # 根据文件名生成一个队列
                filename_queue = tf.train.string_input_producer([filename])
                reader = tf.TFRecordReader()
                # 返回文件名和文件
                _, serialized_example = reader.read(filename_queue)
                features = tf.parse_single_example(serialized_example,
                                                   features={
                                                       'image': tf.FixedLenFeature([], tf.string),
                                                       'label0': tf.FixedLenFeature([], tf.int64),

                                                   })
                # 获取图片数据
                image = tf.decode_raw(features['image'], tf.uint8)
                # 没有经过预处理的灰度图
                image_raw = tf.reshape(image, [224, 224])
                # tf.train.shuffle_batch必须确定shape
                image = tf.reshape(image, [224, 224])
                # 图片预处理
                image = tf.cast(image, tf.float32) / 255.0
                image = tf.subtract(image, 0.5)
                image = tf.multiply(image, 2.0)
                # 获取label
                label0 = tf.cast(features['label0'], tf.int32)

                return image, image_raw, label0

            # 获取图片数据和标签
            image, image_raw, label0 = read_and_decode(TFRECORD_FILE)
            # 使用shuffle_batch可以随机打乱
            image_batch, image_raw_batch, label_batch0 = tf.train.batch(
                [image, image_raw, label0], batch_size=BATCH_SIZE,
                capacity=50000, num_threads=1)
            # 定义网络结构
            train_network_fn = nets_factory.get_network_fn(
                'alexnet_v2',
                num_classes=CHAR_SET_LEN * 1,
                weight_decay=0.0005,
                is_training=False)

            with tf.Session() as sess:
                # inputs: a tensor of size [batch_size, height, width, channels]
                X = tf.reshape(x, [BATCH_SIZE, 224, 224, 1])
                # 数据输入网络得到输出值
                logits, end_points = train_network_fn(X)
                # 预测值
                logits0 = tf.slice(logits, [0, 0], [-1, 10])

                predict0 = tf.argmax(logits0, 1)

                # 初始化
                sess.run(tf.global_variables_initializer())
                # 载入训练好的模型
                saver = tf.train.Saver()
                dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                saver.restore(sess,dir_path+r'/../demo/lib/models/model_distinguish/crack_captcha1.model-6000')
                # saver.restore(sess, '../1/crack_captcha1.model-2500')

                # 创建一个协调器，管理线程
                coord = tf.train.Coordinator()
                # 启动QueueRunner, 此时文件名队列已经进队
                threads = tf.train.start_queue_runners(sess=sess, coord=coord)
                for i in range(1):
                    # 获取一个批次的数据和标签
                    b_image, b_image_raw, b_label0 = sess.run([image_batch, image_raw_batch, label_batch0])
                    # print(b_image_raw)
                    # 显示图片
                    img = Image.fromarray(b_image_raw[0], 'L')
                    # plt.imshow(img)
                    plt.axis('off')
                    # plt.show()
                    # 打印标签
                    # print('lable',b_label0)
                    distance = (b_label0[1] - b_label0[0]) * 1.4
                    lb = []
                    for i in range(len(b_label0) - 1):
                        if distance <= b_label0[i + 1] - b_label0[i]:
                            lb.append(i)
                    # print('lb',lb)
                    # 预测
                    label0 = sess.run([predict0], feed_dict={x: b_image})
                    # 打印预测值
                    predict = str(label0[0]).strip('[[]]').replace(' ', '')
                    predict1 = list(predict)  # str -> list
                    # print(predict1)
                    # print(lb)
                    for i in range(len(lb)):
                        yuan = predict1[lb[i]]
                        predict1[lb[i]] = yuan + '_'
                        # predict1.insert(lb[i], '_')  # 注意不用重新赋值
                    predict = ''.join(predict1)  # list -> str
                    print('predict:', predict)
                    # with open(result_txt, "a") as f:
                    #     f.write(test_images_dir+ filename+':' + predict+ '\n')
                    # 给train数据集打标签
                    # 通知其他线程关闭
                coord.request_stop()
                # 其他所有线程关闭之后，这一函数才能返回
                coord.join(threads)
                return predict

        filename = path.split('/')[-1]
        position(path, filename)
        tf.reset_default_graph()  # 重置tensorflow的旧变量，重置图标
        cut(filename)
        tf.reset_default_graph()  # 重置tensorflow的旧变量，重置图标
        converet(filename)
        tf.reset_default_graph()  # 重置tensorflow的旧变量，重置图标
        predict0 = distinguish(filename)
        tf.reset_default_graph()  # 重置tensorflow的旧变量，重置图标
        position_card = 'images/' + filename
        return predict0, position_card
    predict,position_card=gui(path_)

    img_open1 = Image.open(position_card)
    img_open1 = img_open1.resize((500, 450), Image.ANTIALIAS)
    img1 = ImageTk.PhotoImage(img_open1)
    result_image.config(image=img1)
    result_image.image = img1  # keep a reference
    input_valueText.insert(0,predict)
    print(predict,position_card)


#path = StringVar()
tkinter.Button(root, text='打开文件', command=choosepic).place(x=820, y=230, w=150, h=40)
#file_entry = Entry(root, state='readonly', text=path)
#file_entry.pack()
# 原图片位置
source_image = StringVar()
source_image.set('原图片')
label_source = tkinter.Label(root, textvariable=source_image)
label_source.place(x=100, y=1)

image_label = Label(root, bg='gray')
image_label.place(x=100, y=20, width=400, height=300)


# 提示框
tip = StringVar()
tip.set('选定图片之后，识别过程需要稍等',)
label_object = tkinter.Label(root, textvariable=tip)
label_object.place(x=840, y=350)

result_image = Label(root, bg='gray')
result_image.place(x=100, y=350, width=400, height=300)



# 结果图片位置
object_image = StringVar()
object_image.set('定位结果')
label_object = tkinter.Label(root, textvariable=object_image)
label_object.place(x=100, y=330)

result_image = Label(root, bg='gray')
result_image.place(x=100, y=350, width=400, height=300)

# 输入标注内容
input_valueTitle = StringVar()
input_valueTitle.set('银行卡号')
label_inputTitle = tkinter.Label(root, textvariable=input_valueTitle)
label_inputTitle.place(x=820, y=90)
#输入框
input_valueText = tkinter.Entry(root,width=12)
input_valueText.place(x=820, y=120, width=250, height=40, anchor=NW)
# 启动消息主循环
root.update()
root.mainloop()





