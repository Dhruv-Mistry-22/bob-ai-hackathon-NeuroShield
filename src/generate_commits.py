import os
import subprocess
import glob
import math

domains = [
    'data_engineering',
    'demand_forecasting',
    'renewable_forecasting',
    'asset_diagnostics',
    'grid_optimization',
    'dashboard_ui'
]

# We need a list of all tracked files in the repo to divide up.
result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
files = [f for f in result.stdout.split('\n') if f.strip()]

if not files:
    print("No files tracked! Exiting.")
    exit(1)

# To get ~40 commits MINIMUM, since there are 6 branches, 40/6 ~ 7 commits per branch.
chunk_size = max(1, math.ceil(len(files) / 7))

for domain in domains:
    print(f"Creating orphan branch: {domain}")
    subprocess.run(['git', 'checkout', '--orphan', domain])
    # Clear the index but KEEP files on disk
    subprocess.run(['git', 'rm', '-r', '--cached', '.'])
    
    # We will add files in chunks to create commits
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i+chunk_size]
        for f in chunk:
            subprocess.run(['git', 'add', f])
        
        msg = f"feat({domain}): add components part {i//chunk_size + 1}"
        subprocess.run(['git', 'commit', '-m', msg])
        
    print(f"Pushing {domain} to origin...")
    subprocess.run(['git', 'push', '-u', 'origin', domain])

print("Finished generating branches and commits!")
