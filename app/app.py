#!/usr/bin/env python
# A Flask App
import pickle as pkl
from flask import Flask, render_template, request

app = Flask(__name__)

with open('static/rfr_trained.pkl', 'rb') as f:
    model = pkl.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediction', methods=['GET','POST'])
def prediction():
    make = str(request.form['make'])
    model = str(request.form['model'])
    year = str(request.form['year'])
    color = str(request.form['color'])
    data = [make, model, year, color]
    pred = model.predict(data)
    return render_template('prediction.html', data=data)


if __name__ =='__main__':
    app.run(host='0.0.0.0', port=8080)#, debug=True)