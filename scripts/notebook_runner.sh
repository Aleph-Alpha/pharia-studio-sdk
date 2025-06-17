#!/usr/bin/env -S bash -eu -o pipefail
# next line loads AA_TOKEN from .env file when running bash script locally. In CI this is not necessary since AA_TOKEN is environment variable.
[ -f .env ] && source .env
export AA_TOKEN
# Find all .ipynb files in the directory and pass them to xargs for parallel execution
rm -rf documentation/.ipynb_checkpoints

find documentation -name "*.nbconvert.ipynb" -type f -delete
find documentation -name "*.ipynb" | xargs --max-args 1 --max-procs 6 uv run jupyter nbconvert --to notebook --execute
find documentation -name "*.nbconvert.ipynb" -type f -delete
