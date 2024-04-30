import os
import comp_rl
import torch
import gymnasium as gym
import numpy as np

from time import strftime
from argparse import ArgumentParser
from collections.abc import Sequence

from stable_baselines3 import SAC, PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback

import config
from utils.callback import StopTrainingOnSuccessRateThreshold
from utils.util import find_file

def train(cfg):
    # Training parameters
    ENV_NAME = cfg.env
    POLICY = cfg.policy
    DISCOUNT_RATE = cfg.discount_rate
    TRAINING_STEPS = cfg.epochs
    EVAL_FREQUENCY = cfg.eval_freq
    EVAL_EPISODES = cfg.eval_ep
    SAVE_FREQUENCY = cfg.save_freq
    RESUME_TRAINING = cfg.resume_training
    BASELINE_MODE = 'baseline' in ENV_NAME.lower()
    SKIP_TASKS = cfg.skip_tasks
    DEVICE = cfg.device
    
    if BASELINE_MODE:
        assert 'baseline' in ENV_NAME.lower(), 'Conflict environment specification! Specified baseline training mode but not using baseline environment. Try again with correct --env flag.'

    # Model and log paths
    MODEL_PREFIX = cfg.model_prefix
    HOME_DIR = cfg.dir if RESUME_TRAINING else f'./experiments/{POLICY}/{ENV_NAME}/{strftime("%Y%m%d-%H%M%S")}-id-{np.random.randint(10000)}'
    MODEL_PATH = os.path.join(HOME_DIR, 'models/')
    TB_PATH = os.path.join(HOME_DIR, 'tb/')
    LOG_PATH = os.path.join(HOME_DIR, 'log/')

    device = torch.device(DEVICE)

    # Initialize environment
    env = gym.make(ENV_NAME)

    # Set training_mode=True to sequentially train subtask policies (for compositional training)
    env.unwrapped.training_mode = True
    
    agents = {} 
    tasks = ['baseline'] if BASELINE_MODE else env.unwrapped.tasks

    if isinstance(cfg.success_thres, float):
        # if a scalar then set success threshold to be constant among all tasks
        SUCCESS_THRESHOLD = cfg.success_thres * np.ones(len(tasks))
    elif isinstance(cfg.success_thres, Sequence) and len(cfg.success_thres) == len(tasks):
        # set individual success thresholds for each task
        SUCCESS_THRESHOLD = cfg.success_thres
    else:
        raise RuntimeError("Invalid success threshold flag")

    for task in SKIP_TASKS:
        tasks.remove(task)
    # Initialize SAC policy for all tasks
    for task in tasks:
        env.unwrapped.current_task = task
        if RESUME_TRAINING:
            # Pattern-match task policy path
            if MODEL_PREFIX is None:
                TASK_MODEL_PATH = find_file(MODEL_PATH, prefix=f'{task}/best_model.zip')
            else:
                TASK_MODEL_PATH = find_file(MODEL_PATH, prefix=MODEL_PREFIX)
            # Load previously trained task policy
            if POLICY == 'SAC':
                agents[task] = SAC.load(TASK_MODEL_PATH,                      
                                        tensorboard_log=os.path.join(TB_PATH, f'{task}/'),
                                        device=device)
            elif POLICY == 'PPO':
                agents[task] = PPO.load(TASK_MODEL_PATH,
                                        tensorboard_log=os.path.join(TB_PATH, f'{task}/'),
                                        device=device)
            else:
                raise RuntimeError(f'Invalid policy {POLICY}')
            agents[task].set_env(env)
        else:
            # Initialize policy
            if POLICY == 'SAC':
                agents[task] = SAC('MlpPolicy', env, verbose=1, gamma=DISCOUNT_RATE,
                                    tensorboard_log=os.path.join(TB_PATH, f'{task}/'))
            elif POLICY == 'PPO':
                agents[task] = PPO('MlpPolicy', env, verbose=1, gamma=DISCOUNT_RATE,
                                    tensorboard_log=os.path.join(TB_PATH, f'{task}/'))
            else:
                raise RuntimeError(f'Invalid policy {POLICY}')
    
    # Initialize evaluation environment (with custom logs info_keywords)
    info_kws = ('current_task', 'current_task_action', 'current_task_obs', 'is_success')
    eval_env = Monitor(gym.make(ENV_NAME), 
                       LOG_PATH,
                       info_keywords=info_kws)
    eval_env.unwrapped.training_mode = True
    
    # Train subtask policies sequentially
    for i, (task, agent) in enumerate(agents.items()):
        # Setup current task of environment
        if not BASELINE_MODE:
            env.unwrapped.current_task = task
            eval_env.unwrapped.current_task = task
        
        # Reset environments (to set correct robot init_qpos)
        env.unwrapped.reset()
        eval_env.unwrapped.reset()

        print(f'TRAINING {env.unwrapped.current_task}')
        # print(f'training_mode = {env.unwrapped.training_mode}')

        # Stop training on success rate threshold callback
        stop_training_callback = StopTrainingOnSuccessRateThreshold(success_threshold=SUCCESS_THRESHOLD[i], verbose=1)

        # Evaluation callback
        eval_callback = EvalCallback(eval_env, 
                                    eval_freq=EVAL_FREQUENCY,
                                    n_eval_episodes=EVAL_EPISODES,
                                    callback_on_new_best=stop_training_callback,
                                    deterministic=True,
                                    log_path=LOG_PATH,
                                    best_model_save_path=os.path.join(MODEL_PATH, f'{task}/'),
                                    verbose=1,
                                    render=False)
        
        # Periodically save model callback
        auto_save_callback = CheckpointCallback(save_freq=SAVE_FREQUENCY,
                                                save_path=os.path.join(MODEL_PATH, f'{task}/'),
                                                name_prefix=f'{task}',
                                                save_replay_buffer=True,
                                                verbose=2)
        
        # callbacks = [eval_callback, auto_save_callback]

        callbacks = [eval_callback]
        
        agent.learn(total_timesteps=TRAINING_STEPS,
                    callback=callbacks,
                    reset_num_timesteps=False)
        
        # Save final model
        agent.save(os.path.join(MODEL_PATH, f'{task}_final.zip'))

if __name__ == '__main__':
    cfg = config.train_cfg()
    train(cfg)