import os
import json
import glob
import re
from typing import List
from pprint import pprint
from collections import defaultdict
from xdl.hardware import Component
from xdl.xdl import XDL
from xdl.readwrite.xml_generator import step_to_xml_string, _append_hardware_tree, _append_reagents_tree, _get_step_tree, _get_xdl_string

from bs4 import BeautifulSoup
from chembert.chembert.rolesets import read_rolesets, get_roles, get_action_roleset

from chembert.chembert.ospar_reagents_vessels import get_reagents_and_vessels

from chembert.chembert.ospar_action import OSAdd, OSHeatChill, OSStir, OSEvacuateAndRefill, OSPurge

from dict2xml import dict2xml

import xml.etree.ElementTree as ET
#from chemtag_parser import chemicaltagger, get_chemtypes

#gateway = JavaGateway()
#app = gateway.entry_point


def _append_procedure_tree(
    xdltree: ET.ElementTree,
    steps,
) -> None:
    """Create and add Procedure section to XDL tree.

    Args:
        xdltree (ET.ElementTree): Full XDL XML tree to add steps to.
        steps (List[Step]): Steps to add to XML tree.
        full_properties (bool): If ``True``, all properties will be written.
            If ``False`` only mandatory, non default values and always write
            properties will be written.
        full_tree (bool): If ``True``, full step tree will be written as is the
            case in xdlexe files.
    """
    sections = {}
    procedure_tree = ET.Element("Procedure")
    section_trees = {section.capitalize(): None for section in sections}

    for step in steps:
        step_tree = _get_step_tree(step)
        # XDLEXE, don't worry about procedure sections.
        procedure_tree.extend([*step_tree])


    for _section, section_tree in section_trees.items():
        if section_tree is not None:
            procedure_tree.append(section_tree)
    xdltree.append(procedure_tree)

def objstr2id(text, vessels, reagents):
    obj2id = {}
    for k, v in vessels.items():
        obj2id[str(v)] = k

    for reag in reagents:
        obj2id[str(reag)] = reag.id

    for obj, id in obj2id.items():
        #print(obj, id)
        text = text.replace(obj, id)

    return text

def replace_placeholder(text):
    text = text.replace('-1000 °C', 'reflux')
    text = re.sub(r'mass="([^"]+)"', 'mass="\\1 g"', text)

    return text

def ospar2xdl(actions, rolesets):
    #rolesets = read_rolesets('../roleset_required.txt')

    ospar_actions = []
    for action in actions:
        ar = get_action_roleset(rolesets, action)
        if ar:
            ospar_actions.append(ar)


    ospar_actions, reagents, solvents, vessels = get_reagents_and_vessels(ospar_actions)


    steps = []

    for action in ospar_actions:
        if 'Add' in action.roleset.candidates:
            try:
                act = OSAdd(action, vessels)
                steps.extend(act.steps)
            except:
                continue

        elif 'HeatChill' in action.roleset.candidates or 'HeatChillToTemp' in action.roleset.candidates:
            try:
                act = OSHeatChill(action, vessels)
                steps.extend(act.steps)
            except:
                continue

        elif 'Stir' in action.roleset.candidates or 'StartStir' in action.roleset.candidates:
            try:
                act = OSStir(action, vessels)
                steps.extend(act.steps)
            except:
                continue

        elif 'EvacuateAndRefill' in action.roleset.candidates:
            try:
                act = OSEvacuateAndRefill(action, vessels)
                steps.extend(act.steps)
            except:
                continue

        elif 'Purge' in action.roleset.candidates:
            try:
                act = OSPurge(action, vessels)
                steps.extend(act.steps)
            except:
                continue

    xml_steps = []
    for step in steps:
        s_str = step_to_xml_string(step)
        xml_steps.append(s_str)

    rgts = []
    for reag in reagents:
        rgts.append({'Reagent': {'name': reag.name}})
        #rgts.append(dict2xml({'Reagent': {'name': reag.name}}))


    xdl_root = ET.Element("root")

    reagents.extend(solvents)
    _append_hardware_tree(xdl_root, vessels.values())
    _append_reagents_tree(xdl_root, reagents)
    _append_procedure_tree(xdl_root, steps)

    xdl_str = _get_xdl_string(xdl_root)

    xdl_str = objstr2id(xdl_str, vessels, reagents)
    xdl_str = replace_placeholder(xdl_str)

    return xdl_str
    #print(xdl_str)
    #with open(o_fname, 'w') as f:
    #    f.write(xdl_str)

    #step_tree = _get_step_tree(step, full_properties, full_tree)[0]
    #rgt_dict = {'Reagents': rgts}
    #print(dict2xml(rgt_dict))
    #print(xdl)
