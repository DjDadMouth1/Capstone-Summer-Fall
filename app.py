from flask import Flask, render_template, request, send_file

from werkzeug.utils import redirect
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('htmlPage.html')

@app.route('/', methods=['POST'])
def run_validator():
   new_file = request.files['filename']
   outputselection = request.values['outputSelection']
   filename = str(new_file.filename)
   outputselection = str(outputselection)
   new_file.save(new_file.filename)
   from validator import validator
   validator.custom_validate(filename,outputselection)
   return send_file('report.json')
   
@app.route('/config', methods=['GET'])
def root():
    web_indiv = {}
    url_sequence = 'test'
    web_indiv[url_sequence] = {'url':'testabc','name':'hello','count': 4}
    return render_template('config.html', web_data = web_indiv, url_sequence = url_sequence)


app.run(host='localhost', port=5000)