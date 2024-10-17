import os
import re
import glob
import unicodedata as ud
from py4j.java_gateway import JavaGateway
from bs4 import BeautifulSoup

from xdl.steps.placeholders import *
from xdl.reagents import Reagent
from xdl.hardware import Component, Hardware
from xdl.steps.logging import start_executing_step_msg


chemtag_dict = {'chem': ['NN-CHEMENTITY', 'NN-MIXTURE', 'MOLECULE'],
         'vessel': ['NN-APPARATUS'], #
         'heatchill': ['NN-APPARATUS'], # bath
         'gas': []}

gateway = JavaGateway()
app = gateway.entry_point


def chemicaltagger(text):

    #print('ChemicalTagger model is loaded.')
    #print('----------')

    out_dir = os.path.join(os.getcwd(), 'tmpxml/')
    os.makedirs(out_dir, exist_ok=True)
    try:
        tmpfile = os.path.join(out_dir, 'tmpfile.xml')
        #print(text, tmpfile)
        app.chemtag(text, tmpfile)
    except:
        print('Failed to get a ChemicalTagger annotation.')
        exit()

    with open(tmpfile, 'r') as f:
        soup = BeautifulSoup(f, 'xml')

    return soup


'''
def get_param(value, unit):
    ret = {}
    if unit:
        unit = ud.normalize('NFKD', unit)
        text = value + ' ' + unit
    else:
        text = value

    if value:
        ret_value = float(value)
    else:
        ret_value = None

    return {'text': text, 'value': ret_value, 'unit': unit}
'''

def get_param(value, unit):
    ret = {}
    if unit:
        unit = ud.normalize('NFKD', unit)
        text = value + ' ' + unit
    else:
        text = value

    if value:
        try:
            ret_value = float(value)
        except:
            ret_value = None
    else:
        ret_value = None

    return text


'''
def get_attrs(soup):
    soup = BeautifulSoup(xmltext, 'xml')
    for mol in soup('MOLECULE'):
        m = {'is_chem': False, 'is_solvent': False}
        if mol('OSCARCM') and mol('QUANTITY'):
            m['is_chem'] = True
        if 'role' in mol.attrs:
            m['is_solvent'] = True

        mols.append(m)
'''

def mol_parser(soup):
    vessel = Component(id='tmp', component_type='flask')

    ret_actions = []

    DEFAULT_PROPS = {
        "name": None,
        "id": None,
        "role": "reagent"
    }

    chemicals = []
    solvents = []
    for mol in soup('MOLECULE'):
        mol_dict = {
            'reagent': None,
            'id': None,
            'name': None,
            'volume': get_param(None, None),
            'mass': get_param(None, None),
            'amount': get_param(None, None),
            'role': 'reagent'
        }

        cm = mol.find('OSCARCM')
        if cm:
            name = ' '.join([m.text for m in mol('OSCAR-CM')])
            mol_dict['id'] = name
            mol_dict['name'] = name
            if re.match('^\d+\-mL$', name):
                continue

        vol = mol.find('VOLUME')
        if vol:
            volume = get_param(vol.find('CD').text, vol.find('NN-VOL').text)
            mol_dict['volume'] = volume

        ms = mol.find('MASS')
        if ms:
            mass = get_param(ms.find('CD').text, ms.find('NN-MASS').text)
            mol_dict['mass'] = mass

        am = mol.find('AMOUNT')
        if am:
            amount = get_param(am.find('CD').text, am.find('NN-AMOUNT').text)
            mol_dict['amount'] = amount

        if 'role' in mol.attrs:
            mol_dict['role'] = mol.attrs['role']
            mol_dict['reagent'] = Reagent(**{k:mol_dict[k] for k in ['id', 'name', 'role']})
            solvents.append(mol_dict)
        else:
            mol_dict['reagent'] = Reagent(**{k:mol_dict[k] for k in ['id', 'name', 'role']})
            chemicals.append(mol_dict)



    for solv in solvents:
        #reag = Reagent(solv.fromkeys(['id', 'name', 'role']))
        #print('solv:', solv)
        #act = Add(vessel=vessel, volume=solv['volume']['text'], mass=solv['mass']['text'], amount=solv['amount']['text'], reagent=solv['reagent'])
        act = Add(vessel=vessel, volume=solv['volume'], mass=solv['mass'], amount=solv['amount'], reagent=solv['reagent'])
        ret_actions.append(act)

    for chem in chemicals:
        #reag = Reagent(chem.fromkeys(['id', 'name', 'role']))
        #print('chem:', chem)
        #act = Add(vessel=vessel, volume=chem['volume']['text'], mass=chem['mass']['text'], amount=chem['amount']['text'], reagent=chem['reagent'])
        act = Add(vessel=vessel, volume=chem['volume'], mass=chem['mass'], amount=chem['amount'], reagent=chem['reagent'])
        ret_actions.append(act)

    if len(ret_actions) < 2:
        ret_actions = []

    return chemicals, solvents, ret_actions

'''
def param_parser(soup, label):

    np = soup('NounPhrase')
    if not np:
        return None

    string = None
    cd = None
    if label == 'TEMPERATURE':
        strings = []
        for tp in soup('NN-TEMP'):
            strings.append(tp.text)
        string = ' '.join(strings)

        if string:
            num_unit = mol.find('CD')
            if num_unit:
                cd = num_unit.text

    elif label == 'TIME':
        strings = []
        for tp in soup('NN-TIME'):
            strings.append(tp.text)
        string = ' '.join(strings)

        if string:
            num_unit = mol.find('CD')
            if num_unit:
                cd = num_unit.text
                cd = alpha2digit(cd, 'en')

    if label == 'TEMP_TARGET':
        tempt

    elif label == 'MODIFIER':
        aaaa

    else:
        print('ERROR: "' + label + '" is invalid ARGM')
        exit()

    DEFAULT_PROPS = {
        "name": None,
        "id": None,
        "role": "reagent"
    }


    return chemicals, solvents, ret_actions
'''
def get_chemtypes(soup):

    types = []
    for k, tags in chemtag_dict.items():
        for tag in tags:
            if soup.find(tag):
                types.append(k)
                break

    return types
