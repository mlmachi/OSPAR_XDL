import warnings
import pprint

from xdl.steps.placeholders import *
from xdl.hardware import Component
from chembert.chembert.chemtag_parser import mol_parser
from chembert.chembert.rolesets import ActionRole

from chembert.chembert.param_parser import resolve_temp, resolve_time, resolve_stir_rate, is_gas


def check_param(vessel, param_list, type):
    param = None
    if param_list:
        for param_cand in param_list:
            if type == 'temp':
                try:
                    tmp = HeatChillToTemp(vessel=vessel, temp=param_cand)
                    param = param_cand
                    break
                except:
                    continue

            elif type == 'time':
                try:
                    tmp = HeatChill(vessel=vessel, temp='25°C', time=param_cand)
                    param = param_cand
                    break
                except:
                    continue

        if not param:
            warnings.warn('You should parse ' + str(param_list) + ' into concrete parameter.')

    return param


def check_modifiers(modifiers):

    mod_dict = {'gas': None, 'stir': False, 'stir_rate': None, 'dropwise': None}
    if modifiers:
        for modifier in modifiers:
            if modifier['label'] == 'MODIFIER':
                text = modifier['text']
                if is_gas(text):
                    #mod_dict['gas'] = EvacuateAndRefill(vessel=vessel, gas=gas)
                    mod_dict['gas'] = text

                elif text in ['stirred', 'stirring']:
                    mod_dict['stir'] = True

                elif text in ['dropwise', 'drop-wise']:
                    mod_dict['dropwise'] = True

                else:
                    rate = resolve_stir_rate(text)
                    if rate:
                        mod_dict['stir_rate'] = rate


    return mod_dict

        # if rate: dropwise, xx rpm



class OSAdd:
    def __init__(
        self,
        arset: ActionRole,
        vessels: dict,
    ):
        self.lemma = arset.lemma
        self.roleset = arset.roleset
        self.direction = self._parse_direction(arset)

        self.steps = self._ospar2xdl(arset, vessels)


    def _ospar2xdl(self, arset, vessels):
        from_arg, target_arg = self.direction
        #print(arset.__dict__[target_arg])
        # if the target is specified
        # does reagent or solvent exist?
        '''
        if arset.__dict__[target_arg]:
            to_vessel = arset.__dict__[self.direction[1]][0].vessel
        else:
            ###reactor###
            to_vessel = vessels['reactor']
        '''
        to_vessel = vessels['reactor']

        modifiers = check_modifiers(arset.ARGM)


        steps = []

        if modifiers['gas']:
            steps.append(EvacuateAndRefill(vessel=to_vessel, gas=modifiers['gas']))

        # target
        targets = arset.__dict__[target_arg]
        if targets:
            if len(targets) > 1:
                print(self.lemma, arset)
                print('Worning: more than 1 target_arg.')
                print()

            arg_target = targets[0]
            reag_solv = arg_target.reagents + arg_target.solvents
            if reag_solv:
                # implicit actions: A in B
                if arg_target.xdl_actions:
                    for step in arg_target.xdl_actions:
                        steps.append(step)

                    ###reactor###
                    step = Transfer(from_vessel=arg_target.vessel,
                             to_vessel=vessels['reactor'],
                    )
                    steps.append(step)

                else:
                    step = Add(vessel=vessels['reactor'], **reag_solv[0])
                    steps.append(step)

        if arset.TEMPERATURE:
            #conversion
            ftemp = False
            for temp in arset.TEMPERATURE:
                try:
                    ftemp = True
                    steps.append(HeatChillToTemp(vessel=to_vessel, temp=temp))
                    break
                    #steps.append(STARTHeatChill())
                except:
                    continue

            if not ftemp:
                print('You must parse', arset.TEMPERATURE, 'into concrete temperature.')

                temp = check_param(to_vessel, arset.TEMPERATURE, 'temp')
                if not temp:
                    temp = resolve_temp(arset.ARGM)

                if temp:
                    steps.append(HeatChillToTemp(vessel=to_vessel, temp=temp))

        if modifiers['stir']:
            steps.append(StartStir(vessel=to_vessel, stir_speed=modifiers['stir_rate']))

        # from
        if arset.__dict__[from_arg]:
            for j, arg_ent in enumerate(arset.__dict__[from_arg]):
                ###CHECK TYPE of ENT###
                reag_solv = arg_ent.reagents + arg_ent.solvents

                time = check_param(to_vessel, arset.TIME, 'time')
                if not time:
                    time = resolve_time(arset.ARGM)

                if reag_solv:
                    # implicit actions: A in B
                    if arg_ent.xdl_actions:
                        for step in arg_ent.xdl_actions:
                            steps.append(step)

                        ###reactor###
                        step = Transfer(from_vessel=arg_ent.vessel,
                                 to_vessel=to_vessel,
                                 time=time
                        )
                        steps.append(step)

                    else:
                        step = Add(vessel=to_vessel, time=time, dropwise=modifiers['dropwise'], **reag_solv[0])
                        steps.append(step)
                else:
                    if arg_ent.vessel != to_vessel:
                        step = Transfer(from_vessel=arg_ent.vessel,
                                 to_vessel=to_vessel,
                                 time=time,
                        )
                        steps.append(step)

                if modifiers['stir']:
                    steps.append(StopStir(vessel=to_vessel, stir_speed=modifiers['stir_rate']))

        return steps


    def _parse_direction(self, arset):
        dr_str = arset.roleset.direction
        direction = dr_str.split('to')
        return direction

    def _check_vessels(self, arset):
        if len(arset.__dict__[self.direction[1]]) > 1:
            print('Error: there are multiple target vessels.')
            exit()


