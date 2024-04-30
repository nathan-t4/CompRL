import os
import json
from time import strftime
from ml_collections import config_dict
import ml_collections.config_dict


# def train_cfg():
#     cfg = config_dict.FrozenConfigDict({
#         'env': 'CompLift-IIWA',
#         'policy': 'SAC',
#         'discount_rate': 0.96,
#         'epochs': int(2.5e5),
#         'eval_freq': int(1e4),
#         'eval_ep': 20,
#         'save_freq': int(5e3),
#         'resume_training': False,
#         'skip_tasks': [],
#         'success_thres': 0.95,
#         'model_prefix': '',
#         'dir': '',
#     })

#     return cfg

def train_cfg():
    cfg = config_dict.FrozenConfigDict({
        'env': 'BaselineLift-IIWA',
        'policy': 'SAC',
        'discount_rate': 0.96,
        'epochs': int(2e5),
        'eval_freq': int(1e4),
        'eval_ep': 20,
        'save_freq': int(5e3),
        'resume_training': False,
        'skip_tasks': [],
        'success_thres': 0.95,
        'model_prefix': '',
        'dir': '',
        'device': 'cpu', # or 'cuda' for GPU
    })

    return cfg

def eval_cfg():
    cfg = config_dict.FrozenConfigDict({
        'env': 'BaselineLift-IIWA',
        'dir': 'results/BaselineLift-IIWA/models',
        'policy': 'SAC',
        'eps': 5,
        'tasks': 'all',
        'prefix': '*',
    })

    return cfg

# def eval_cfg():
#     cfg = config_dict.FrozenConfigDict({ 
#         'env': 'CompLift-IIWA',
#         'dir': 'results/CompLift-IIWA/models',
#         'policy': 'SAC',
#         'eps': 5,
#         # 'tasks': ['reach', 'grasp', 'lift'],
#         'tasks': 'all',
#         'prefix': '*',
#     })

#     return cfg   
