# CompRL

## Setup
```
python3 -m venv env
source env/bin/activate
pip install -e .
```
Setup robosuite private macro file:
```
python $PWD/env/lib/python3.9/site-packages/robosuite/scripts/setup_macros.py
```

## Run
### Compositional RL Training
There is the option to either train the baseline or compositional reinforcement learning policy. See `scripts/config.py` to adjust training parameters.
```
python scripts/train.py
```
The training parameters used to train the baseline and compositional RL policies are given in `scripts/config.py`. 

### Evaluation
See `scripts/config.py` to adjust evaluation parameters.
```
python scripts/eval.py
```
