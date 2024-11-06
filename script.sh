pip install --use-pep -r requirements.txt
cde data download

python3 src/download_wordnet.py

# Installation of XDL
git clone https://gitlab.com/croningroup/chemputer/xdl.git
pip install -e ./xdl

# Installation of CLAIRify
git clone https://github.com/ac-rad/xdl-generation/
mv xdl-generation xdl_generation

# Installation of brat 
git clone https://github.com/nlplab/brat.git
cd brat
bash install.sh
cd ..
