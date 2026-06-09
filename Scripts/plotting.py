import matplotlib.pyplot as plt
import pandas as pd

# --- 1. MODULAR PER-TEST DATA ENTRY ---
# Every row represents one full experiment. To update a value, just change it in that specific row.
test_records = [
    # Baseline/Air cutting tests (0.x)
    {"test_id": "0.1", "rpm": 250, "feed_rate": 25, "torque": -0.25,  "torque_std": 0.352, "x_force": -2.834, "x_force_std": 23.57,  "y_force": 2.81,   "y_force_std": 24.35,  "z_force": 6.67,   "z_force_std": 21.47},
    {"test_id": "0.2", "rpm": 200, "feed_rate": 20, "torque": -0.39,  "torque_std": 1.432, "x_force": -3.143, "x_force_std": 134.8,  "y_force": -10.07, "y_force_std": 118.5,  "z_force": -1.774, "z_force_std": 114.0},
    {"test_id": "0.3", "rpm": 150, "feed_rate": 11, "torque": -0.728, "torque_std": 1.298, "x_force": 0.957,  "x_force_std": 123.8,  "y_force": -6.321, "y_force_std": 102.04, "z_force": 17.26,  "z_force_std": 105.44},
    {"test_id": "0.4", "rpm": 100, "feed_rate": 10, "torque": -0.298, "torque_std": 0.431, "x_force": 7.029,  "x_force_std": 37.12,  "y_force": -3.26,  "y_force_std": 32.76,  "z_force": -1.58,  "z_force_std": 18.73},
    
    # Active cutting tests (1 to 12)
    {"test_id": "1",   "rpm": 100, "feed_rate": 7,  "torque": -2.206, "torque_std": 0.48,   "x_force": -2.873, "x_force_std": 18.02,  "y_force": -10.19, "y_force_std": 13.55,  "z_force": 34.48,  "z_force_std": 11.98},
    {"test_id": "2",   "rpm": 100, "feed_rate": 9,  "torque": -1.625, "torque_std": 0.4789, "x_force": -2.731, "x_force_std": 17.46,  "y_force": -8.899, "y_force_std": 12.8,   "z_force": 32.25,  "z_force_std": 11.72},
    {"test_id": "3",   "rpm": 100, "feed_rate": 10, "torque": -1.566, "torque_std": 0.528,  "x_force": 1.066,  "x_force_std": 19.3,   "y_force": -10.67, "y_force_std": 13.99,  "z_force": 32.2,   "z_force_std": 11.78},
    
    {"test_id": "4",   "rpm": 150, "feed_rate": 11, "torque": -1.282, "torque_std": 0.404,  "x_force": 0.517,  "x_force_std": 16.35,  "y_force": -12.78, "y_force_std": 14.52,  "z_force": 31.54,  "z_force_std": 11.77},
    {"test_id": "5",   "rpm": 150, "feed_rate": 13, "torque": -2.22,  "torque_std": 0.402,  "x_force": -0.655, "x_force_std": 16.26,  "y_force": -8.579, "y_force_std": 16.51,  "z_force": 36.69,  "z_force_std": 13.03},
    {"test_id": "6",   "rpm": 150, "feed_rate": 15, "torque": -1.914, "torque_std": 0.455,  "x_force": -1.068, "x_force_std": 16.79,  "y_force": -11.66, "y_force_std": 15.76,  "z_force": 34.43,  "z_force_std": 13.16},
    
    {"test_id": "7",   "rpm": 200, "feed_rate": 15, "torque": -1.543, "torque_std": 0.49,   "x_force": -2.676, "x_force_std": 25.18,  "y_force": -8.728, "y_force_std": 19.53,  "z_force": 31.796, "z_force_std": 20.9},
    {"test_id": "8",   "rpm": 200, "feed_rate": 17, "torque": -2.115, "torque_std": 0.485,   "x_force": -0.588, "x_force_std": 27.66,  "y_force": -9.072, "y_force_std": 23.12,  "z_force": 38.92,  "z_force_std": 21.79},
    {"test_id": "9",   "rpm": 200, "feed_rate": 20, "torque": -1.384, "torque_std": 0.437,  "x_force": -0.967, "x_force_std": 23.6,   "y_force": -4.64,  "y_force_std": 22.73,  "z_force": 25.05,  "z_force_std": 20.78},
    
    {"test_id": "10",  "rpm": 250, "feed_rate": 18, "torque": -1.42,  "torque_std": 0.669,  "x_force": -2.025, "x_force_std": 26.39,  "y_force": -5.512, "y_force_std": 24.98,  "z_force": 26.5,   "z_force_std": 20.73},
    {"test_id": "11",  "rpm": 250, "feed_rate": 22, "torque": -2.244, "torque_std": 0.678,  "x_force": -0.149,  "x_force_std": 29.58,  "y_force": -14.89, "y_force_std": 36.1,  "z_force": 40.9,   "z_force_std": 25.39},
    {"test_id": "12",  "rpm": 250, "feed_rate": 25, "torque": -1.697, "torque_std": 0.69,   "x_force": -0.769, "x_force_std": 28.02,  "y_force": -8.925, "y_force_std": 30.66,  "z_force": 29.97,  "z_force_std": 23.54}
]

