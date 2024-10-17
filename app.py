"""
    MIT License

    Copyright (c) 2024 Kojiro Machi
    except where otherwise indicated.

    The prompt() and generate_xdl() function were modified by Kojiro Machi on September 23, 2024.

    The prompt() and generate_xdl() function are:

    Copyright (c) 2023 Sebastian Arellano-Rubach, Zhi Ji, Marta Skreta, and Naruki Yoshikawa

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""



from flask import Flask, render_template, url_for, request, make_response
from datetime import datetime

import json
from src.utils import Args, read_ann, write_ann
from urllib.parse import urljoin

import os
import sys
import torch
import numpy as np
from collections import defaultdict
from transformers import (AutoTokenizer,
                          AutoModelForTokenClassification,
                          AutoModelForSequenceClassification,
                          pipeline)


from chembert.chembert.parameters import ParamsPred
from chembert.chembert.rolesets import read_rolesets
from chembert.chembert.ospar2xdl import ospar2xdl
from chembert.chembert.utils import (get_token_idx,
                   span2ann,
                   label2idx,
                   use_first,
                   get_brat_info,
                   get_roleset_info,
                   marked_sents)



from nltk.stem.wordnet import WordNetLemmatizer
wnl = WordNetLemmatizer()

with open('src/lemma_norm_dict.json', 'r') as f:
    norm_dict = json.load(f)

from pprint import pprint

app = Flask(__name__)

args = Args('config.json')

if args.chembert_config_file:
    params = ParamsPred(args.chembert_config_file)

    rolesets = read_rolesets(params.roleset_file)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print('device:', device)

    ner_tokenizer = AutoTokenizer.from_pretrained(params.trained_model_entity, max_length=params.max_seq_len, is_fast=True)
    ent_model = AutoModelForTokenClassification.from_pretrained(params.trained_model_entity).to(device)
    act_model = AutoModelForTokenClassification.from_pretrained(params.trained_model_action).to(device)
    prm_model = AutoModelForTokenClassification.from_pretrained(params.trained_model_params).to(device)

    re_tokenizer = AutoTokenizer.from_pretrained(params.trained_model_re, max_length=params.max_seq_len, is_fast=True)
    re_model = AutoModelForTokenClassification.from_pretrained(params.trained_model_re).to(device)

    pipe = pipeline('text-classification', model=params.trained_model_re, device=device)


if args.use_clairify:
    import openai
    from tqdm import tqdm

    import time
    wd = os.getcwd()
    root_dir = "/".join(wd.split("/"))
    sys.path.append(root_dir)
    from xdl_generation.verifier import verify

    openai.api_key = args.OpenAI_API_key # your OpenAI API key #os.environ["OPENAI_API_KEY"]
    client = openai.OpenAI(api_key=openai.api_key)

    XDL = open('xdl_generation/XDL_description.txt', "r").read()


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/set_iframe", methods = ["GET"])
def set_iframe():
    if request.method == "GET":
        brat_url = args.brat_working_dir
        dict = {"brat_url": brat_url}
    return json.dumps(dict)


@app.route("/make_brat", methods = ["POST"])
def make_brat():
    if request.method == "POST":
        text = request.form["text"]
        fname = request.form["fname"]
        if not fname:
            fname = 'tmp'

        keep_action = True
        keep_ent = True

        brat_path = os.path.join(args.brat_working_dir, fname)
        new_text, actions, ner_actions, ner_others, roleset_info = text2ospar(text)
        txtfile = os.path.join(args.brat_dir, fname + '.txt')
        annfile = os.path.join(args.brat_dir, fname + '.ann')
        write_ann(txtfile, annfile, new_text, actions, ner_actions, ner_others, roleset_info, keep_action, keep_ent)

        dict = {"brat_path": brat_path}
    return json.dumps(dict)


@app.route("/make_xdl", methods = ["POST"])
def make_xdl():
    if request.method == "POST":
        # ここにPythonの処理を書く
        try:
            brat_path = request.form["brat_path"]

            if brat_path[-1] == '/':
                brat_path = brat_path[:-1]

            brat_id = brat_path.split('/')[-1]
            annfile = os.path.join(args.brat_dir, brat_id + '.ann')
            actions = read_ann(annfile)
            xdl_str = ospar2xdl(actions, rolesets)

        except Exception as e:
            xdl_str = str(e)
        dict = {"xdl_str": xdl_str}
    return json.dumps(dict)


@app.route("/make_xdl_gpt", methods = ["POST"])
def make_xdl_gpt():
    if request.method == "POST":
        try:
            text = request.form["text"]
            brat_path = request.form["brat_path"]

            if brat_path[-1] == '/':
                brat_path = brat_path[:-1]

            if not text:
                brat_id = brat_path.split('/')[-1]
                txtfile = os.path.join(args.brat_dir, brat_id + '.txt')
                with open(txtfile, 'r') as f:
                    text = f.read()

            correct_syntax, xdl, errors = generate_xdl(text)

        except Exception as e:
            xdl = str(e)
        dict = {"xdl_str": xdl}
    return json.dumps(dict)


@app.route("/save_xdl", methods = ["POST"])
def save_xdl():
    if request.method == "POST":
        try:
            text = request.form["text"]
            fname = request.form["fname"]
            if fname:
                brat_url = brat_dir + fname
            else:
                brat_url = brat_dir + 'tmp'
        except Exception as e:
            xdl = str(e)
        dict = {"xdl": xdl}
    return json.dumps(dict)


def text2ospar(raw_text):
    if raw_text == None:
        exit()

    ret_texts = []

    actions = []

    ner_actions_all = {}
    ner_others_all = {}
    roleset_info = {}

    sent_tokens, token_spans, sent_texts, sent_spans = get_token_idx(raw_text)
    prev = 0

    ent_idx = 1
    for tokens, spans, text, s_spans in zip(sent_tokens, token_spans, sent_texts, sent_spans):
        ret_texts.append(text)
        inputs = ner_tokenizer(tokens, return_tensors="pt", is_split_into_words=True).to(device)

        ner_ann = {}
        models = {'entity': ent_model, 'action': act_model, 'params': prm_model}
        for k, model in models.items():
            with torch.no_grad():
                logits = model(**inputs).logits
                predictions = torch.argmax(logits, dim=2)

            predicted_token_class = [model.config.id2label[t.item()] for t in predictions[0]]
            labels = use_first(inputs, predicted_token_class)
            idxs = label2idx(labels)
            ann = span2ann(raw_text, spans, idxs, s_spans)
            ner_ann[k] = ann

        ner_actions, ner_others, ent_idx = get_brat_info(ner_ann, ent_idx)
        ner_actions_all.update(ner_actions)
        ner_others_all.update(ner_others)

        marked_list = marked_sents(text, ner_actions, ner_others)
        for act_idx, pairs in marked_list.items():
            action = defaultdict(list)
            lemma = WordNetLemmatizer().lemmatize(ner_actions[act_idx][1].lower(),'v')
            if lemma in norm_dict:
                lemma = norm_dict[lemma]

            action['action'] = act_idx

            if lemma in rolesets:
                roleset_info[act_idx] = get_roleset_info(rolesets[lemma], act_idx)

            roles = []
            for pair in pairs:
                if not pairs:
                    continue
                pred = pipe(pair[0])[0]
                label = pred['label']

                if label != 'NO_RELATION':
                    action[label].append(pair[2])

            actions.append(action)

    ret_text = '\n'.join(ret_texts)
    return ret_text, actions, ner_actions_all, ner_others_all, roleset_info


def prompt(instructions, description, max_tokens, task="\nConvert to XDL:\n", constraints=""):
    """prompt.

    Parameters
    ----------
    instructions :
        instructions
    description :
        description
    max_tokens :
        max_tokens
    task :
        task
    """
    prompt=description +constraints+ "\nConvert to XDL:\n" + instructions
    response = client.chat.completions.create(
        model=args.GPT_model,  # the model name of GPT which you use
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].message.content


def generate_xdl(instructions, available_hardware=None, available_reagents=None):
    prev_instr = instructions
    correct_syntax = False
    errors = {}
    task = "\nConvert to XDL:\n"

    constraints=""
    if available_hardware!= None:
        hardware_str = ", ".join(available_hardware)[:-2]
        constraints = f"\nThe available Hardware is: {hardware_str}\n"
    if available_reagents!= None:
        reagents_str = ", ".join(available_reagents)[:-2]
        constraints += f"\nThe available Reagents are: {reagents_str}\n"


    prev_output = ''
    for step in range(10):
        print(constraints+"\nConvert to XDL:\n" + instructions)
        try:
            gpt3_output = prompt(instructions, XDL, 1000, task, constraints)
        except openai.error.InvalidRequestError:
            gpt3_output = prompt(instructions, XDL, 750, task, constraints)
        print("gpt3 output:::")
        print(gpt3_output)
        print("******")
        if prev_output == gpt3_output:
            break
        prev_output = gpt3_output

        if '<XDL>' in gpt3_output and '</XDL>' in gpt3_output:
            gpt3_output = gpt3_output[gpt3_output.index("<XDL>"):gpt3_output.index("</XDL>")+len('</XDL>')]
            prev_output = gpt3_output

        compile_correct = verify.verify_xdl(gpt3_output, available_hardware, available_reagents)
        errors[step] = {
            "errors": compile_correct,
            "instructions": instructions,
            "gpt3_output": gpt3_output,
        }
        if len(compile_correct) == 0:
            correct_syntax = True
            break
        else:
            error_list = set()
            for ii in compile_correct:
                for jj in ii["errors"]:
                    error_list.add(jj)
            abl=2
            if abl== 0:
                error_message = "\n{}\nThis XDL was not correct. Please fix the errors.".format(
                    gpt3_output
                )
            elif abl==1:
                error_message = "These are XDL errors.\n{}\nPlease fix the errors.".format(
                    "\n".join(list(error_list))
                )
            #### BEST ONE:
            elif abl==2:
                error_message = "\n{}\nThis XDL was not correct. These were the errors\n{}\nPlease fix the errors.".format(
                    gpt3_output,
                    "\n".join(list(error_list))
                )
            instructions = prev_instr + " " + error_message

        time.sleep(args.clairify_interval_sec)

    if correct_syntax:
        return correct_syntax, gpt3_output, errors
    else:
        return correct_syntax, "The correct XDL could not be generated.", errors




if __name__ == "__main__":
    app.server.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.run(debug=True)
