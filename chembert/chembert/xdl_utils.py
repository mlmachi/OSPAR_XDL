from typing import List
from pprint import pprint

from chembert.chembert.chemtag_parser import chemicaltagger, get_chemtypes, mol_parser

#.lemmatize(items[2].lower(),'v')


class Color:
	BLACK          = '\033[30m'#(文字)黒
	RED            = '\033[31m'#(文字)赤
	GREEN          = '\033[32m'#(文字)緑
	YELLOW         = '\033[33m'#(文字)黄
	BLUE           = '\033[34m'#(文字)青
	MAGENTA        = '\033[35m'#(文字)マゼンタ
	CYAN           = '\033[36m'#(文字)シアン
	WHITE          = '\033[37m'#(文字)白
	COLOR_DEFAULT  = '\033[39m'#文字色をデフォルトに戻す
	RESET          = '\033[0m'#全てリセット

class Role:
    def __init__(
        self,
        #role: str,
        description: str,
        required: int,
        type: str = None,
        types: List[str] = None,
    ):
        #self.role = role
        self.description = description
        self.required = required
        if type:
            self.types = self._parse_types(type)
        elif types:
            self.types = types
        else:
            self.types = None
            #print('Error: type or types should be given for Role.')
            #print(description)
            #exit()

    def _parse_types(self, type):
        types = None
        if type:
            types = type.split('/')
        return types

    def print_attrs(self):
        for k, v in self.__dict__.items():
            print(k + ':', v)

class ActionRole:
    def __init__(
        self,
        text: str,
        label: str,
        start: int,
        end: int,
        types: List[str] = None,
        chemtag: str = None
    ):
        self.text = text
        self.label = label
        self.start = start
        self.end = end

        self.chemicals = {}
        self.xdl_actions = None

        if types:
            self.types = types
        elif chemtag:
            soup = BeautifulSoup(chemtag)
            self.types = get_chemtypes(soup)
        else:
            soup = chemicaltagger(text)
            self.types = get_chemtypes(soup)

        if 'chem' in self.types:
            chemicals, solvents, xdl_actions = mol_parser(soup)
            self.chemicals['reagent'] = chemicals
            self.chemicals['solvents'] = solvents
            self.xdl_acitons = xdl_acitons

    def print_attrs(self):
        for k, v in self.__dict__.items():
            print(k + ':', v)

#role = Role('desc', 0, 'vessel')
#print(role.__dict__)
#ar = ActionRole(role, **{'text': 'a mixture', 'label': 'TIME', 'start': 146, 'end': 152})
#print(ar.text)
#exit()



class Roleset:
    def __init__(
        self,
        lemma: str,
        required_roles: List[int],
        direction: str = None,
        ARG0: Role = None,
        ARG1: Role = None,
        ARG2: Role = None
    ):
        self.lemma = lemma
        self.required_roles = required_roles
        self.direction = direction

        self.ARG0 = ARG0
        self.ARG1 = ARG1
        self.ARG2 = ARG2

    def _check_attrs(self, attributes):
        err_flag = False
        for attr in attributes:
            if not attr:
                print(attr)
                err_flag = True
        if err_flag:
            exit()

    def print_attrs(self):
        for k, v in self.__dict__.items():
            print(k + ':', v)


