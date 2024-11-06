# A Framework for Reviewing Results of Automated Conversion of Structured Organic Synthesis Procedures from Literature

This repository contains a framework for the paper: [A Framework for Reviewing the Results of Automated Conversion of Structured Organic Synthesis Procedures from the Literature]().

This repository provides a framework for editing automatically converted [chemical description language (XDL)](https://croningroup.gitlab.io/chemputer/xdl/standard/index.html) from literature with annotated text in the [Organic Synthesis Procedure with Argument Roles (OSPAR)](https://pubs.acs.org/doi/10.1021/acs.jcim.3c01449) format.


## Environment
- Ubuntu 24.04
- Python 3.8

### Tips: How to install Python3.8 on Ubuntu 24.04?
The default Python version in Ubuntu 24.04 is Python3.12
Here is an example for installing 

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install -y python3.8
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
sudo apt install -y python3.8-dev
sudo apt install -y python3.8-distutils
sudo apt install -yy python3-pip
```


## Installation and preparation

### Clone this repogitory and download requirements
```
git clone https://github.com/mlmachi/OSPAR_XDL
cd OSPAR_XDL
bash script.sh
```

Requirements are listed in `requirements.txt`.

### Other Requirements
1. ChemicalTagger
2. CodeMirror 5
3. Fine-tuned ChemBERT models
4. ChemDataExtractor
5. brat
6. py4j

### ChemicalTagger
Install ChemicalTagger to your java environment from [https://github.com/BlueObelisk/chemicaltagger](https://github.com/BlueObelisk/chemicaltagger)

#### Installation guide for users who are not familier with Java
[Maven](https://maven.apache.org/) is required to install ChemicalTagger.
```
sudo apt install -y maven
```

After installing Maven, run the following scripts.
```
git clone https://github.com/BlueObelisk/chemicaltagger
cd chemicaltagger
mvn install
mvn dependency:copy-dependencies -DoutputDirectory=lib
```

As a result, jar file for ChemicalTagger is generated as `OSPAR_XDL/chemicaltagger/target/cheicalTagger-x.x-SNAPSHOT.jar`, and dependencies are generated as `OSPAR_XDL/chemidcaltagger/lib/*.jar`.

Then, you can use ChemicalTagger by adding these jar files to your `CLASSPATH` environment variable.

You can see details about `CLASSPATH` on [https://docs.oracle.com/javase/8/docs/technotes/tools/unix/classpath.html](https://docs.oracle.com/javase/8/docs/technotes/tools/unix/classpath.html).


### CodeMirror 5
Download CodeMirror 5 from [https://codemirror.net/5/](https://codemirror.net/5/).

After unzipping the file, you can obtain `codemirror/codemirror5.xx.xx`.

Then, extract `codemirror5.xx.xx` and rename it `codemirror`.

Finally, place the renamed file into `OSPAR_XDL/static` (as a result, `OSPAR_XDL/static/codemirror/` is obtained).

### fine-tuned ChemBERT models
Download `model.zip` from [https://doi.org/10.6084/m9.figshare.27233541](https://doi.org/10.6084/m9.figshare.27233541).

After unzipping the file, you can obtain `models/models/`.

Then, place the `models` in subdirectory into `OSPAR_XDL/chembert` (as a result, `OSPAR_XDL/chembert/models/` is obtained).


### ChemDataExtractor
[ChemDataExtractor](http://chemdataextractor.org/) is used to split sentences.

While ChemDataExtractor is already installed when you run `script.py`, you need to download models by running: 
```
cde data download
```

If `cde data download` raises some errors, the error may be solved by rebooting your computer.


### brat
brat can be downloaded from here [https://brat.nlplab.org/](https://brat.nlplab.org/).

https://github.com/nlplab/brat
```
git clone https://github.com/nlplab/brat.git
cd brat
bash install.sh
```

After the download is complete, run the following command to enable the OSPAR format annotations.

```
mv ../brat_configs/*.conf data/
```

### py4j
The user need to place `.jar` file, which is downloaded by `script.sh`, into your `CLASSPATH` directory.

In our environment, the downloaded file is originally located in `/home/<USERNAME>/.local/share/py4j/py4j0.10.9.7.jar`.

You can see the details of py4j on [https://www.py4j.org/install.html](https://www.py4j.org/install.html).


### Configs
Configs were written in `configs.json`.

You should set your OpenAI_API_KEY when you use CLAIRify.

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
1. brat: `python3 standalone.py` in `OSPAR_XDL/brat/` directory
2. ChemicalTagger: `java ChemicalTaggerApp`
3. Webapp: `flask run`

After the servers are started, you can access `http://127.0.0.1:5000` to use the framework.

If `flask run` raises some errors, the error may be solved by rebooting your computer.


## Contact
If you have any questions and suggestions, please create an issue or email to [machi@eis.hokudai.ac.jp](mailto:machi@eis.hokudai.ac.jp).
