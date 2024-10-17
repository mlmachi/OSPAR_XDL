import numpy as np
import re
#import os
#os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import evaluate

from chemdataextractor.doc import Paragraph

def get_token_idx(raw_text):
    sents = raw_text.split('\n')
    sent_texts = []
    #print(sents)
    for text in sents:
        para = Paragraph(text)
        sent_texts += para.raw_sentences

    start = 0
    end = 0
    sentences = []

    # this pattern is from standoff2conll (https://github.com/spyysalo/standoff2conll), MIT licenced.
    pattern = re.compile(r'([^\W_]+|.)')
    for sent in sent_texts:
        sent = sent.strip()
        tokenized = [token for token in pattern.split(sent) if len(token) > 0 and token != ' ']
        sentences.append(tokenized)

    sents = []
    spans = []
    sent_spans = []
    for s, text in zip(sentences, sent_texts):
        start2 = 0
        end2 = 0
        tokens = []
        token_spans = []
        s_spans = []
        if len(s) < 1:
            continue
        for line in s:
            if len(line) > 0:
                start = raw_text.find(line, end)
                end = start + len(line)
                tokens.append(line)
                token_spans.append([start, end])

                start2 = text.find(line, end2)
                end2 = start2 + len(line)
                s_spans.append([start2, end2])

        sents.append(tokens)
        spans.append(token_spans)
        sent_spans.append(s_spans)

    return sents, spans, sent_texts, sent_spans

def span2ann(text, spans, idxs, s_spans):
    ann_lines = []
    for idx in idxs:
        s_start = s_spans[idx[1]][0]
        s_end = s_spans[idx[2]][1]
        start = spans[idx[1]][0]
        end = spans[idx[2]][1]

        #ann_lines.append([idx[0], text[start:end], start, end, s_start, s_end])
        ann_lines.append([idx[0], text[start:end], s_start, s_end, start, end])


    return ann_lines


def label2idx(labels):

    ret = []
    ann = []
    i = 0
    for i, label in enumerate(labels):
        # token: list(token, label)
        # idx: list(token, start, end)
        if ann:
            if label[0] == 'I':
                ann[2] = i
                if label[2:] != ann[0]:
                    ret.append(ann)
                    ann = []
            else:
                ret.append(ann)
                ann = []

        if label[0] == 'B':
            ann = [label[2:], i, i]

    if ann:
        ret.append(ann)


    return ret


def use_first(inputs, predicted_labels):

    word_ids = inputs.word_ids()  # Map tokens to their respective word.
    previous_word_idx = None
    labels = []
    for word_idx, label in zip(word_ids, predicted_labels):  # Set the special tokens to -100.
        if word_idx != None and word_idx != previous_word_idx:  # Only label the first token of a given word.
            labels.append(label)
        previous_word_idx = word_idx
    return labels


def get_rel_span(sent_dict, rel_dict, rel_labels):
    ent1 = []
    ent2 = []
    for line in sent:
        if line[1] in ['REACTION_STEP']:
            ent1.append(line)
        else:
            ent2.append(line)
    for e1 in ent1:
        for e2 in ent2:
            if e1[0] in rel_dict:
                if e2[0] in rel_dict[e1[0]]:
                    label = rel_labels[e1[0]+e2[0]]
                    e1span = str(e1[2]) + '_' + str(e1[3])
                    e2span = str(e2[2]) + '_' + str(e2[3])
                    relations[i][e1span + '-' + e2span] = label
    return relations


def get_brat_info(ner_ann, idx):
    ner_actions = {}
    ner_others = {}

    for act in ner_ann['action']:
        ner_actions[str(idx)] = act
        idx += 1

    for ent in ner_ann['entity']:
        ner_others[str(idx)] = ent
        idx += 1

    for prm in ner_ann['params']:
        ner_others[str(idx)] = prm
        idx += 1


    '''
    i = 1
    for act in ner_ann['action']:
        ner_actions['T' + str(i)] = act
        i += 1

    for ent in ner_ann['entity']:
        ner_others['T' + str(i)] = ent
        i += 1

    for prm in ner_ann['params']:
        ner_actions['T' + str(i)] = prm
        i += 1

    '''

    return ner_actions, ner_others, idx


def get_roleset_info(roleset, idx):
    head = '#' + idx
    mid = 'AnnotatorNotes T' + idx

    roles = []
    for i, required in enumerate(roleset.required_roles):
        if required == 2:
            arg = 'ARG' + str(i)
            description = arg + ': ' + roleset.__dict__[arg].description + ' (Required)'
            roles.append(description)

        elif roleset.required_roles[i] == 1:
            arg = 'ARG' + str(i)
            description = arg + ': ' + roleset.__dict__[arg].description + ' (Optional)'
            roles.append(description)

    tail = ', '.join(roles)

    roleset_info = '\t'.join([head, mid, tail])

    return roleset_info

def marked_sents(text, actions, others):
    pairs = {}

    ent1 = actions
    ent2 = others

    for e1idx, e1 in ent1.items():
        relations = []
        for e2idx, e2 in ent2.items():
            txt = text
            e1i = [e1[2], e1[3]]
            e2i = [e2[2], e2[3]]
            if e1i[0] < e2i[0]:
                txt = txt[:e1i[0]] + '[E1]' + txt[e1i[0]:e1i[1]] + '[/E1]' + txt[e1i[1]:e2i[0]] + '[E2]' + txt[e2i[0]:e2i[1]] + '[/E2]' + txt[e2i[1]:]
            elif e1i[0] > e2i[0]:
                txt = txt[:e2i[0]] + '[E2]' + txt[e2i[0]:e2i[1]] + '[/E2]' + txt[e2i[1]:e1i[0]] + '[E1]' + txt[e1i[0]:e1i[1]] + '[/E1]' + txt[e1i[1]:]
            else:
                txt = txt[:e1i[0]] + '[E1]' + '[E2]' + txt[e1i[0]:e1i[1]] + '[/E2]' + '[/E1]' + txt[e2i[1]:]
            relations.append([txt, e1idx, e2idx])

        pairs[e1idx] = relations

    return pairs

def marked_sents_cui(text, actions, others):
    pairs = {}

    ent1 = actions
    ent2 = others

    for e1 in ent1:
        relations = []
        for e2 in ent2:
            txt = text
            e1i = [e1[2], e1[3]]
            e2i = [e2[2], e2[3]]
            if e1i[0] < e2i[0]:
                txt = txt[:e1i[0]] + '[E1]' + txt[e1i[0]:e1i[1]] + '[/E1]' + txt[e1i[1]:e2i[0]] + '[E2]' + txt[e2i[0]:e2i[1]] + '[/E2]' + txt[e2i[1]:]
            elif e1i[0] > e2i[0]:
                txt = txt[:e2i[0]] + '[E2]' + txt[e2i[0]:e2i[1]] + '[/E2]' + txt[e2i[1]:e1i[0]] + '[E1]' + txt[e1i[0]:e1i[1]] + '[/E1]' + txt[e1i[1]:]
            else:
                txt = txt[:e1i[0]] + '[E1]' + '[E2]' + txt[e1i[0]:e1i[1]] + '[/E2]' + '[/E1]' + txt[e2i[1]:]
            relations.append([txt, e1, e2])
        pairs['_'.join(list(map(str, e1))[1:])] = relations

    return pairs