# --- 2. DATAFRAME GENERATION & PROCESSING ---
df = pd.DataFrame(test_records)

# Filter for tracking active cutting metrics (Test IDs >= 1)
df_cutting = df[df['test_id'].astype(float) >= 1.0].copy()

# --- 3. SEPARATED PLOTTING BY RPM GROUP ---
rpm_groups = sorted(df_cutting['rpm'].unique())

# Setup a 2x2 multi-panel layout
fig, axes = plt.subplots(3, 1, figsize=(14, 10))
axes = axes.flatten()

# Group colors systematically
colors = {100: 'tab:blue', 150: 'tab:green', 200: 'tab:orange', 250: 'tab:red'}

for rpm_val in sorted(df_cutting['rpm'].unique()):
    sub_set = df_cutting[df_cutting['rpm'] == rpm_val].sort_values('feed_rate')
    c = colors[rpm_val]
    
    # X-Force: Dashed line with Circles
    axes[0].errorbar(sub_set['feed_rate'], sub_set['x_force'], yerr=sub_set['x_force_std'], 
                 fmt='^-', color=c, capsize=3, label=f'{rpm_val} RPM (X-Force)')
    
    # Y-Force: Dotted line with Squares
    axes[1].errorbar(sub_set['feed_rate'], sub_set['y_force'], yerr=sub_set['y_force_std'], 
                 fmt='^-', color=c, capsize=3, label=f'{rpm_val} RPM (Y-Force)')
    
    # Z-Force: Solid line with Triangles
    axes[2].errorbar(sub_set['feed_rate'], sub_set['z_force'], yerr=sub_set['z_force_std'], 
                 fmt='^-', color=c, capsize=3, label=f'{rpm_val} RPM (Z-Force)')

# --- AXIS 0: X-FORCE ---
axes[0].set_title('Comparison of Force (X) vs Speed across RPM Groups', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Feed Rate Speed (mm/s)', fontsize=12)
axes[0].set_ylabel('Force Value (N)', fontsize=12)
axes[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
axes[0].grid(True, linestyle='--', alpha=0.5)

# --- AXIS 1: Y-FORCE ---
axes[1].set_title('Comparison of Force (Y) vs Speed across RPM Groups', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Feed Rate Speed (mm/s)', fontsize=12)
axes[1].set_ylabel('Force Value (N)', fontsize=12)
axes[1].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
axes[1].grid(True, linestyle='--', alpha=0.5)

# --- AXIS 2: Z-FORCE ---
axes[2].set_title('Comparison of Force (Z) vs Speed across RPM Groups', fontsize=14, fontweight='bold')
axes[2].set_xlabel('Feed Rate Speed (mm/s)', fontsize=12)
axes[2].set_ylabel('Force Value (N)', fontsize=12)
axes[2].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
axes[2].grid(True, linestyle='--', alpha=0.5)

# --- GLOBAL FIGURE FORMATTING ---
plt.tight_layout()  # Formats the whole canvas cleanly once
plt.show()