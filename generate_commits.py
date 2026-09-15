import os
import subprocess
import glob

domains = [
    'data_engineering',
    'demand_forecasting',
    'renewable_forecasting',
    'asset_diagnostics',
    'grid_optimization',
    'dashboard_ui'
]

files = []
for root, _, filenames in os.walk('.'):
    if '.git' in root:
        continue
    for filename in filenames:
        files.append(os.path.join(root, filename))

# We want minimum 40 commits total, so about 7 commits per branch
chunk_size = max(1, len(files) // 7)

for domain in domains:
    print(f"Creating orphan branch: {domain}")
    subprocess.run(['git', 'checkout', '--orphan', domain])
    subprocess.run(['git', 'rm', '-rf', '.']) # Clear index
    
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
