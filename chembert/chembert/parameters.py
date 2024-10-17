import os
import json
import argparse
import errno

class Params:
    def __init__(self, config_file, check_files=True):
        self.config_file = config_file

        self.data_dir = '../data/try/' # dataset directory to use
        self.pretrained_dir = ''
        self.trained_model_dir = '' # trained model directory to load
        self.model_output_dir = '' # model dirctory to save
        self.pred_file = '' # target file to predict
        self.pred_out_file = ''

        self.serialization_dir = None

        # hparams of model
        self.learning_rate = 2e-5 # initial learning rate
        self.weight_decay = 0.01
        self.train_batch_size = 16 # size for each minibatch for training
        self.pred_batch_size = 32 # size for each minibatch for prediction
        self.max_seq_len = 256 # max sequence length
        self.num_epochs = 10 # max number of training epochs

        self.sub_token_mode = 'first'
        self.ignore_loss_on_o_tags = False

        self.label_encoding = None

        self.eval_metric = None
        self.greater_is_better = None
        self.eval_steps = 1
        self.eval_accumulation_steps = 10
        self.evaluation_strategy = 'epoch'
        self.save_strategy = 'epoch'

        self.num_workers = 6

        # hparams for logging and early stopping
        self.patience = None # training is stopped if no improvement for [patience] epochs
        self.num_keep_models = 2
        #self.save_top_k = 3 # the number of models to save

        # oparations
        self.do_train = False # whether to run training
        self.do_test = False # whether to run the model on the test set
        self.do_predict = False # whether to run the model on target data

        # random seeds for reproductivity
        self.seed = 133
        #self.numpy_seed = 133
        #self.torch_seed = 133

        self._load_json()
        #if check_files:
        #   self._check_files()

    def _load_json(self):
        with open(self.config_file, 'r') as f:
            jdict = json.load(f)
        for k, v in jdict.items():
            self.__dict__[k] = v

    def _check_files(self):
        print('===Checking files in config...===')
        names = []
        if self.do_train:
            names.extend(['data_dir', 'bert_dir',])
        if self.do_test:
            names.extend(['data_dir', 'bert_dir'])
        if self.do_predict:
            names.extend(['bert_dir', 'trained_model_dir', 'pred_file'])
        names = sorted(set(names))
        for name in names:
            path = self.__dict__[name]
            print(name + ': ' + path)
            if path is not None:
                if not os.path.exists(path):
                    raise FileNotFoundError(os.strerror(errno.ENOENT), path)
        print('===All files were found===')

    def save_params(self, save_file):
        params = vars(self)
        with open(save_file, 'w') as f:
            json.dump(params, f, indent=4)

class ParamsPred(Params):
    def __init__(self, config_file):
        super().__init__(config_file)

        self.config_file = config_file

        # trained models
        self.trained_model_entity = '' # trained model directory to load
        self.trained_model_action = ''
        self.trained_model_params = ''
        self.trained_model_re = ''

        self.roleset_file = ''

        self.pred_file = '' # target file to predict
        self.pred_out_file = ''

        self.pred_batch_size = 32 # size for each minibatch for prediction
        self.max_seq_len = 384 # max sequence length

        self.num_workers = 6

        self._load_json()

    def print_models(self):
        print('models:')
        print('  entity:', self.trained_model_entity)
        print('  action:', self.trained_model_action)
        print('  params:', self.trained_model_params)
        print('  RE:', self.trained_model_re)
