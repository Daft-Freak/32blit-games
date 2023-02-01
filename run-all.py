import glob
import subprocess
import sys

for repo_dir in glob.glob('repos/**/*'):
    result = subprocess.run(sys.argv[1:], cwd=repo_dir)

    if result.returncode:
        exit(result.returncode)
