from pathlib import Path

import yaml

HOME_PATH = Path(__file__).resolve().parent.parent

with open(Path(HOME_PATH, 'config.yml'), 'r') as file:
    config = yaml.safe_load(file)

DATA_PATH = Path(HOME_PATH, config['data_path']).resolve()
DB_PATH = Path(DATA_PATH, config['db_name']).resolve()