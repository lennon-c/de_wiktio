""" Settings module."""	

# %% imports
from pathlib import Path    
import json

# %% class
class Settings:
    """Settings class for the de_wiktio package.
    
    Allowed keys: 
    - `XML_FILE`, for path to the XML dump file 
    - `DICT_PATH`, for path to the dictionary folder 
    
    Settings are saved in the `config.json` file in the package folder. 
    If the configuration file does not exist, it will be created when `get` or `set` methods are called.
    """
    _package_folder = Path(__file__).parent
    _file = _package_folder / 'config.json'
 
    @classmethod
    def _load(cls):
        try:
            with open(cls._file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            cls._create_file()
            return {}

    @classmethod
    def _create_file(cls):
        with open(cls._file, 'w') as f:
            json.dump({}, f)
        print(f"Created new configuration file: {cls._file}")

    @classmethod
    def _save_config(cls, config):
        with open(cls._file, 'w') as f:
            json.dump(config, f, indent=4)

    @classmethod
    def get(cls, key, default=None) -> str:
        """Get a value from the configuration file.
        
        Allowed keys are: `XML_FILE`, `DICT_PATH`."""
        config = cls._load()
        return config.get(key, default)

    @classmethod
    def set(cls, key, value):
        """Set a value in the configuration file.
        
        Allowed keys: 
            - `XML_FILE`, for path to the XML dump file 
            - `DICT_PATH`, for path to the dictionary folder 
        
        To delete a value, set it to `None`.
        """
        config = cls._load()
        config[key] = value
        cls._save_config(config)

