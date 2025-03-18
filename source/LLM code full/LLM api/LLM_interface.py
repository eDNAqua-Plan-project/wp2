#!/usr/bin/env python
# coding: utf-8

# title=LLM_interface
# 
# version=0.2 (beta)
# 
# date=15.07.2024
# 
# authors=Yulyana Kalesnik, Dawid Krawczyk

# Importing libraries
from LLM_connector import LLM_connector
from LlamaExpert import LlamaExpert
from flask import Flask, jsonify,request
import subprocess

# Definition of device map

device_map = {'model.embed_tokens': 0, 'model.layers.0': 0, 'model.layers.1': 0, 'model.layers.2': 0, 'model.layers.3': 0, 
              'model.layers.4': 0, 'model.layers.5': 0, 'model.layers.6': 0, 'model.layers.7': 1, 'model.layers.8': 1, 
              'model.layers.9': 1, 'model.layers.10': 1, 'model.layers.11': 1, 'model.layers.12': 1, 'model.layers.13': 1, 
              'model.layers.14': 1, 'model.layers.15': 2, 'model.layers.16': 2, 'model.layers.17': 2, 'model.layers.18': 2, 
              'model.layers.19': 2, 'model.layers.20': 2, 'model.layers.21': 2, 'model.layers.22': 2, 'model.layers.23': 3, 
              'model.layers.24': 3, 'model.layers.25': 3, 'model.layers.26': 3, 'model.layers.27': 3, 'model.layers.28': 3, 
              'model.layers.29': 3, 'model.layers.30': 3, 'model.layers.31': 3, 'model.layers.32': 4, 'model.layers.33': 4, 
              'model.layers.34': 4, 'model.layers.35': 4, 'model.layers.36': 4, 'model.layers.37': 4, 'model.layers.38': 4, 
              'model.layers.39': 4, 'model.norm': 4, 'lm_head': 4}

# Creating model and chatbot

llama_model = LLM_connector("./llama-2-13b-chat-hf",device_map=device_map, temperature=.1,
                 max_new_tokens=500, repetition_penalty=1.1, use_cache=True, num_returns=1,
                 top_k=5, do_sample=True)
llama_expert = LlamaExpert(llama_model)

# API section

app = Flask(__name__)

@app.route('/llm', methods=['POST'])
def get_answer():
    # result = subprocess.check_output(['llm']).decode('utf-8')
    # return jsonify({'date': result.strip()})
    if request.method == 'POST':
        data = request.json
        data['Context'] = data['Context'].replace('Human:','human:').replace('Context:','context:').replace('Question:','question:').replace('Answer:','answer:')
        resp = llama_expert.ask_question(data['Question'],data['Context'])
        human = resp[resp.find('Human:')+6:resp.find('Context:')].strip()
        context = resp[resp.find('Context:')+8:resp.find('Question:')].strip()
        question = resp[resp.find('Question:')+9:resp.find('Answer:')].strip()
        answer = resp[resp.find('Answer:')+7:].strip()
        return jsonify(dict(Human=human,Context=context,Question=question,Answer=answer))
    return jsonify({'Response':'No content'})

@app.route('/checkConnection',methods=['POST'])
def checkConnection():
    return jsonify({'Connection':'OK'})

if __name__ == '__main__':
    raise RuntimeError('This app doesn`t work directly. You have to run it with python, ipython or jupyter.')