import yaml
from copy import deepcopy
from os import makedirs
from os.path import dirname, join, realpath


path = realpath(__file__)
script_dir = dirname(path)
sc_code_dir = dirname(script_dir)
root_dir = dirname(dirname(sc_code_dir))
maro_rl_dir = join(root_dir, "maro", "rl")
maro_sc_dir = join(root_dir, "maro", "simulator", "scenarios", "supply_chain")
config_path = join(sc_code_dir, "config.yml")
dockerfile_path = join(root_dir, "docker_files", "dev.df")

with open(config_path, "r") as fp:
    config = yaml.safe_load(fp)
    num_actors = config["distributed"]["num_actors"]
    redis_host = config["distributed"]["redis_host"]

docker_compose_manifest = {
    "version": "3.9",
    "services": {
        "redis": {"image": "redis:6", "container_name": redis_host},
        "learner": {
            "build": {"context": root_dir, "dockerfile": dockerfile_path},
            "image": "maro-sc",
            "container_name": "learner",
            "volumes": [
                f"{sc_code_dir}:/maro/examples/supply_chain",
                f"{maro_rl_dir}:/maro/maro/rl",
                f"{maro_sc_dir}:/maro/maro/simulator/scenarios/supply_chain"
            ],
            "command": ["python3", "/maro/examples/supply_chain/main.py", "-w", "1"]
        }
    }
}

for i in range(num_actors):
    actor_id = f"actor.{i}"
    actor_manifest = deepcopy(docker_compose_manifest["services"]["learner"])
    del actor_manifest["build"]
    actor_manifest["command"][-1] = "2"
    actor_manifest["container_name"] = actor_id
    actor_manifest["environment"] = [f"COMPONENT={actor_id}"]
    docker_compose_manifest["services"][actor_id] = actor_manifest

with open(join(sc_code_dir, "docker-compose.yml"), "w") as fp:
    yaml.safe_dump(docker_compose_manifest, fp)
