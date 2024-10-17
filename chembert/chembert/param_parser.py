import re

from bs4 import BeautifulSoup
from text_to_num import alpha2digit

TEMP_DICT = {
    'room temperature': '25 °C',
    'rt': '25 °C',
    'ambient temperature': '25 °C',
    'reflux': '-1000 °C'
}

TIME_DICT = {
    'overnight': '16 h'
}

STIR_RATE_DICT = {
    'vigorous': '500 rpm',
    'vigorously': '500 rpm'
}

gas_vocab = ['nitrogen', 'oxygen', 'air', 'argon']


def is_gas(word):
    if word in gas_vocab:
        return True
    else:
        return False


r_pattern = r'(\d*\.*\d+)\-(\d*\.*\d+)'
r_regex = re.compile(r_pattern)

def get_pattern_by_regex(text, regex):
    match = regex.findall(text)
    if match:
        return match[0]
    else:
        return None

rpm_pattern = r'\d+ rpm'
rpm_regex = re.compile(rpm_pattern)

def resolve_stir_rate(text):
    rate = get_pattern_by_regex(text, rpm_regex)
    if text in STIR_RATE_DICT:
        rate = STIR_RATE_DICT[text]

    '''
    ret_rate = None
    if rate:
        ret_rate = rate
    else:
        if text in STIR_RATE_DICT:
            ret_rate = STIR_RATE_DICT[text]
    '''

    return rate


def replace_by_dict(text, type):
    if type == 'temp':
        pattern_dict = TEMP_DICT
    elif type == 'time':
        pattern_dict = TIME_DICT
    else:
        return text, None

    pattern = re.compile(r'\b(' + '|'.join(re.escape(key) for key in pattern_dict.keys()) + r')\b', re.IGNORECASE)

    replaced_parts = []

    # 置換関数の定義
    def replacer(match):
        original_text = match.group(0)
        replacement_text = str(pattern_dict[original_text.lower()])
        replaced_parts.append((original_text, replacement_text))
        return replacement_text

    # 置換実行
    replaced_text = pattern.sub(replacer, text)

    return replaced_text, replaced_parts

def get_temp_by_chemtag(xml):
    temps = []
    soup = BeautifulSoup(xml, 'lxml-xml')
    for cd in soup.find_all('CD'):
        next_node = cd.next_sibling
        if not next_node:
            continue
        #value_text = cd.text
        value_text = alpha2digit(cd.text, 'en')

        # Use the later value of range. e.g., "25" of "23-25 C"
        range = get_pattern_by_regex(value_text, r_regex)
        if range:
            value_text = range[1]

        if next_node.name == 'NN-TEMP':
            temps.append({'value': float(value_text), 'unit': next_node.text, 'text': value_text + next_node.text})

    value = -1000
    ret_temp = []
    for temp in temps:
        if temp['value'] > value:
            ret_temp = temp['text']

    return ret_temp


def get_time_by_chemtag(xml):
    times = []
    soup = BeautifulSoup(xml, 'lxml-xml')
    for cd in soup.find_all('CD'):
        next_node = cd.next_sibling
        if not next_node:
            continue
        #value_text = cd.text
        value_text = alpha2digit(cd.text, 'en')

        # Use the later value of range. e.g., "5" of "3-5 min"
        range = get_pattern_by_regex(value_text, r_regex)
        if range:
            value_text = range[1]

        if next_node.name == 'NN-TIME':
            times.append({'value': float(value_text), 'unit': next_node.text, 'text': value_text + ' ' + next_node.text})

    value = -1
    ret_time = ''
    for time in times:
        if time['value'] > value:
            ret_time = time['text']

    return ret_time


def resolve_temp(ARGMs):
    if not ARGMs:
        return None

    ret_temp = None
    for argm in ARGMs:
        if argm['label'] == 'TEMPERATURE':
            temp = get_temp_by_chemtag(argm['chemtag'])
            if not temp:
                replaced_text, replaced_parts = replace_by_dict(argm['text'], 'temp')
                if replaced_parts:
                    temp = replaced_parts[0][1]

            if temp:
                ret_temp = temp

    return ret_temp

def resolve_time(ARGMs):
    if not ARGMs:
        return None

    ret_time = None
    for argm in ARGMs:
        if argm['label'] == 'TIME':
            time = get_time_by_chemtag(argm['chemtag'])
            if not time:
                replaced_text, replaced_parts = replace_by_dict(argm['text'], 'time')
                if replaced_parts:
                    time = replaced_parts[0][1]

                if time:
                    ret_time = time

    return ret_time
