kpid python
git pull
source activate fzy
nohup python -m visdom.server -p 8888 &
nohup python train.py --steps 30000 &
nvidia-smi