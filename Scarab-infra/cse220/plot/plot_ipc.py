import os
import json
import argparse
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rc('font', size=14)

def read_descriptor_from_json(descriptor_filename):
    # Read the descriptor data from a JSON file
    try:
        with open(descriptor_filename, 'r') as json_file:
            descriptor_data = json.load(json_file)
        return descriptor_data
    except FileNotFoundError:
        print(f"Error: File '{descriptor_filename}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{descriptor_filename}': {e}")
        return None

def get_dcache(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    dcache_miss_ratio = {}

    try:
        benchmarks_groups = [benchmarks_org[i:i+8] for i in range(0, len(benchmarks_org), 8)]
        
        for config_key in descriptor_data["configurations"].keys():
            dcache_miss_ratio[config_key] = []

            for group in benchmarks_groups:
                dcache_config = []
                avg_dcache_miss_ratio = {'compulsory': 0, 'conflict': 0, 'capacity': 0}
                cnt_benchmarks = 0

                for benchmark in group:
                    benchmark_name = benchmark.split("/")
                    exp_path = os.path.join(sim_path, benchmark, descriptor_data["experiment"], config_key)
                    compulsory, conflict, capacity = 0, 0, 0
                    dcache_hits = 0

                    with open(os.path.join(exp_path, 'memory.stat.0.csv')) as f:
                        lines = f.readlines()
                        for line in lines:
                            tokens = [x.strip() for x in line.split(',')]
                            if 'DCACHE_MISS_ONPATH_COMPULSORY_count' in line:  
                                compulsory = float(tokens[1])
                            elif 'DCACHE_MISS_ONPATH_CONFLICT_count' in line:  
                                conflict = float(tokens[1])
                            elif 'DCACHE_MISS_ONPATH_CAPACITY_count' in line:  
                                capacity = float(tokens[1])
                            elif 'DCACHE_HIT_ONPATH_count' in line:
                                dcache_hits = float(tokens[1])

                    total_misses = compulsory + conflict + capacity
                    total_accesses = total_misses + dcache_hits
                    if total_accesses > 0:
                        dcache_config.append({
                            'compulsory': compulsory / total_accesses,
                            'conflict': conflict / total_accesses,
                            'capacity': capacity / total_accesses
                        })
                    avg_dcache_miss_ratio['compulsory'] += compulsory / total_accesses
                    avg_dcache_miss_ratio['conflict'] += conflict / total_accesses
                    avg_dcache_miss_ratio['capacity'] += capacity / total_accesses
                    cnt_benchmarks += 1


                avg_miss_ratio = {k: v / cnt_benchmarks for k, v in avg_dcache_miss_ratio.items()}
                dcache_config.append(avg_miss_ratio)
                dcache_miss_ratio[config_key].append(dcache_config)

        for i, group in enumerate(benchmarks_groups):
            group_with_avg = group.copy()
            if i == len(benchmarks_groups) - 1:  
                group_with_avg.append('Avg')

            plot_data(group_with_avg if i == len(benchmarks_groups) - 1 else group, {key: dcache_miss_ratio[key][i] for key in dcache_miss_ratio}, 'Dcache Miss Ratio', f"{output_dir}/FigureB_Group{i+1}.png")

    except Exception as e:
        print(e)

import matplotlib.patches as mpatches

import matplotlib.patches as mpatches

def plot_data(benchmarks, data, ylabel_name, fig_name, ylim=None):
    colors = {
        'compulsory': '#ff6666',  # red
        'conflict': '#6666ff',    # blue
        'capacity': '#66ff66'     # green
    }

    num_benchmarks = len(benchmarks) 
    ind = np.arange(num_benchmarks)
    width = 0.12
    fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)

    for idx, (key, values) in enumerate(data.items()):
        conflict_misses = [v['conflict'] for v in values[:num_benchmarks]]
        capacity_misses = [v['capacity'] for v in values[:num_benchmarks]]
        compulsory_misses = [v['compulsory'] for v in values[:num_benchmarks]]
        bottom = np.zeros(num_benchmarks)
        bars = ax.bar(ind + idx * width, capacity_misses, width, color=colors['capacity'], edgecolor="none")
        bottom += np.array(capacity_misses)
        bars += ax.bar(ind + idx * width, conflict_misses, width, bottom=bottom, color=colors['conflict'], edgecolor="none")
        bottom += np.array(conflict_misses)
        bars += ax.bar(ind + idx * width, compulsory_misses, width, bottom=bottom, color=colors['compulsory'], edgecolor="none")

    ax.set_xlabel("Benchmarks")
    ax.set_ylabel(ylabel_name)
    ax.set_xticks(ind)
    ax.set_xticklabels(benchmarks, rotation=27, ha='right')
    ax.grid('x')
    if ylim is not None:
        ax.set_ylim(ylim)

    # Custom legend patches
    compulsory_patch = mpatches.Patch(color=colors['compulsory'], label='Compulsory')
    conflict_patch = mpatches.Patch(color=colors['conflict'], label='Conflict')
    capacity_patch = mpatches.Patch(color=colors['capacity'], label='Capacity')
    
    # Arrange legend items in a vertical column
    ax.legend(handles=[capacity_patch, conflict_patch, compulsory_patch], loc="upper left", ncol=1)
    
    fig.tight_layout()
    plt.savefig(fig_name, format="png", bbox_inches="tight")






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o','--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d','--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s','--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)
    get_dcache(descriptor_data, args.simulation_path, args.output_dir)
    plt.grid('x')
    plt.tight_layout()
    plt.show()
