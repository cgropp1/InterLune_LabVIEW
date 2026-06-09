import numpy as np
import pandas as pd
from nptdms import TdmsFile
from scipy.signal import butter, filtfilt, sosfiltfilt
import matplotlib.pyplot as plt
from scipy.fft import rfft, rfftfreq, irfft

AMPLITUDE_THRESHOLD = .5e-5

STEADY_STATE_DURATION_SEC = 200

def fft_amplitude_threshold_filter(data, fs, amplitude_threshold):
    """
    Applies a Real FFT filter that zeroes out frequency components 
    whose true physical amplitude falls below a given threshold.
    Preserves the DC component (0 Hz).
    
    Parameters:
    -----------
    data : array_like
        The input time-domain signal array.
    fs : float
        The sampling frequency of the data (Hz).
    amplitude_threshold : float
        The minimum physical amplitude required to keep a frequency component.
        
    Returns:
    --------
    reconstructed_signal : ndarray
        The filtered time-domain signal.
    frequencies : ndarray
        The frequency bins associated with the FFT.
    filtered_magnitudes : ndarray
        The true physical magnitudes after thresholding.
    """
    num_samples = len(data)
    sample_spacing = 1.0 / fs
    
    # Step A: Compute the Real FFT
    fft_data = rfft(data)
    frequencies = rfftfreq(num_samples, d=sample_spacing)
    
    # Step B: Scale to true physical amplitude
    magnitudes = np.abs(fft_data) * (2.0 / num_samples)
    
    # Filter out frequencies below the threshold (Keep DC component at index 0)
    filter_mask = magnitudes >= amplitude_threshold
    filter_mask[0] = True 
    
    filtered_fft_data = np.where(filter_mask, fft_data, 0.0)
    
    # Recalculate magnitudes after filtering for plotting
    filtered_magnitudes = np.abs(filtered_fft_data) * (2.0 / num_samples)
    
    # Step C: Reconstruct via IFFT (explicitly forcing original sample length)
    reconstructed_signal = irfft(filtered_fft_data, n=num_samples)
    
    return reconstructed_signal, frequencies, filtered_magnitudes

def butter_lowpass_filter(data, cutoff, fs, order=5):
    # Using 'sos' (second-order sections) for better numerical stability than 'ba'
    sos = butter(order, cutoff, fs=fs, btype='low', output='sos')
    return sosfiltfilt(sos, data)

def butter_bandstop_filter(data, lowcut, highcut, fs, order=5):
    sos = butter(order, [lowcut, highcut], fs=fs, btype='bandstop', output='sos')
    return sosfiltfilt(sos, data)

def find_steady_state_indices(signal, window_size_samples):
    """
    Finds the steady state region by sliding a window across the signal
    and identifying the window with the lowest standard deviation (most stable).
    """
    num_samples = len(signal)
    if num_samples <= window_size_samples:
        raise ValueError("Signal length is shorter than the requested window size.")
        
    # Calculate rolling standard deviation manually for efficiency
    # (We exclude the very beginning/end edges to avoid startup/shutdown transients)
    search_start = int(num_samples * 0.1)  # Skip first 10% of data
    search_end = int(num_samples * 0.9)    # Skip last 10% of data
    
    best_std = float('inf')
    best_start_idx = search_start
    
    for start_idx in range(search_start, search_end - window_size_samples):
        end_idx = start_idx + window_size_samples
        current_std = np.std(signal[start_idx:end_idx])
        
        if current_std < best_std:
            best_std = current_std
            best_start_idx = start_idx
            
    return best_start_idx, best_start_idx + window_size_samples

# 1. Load TDMS Data
# Note: Using raw string (r"...") to handle windows backslashes cleanly
file_path = r"C:\Users\Cole\Documents\GitHub\InterLune_LabVIEW\Interlune_MLSS_Testing\Interlune_MLSS_Test1.1\Combined_Output\Combined_Load_and_Torque.tdms"
tdms_file = TdmsFile.read(file_path)

# Access the first group (equivalent to data{1} in MATLAB)
# Adjust the group name string if your TDMS has a specific group name
group = tdms_file.groups()[0]

# Extract time and convert to seconds
time = group['Time'].data
timeSec = time / 1000.0

# 2. Extract Channels into a dictionary (replacing MATLAB's Force cell array)
# Mapping channels to match your Force{1} to Force{13} indexing (1-based for clarity)
Force = {}
Force[1] = group['Distance'].data       # Y1
Force[5] = group['Untitled 2'].data     # X1
Force[9] = group['Untitled 3'].data     # Z1

Force[2] = group['Untitled 4'].data     # Y2
Force[6] = group['Untitled 5'].data     # X2
Force[10] = group['Untitled 6'].data    # Z2

Force[3] = group['Untitled 7'].data     # Y3
Force[7] = group['Untitled 8'].data     # X3
Force[11] = group['Untitled 9'].data    # Z3

Force[4] = group['Untitled 10'].data    # Y4
Force[8] = group['Untitled 11'].data    # X4
Force[12] = group['Untitled 12'].data   # Z4

Force[13] = group['Untitled 13'].data   # torque

# 3. Center Data Around Zero
for i in range(1, 14):
    meanZero = np.mean(Force[i][0:500])
    Force[i] = Force[i] - meanZero

# 4. Define Filtering Functions
dt = np.mean(np.diff(timeSec))
fs = 1.0 / dt
print(f"Sampling Frequency (fs): {fs}")

