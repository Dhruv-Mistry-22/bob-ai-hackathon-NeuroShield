import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

def main():
    sum_df = pd.read_csv('outputs/optimization/optimization_summary.csv')
    act_df = pd.read_csv('outputs/optimization/optimization_actions.csv')
    
    # Ensure datetimes are sorted
    sum_df['timestamp'] = pd.to_datetime(sum_df['timestamp'])
    sum_df = sum_df.sort_values('timestamp')
    
    # 1. Action impact (Curtailment)
    plt.figure(figsize=(10, 5))
    plt.plot(sum_df['timestamp'], sum_df['baseline_curtailment'].rolling(50).mean(), label='Baseline Curtailment')
    plt.plot(sum_df['timestamp'], sum_df['optimized_curtailment'].rolling(50).mean(), label='Optimized Curtailment')
    plt.title('Estimated Curtailment Impact (50-step moving average)')
    plt.ylabel('Curtailment (MW)')
    plt.legend()
    plt.savefig('outputs/optimization/plot_action_impact.png')
    plt.close()
    
    # 2. Transmission stress
    plt.figure(figsize=(10, 5))
    plt.plot(sum_df['timestamp'], sum_df['baseline_transmission_utilization'].rolling(50).mean(), label='Baseline Utilization')
    plt.plot(sum_df['timestamp'], sum_df['optimized_transmission_utilization'].rolling(50).mean(), label='Optimized Utilization')
    plt.axhline(0.85, color='red', linestyle='--', label='Target Utilization (0.85)')
    plt.title('Estimated Transmission Stress (50-step moving average)')
    plt.ylabel('Utilization %')
    plt.legend()
    plt.savefig('outputs/optimization/plot_transmission_stress.png')
    plt.close()
    
    # 3. Resource activation bar chart (snapshot of a high-risk time)
    high_risk_time = act_df[act_df['action_mw'] > 10]['timestamp'].iloc[0] if len(act_df[act_df['action_mw'] > 10]) > 0 else None
    
    if high_risk_time:
        snapshot = act_df[act_df['timestamp'] == high_risk_time]
        plt.figure(figsize=(8, 5))
        plt.bar(snapshot['resource_type'], snapshot['action_mw'])
        plt.title(f'Resource Activation at {high_risk_time}')
        plt.ylabel('Action (MW)')
        plt.savefig('outputs/optimization/plot_resource_activation.png')
        plt.close()

    print("Plots generated.")

if __name__ == '__main__':
    main()
