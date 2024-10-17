# Ref: https://github.com/gyan42/mozhi-datasets/blob/main/sroie2019/sroie2019_dataset.py

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import datasets
from datasets import config
from datasets.utils import logging



logger = datasets.logging.get_logger(__name__)

class OSPARNER(datasets.GeneratorBasedBuilder):

    #BUILDER_CONFIGS = [
    #    OSPARNERConfig(name='OSPAR', version=datasets.Version('1.0'), description='OSPAR dataset'),
    #]

    def __init__(self, data_dir):
        self._train_file = os.path.join(data_dir, 'train.tsv')
        self._val_file = os.path.join(data_dir, 'dev.tsv')
        self._test_file = os.path.join(data_dir, 'test.tsv')
        self.ner_tags, self.label2id = self._make_label_vocab()
        self.id2label = {v: k for k, v in self.label2id.items()}
        super(OSPARNER, self).__init__(data_dir)

    def _make_label_vocab(self):
        labels = []
        with open(self._train_file, 'r') as lines:
            for line in lines:
                line = line.strip()
                if line:
                    items = line.split('\t')
                    labels.append(items[3])

        labels = sorted(set(labels))
        label2id = {'O': 0}
        i = 1
        for label in labels:
            if label != 'O':
                label2id[label] = i
                i += 1

        return labels, label2id

    def _info(self):
        return datasets.DatasetInfo(
            description='OSPAR',
            features=datasets.Features(
                {
                    'id': datasets.Value('string'),
                    'tokens': datasets.Sequence(datasets.Value('string')),
                    'ner_tags': datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=sorted(list(self.ner_tags))
                        )
                    )
                }
            ),
            supervised_keys=None,
            homepage='',
            #citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        urls_to_download = {
            'train': self._train_file,
            'dev': self._val_file,
            'test': self._test_file,
        }
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={'filepath': downloaded_files['train']}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={'filepath': downloaded_files['dev']}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={'filepath': downloaded_files['test']}),
        ]

    def _generate_examples(self, filepath):
        logger.info('⏳ Generating examples from = %s', filepath)
        with open(filepath, 'r') as lines:
            id = 0
            tokens = []
            ner_tags = []
            for line in lines:
                if line == '' or line == '\n':
                    if tokens:
                        yield id, {
                            'id': str(id),
                            'tokens': tokens,
                            'ner_tags': ner_tags,
                        }
                        id += 1
                        tokens = []
                        ner_tags = []
                else:
                    items = line.strip().split('\t')
                    tokens.append(items[0])
                    ner_tags.append(self.label2id[items[3]])

            if tokens:
                yield id, {
                    'id': str(id),
                    'tokens': tokens,
                    'ner_tags': ner_tags,
                }

class OSPARRE(datasets.GeneratorBasedBuilder):

    #BUILDER_CONFIGS = [
    #    OSPARNERConfig(name='OSPAR', version=datasets.Version('1.0'), description='OSPAR dataset'),
    #]

    def __init__(self, data_dir):
        self._train_file = os.path.join(data_dir, 'train.tsv')
        self._val_file = os.path.join(data_dir, 'dev.tsv')
        self._test_file = os.path.join(data_dir, 'test.tsv')
        self.labels, self.label2id = self._make_label_vocab()
        self.id2label = {v: k for k, v in self.label2id.items()}
        super(OSPARRE, self).__init__(data_dir)

    def _make_label_vocab(self):
        labels = []
        with open(self._train_file, 'r') as lines:
            for line in lines:
                line = line.strip()
                if line:
                    items = line.split('\t')
                    labels.append(items[1])

        labels = sorted(set(labels))
        label2id = {}
        i = 0
        for label in labels:
            label2id[label] = i
            i += 1

        return labels, label2id

    def _info(self):
        return datasets.DatasetInfo(
            description='OSPAR',
            features=datasets.Features(
                {
                    'id': datasets.Value('string'),
                    'text': datasets.Value('string'),
                    'label': datasets.features.ClassLabel(names=sorted(list(self.labels)))
                }
            ),
            supervised_keys=None,
            homepage='',
            #citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        urls_to_download = {
            'train': self._train_file,
            'dev': self._val_file,
            'test': self._test_file,
        }
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={'filepath': downloaded_files['train']}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={'filepath': downloaded_files['dev']}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={'filepath': downloaded_files['test']}),
        ]

    def _generate_examples(self, filepath):
        logger.info('⏳ Generating examples from = %s', filepath)
        with open(filepath, 'r') as lines:
            id = 0
            for line in lines:
                if line:
                    items = line.strip().split('\t')
                    yield id, {
                        'id': str(id),
                        'text': items[0],
                        'label': items[1],
                    }
                    id += 1
