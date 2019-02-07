import os

from flask import Flask, request,Response,jsonify
from flask_cors import *
import json
import cv2
import numpy as np
import base64
import socket
from flask import Flask
from flask_cache import Cache

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'eyesight.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    CORS(app, support_credentials=True)


    # 使用Flask-Cache
    # http://www.pythondoc.com/flask-cache/index.html

    # Check Configuring Flask-Cache section for more details
    cache = Cache(app,config={'CACHE_TYPE': 'simple'})  
    cache.init_app(app)

    @cache.cached(timeout=50, key_prefix='classIdCnt')
    def cache_classIdCnt(method,data):
        if(method == "save"):
            saved_id = json.dumps(data)
            cache.set('classidcnt', saved_id, timeout=10)
            
            print("classid缓存成功")
        elif (method == "load"):
            return cache.get('classidcnt')

    #Video streaming generator function
    def gen(type):
        while True:
            if type == 'POST':
                fopen=[open('loaded.jpg', 'rb').read()]
                frame = fopen[0]
                time.sleep(0.1)
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            elif type == 'UDP':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
                host = ''
                port = 1082
                server_address = (host, port)
                sock.bind(server_address)
                data, server = sock.recvfrom(65507)
                print("Fragment size : {}".format(len(data)))
                if len(data) == 4:
                        # This is a message error sent back by the server
                        if(data == "FAIL"):
                                continue
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
        

    # a simple page that says hello
    @app.route('/hello',methods=['GET','POST'])
    def hello():
        if(request.method == 'POST'):
            post_json = request.get_json()
            return jsonify({'you sent':post_json}),201
        else:
            return jsonify({'about':"Hello World"})
    
    # route带参数
    #  http://127.0.0.1:5000/multi/100
    @app.route('/multi/<int:num>',methods=['GET'])
    def get_multuply(num):
        return jsonify({'result':num*10})


    # API Objectdatas resource
    
    @app.route('/api/objectdatas',methods=['GET','POST'])
    def api_objects():
        if (request.method == 'POST'):
            objects_json = request.get_json()
            obj_ndarray = np.array(objects_json['data'])
            print(obj_ndarray)
            cv2.imwrite('eyesight/objectdatas/%s.jpg' % "test",obj_ndarray)
            print("目标剪切图片保存完成")
            return jsonify({'objects_data':objects_json}),201

        else:
            print("GET")

    # API livestream
    @app.route('/api/livestream/udp',methods=['GET'])
    def api_livestream():
            # Create a UDP socket
       
        return Response(gen('UDP'),mimetype='multipart/x-mixed-replace; boundary=frame')
                
    # API classid
    # 每一帧目标捕获数统计
    @app.route('/api/classid',methods=['GET','POST'])
    def api_classid():
        if (request.method == 'POST'):
            classid_json = request.get_json()
            classid_data = classid_json['data']
            print(classid_data) 
            cache_classIdCnt("save",classid_data)

            return jsonify({'clasdid_data':classid_data}),201

        elif (request.method == 'GET'):
            print("GET CLASS ID---")
            print(cache_classIdCnt("load",None))
            return cache_classIdCnt("load",None)
    # sample 
    #serach query
    @app.route('/search', methods=['GET', 'POST'])
    @cross_origin(supports_credentials=True)
    
    def search():
        params = {'query': request.args.get('query')}
        if params['query'] == 'test':
            persons = [{
                'name': 'david',
                'age': 10
            }, {
                'name': 'black',
                'age': 19
            }]
            print("test")
            return json.dumps(persons)
        
    
        if params['query'] == 'object':
            path = 'eyesight/objectdatas'
            datas = []
            for file in os.listdir(path):
                name = file.split(':',1)[0]
                value = file.split(':',1)[1][:-3]
                #img = cv2.imread(path + '/'+file).tolist()
                with open(path + '/'+file, 'rb') as f:
                     img=base64.b64encode(f.read())
                img = img.decode('utf-8') #将image2str转为str
                #imgstr = bytes.decode(img)
                #img = Response(img, mimetype="image/jpeg")
                #print(name+value)
                datas.append({'img':img,'name':name,'value':value})
            #print(datas)
            return json.dumps(datas)


        return "OK"
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    return app