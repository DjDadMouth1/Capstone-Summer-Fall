from flask import Flask, render_template, request, send_file

from werkzeug.utils import redirect
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('htmlPage.html')

@app.route('/', methods=['POST'])
def run_validator():
   new_file = request.files['filename']
   filename = str(new_file.filename)
   new_file.save(new_file.filename)
   from validator import validator
   validator.custom_validate(filename)
   return send_file('report.json')

if __name__ == "__main__":
   app.run(host='localhost', port=5000)