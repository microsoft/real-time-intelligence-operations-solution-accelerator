
import json
import os
from pathlib import Path

class AZDEnvironmentLoader:
    def __init__(self, directory: str = None, required: bool = False, log_events: bool = True):

        if directory is None:
            curr_script_path = Path(__file__)
            project_root = curr_script_path.parent
            while project_root != project_root.parent:
                if (project_root / '.azure').exists():
                    break
                project_root = project_root.parent
            directory = project_root / '.azure'

        self.directory = directory
        self.required = required
        self.log_events = log_events
        self.env_file = ''
        self.default_env = ''

        azure_dir = Path(self.directory)
        if azure_dir.name != '.azure':
            azure_dir = azure_dir / '.azure'

        config_file = azure_dir / 'config.json'
        
        if not config_file.exists():
            self._handle_invalid_env("AZD config.json file not found")
            return
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.default_env = config.get('defaultEnvironment')
        if not self.default_env:
            self._handle_invalid_env("No defaultEnvironment set in AZD config.json")
            return
        
        env_dir = azure_dir / self.default_env
        self.env_file = env_dir / '.env'

    def _log(self, message: str):
        if self.log_events:
            print(message)

    def _handle_invalid_env(self, message: str):
        if self.required:
            raise EnvironmentError(f"❌ Error: {message}.")
        else:
            self._log(f"⚠️  Warning: {message}.")

    def set_env_vars(self):
        """Load environment variables from AZD environment if not already set."""
        try:            
            if not self.env_file or not self.env_file.exists():
                self._handle_invalid_env(f"No .env file found for the default environment '{self.default_env}'")
                return
            
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and not os.getenv(key):
                            self._log(f"Setting environment variable: {key}")
                            os.environ[key] = value

            self._log(f"✅ Loaded AZD environment variables from: {self.default_env}")
        except Exception as e:
            if self.required:
                raise e
            else:
                self._log(f"⚠️  Warning: Failed to load AZD environment variables. {str(e)}")