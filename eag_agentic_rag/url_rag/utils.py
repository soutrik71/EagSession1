import yaml


def read_yaml_file(file_path):
    """
    Read a YAML file and return its contents.
    """
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data
