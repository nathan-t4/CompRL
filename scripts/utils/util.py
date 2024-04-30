import os
import glob
import random

import torch
import numpy as np
import stable_baselines3 as sb3
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.policies import obs_as_tensor 
# from wrapper import MDP

def find_file(dir, prefix=''):
    file = glob.glob(os.path.join(dir, prefix))
    assert len(file) == 1, f'Found {len(file)} files in directory {os.path.join(dir, prefix)}!'

    return file[0]

def load_agents(dir, policy, baseline, tasks, prefix='', tb_path='', device=None):
    agents = {}
    if baseline:
        TASK_MODEL_FILE = find_file(dir, f'{prefix}.zip')
        if policy == 'SAC':
            agents['baseline'] = SAC.load(TASK_MODEL_FILE)
        elif policy == 'PPO':
            agents['baseline'] = PPO.load(TASK_MODEL_FILE)
        else:
            raise RuntimeError('Invalid policy')
        print(f'Loaded baseline policy...')
    else:
        for task in tasks:
            TASK_MODEL_FILE = find_file(dir, f'{task}/{prefix}.zip')            
            if policy == 'SAC':
                agents[task] = SAC.load(TASK_MODEL_FILE)
            elif policy == 'PPO':
                agents[task] = PPO.load(TASK_MODEL_FILE)
            else:
                raise RuntimeError('Invalid policy')
            print(f'Loaded {task} {policy} policy...')
    return agents

def get_PPO_prob_dist(agent, obs):
    assert isinstance(agent, PPO)
    if not isinstance(obs, torch.Tensor):
        obs = agent.policy.obs_to_tensor(obs)[0]
    dist = agent.policy.get_distribution(obs)

    assert isinstance(dist.distribution, torch.distributions.normal.Normal)

    # TODO: or just return the torch normal distribution dist.distribution instead?
    # return [dist.distribution.loc, dist.distribution.scale]
    return dist.distribution