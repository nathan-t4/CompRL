import os
import glob
import comp_rl
import sys

import numpy as np

import config
from utils.util import *
from utils.wrapper import MDP

def rollout(env, agents, baseline_mode, eps=1, tasks=None, required_success=False, verbose=True, render=True):
    assert all([task in env.unwrapped.tasks for task in tasks]), \
        f'Invalid tasks {tasks} for {env} environment'
    env.unwrapped.tasks = tasks # TODO: check that order is preserved 

    stats = {}
    done = False
    e = 0
    success = 0
    subtask_obs_buffer = {f'{task}': [] for task in tasks}
    subtask_buffer = []
    q_buffer = []
    action_buffer = []
    reward_buffer = []
    reward_criteria_buffer = []
    env.reset()

    env.training_mode = True

    counter = 0
    while counter < eps:
        if done:
            stats[f'rollout_{counter}'] = {}
            if info['task_success']: 
                print(f'Episode {e} success', end='\r')
                # print(f'init qpos {info["init_qpos"]}')
                stats[f'rollout_{counter}']['is_success'] = 1
                success += 1

                # Log data if successful rollout
                stats[f'rollout_{counter}']['obs'] = np.array(q_buffer)
                stats[f'rollout_{counter}']['subtask_obs'] = subtask_obs_buffer
                stats[f'rollout_{counter}']['subtask'] = subtask_buffer
                stats[f'rollout_{counter}']['action'] = np.array(action_buffer)
                stats[f'rollout_{counter}']['reward'] = np.array(reward_buffer)
                stats[f'rollout_{counter}']['reward_criteria'] = np.array(reward_criteria_buffer)
                # data = concatenate the obs, actions, and rewards by timestep
                # np.shape = ((obs,action,reward),timesteps)
                if baseline_mode:
                    # all observations are the same shape
                    task_obs = np.concatenate(([subtask_obs_buffer[f'{task}'] for task in tasks]))
                    stats[f'rollout_{counter}']['data'] = np.vstack((np.array(task_obs).T,
                                                            np.array(action_buffer).T,
                                                            np.array(reward_buffer).T))
                else:
                    # observation shape depends on subtask
                    stats[f'rollout_{counter}']['data'] = {
                        f'{task}': np.vstack((np.array(subtask_obs_buffer[f'{task}']).T,
                                              np.array(action_buffer)[:np.shape(subtask_obs_buffer[f'{task}'])[0]].T,
                                              np.array(reward_buffer)[:np.shape(subtask_obs_buffer[f'{task}'])[0]].T)) 
                                              for task in tasks}  
            else:
                # print(reward_criteria_buffer)
                if verbose: print(f'Subtask {env.unwrapped.current_task} success:', info['is_success'])
                stats[f'rollout_{counter}']['is_success'] = 0
            
            # reset buffers
            q_buffer = []
            subtask_obs_buffer = {f'{task}': [] for task in tasks}
            subtask_buffer = []
            action_buffer = []
            reward_buffer = []
            reward_criteria_buffer = []
            # Reset environment and task
            env.unwrapped.fresh_reset = True
            obs, info = env.reset()
            if len(tasks) == 1: env.unwrapped.current_task = tasks[0]
            e = e + 1
        
        # Debug: Check init_qpos is correct (TODO: move somewhere else)
        # env.unwrapped._env.robots[0].init_qpos = env.unwrapped._robot_init_qpos[env.unwrapped.current_task]
        # env.unwrapped._env.robots[0].reset(deterministic=True)
        # print(env.unwrapped._env.robots[0].init_qpos)
        
        # Force reset if current_task should not be evaluated
        if env.unwrapped.current_task not in tasks:
            done = True
            continue

        current_policy = agents['baseline'] if baseline_mode else agents[env.unwrapped.current_task]

        # Since obs depends on subtask, retrieve obs again in case subtask has changed
        obs = env.unwrapped._get_obs()
      
        action, _states = current_policy.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        
        done = terminated or truncated

        # Log robot joint positions 
        observation = info['observation']
        q_sin = observation['robot0_joint_pos_sin']
        q_cos = observation['robot0_joint_pos_cos']
        q = np.arctan2(q_sin, q_cos)

        q_buffer.append(q) 
        subtask_obs_buffer[f'{env.unwrapped.current_task}'].append(info['current_task_obs'])
        subtask_buffer.append(env.unwrapped.current_task)
        action_buffer.append(info['current_task_action'])
        reward_buffer.append(reward)
        reward_criteria_buffer.append(info['reward_criteria'])

        # print('init qpos', info['init_qpos'])

        if render:
            env.render()
        # required_success determines whether to only count successful runs
        counter = success if required_success else e
        
    stats['success_rate'] = (success / eps) * 100

    env.close()
    return stats

def rollout_mdp(M, eps=1, required_success=False, verbose=True, render=True):
    ''' rollout using MDP wrapper '''
    assert isinstance(M, MDP)
    stats = rollout(M.env, M.agent, M.baseline, eps=eps, tasks=M.tasks, required_success=required_success, verbose=verbose, render=render)
    return stats

if __name__ == '__main__':
    cfg = config.eval_cfg()

    BASELINE_MODE = 'baseline' in cfg.env.lower()
    # Test MDP wrapper
    M = MDP(env=cfg.env, 
            dir=cfg.dir, 
            policy=cfg.policy, 
            baseline_mode=BASELINE_MODE, 
            tasks=cfg.tasks,
            prefix=cfg.prefix,
        )

    # Evaluate
    info = rollout_mdp(M, eps=cfg.eps)
    # print('Subtask', info['rollout_0']['subtask'])
    # print('Reward criteria', info['rollout_0']['reward_criteria'])
    print(f'Success rate: {info["success_rate"]}')