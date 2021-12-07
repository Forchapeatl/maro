from maro.rl_v3.policy import DiscretePolicyGradient
from maro.rl_v3.policy_trainer import DiscreteMADDPG, DistributedDiscreteMADDPG
from maro.rl_v3.workflow import preprocess_get_policy_func_dict

from .config import algorithm, running_mode
from .nets import MyActorNet, MyMultiCriticNet

ac_conf = {
    "reward_discount": .0,
    "num_epoch": 10
}

# #####################################################################################################################
if algorithm == "discrete_maddpg":
    get_policy_func_dict = {
        f"{algorithm}.{i}": lambda name: DiscretePolicyGradient(
            name=name, policy_net=MyActorNet()) for i in range(4)
    }
    get_trainer_func_dict = {
        f"{algorithm}.{i}_trainer": lambda name: DistributedDiscreteMADDPG(
            name=name, get_q_critic_net_func=lambda: MyMultiCriticNet(), device="cpu", **ac_conf
        ) for i in range(4)
    }
else:
    raise ValueError

policy2trainer = {
    f"{algorithm}.{i}": f"{algorithm}.{i}_trainer" for i in range(4)
}
# #####################################################################################################################

get_policy_func_dict = preprocess_get_policy_func_dict(
    get_policy_func_dict, running_mode
)
