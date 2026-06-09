import numpy as np
import matplotlib.pyplot as plt
from nptdms import TdmsFile
from scipy.fft import rfft, rfftfreq, irfft

# ==========================================
# 1. CONFIGURATION & CONFIGURABLE PARAMETERS
# ==========================================
TDMS_FILE_PATH = r"C:\Users\Cole\Documents\GitHub\InterLune_LabVIEW\Interlune_MLSS_Testing\Interlune_MLSS_Test1\Combined_Output\Combined_Load_and_Torque.tdms"
GROUP_NAME = "SonarAlt"  # Change to your TDMS group name
TIME_CHANNEL = "Time"  # Change to your time column name

# List your 13 sensor channel names as they appear in the TDMS file
SENSOR_CHANNELS = [
    "Distance",
    "Untitled 2",
    "Untitled 3",
    "Untitled 4",
    "Untitled 5",
    "Untitled 6",
    "Untitled 7",
    "Untitled 8",
    "Untitled 9",
    "Untitled 10",
    "Untitled 11",
    "Untitled 12",
    "Untitled 13",
]

# Set your amplitude threshold for filtering
# Any frequency component with a magnitude below this will be eliminated
AMPLITUDE_THRESHOLD = 0.5

# ==========================================
# 2. LOAD TDMS DATA
# ==========================================
print(f"Loading {TDMS_FILE_PATH}...")
tdms_file = TdmsFile.read(TDMS_FILE_PATH)
group = tdms_file[GROUP_NAME]

# Extract time array
time_data = group[TIME_CHANNEL].data
num_samples = len(time_data)

# Calculate sampling rate (Fs = 1 / delta_t)
# Assumes uniform sampling
sample_spacing = time_data[1] - time_data[0]
sampling_rate = 1.0 / sample_spacing

print(f"Loaded {num_samples} samples at {sampling_rate:.2f} Hz.")

# Dictionaries to hold the final processed signals and spectrum results
processed_signals = {}
fft_results = {}

# ==========================================
# 3. FFT -> FILTER -> IFFT PIPELINE
# ==========================================
for sensor in SENSOR_CHANNELS:
    sensor_data = group[sensor].data

    # Step A: Compute the Real FFT
    fft_data = rfft(sensor_data)
    frequencies = rfftfreq(num_samples, d=sample_spacing)

    # Step B: Scale to true physical amplitude
    # True Amplitude = |FFT| * (2.0 / N)
    magnitudes = np.abs(fft_data) * (2.0 / num_samples)

    # Filter out frequencies below the threshold (Keep DC component at index 0)
    filter_mask = magnitudes >= AMPLITUDE_THRESHOLD
    filter_mask[0] = True 
    
    filtered_fft_data = np.where(filter_mask, fft_data, 0.0)
    # Recalculate magnitudes after filtering for plotting
    filtered_magnitudes = np.abs(filtered_fft_data) * (2.0 / num_samples)

    # Step C: Reconstruct via IFFT
    reconstructed_signal = irfft(filtered_fft_data, n=num_samples)

    # Save data for plotting
    processed_signals[sensor] = reconstructed_signal
    fft_results[sensor] = {
        "frequencies": frequencies,
        "filtered_magnitudes": filtered_magnitudes
    }

print("Processing complete. Generating plots...")

# ==========================================
# 4. VISUALIZE ALL SENSORS (FILTERED FFT)
# ==========================================
fig, axes = plt.subplots(nrows=5, ncols=3, figsize=(16, 20), sharex=False)
axes = axes.flatten()  # Flatten grid to a 1D array for easy iteration

for i, sensor in enumerate(SENSOR_CHANNELS):
    ax = axes[i]
    
    freqs = fft_results[sensor]["frequencies"]
    mags = fft_results[sensor]["filtered_magnitudes"]
    
    # FIXED HERE: Removed 'use_line_collection=True' to avoid TypeError
    ax.stem(freqs, mags, linefmt='b-', markerfmt='bo', basefmt='r-')
    
    # Visual adjustments to ensure readability
    ax.set_title(f"{sensor} - Remaining FFT", fontsize=11, fontweight='bold')
    ax.set_ylabel("Amplitude", fontsize=9)
    ax.set_xlabel("Frequency (Hz)", fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.6)

# Hide the last 2 unused subplots in the 5x3 grid
for j in range(len(SENSOR_CHANNELS), len(axes)):
    axes[j].axis('off')

# Automatically adjust spacing to completely prevent label truncation or overlap
plt.tight_layout()

# Save the plot layout
output_plot_path = "all_sensors_filtered_fft.png"
plt.savefig(output_plot_path, dpi=300)
print(f"FFT plot saved successfully as '{output_plot_path}'")
plt.show()