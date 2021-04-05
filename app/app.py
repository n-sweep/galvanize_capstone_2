#!/usr/bin/env python
# A Flask App
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediction', methods=['GET','POST'])
def prediction():
    make = str(request.form['make'])
    model = str(request.form['model'])
    year = str(request.form['year'])
    color = str(request.form['color'])
    return render_template('prediction.html', data=[make, model, year, color])


if __name__ =='__main__':
    app.run(host='0.0.0.0', port=8080)#, debug=True)