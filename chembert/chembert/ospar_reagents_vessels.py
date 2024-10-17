from collections import defaultdict
from xdl.hardware import Component

#from chemtag_parser import chemicaltagger, get_chemtypes

#gateway = JavaGateway()
#app = gateway.entry_point

def get_reagents_and_vessels1(os_actions):
    reagents = []
    solvents = []
    vessels = []

    reactor = Component(id='reactor', component_type='reactor')
    vessels.append(reactor)

    r_i = 1
    s_i = 1
    t_i = 1
    reag_dict = {}
    solv_dict = {}
    chem2v_id = {}
    org_reag = {}
    for i, action in enumerate(os_actions):
        for arg in ['ARG1', 'ARG2']:
            if action.__dict__[arg]:
                replaced = {}
                for j, e in enumerate(action.__dict__[arg]):
                    v_ids = []
                    for r_idx, reag in enumerate(e.reagents):
                        chem_id = reag['id']
                        if chem_id not in reag_dict:
                            reag_dict[chem_id] = reag['reagent']
                            reagents.append(reag['reagent'])

                            v_id = 'r' + str(r_i) + '_' + chem_id
                            chem2v_id[chem_id] = v_id
                            r_i += 1

                            vessel = Component(id=v_id, component_type='flask')
                            vessels.append(vessel)

                        else:
                            os_actions[i].__dict__[arg][j].reagents[r_idx]['reagent'].id = reag_dict[chem_id] ####
                            replaced[chem_id] = reag_dict[chem_id]

                            v_id = chem2v_id[chem_id]

                        v_ids.append(v_id.split('_')[0])

                    for s_idx, solv in enumerate(e.solvents):
                        chem_id = solv['id']
                        if chem_id not in solv_dict:
                            solv_dict[chem_id] = solv['reagent']
                            solvents.append(solv['reagent'])

                            v_id = 's' + str(s_i) + '_' + chem_id
                            chem2v_id[chem_id] = v_id
                            s_i += 1

                            vessel = Component(id=v_id, component_type='flask')
                            vessels.append(vessel)

                        else:
                            os_actions[i].__dict__[arg][j].solvents[s_idx]['reagent'].id = solv_dict[chem_id] ####
                            replaced[chem_id] = solv_dict[chem_id]

                            v_id = chem2v_id[chem_id]

                        v_ids.append(v_id.split('_')[0])

                    len_chem = len(e.reagents) + len(e.solvents)
                    if len_chem > 1:
                        mix_id = 'mix_' + '_'.join(sorted(v_ids))
                        t_i += 1

                        vessel = Component(id=mix_id, component_type='flask')
                        vessels.append(vessel)
                        for k, xdl_act in enumerate(e.xdl_actions):
                            os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['vessel'] = vessel
                            os_actions[i].__dict__[arg][j].xdl_actions[k].properties['vessel'] = str(vessel)

                            rid = os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['reagent'].id

                            if rid in replaced:
                                os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['reagent'] = replaced[rid]
                                os_actions[i].__dict__[arg][j].xdl_actions[k].properties['reagent'] = str(replaced[rid])

                        os_actions[i].__dict__[arg][j].vessel = vessel

                    elif len_chem == 1:
                        os_actions[i].__dict__[arg][j].vessel = vessel

                    else:
                        os_actions[i].__dict__[arg][j].vessel = reactor

    vessel_dict = {}
    for vessel in vessels:
        vessel_dict[vessel.id] = vessel

    return os_actions, reagents, solvents, vessel_dict



def get_reagents_and_vessels(os_actions):
    reagents = []
    solvents = []
    vessels = []

    reactor = Component(id='reactor', component_type='reactor')
    vessels.append(reactor)

    r_i = 1
    s_i = 1
    t_i = 1
    chem_dict = {}
    chem2v_id = {}
    for i, action in enumerate(os_actions):
        for arg in ['ARG1', 'ARG2']:
            if action.__dict__[arg]:
                replaced = {}
                for j, e in enumerate(action.__dict__[arg]):
                    v_ids = []
                    for r_idx, reag in enumerate(e.reagents):
                        chem_id = reag['id']
                        if chem_id not in chem_dict:
                            chem_dict[chem_id] = reag['reagent']
                            reagents.append(reag['reagent'])

                            v_id = 'r' + str(r_i) + '_' + chem_id
                            chem2v_id[chem_id] = v_id
                            r_i += 1

                            vessel = Component(id=v_id, component_type='flask')
                            vessels.append(vessel)

                        else:
                            os_actions[i].__dict__[arg][j].reagents[r_idx]['reagent'] = chem_dict[chem_id] ####
                            replaced[chem_id] = chem_dict[chem_id]

                            v_id = chem2v_id[chem_id]

                        v_ids.append(v_id.split('_')[0])

                    for s_idx, solv in enumerate(e.solvents):
                        chem_id = solv['id']
                        if chem_id not in chem_dict:
                            chem_dict[chem_id] = solv['reagent']
                            solvents.append(solv['reagent'])

                            v_id = 's' + str(s_i) + '_' + chem_id
                            chem2v_id[chem_id] = v_id
                            s_i += 1

                            vessel = Component(id=v_id, component_type='flask')
                            vessels.append(vessel)

                        else:
                            os_actions[i].__dict__[arg][j].solvents[s_idx]['reagent'] = chem_dict[chem_id] ####
                            replaced[chem_id] = chem_dict[chem_id]

                            v_id = chem2v_id[chem_id]

                        v_ids.append(v_id.split('_')[0])

                    len_chem = len(e.reagents) + len(e.solvents)
                    if len_chem > 1:
                        mix_id = 'mix_' + '_'.join(sorted(v_ids))
                        t_i += 1

                        vessel = Component(id=mix_id, component_type='flask')
                        vessels.append(vessel)
                        for k, xdl_act in enumerate(e.xdl_actions):
                            os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['vessel'] = vessel
                            os_actions[i].__dict__[arg][j].xdl_actions[k].properties['vessel'] = str(vessel)

                            rid = os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['reagent'].id

                            if rid in replaced:
                                os_actions[i].__dict__[arg][j].xdl_actions[k].init_props['reagent'] = replaced[rid]
                                os_actions[i].__dict__[arg][j].xdl_actions[k].properties['reagent'] = str(replaced[rid])
                        os_actions[i].__dict__[arg][j].vessel = vessel

                    elif len_chem == 1:
                        os_actions[i].__dict__[arg][j].vessel = vessel

                    else:
                        os_actions[i].__dict__[arg][j].vessel = reactor

    vessel_dict = {}
    for vessel in vessels:
        vessel_dict[vessel.id] = vessel

    return os_actions, reagents, solvents, vessel_dict
