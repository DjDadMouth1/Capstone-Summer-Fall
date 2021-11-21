from flask import Flask, render_template, request, send_file

from werkzeug.utils import redirect
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('htmlPage.html')

@app.route('/', methods=['POST'])
def run_validator():
   if request.files['filename'].filename != '':
      new_file = request.files['filename']
      outputselection = request.values['outputSelection']
      filename = str(new_file.filename)
      outputselection = str(outputselection)
      new_file.save(new_file.filename)
      from validation import validator
      validator.custom_validate(filename,outputselection)
      return send_file('report.json')
   else:
      return render_template('htmlPage.html')
   
@app.route('/config', methods=['GET','POST'])
def config():
   if request.method == 'POST':
      data = request.form.to_dict()
      new_cfg = {}
      for key,value in data.items():
         if value != '':
            if key.split('[')[0]in new_cfg:
               new_cfg[key.split('[')[0]].append(value)
            else:
               new_cfg[key.split('[')[0]] = [value]
      with open('./settings/fields.cfg','w') as outfile:
         for key,value in new_cfg.items():
            line = str(key) + ' = ' + ','.join(value) + '\n'
            print(line)
            outfile.write(line.upper())
      
   cfg_dict = {}
   cfg_file = open('./settings/fields.cfg')
   for line in cfg_file:
      if not line.startswith('#'): 
         key, value = line.split('=')
         cfg_dict[key.strip()] = value.strip().split(',')

   return render_template('fieldconfig.html', config_dict = cfg_dict)
   
if __name__ == "__main__":
   app.run(host='localhost', port=5000)