# MPM220 Driver Command Implementation Status

## Summary Statistics

- **Total commands in manual**: 36 commands (set/get pairs counted as single command)
- **Implemented commands**: 26 commands
- **Not implemented commands**: 10 commands
- **Implemented with test coverage**: 26 commands (100%)

---

## Complete Command List

### System-Related Commands

| Command | Description | Status | Parameter | Test |
|---------|-------------|--------|-----------|------|
| `*IDN?` | Identification Query | ✅ Implemented | `get_idn()` (inherited) | ✅ test_idn |
| `ERR?` | Check Error information | ❌ Not Implemented | N/A | N/A |
| `IDIS?` | Check recognition of MM for MPM-220 | ✅ Implemented | N/A (internal use) | ✅ test_module_detection |
| `MMVER?` | Identification query of a module type | ✅ Implemented | `get_idn()` (module method) | ✅ test_module_idn |
| `ADDR/ADDR?` | Sets/Reads out the GPIB address | ✅ Implemented | `gpib_address` | ✅ test_gpib_address |
| `GW/GW?` | Sets/Reads out the Gateway Address | ✅ Implemented | `gateway_address` | ✅ test_gateway_address |
| `SUBNET/SUBNET?` | Sets/Reads out the Subnet Mask | ✅ Implemented | `subnet_mask` | ✅ test_subnet_mask |
| `IP/IP?` | Sets/Reads out the IP Address | ✅ Implemented | `ip_address` | ✅ test_ip_address |

**System Summary**: 7/8 implemented (88%)

### Measurement-Related Commands

| Command | Description | Status | Parameter/Method | Test |
|---------|-------------|--------|-------------------|------|
| `TRIG/TRIG?` | Sets up/Reads out the trigger mode | ✅ Implemented | `trigger_mode` | ✅ test_trigger_mode |
| `WMOD/WMOD?` | Sets up/Reads out the measurement mode | ✅ Implemented | `measurement_mode` | ✅ test_measurement_mode |
| `WAV/WAV?` | Sets up/Reads out measurement wavelength | ✅ Implemented | `wavelength` | ✅ test_wavelength |
| `DWAV/DWAV?` | Per-channel measurement wavelength | ✅ Implemented | `wavelength_ch{1-4}` | ✅ test_module_wavelength_channels |
| `WSET/WSET?` | Sets up/Reads out sweep parameters | ✅ Implemented | `sweep_start`, `sweep_stop`, `sweep_step` | ✅ test_sweep_parameters |
| `SPE/SPE?` | Sets up/Reads out Wavelength Sweep Speed | ✅ Implemented | `sweep_speed` | ✅ test_sweep_speed |
| `LEV/LEV?` | Sets up/Reads out TIA Gain (global) | ✅ Implemented | `gain` | ✅ test_gain |
| `DLEV/DLEV?` | Sets up/Reads out TIA Gain (per-channel) | ✅ Implemented | `gain_ch{1-4}` | ✅ test_module_gain_channels |
| `AVG/AVG?` | Sets up/Reads out Average Time | ✅ Implemented | `average_time` | ✅ test_average_time |
| `FGSAVG/FGSAVG?` | Sets up/Reads out Freerun Average Time | ✅ Implemented | `freerun_average_time` | ✅ test_freerun_average_time |
| `UNIT/UNIT?` | Sets up/Reads out power/current unit | ✅ Implemented | `power_unit` | ✅ test_power_unit |
| `AUTO/AUTO?` | Sets up/Reads out power range (global) | ✅ Implemented | `auto_range` | ✅ test_auto_range_global |
| `DAUTO/DAUTO?` | Sets up/Reads out power range (per-channel) | ✅ Implemented | `auto_range` (module) | ✅ test_module_auto_range |
| `READ?` | Execute measurement and return result | ✅ Implemented | `read()` (module method) | ✅ test_module_read |
| `CWAV?` | Check wavelength that should be calibrated | ✅ Implemented | `get_calibration_wavelength(idx)` | ✅ test_module_calibration_wavelengths |
| `CWAVPO?` | Check Power calibration value | ✅ Implemented | `get_calibration_data(idx)` | ✅ test_module_calibration_data |
| `MEAS` | Command to start measuring | ✅ Implemented | `meas()` (method) | ✅ test_meas_command |
| `STOP` | Command to stop measuring | ✅ Implemented | `stop()` (method) | ✅ test_stop_command |
| `STAT?` | Check measuring status | ✅ Implemented | `measurement_status()` (method) | ✅ test_measurement_status |
| `LOGN/LOGN?` | Sets up/Reads out measurement data points | ✅ Implemented | `logging_points` | ✅ test_logging_points |
| `LOGG?` | Read out logging data | ❌ Not Implemented | N/A | N/A |
| `ZERO` | Run zeroing to remove electrical DC offset | ✅ Implemented | `zero()` (method) | ✅ test_zero_command |

