kpid python
git pull
source activate fzy
nohup python -m visdom.server -p 8888 &
python train.py
nvidia-smi