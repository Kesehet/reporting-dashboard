import os
import json



def read_env_to_json(env_path=".env"):
    env_dict = {}
    if not os.path.exists(env_path):
        return json.dumps(env_dict)
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip().strip('"').strip("'")
    return env_dict

def get_env_value(key, env_path=".env"):
    return read_env_to_json(env_path).get(key, None)