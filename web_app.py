# #from rasa_core.channels.facebook import FacebookInput
# from rasa.core.channels.socketio import SocketIOInput
# from rasa.core.interpreter import RasaNLUInterpreter
# import yaml
# from rasa.core.utils import EndpointConfig
# from rasa.core.agent import Agent
# from flask import Flask
# from flask import render_template, jsonify, request
# import requests
# from urllib.request import urlopen
# import json
# #from models import *
# #from responses import *
#
# import random
# app = Flask(__name__)
#
#
#
# @app.route('/')
# def hello_world():
#
#     return render_template('index.html')
#     #return render_template('home.html')
#
#
# app.config["DEBUG"] = True
# if __name__ == "__main__":
#     app.run(port=8000)
#
#
#

from flask import Flask, redirect, url_for, request, render_template
import requests
import json
import requests
import json

# app = Flask(__name__, template_folder= 'templates')
# context_set = ""
#
# @app.route('/', methods = ['POST', 'GET'])
# def index():
#     if request.method == 'GET':
#       print("request",request.args)
#
#       val1 = str(request.args.get('text'))
#       print("value",val1)
#       data = json.dumps({"sender": "Rasa","message": val1})
#       headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
#       res = requests.post('http://localhost:5005/webhooks/rest/webhook', data= data, headers = headers)
#       res = res.json()
#       print(res)
#       # val = res[0]['text']
#       # return render_template('index.html',val=val)
#       if len(res)>1:
#         d=""
#         for i in res:
#            val = i['text']
#            print("qqqqqq",val)
#            d=d+"\n"+val
#         print("-->",d)
#         return render_template('index.html',val=d)
#       else:
#         val = res[0]['text']
#         return render_template('index.html', val=val)

# app = Flask(__name__, template_folder= 'Templates')
# context_set = ""
#
# @app.route('/', methods = ['POST', 'GET'])
# def index():
#     return render_template('index.html')
# if __name__ == '__main__':
#   app.run(debug=True)

from flask import Flask, redirect, url_for, request, render_template
import requests
import json

app = Flask(__name__, template_folder= 'Templates')
context_set = ""

@app.route('/', methods = ['POST', 'GET'])
def index():
    try:
      if request.method == 'GET':
        val = str(request.args.get('text'))
        print(val)
        # if val =="None":
        #   val ="bye"
        data = json.dumps({"sender": "Rasa","message": val})
        print(data)
        headers = {'Content-type': 'application/json'}
        res = requests.post('http://localhost:5005/webhooks/rest/webhook', data= data, headers=headers)
        res = res.json()
        print("1",res)
        if len(res) > 1:
          d = ""
          for i in res:
            val = i['text']
            d = d + "\n" + val
          print("-->", d)
          return render_template('index.html', val=d)
        else:
          val = res[0]['text']
          return render_template('index.html', val=val)
    except:
      print("error")


if __name__ == '__main__':
  app.run(debug=True)