class ActionRoleset:
    def __init__(
        self,
        lemma: str,
        roleset: Roleset,
        ARG0: List[ActionRole] = None,
        ARG1: List[ActionRole] = None,
        ARG2: List[ActionRole] = None,
        ARGM: List[dict] = None
    ):
        self.lemma = lemma
        self.roleset = roleset

        self.ARG0 = ARG0
        self.ARG1 = ARG1
        self.ARG2 = ARG2
        self.ARGM = ARGM

        self._check_args()

        self.TEMPERATURE = None
        self.TEMP_TARGET = None
        self.TIME = None
        self.MODIFIER = None

        self._parse_params()



    def _check_args(self):
        for role_str in ['ARG0', 'ARG1', 'ARG2']:
            i = int(role_str[-1])
            role = getattr(self.roleset, role_str)
            if role == None:
                self._check_role(self.roleset.required_roles[i])
            else:
                self._check_type(role_str, role.types)

    def _check_role(self, j):
        if j == 2:
            print(Color.RED + f'Error: ARG{i} must be required.')
            print(f'roleset: {self.lemma}' + Color.RESET)
            exit()
        elif j == 1:
            print(Color.BLUE + f'Caution: ARG{i} is not exist, but it is not necessary.')
            print(f'roleset: {self.lemma}' + Color.RESET)
            print()

    def _check_type(self, role_str, types):
        target_types = self.roleset.__dict__[role_str].types
        flag = False
        for type in types:
            if type in target_types:
                flag = True

        if flag == False:
            print(Color.BLUE + 'Caution: type is not appropreate.')
            print(f'Given: {type}')
            print('Candidates: ' + ', '.join(role.types))
            print(f'roleset: {self.lemma}' + Color.RESET)
            print()

    def _parse_params(self):
        if self.ARGM:
            for param in self.ARGM:
                if self.__dict__[param['label']]:
                    self.__dict__[param['label']].append(param)
                else:
                    self.__dict__[param['label']] = [param]


    def attr(self, name):
        return self.__dict__[name]


    def print_attrs(self):
        for k, v in self.__dict__.items():
            print(k + ':', v)


def read_rolesets(file):
    first = True
    rolesets = {}
    with open(file, 'r') as lines:
        for line in lines:
            items = line.strip().split('\t')
            if first:
                columns = items
                first = False
            else:
                d = {}
                #print(items)
                #print('')
                for i, k in enumerate(columns):
                    if items[i]:
                        value = items[i]
                        if k.endswith('required'):
                            value = int(value)
                        d[k] = value
                    else:
                        if k.endswith('required'):
                            d[k] = -1
                        else:
                            d[k] = None

                #required = [int(d['ARG0_required']), int(d['ARG1_required']), int(d['ARG2_required'])]
                required_roles = []
                for i in range(3):
                    r = d[f'ARG{i}_required']
                    required_roles.append(r)

                ARG0, ARG1, ARG2 = get_roles(d)

                rolesets[items[0]] = Roleset(
                                        lemma=items[0],
                                        required_roles=required_roles,
                                        direction=d['direction'],
                                        ARG0=ARG0,
                                        ARG1=ARG1,
                                        ARG2=ARG2
                                     )

    return rolesets

def get_roles(d):
    roles = []
    for i in range(3):
        if d[f'ARG{i}']:
            role = Role(d[f'ARG{i}'], d[f'ARG{i}_required'], d[f'ARG{i}_type'])
        else:
            role = None
        roles.append(role)

    return roles

def get_action_roleset(rolesets, action_dict):
    lemma = action_dict['action'][0]['lemma']
    if lemma not in rolesets:
        print(Color.RED + f'Error: lemma "{lemma}" is not defined' + Color.RESET)
        exit()

    kwargs = {}
    for k, args in action_dict.items():
        if k.startswith('ARG') and k != 'ARGM':
            kwargs[k] = []
            for arg in args:
                arole = ActionRole(**arg)
                kwargs[k].append(arole)


    ar = ActionRoleset(roleset=rolesets[lemma], lemma=lemma, **kwargs)
    return ar
'''
rolesets = read_rolesets('../roleset_required.txt')
ar = get_action_roleset(rolesets, action_dict)
ar.print_attrs()
ar.roleset.print_attrs()
for arg in ['ARG1', 'ARG2']:
    if ar.__dict__[arg]:
        for e in ar.__dict__[arg]:
            e.print_attrs()
'''
#ar.ARG1.print_attrs()
#ar.ARG2.print_attrs()
