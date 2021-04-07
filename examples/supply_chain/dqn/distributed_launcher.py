# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import argparse
import yaml
from multiprocessing import Process
from os import getenv
from os.path import dirname, join, realpath

from maro.rl import (
    Actor, ActorManager, DQN, DQNConfig, DistLearner, FullyConnectedBlock, LinearParameterScheduler, MultiAgentWrapper,
    OptimOption, SimpleMultiHeadModel
)
from maro.simulator import Env
from maro.utils import set_seeds

from examples.supply_chain.env_wrapper import SCEnvWrapper
from examples.supply_chain.dqn.agent import get_sc_agents


DEFAULT_CONFIG_PATH = join(dirname(realpath(__file__)), "config.yml")
with open(getenv("CONFIG_PATH", default=DEFAULT_CONFIG_PATH), "r") as config_file:
    config = yaml.safe_load(config_file)

# for distributed / multi-process training
GROUP = getenv("GROUP", default=config["distributed"]["group"])
REDIS_HOST = config["distributed"]["redis_host"]
REDIS_PORT = config["distributed"]["redis_port"]
NUM_ACTORS = int(getenv("NUMACTORS", default=config["distributed"]["num_actors"]))


def sc_dqn_learner():
    agent = get_sc_agents(Env(**config["training"]["env"]).agent_idx_list, config["agent"])
    scheduler = LinearParameterScheduler(config["training"]["max_episode"], **config["training"]["exploration"])
    actor_manager = ActorManager(
        NUM_ACTORS, GROUP, proxy_options={"redis_address": (REDIS_HOST, REDIS_PORT), "log_enable": False}
    )
    learner = DistLearner(
        agent, scheduler, actor_manager,
        agent_update_interval=config["training"]["agent_update_interval"],
        required_actor_finishes=config["distributed"]["required_actor_finishes"],
        discard_stale_experiences=False
    )
    learner.run()


def sc_dqn_actor():
    env = Env(**config["training"]["env"])
    agent = get_sc_agents(env.agent_idx_list, config["agent"])
    actor = Actor(SCEnvWrapper(env), agent, GROUP, proxy_options={"redis_address": (REDIS_HOST, REDIS_PORT)})
    actor.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--whoami", type=int, choices=[0, 1, 2], default=0,
        help="Identity of this process: 0 - multi-process mode, 1 - learner, 2 - actor"
    )

    args = parser.parse_args()
    if args.whoami == 0:
        actor_processes = [Process(target=sc_dqn_actor) for i in range(NUM_ACTORS)]
        learner_process = Process(target=sc_dqn_learner)

        for i, actor_process in enumerate(actor_processes):
            set_seeds(i)  # this is to ensure that the actors explore differently.
            actor_process.start()

        learner_process.start()

        for actor_process in actor_processes:
            actor_process.join()

        learner_process.join()
    elif args.whoami == 1:
        sc_dqn_learner()
    elif args.whoami == 2:
        sc_dqn_actor()
