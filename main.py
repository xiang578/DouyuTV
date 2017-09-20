# -*- coding:utf-8 -*-
# author: xiang578
# email: i@xiang578
# blog: www.xiang578.com

import multiprocessing
import socket
import re
import time
import pymongo


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostbyname("openbarrage.douyutv.com")
port = 8601
client.connect((host, port))

danmu_re = re.compile(b'txt@=(.+?)/cid@')
username_re = re.compile(b'nn@=(.+?)/txt@')
uid_re = re.compile(b'uid@=(.+?)/nn@')
type_re = re.compile(b'type@=(.+?)/')


def sendmsg(msgstr):
    msg = msgstr.encode('utf-8')
    data_length = len(msg) + 8
    code = 689
    msghead = int.to_bytes(data_length, 4, 'little') \
        + int.to_bytes(data_length, 4, 'little') \
        + int.to_bytes(code, 4, 'little')
    client.send(msghead)
    sent = 0
    while sent < len(msg):
        tn = client.send(msg[sent:])
        sent = sent + tn


def danmu(roomid):
    db_clients = pymongo.MongoClient('localhost', port=27017)
    db = db_clients['DouyuTVdanmu']
    col = db['info']
    msgstr = 'type@=loginreq/roomid@={}/\0'.format(roomid)
    sendmsg(msgstr)
    msg_more = 'type@=joingroup/rid@={}/gid@=-9999/\0'.format(roomid)
    sendmsg(msg_more)
    while True:
        # 服务端返回的数据
        data = client.recv(1024)
        if not data:
            continue
        data_type = type_re.findall(data)
        # print(data_type[0].decode('utf8'))
        if len(data_type) == 0 or data_type[0].decode('utf8') != "chatmsg":
            continue
        # 通过re模块找发送弹幕的用户名和内容
        danmu_username = username_re.findall(data)
        danmu_content = danmu_re.findall(data)
        danmu_uid = uid_re.findall(data)
        if not data:
            break
        else:
            for i in range(0, len(danmu_content)):
                try:
                    # 输出信息
                    print('uid: {} nn[{}]:{}'.format(danmu_uid[0].decode('utf8'), danmu_username[0].decode('utf8'), danmu_content[0].decode(encoding='utf8')))
                    product = {
                        'uid': danmu_uid[0].decode('utf8'),
                        'nickname': danmu_username[0].decode('utf8'),
                        'damu': danmu_content[0].decode('utf8')
                    }
                    # print(product)
                    col.insert_one(product)
                except Exception as e:
                    print(e)


def keeplive():
    while True:
        msg = 'type@=keeplive/tick@=' + str(int(time.time())) + '/\0'
        sendmsg(msg)
        # print("keeplive")
        time.sleep(30)


if __name__ == '__main__':
    # 老乡开下门
    room_id = 318624

    main_process = multiprocessing.Process(target=danmu, args=(room_id,))
    keep_live_process = multiprocessing.Process(target=keeplive)

    main_process.start()
    keep_live_process.start()
