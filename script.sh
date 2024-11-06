pip install --use-pep517 -r requirements.txt
python3 src/download_wordnet.py

# Installation of XDL
git clone https://gitlab.com/croningroup/chemputer/xdl.git
pip install -e ./xdl

# Installation of CLAIRify
git clone https://github.com/ac-rad/xdl-generation/
mv xdl-generation xdl_generation

