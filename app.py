from flask import Flask, render_template
import validate
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('htmlPage.html')

@app.route('/validate/')
def run_validator(file):
   validate.custom_validate(file)
   return 'Done!'
   
if __name__ == '__main__':
   app.run(host='localhost', port=5000)