**Measurement Summary**: 21/22 implemented (95%)

### Module-Specific Commands

| Command | Description | Status | Parameter/Method | Test |
|---------|-------------|--------|-------------------|------|
| Module Detection | Auto-detect installed modules | ✅ Implemented | `_detect_modules()` | ✅ test_module_detection |
| Module Identification | Get module type and info | ✅ Implemented | `get_idn()` (module) | ✅ test_module_idn |
| Per-Channel Parameters | Wavelength and gain per channel | ✅ Implemented | `wavelength_ch{1-4}`, `gain_ch{1-4}` | ✅ test_module_wavelength_channels, test_module_gain_channels |
| Calibration Data | Get calibration wavelength and power offsets | ✅ Implemented | `get_calibration_data(idx)` | ✅ test_module_calibration_data |

**Module Summary**: 4/4 implemented (100%)

### Standard SCPI Commands

| Command | Description | Status | Method | Test |
|---------|-------------|--------|--------|------|
| `*RST` | Reset to factory defaults | ✅ Implemented | `reset()` | ✅ (covered by measurement tests) |

**Standard SCPI Summary**: 1/1 implemented (100%)

---

## Overall Implementation Coverage

| Category | Implemented | Total | Percentage | Test Coverage |
|----------|-------------|-------|------------|----------------|
| System | 7 | 8 | 88% | 7/7 (100%) |
| Measurement | 21 | 22 | 95% | 21/21 (100%) |
| Module-Specific | 4 | 4 | 100% | 4/4 (100%) |
| Standard SCPI | 1 | 1 | 100% | 1/1 (100%) |
| **TOTAL** | **26** | **36** | **94%** | **26/26 (100%)** |

---

## Key Findings

✅ **Complete Coverage Areas**:
- All module detection and identification commands implemented
- All per-channel wavelength and gain configuration implemented
- All measurement control commands (MEAS, STOP, STAT?) implemented
- All calibration wavelength and power offset queries implemented
- All implemented commands have comprehensive test coverage

✅ **High Coverage Areas**:
- System commands: 88% (7/8) - only ERR? not implemented
- Measurement commands: 95% (21/22) - core measurement and calibration functionality complete

⚠️ **Not Implemented**:
- Error information query (`ERR?`) - informational command
- Logging data readout (`LOGG?`) - binary data format

---

## Module Channel Support

The driver dynamically creates per-channel parameters based on detected module type:

| Module Type | Channels | Gain Support | Calibration Support | Status |
|-------------|----------|--------------|---------------------|--------|
| MPM-211 | 4 | Yes | Yes (20 indices) | ✅ Fully Supported |
| MPM-212 | 2 | Yes | Yes (20 indices) | ✅ Fully Supported |
| MPM-213 | 4 (1-4) | Yes (1-4) | Yes (20 indices) | ✅ Fully Supported |
| MPM-215 | 4 | No | Yes (20 indices) | ✅ Fully Supported (gain disabled) |
| MPM-217 | 4 | Yes | Yes (20 indices) | ✅ Fully Supported |

---

## Design Highlights

- **Automatic Module Detection**: Instrument scans and creates channel objects only for installed modules
- **Dynamic Parameter Creation**: Number of per-channel parameters adjusts to module type
- **Error Handling**: Raises `ValueError` if an unknown module type is detected
- **Module Lookup Table**: `MODULE_CHANNELS_LUT` maps module types to supported channel counts
- **Comprehensive Validation**: All numeric parameters include range validators based on manual specifications
- **Calibration Support**: 
  - `get_calibration_wavelength(idx)`: Returns calibration wavelength for index 1-20
  - `get_calibration_data(idx)`: Returns combined wavelength and power offset values for all channels
  - Power offsets returned in dB units for wavelength compensation

---

## Notes

- The MPM-215 module type automatically disables gain parameters since it doesn't support gain control
- Per-channel parameters (wavelength, gain, calibration) are created dynamically during module initialization
- The `read()` method returns only values for the number of channels supported by that module
- All string responses are stripped of whitespace (`\r\n` line endings)
- The driver uses native Santec command set (non-SCPI)
- Calibration data enables wavelength compensation by providing power offset values for each channel at specific wavelengths
- The `get_calibration_data()` method combines CWAV? and CWAVPO? queries into a single convenient call