fft_analysis_results = {}

for i in range(1, 14):
    Force[i] = butter_lowpass_filter(Force[i], 10,fs)
    Force[i] = butter_bandstop_filter(Force[i], 0.15, 0.2, fs)
    filtered_signal, freqs, filtered_mags = fft_amplitude_threshold_filter(
        data=Force[i], 
        fs=fs, 
        amplitude_threshold=AMPLITUDE_THRESHOLD
    )
    Force[i] = filtered_signal
    fft_analysis_results[i] = {"frequencies": freqs, "magnitudes": filtered_mags}

# 5. Convert Data into Forces and Torques
sumX = (Force[5] * 175923.8) + (Force[6] * 175305.9) + (Force[7] * 183184.3) + (Force[8] * 174613.95)
sumY = (Force[1] * 179223.9) + (Force[2] * 178683.4) + (Force[3] * 178428.8) + (Force[4] * 178179.9)
sumZ = (Force[9] * 191816.6) + (Force[10] * 196106.8) + (Force[11] * 194644.2) + (Force[12] * 195387.14)
torque = Force[13] * 20.0

# 6. Compute Averages (Python uses 0-based indexing)
# Note: indices match MATLAB's 15000:27000 (which is 14999:27000 in Python slice notation)
window_size_samples = int(STEADY_STATE_DURATION_SEC * fs)

# Find the flat region using the Torque profile
startState, endState = find_steady_state_indices(sumZ, window_size_samples)

XSS = sumX[startState:endState]
XAve = np.mean(XSS)
Xstd = np.std(XSS, ddof=1) # ddof=1 matches MATLAB's std(XSS, 1) or default sample std

YSS = sumY[startState:endState]
YAve = np.mean(YSS)
Ystd = np.std(YSS, ddof=0) # ddof=0 matches MATLAB's population std style for default std(YSS)

ZSS = sumZ[startState:endState]
ZAve = np.mean(ZSS)
Zstd = np.std(ZSS, ddof=0)

torqueSS = torque[startState:endState]
torqueAve = np.mean(torqueSS)
torqueStd = np.std(torqueSS, ddof=0)

# Print Results
print(f"Average Torque: {torqueAve:f}")
print(f"Torque Standard Deviation: {torqueStd:f}")
print(f"Average X-Force: {XAve:f}")
print(f"X-Force Standard Deviation: {Xstd:f}")
print(f"Average Y-Force: {YAve:f}")
print(f"Y-Force Standard Deviation: {Ystd:f}")
print(f"Average Z-Force: {ZAve:f}")
print(f"Z-Force Standard Deviation: {Zstd:f}")

# 7. Smooth Force Data
bandStart = 0.1
bandEnd = 4.5

smoothX = butter_bandstop_filter(sumX, bandStart, bandEnd, fs)
smoothY = butter_bandstop_filter(sumY, bandStart, bandEnd, fs)
smoothZ = butter_bandstop_filter(sumZ, bandStart, bandEnd, fs)
smoothTorque = butter_bandstop_filter(torque, bandStart, bandEnd, fs)

# smoothX = sumX
# smoothY = sumY
# smoothZ = sumZ
# smoothTorque = torque

# Savitzky-Golay filter setup
# MATLAB's smoothdata(..., 'sgolay', fs) approximates a window size. 
# We'll use a standard window length (must be odd) and polynomial order (typically 2).
window_len = int(fs) if int(fs) % 2 != 0 else int(fs) + 1 
if window_len < 3: window_len = 5 # Ensure valid window size

from scipy.signal import savgol_filter
smoothX2 = savgol_filter(smoothX, window_length=window_len, polyorder=2)
smoothY2 = savgol_filter(smoothY, window_length=window_len, polyorder=2)
smoothZ2 = savgol_filter(smoothZ, window_length=window_len, polyorder=2)
smoothTorque2 = savgol_filter(smoothTorque, window_length=window_len, polyorder=2)

# 8. Plotting (Equivalent to tiledlayout(4,1))
fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)

# Plot 1: Torque
axs[0].plot(timeSec, torque, color='#80B3FF', label='Forces')
axs[0].plot(timeSec, smoothTorque2, color='blue', label='Trendline')
axs[0].axhline(torqueAve, color='red', label='Steady State Average')
axs[0].set_title('Torque Plot')
axs[0].set_ylabel('N/m')
axs[0].legend()

# Plot 2: X Plot
axs[1].plot(timeSec, sumX, color='#80B3FF')
axs[1].plot(timeSec, smoothX2, color='blue')
axs[1].axhline(XAve, color='red')
axs[1].set_title('X Plot')
axs[1].set_ylabel('N')

# Plot 3: Y Plot
axs[2].plot(timeSec, sumY, color='#80B3FF')
axs[2].plot(timeSec, smoothY2, color='blue')
axs[2].axhline(YAve, color='red')
axs[2].set_title('Y Plot')
axs[2].set_ylabel('N')

# Plot 4: Z Plot
axs[3].plot(timeSec, sumZ, color='#80B3FF')
axs[3].plot(timeSec, smoothZ2, color='blue')
axs[3].axhline(ZAve, color='red')
axs[3].set_title('Z Plot')
axs[3].set_xlabel('Time (S)')
axs[3].set_ylabel('N')

try:
    plt.tight_layout()
    plt.show()
except KeyboardInterrupt:
    print()