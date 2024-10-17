# A Framework for Reviewing Results of Automated Conversion of Structured Organic Synthesis Procedures from Literature

This repository contains a framework for the paper: [A Framework for Reviewing the Results of Automated Conversion of Structured Organic Synthesis Procedures from the Literature]().

This repository provides a framework for editing automatically converted [chemical description language (XDL)](https://croningroup.gitlab.io/chemputer/xdl/standard/index.html) from literature with annotated text in the [Organic Synthesis Procedure with Argument Roles (OSPAR)](https://pubs.acs.org/doi/10.1021/acs.jcim.3c01449) format.


## Installation and preparation

### Clone this repogitory and download requirements
1. `git clone https://github.com/mlmachi/OSPAR_webapp`
2. `cd OSPAR_webapp`
3. `bash script.sh`

Requirements are listed in `requirements.txt`.

### Other Requirements
1. brat
2. ChemicalTagger
3. CodeMirror 5
4. Fine-tuned ChemBERT models

### brat
brat can be downloaded from here [https://brat.nlplab.org/](https://brat.nlplab.org/).

After the download is complete, run the following command to enable the OSPAR format annotations.
`mv brat_configs/*.conf brat/data/`


### ChemicalTagger
Install ChemicalTagger to your java environment from [https://github.com/BlueObelisk/chemicaltagger](https://github.com/BlueObelisk/chemicaltagger)

### CodeMirror 5
Download CodeMirror 5 from https://codemirror.net/5/.
Unzip the file and rename the file `codemirror`
Place the renamed file into `static` (as a result, `./static/codemirror/` is obtained).

### fine-tuned ChemBERT models
Download `model.zip` from https://doi.org/10.6084/m9.figshare.27233541.
Unzip the file and place the file into `chembert` (as a result, `./chembert/model/` is obtained).

### Configs
Configs were written in `configs.json`.

| argument | description | default |
| ---- | ---- | ---- |
| brat_dir | Where to save generated OSPAR annotation from text. | brat/data/ospar/ |
| brat_url | URL of brat server. | http://127.0.0.1:8001/ |
| brat_working_dir | URL of brat server with the name of working directory | http://127.0.0.1:8001/index.xhtml#/ospar/ |
| chembert_config_file | Configs of ChemBERT models. | chembert/configs/pipeline.json |
| use_clairify | Whether to use CLAIRify. | True |
| GPT_model | [GPT model name](https://platform.openai.com/docs/models) | gpt-4o-2024-05-13  |
| OpenAI_API_KEY | OpenAI_API_KEY | None |
| clairify_interval_sec | The interval for accessing the OpenAI API (second) | 21 |


## How to run
Start the following servers:
1. brat: `python2 standalone.py`
2. ChemicalTagger: `java ChemicalTaggerApp`
3. Webapp: `flask run`

After the servers are started, you can access http://127.0.0.1:5000 to use the framework.

## Contact
If you have any questions and suggestions, please create an issue or email to [machi@eis.hokudai.ac.jp](mailto:machi@eis.hokudai.ac.jp).
