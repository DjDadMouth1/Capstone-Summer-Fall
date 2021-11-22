from flask import Flask, render_template, request, send_file

from werkzeug.utils import redirect
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('htmlPage.html')

@app.route('/', methods=['POST'])
def run_validator():
   if request.method == 'POST':
      if request.files['filename'].filename != '':
         new_file = request.files['filename']
         outputselection = request.values['outputSelection']
         filename = str(new_file.filename)
         outputselection = str(outputselection)
         new_file.save(new_file.filename)
         from validation import validator
         report_name = validator.custom_validate(filename,outputselection)
         return render_template('htmlPage.html', report = report_name)
   else:
      return render_template('htmlPage.html')
   
@app.route('/field_config', methods=['GET','POST'])
def check_config():
   if request.method == 'POST':
      data = request.form.to_dict()
      new_check_cfg = {}
      for key,value in data.items():
         if value != '':
            if key.split('[')[0]in new_check_cfg:
               new_check_cfg[key.split('[')[0]].append(value)
            else:
               new_check_cfg[key.split('[')[0]] = [value]
      with open('./settings/fields.cfg','w') as outfile:
         for key,value in new_check_cfg.items():
            line = str(key) + ' = ' + ','.join(value) + '\n'
            print(line)
            outfile.write(line.upper())
      
   field_cfg = {}
   field_cfg_file = open('./settings/fields.cfg')
   for line in field_cfg_file:
      if not line.startswith('#'): 
         key, value = line.split('=')
         field_cfg[key.strip()] = value.strip().split(',')

   return render_template('fieldconfig.html', config_dict = field_cfg)

@app.route('/check_select', methods=['GET','POST'])
def check_select():
   if request.method == 'POST':
      data = request.form.to_dict()
      new_check_selection = ''
      print(data)
      with open('./settings/checks.cfg','r') as outfile:
         for line in outfile:
            custom_check = line.split('=')[0].strip()
            if custom_check in data:
               new_check_selection += custom_check + ' = 1\n'
            else:
               new_check_selection += custom_check + ' = 0\n'

      with open('./settings/checks.cfg','w') as outfile:
         outfile.write(new_check_selection)
      
   check_selection = {}
   check_file = open('./settings/checks.cfg')
   for line in check_file:
      if not line.startswith('#'): 
         key, value = line.split('=')
         check_selection[key.strip()] = int(value.strip())

   return render_template('checkconfig.html', check_select = check_selection)
   
if __name__ == "__main__":
   app.run(host='localhost', port=5000)