class OSHeatChill:
    def __init__(
        self,
        arset: ActionRole,
        vessels: dict,
    ):
        self.lemma = arset.lemma
        self.roleset = arset.roleset

        self.steps = self._ospar2xdl(arset, vessels)

    def _ospar2xdl(self, arset, vessels):
        vessel = vessels['reactor']

        steps = []
        #print(arset.__dict__)
        #print(arset.roleset.__dict__)

        if not arset.TEMPERATURE:
            print(arset.__dict__)
            print('Warning: There is no temperature.')
            print('Skip this action.')
            print()
            return steps
            #raise ValueError('There is no temperature.')

        modifiers = check_modifiers(arset.ARGM)

        if modifiers['gas']:
            steps.append(EvacuateAndRefill(vessel=vessel, gas=modifiers['gas']))

        if modifiers['stir']:
            steps.append(StartStir(vessel=vessel, stir_speed=modifiers['stir_rate']))


        temp = check_param(vessel, arset.TEMPERATURE, 'temp')
        if not temp:
            temp = resolve_temp(arset.ARGM)

        time = check_param(vessel, arset.TIME, 'time')
        if not time:
            time = resolve_time(arset.ARGM)

        if temp:
            if time:
                steps.append(HeatChill(vessel=vessel, temp=temp, time=time))
            else:
                steps.append(HeatChillToTemp(vessel=vessel, temp=temp))

        if modifiers['stir']:
            steps.append(StopStir(vessel=vessel, stir_speed=modifiers['stir_rate']))



        return steps




class OSStir:
    def __init__(
        self,
        arset: ActionRole,
        vessels: dict,
    ):
        self.lemma = arset.lemma
        self.roleset = arset.roleset

        self.steps = self._ospar2xdl(arset, vessels)

    def _ospar2xdl(self, arset, vessels):
        vessel = vessels['reactor']

        steps = []

        modifiers = check_modifiers(arset.ARGM)

        if modifiers['gas']:
            steps.append(EvacuateAndRefill(vessel=vessel, gas=modifiers['gas']))

        temp = check_param(vessel, arset.TEMPERATURE, 'temp')
        if not temp:
            temp = resolve_temp(arset.ARGM)

        time = check_param(vessel, arset.TIME, 'time')
        if not time:
            time = resolve_time(arset.ARGM)

        if temp:
            if time:
                steps.append(HeatChillToTemp(vessel=vessel, temp=temp))
                steps.append(Stir(vessel=vessel, time=time, stir_speed=modifiers['stir_rate']))
            else:
                steps.append(HeatChillToTemp(vessel=vessel, temp=temp))
                steps.append(StartStir(vessel=vessel, stir_speed=modifiers['stir_rate']))
        else:
            if time:
                steps.append(Stir(vessel=vessel, time=time, stir_speed=modifiers['stir_rate']))
            else:
                steps.append(StartStir(vessel=vessel, stir_speed=modifiers['stir_rate']))

        return steps


class OSEvacuateAndRefill:
    def __init__(
        self,
        arset: ActionRole,
        vessels: dict,
    ):
        self.lemma = arset.lemma
        self.roleset = arset.roleset

        self.steps = self._ospar2xdl(arset, vessels)

    def _ospar2xdl(self, arset, vessels):
        vessel = vessels['reactor']

        steps = []

        for argstr in ['ARG1', 'ARG2']:
            role = getattr(arset.roleset, argstr)
            if role:
                types = role.types
                if 'gas' in types:
                    args = getattr(arset, argstr)
                    if args:
                        for arg in args:
                            text = arg.text
                            if is_gas(text):
                                # repeats will be extracted in future virsion
                                repeats = None
                                steps.append(EvacuateAndRefill(vessel=vessel, gas=text, repeats=repeats))
                                break

        return steps

class OSPurge:
    def __init__(
        self,
        arset: ActionRole,
        vessels: dict,
    ):
        self.lemma = arset.lemma
        self.roleset = arset.roleset

        self.steps = self._ospar2xdl(arset, vessels)

    def _ospar2xdl(self, arset, vessels):
        vessel = vessels['reactor']

        steps = []

        time = check_param(vessel, arset.TIME, 'time')
        if not time:
            time = resolve_time(arset.ARGM)

        for argstr in ['ARG1', 'ARG2']:
            role = getattr(arset.roleset, argstr)
            if role:
                types = role.types
                if 'gas' in types:
                    args = getattr(arset, argstr)
                    if args:
                        for arg in args:
                            text = arg.text
                            if is_gas(text):
                                # repeats will be extracted in future virsion
                                repeats = None
                                steps.append(Purge(vessel=vessel, gas=text, time=time))
                                break

        return steps
