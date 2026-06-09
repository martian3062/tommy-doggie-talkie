import os
from pathlib import Path


os.environ["DATABASE_URL"] = "sqlite:///./test_dog_translator.db"
os.environ["RUN_JOBS_INLINE"] = "true"
Path("test_dog_translator.db").unlink(missing_ok=True)
