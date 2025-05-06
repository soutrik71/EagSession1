import yaml
import os
import shutil
from loguru import logger


def read_yaml_file(file_path):
    """
    Read a YAML file and return its contents.
    """
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data


def check_and_reset_index(index_name: str, reset_index: bool) -> None:
    """
    Check if the index needs to be reset based on configuration

    Args:
        index_name: Path to the index folder
        reset_index: Whether to reset the index
    """
    if reset_index and os.path.exists(index_name):
        logger.warning(
            f"reset_index is set to True. Deleting existing index at '{index_name}'"
        )
        try:
            shutil.rmtree(index_name)
            logger.success(f"Successfully deleted index folder '{index_name}'")
        except Exception as e:
            logger.error(f"Error deleting index folder '{index_name}': {e}")
    elif not reset_index and os.path.exists(index_name):
        logger.info(
            f"reset_index is set to False. Keeping existing index at '{index_name}'"
        )
