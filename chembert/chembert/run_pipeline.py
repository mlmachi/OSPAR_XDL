import os
import sys
import json
import glob
import torch
import numpy as np
from collections import defaultdict
from transformers import (AutoTokenizer,
                          AutoModelForTokenClassification,
                          AutoModelForSequenceClassification,
                          pipeline)

from nltk.stem.wordnet import WordNetLemmatizer
wnl = WordNetLemmatizer()

from chembert.chembert.parameters import ParamsPred
from chembert.chembert.rolesets import get_action_roleset, read_rolesets
from chembert.chembert.ospar2xdl import ospar2xdl
from chembert.chembert.utils import (get_token_idx,
                   span2ann,
                   label2idx,
                   use_first,
                   marked_sents_cui)


def main():
    sargs = sys.argv
    config_file = sargs[1]
    input_dir = sargs[2]
    if len(sargs) > 3:
        output_dir = sargs[3]
    else:
        if sargs[2][-1] == '/':
            sargs[2] = sargs[2][:-1]
        output_dir = sargs[2] + '_output/'
    os.makedirs(output_dir, exist_ok=True)

    args = ParamsPred(config_file)

    with open('src/lemma_norm_dict.json', 'r') as f:
        norm_dict = json.load(f)

    rolesets = read_rolesets(args.roleset_file)

    args.print_models()

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    ner_tokenizer = AutoTokenizer.from_pretrained(args.trained_model_entity, max_length=args.max_seq_len, is_fast=True)
    ent_model = AutoModelForTokenClassification.from_pretrained(args.trained_model_entity).to(device)
    act_model = AutoModelForTokenClassification.from_pretrained(args.trained_model_action).to(device)
    prm_model = AutoModelForTokenClassification.from_pretrained(args.trained_model_params).to(device)

    re_tokenizer = AutoTokenizer.from_pretrained(args.trained_model_re, max_length=args.max_seq_len, is_fast=True)
    re_model = AutoModelForTokenClassification.from_pretrained(args.trained_model_re).to(device)

    for infile in glob.glob(os.path.join(input_dir, '*.txt')):
        print(infile)
        outfile =  output_dir + infile.split('/')[-1].split('.')[0] + '.xdl'

        try:
            with open(infile, 'r') as f:
                raw_text = f.read()

            actions = []
            sent_tokens, token_spans, sent_texts, sent_spans = get_token_idx(raw_text)

            prev = 0
            for tokens, spans, text, s_spans in zip(sent_tokens, token_spans, sent_texts, sent_spans):
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
                    # ann: list([label, ent_text, start, end])
                    ann = span2ann(raw_text, spans, idxs, s_spans)
                    ner_ann[k] = ann

                ner_actions = ner_ann['action']
                ner_others = ner_ann['entity'] + ner_ann['params']
                marked_list = marked_sents_cui(text, ner_actions, ner_others)

                pipe = pipeline('text-classification', model=args.trained_model_re, device=device)

                for _, pairs in marked_list.items():
                    if not pairs:
                        continue

                    action = defaultdict(list)
                    lemma = WordNetLemmatizer().lemmatize(pairs[0][1][1].lower(),'v')
                    if lemma in norm_dict:
                        lemma = norm_dict[lemma]

                    action['action'] = [{'text': pairs[0][1][1], 'lemma': lemma, 'start': pairs[0][1][2], 'end': pairs[0][1][3]}]
                    roles = []
                    for pair in pairs:
                        pred = pipe(pair[0])[0]
                        label = pred['label']

                        if label != 'NO_RELATION':
                            action[label].append({'label': pair[2][0], 'text': pair[2][1], 'start': pair[2][2], 'end': pair[2][3]})

                    actions.append(action)

            xdl_str = ospar2xdl(actions, rolesets)

            with open(outfile, 'w') as f:
                f.write(xdl_str)
        except:
            continue


    return



if __name__=='__main__':
    main()
