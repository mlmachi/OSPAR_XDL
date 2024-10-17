import os
import json
import argparse
import errno
from collections import defaultdict
from nltk.stem.wordnet import WordNetLemmatizer
from urllib.parse import urljoin

class Args:
    def __init__(self, config_file):
        self.config_file = config_file

        self.brat_dir = None
        self.brat_url = 'http://127.0.0.1:8001/'
        self.brat_working_dir = None
        self.chembert_config_file = 'chemtools/chembert/configs/pipeline.json'
        self.use_clairify = True
        self.clairify_interval_sec = 21
        self.GPT_model = 'gpt-4o-2024-05-13'
        self.OpenAI_API_key = None

        self._load_json()
        self._check_files()
        #if check_files:
        #   self._check_files()

    def _load_json(self):
        with open(self.config_file, 'r') as f:
            jdict = json.load(f)
        print(jdict)
        for k, v in jdict.items():
            self.__dict__[k] = v


    def _check_files(self):
        print('===Checking files in config...===')
        names = []
        if self.brat_dir:
            os.makedirs(self.brat_dir, exist_ok=True)
        else:
            print('\"brat_dir\" in config file must be required.')
            exit()

        if not self.brat_url:
            print('\"brat_url\" is not defined in config.json.')
            print('default value \"http://127.0.0.1:8001/\" is used now.')

        if not os.path.exists(self.chembert_config_file):
            print('Warning \"chembert_config_file\"')
            print(self.chembert_config_file, 'is not exist.')

        if not self.brat_working_dir:
            suffix = self.brat_dir.split('brat/data/')[-1]
            tmp_url = urljoin(self.brat_url, '/#/')
            self.brat_working_dir = os.path.join(tmp_url, suffix)
            print(self.brat_working_dir)

wnl = WordNetLemmatizer()

with open('src/lemma_norm_dict.json', 'r') as f:
    norm_dict = json.load(f)

def read_ann(annfile, remove_workup=True):
    action_ents = {}
    arguments = {}

    actions = {}
    print(annfile)
    relations = []

    wu_idx = 1000000
    with open(annfile, 'r') as lines:
        for line in lines:
            items = line.strip().split('\t')
            if items[0][0] == 'T':
                label, start, end = items[1].split(' ')
                if label == 'REACTION_STEP':
                    lemma = WordNetLemmatizer().lemmatize(items[2].lower(),'v')
                    if lemma in norm_dict:
                        lemma = norm_dict[lemma]
                    action_ents[items[0]] = {'text': items[2], 'lemma': lemma, 'start': int(start), 'end': int(end)}
                elif label == 'B_Workup':
                    wu_idx = int(start)

                else:
                    arguments[items[0]] = {'text': items[2], 'label': label, 'start': int(start), 'end': int(end)}

            elif items[0][0] == 'R':
                args = items[1].split(' ')
                relations.append(args)

    if wu_idx != 1000000:
        del_list = []
        for k, v in action_ents.items():
            if v['start'] >= wu_idx:
                del_list.append(k)

        for k in del_list:
            del action_ents[k]

        del_list = []

        for k, v in arguments.items():
            if v['start'] >= wu_idx:
                del_list.append(k)

        for k in del_list:
            del arguments[k]

    for args in relations:
        label = args[0]
        e1 = args[1].split(':')[1]
        if e1 not in action_ents:
            continue

        if e1 not in actions:
            actions[e1] = defaultdict(list)
            actions[e1]['action'].append(action_ents[e1])
        e2 = args[2].split(':')[1]
        actions[e1][label].append(arguments[e2])


    for k, action in actions.items():
        for role, args in action.items():
            if role.startswith('ARG'):
                action[role] = sorted(action[role], key=lambda x: x['start'])

    tmp_actions = {}
    for k, action in actions.items():
        tmp_actions[int(action['action'][0]['start'])] = action

    ret_actions = []
    for i in sorted(tmp_actions):
        ret_actions.append(tmp_actions[i])

    return ret_actions


def write_ann(txtfile, annfile, text, actions, ner_actions, ner_others, roleset_info, keep_action=False, keep_ent=False):
    ent_actions = []
    ent_others = []
    ent_lines = []
    rel_lines = []
    r_idx = 1

    for action in actions:
        if (len(action) < 2) and (keep_action == False):
            continue

        e_idx = action['action']
        act_head = 'T' + e_idx

        ent_actions.append(e_idx)

        for role in action:
            if role == 'action':
                continue

            for ent in action[role]:
                ent_head = 'T' + ent
                ent_others.append(ent)

                rel_dict = {'head': 'R' + str(r_idx), 'label': role, 'Arg1': act_head, 'Arg2': ent_head}
                r_idx += 1
                rel_line = rel2line(rel_dict)
                rel_lines.append(rel_line)

    roleset_info_lines = []
    if keep_action:
        for act_idx in ner_actions:
            ent_line = ent2line(act_idx, ner_actions[act_idx])
            ent_lines.append(ent_line)
            if act_idx in roleset_info:
                roleset_info_lines.append(roleset_info[act_idx])
    else:
        for act_idx in ner_actions:
            if act_idx in ent_actions:
                ent_line = ent2line(act_idx, ner_actions[act_idx])
                ent_lines.append(ent_line)
                if act_idx in roleset_info:
                    roleset_info_lines.append(roleset_info[act_idx])

    if keep_ent:
        for ent_idx in ner_others:
            ent_line = ent2line(ent_idx, ner_others[ent_idx])
            ent_lines.append(ent_line)
    else:
        for ent_idx in ner_others:
            if ent_idx in ent_others:
                ent_line = ent2line(ent_idx, ner_others[ent_idx])
                ent_lines.append(ent_line)

    ann_lines = ent_lines + rel_lines + roleset_info_lines


    #for line in ann_lines:
    #    print(line)

    with open(txtfile, 'w') as f:
        f.write(text)

    with open(annfile, 'w') as f:
        f.write('\n'.join(ann_lines))



def ent2line(e_idx, entity):
    head = 'T' + e_idx
    mid = entity[0] + ' ' + str(entity[4]) + ' ' + str(entity[5])
    tail = entity[1]

    line = '\t'.join([head, mid, tail])

    return line

def rel2line(relation):
    head = relation['head']
    tail = relation['label'] + ' ' + 'Arg1:' + relation['Arg1'] + ' ' + 'Arg2:' + relation['Arg2']

    line = '\t'.join([head, tail])

    return line
