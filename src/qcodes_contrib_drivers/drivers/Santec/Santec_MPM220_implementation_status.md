# MPM220 Driver Command Implementation Status

## Summary Statistics

- **Total commands in manual**: 30 commands (22 measurement + 8 system)
- **Implemented commands**: 29 commands
- **Not implemented commands**: 1 command
- **Implementation coverage**: 97%
- **Test coverage**: 29/29 implemented commands (100%)

---

## Complete Command List

### System-Related Commands

| Command          | Description                           | Status        | Parameter               | Test                  |
|------------------|---------------------------------------|---------------|-------------------------|-----------------------|
| `*IDN?`          | Identification Query                  | ✅ Implemented | `get_idn()` (inherited) | ✅ test_idn            |
| `ERR?`           | Check Error information               | ✅ Implemented | `error`                 | ✅ test_error          |
| `IDIS?`          | Check recognition of MM for MPM-220   | ✅ Implemented | `module_status`         | ✅ test_module_status  |
| `MMVER?`         | Identification query of a module type | ✅ Implemented | `module.get_idn()`      | ✅ test_module_idn     |
| `ADDR/ADDR?`     | Sets/Reads out the GPIB address       | ✅ Implemented | `gpib_address`          | ✅ test_gpib_address   |
| `GW/GW?`         | Sets/Reads out the Gateway Address    | ✅ Implemented | `gateway_address`       | ✅ test_gateway_address|
| `SUBNET/SUBNET?` | Sets/Reads out the Subnet Mask        | ✅ Implemented | `subnet_mask`           | ✅ test_subnet_mask    |
| `IP/IP?`         | Sets/Reads out the IP Address         | ✅ Implemented | `ip_address`            | ✅ test_ip_address     |

**System Summary**: 8/8 implemented (100%)

### Measurement-Related Commands

| Command          | Description                                | Status            | Parameter/Method                          | Test                                    |
|------------------|--------------------------------------------|-------------------|-------------------------------------------|-----------------------------------------|
| `TRIG/TRIG?`     | Sets up/Reads out the trigger mode         | ✅ Implemented     | `trigger_mode`                            | ✅ test_trigger_mode                     |
| `WMOD/WMOD?`     | Sets up/Reads out the measurement mode     | ✅ Implemented     | `measurement_mode`                        | ✅ test_measurement_mode                 |
| `WAV/WAV?`       | Sets up/Reads out measurement wavelength   | ✅ Implemented     | `wavelength`                              | ✅ test_wavelength                       |
| `DWAV/DWAV?`     | Per-channel measurement wavelength         | ✅ Implemented     | `ch{N}.wavelength`                        | ✅ test_module_wavelength_channels       |
| `WSET/WSET?`     | Sets up/Reads out sweep parameters         | ✅ Implemented     | `sweep_start`, `sweep_stop`, `sweep_step` | ✅ test_sweep_parameters                 |
| `SPE/SPE?`       | Sets up/Reads out Wavelength Sweep Speed   | ✅ Implemented     | `sweep_speed`                             | ✅ test_sweep_speed                      |
| `LEV/LEV?`       | Sets up/Reads out TIA Gain (global)        | ✅ Implemented     | `gain`                                    | ✅ test_gain                             |
| `DLEV/DLEV?`     | Sets up/Reads out TIA Gain (per-channel)   | ✅ Implemented     | `ch{N}.gain`                              | ✅ test_module_gain_channels             |
| `AVG/AVG?`       | Sets up/Reads out Average Time             | ✅ Implemented     | `average_time`                            | ✅ test_average_time                     |
| `FGSAVG/FGSAVG?` | Sets up/Reads out Freerun Average Time     | ✅ Implemented     | `freerun_average_time`                    | ✅ test_freerun_average_time             |
| `UNIT/UNIT?`     | Sets up/Reads out power/current unit       | ✅ Implemented     | `power_unit`                              | ✅ test_power_unit                       |
| `AUTO/AUTO?`     | Sets up/Reads out power range (global)     | ✅ Implemented     | `auto_range`                              | ✅ test_auto_range_global                |
| `DAUTO/DAUTO?`   | Sets up/Reads out power range (per-module) | ✅ Implemented     | `module.auto_range`                       | ✅ test_module_auto_range                |
| `READ?`          | Execute measurement and return result      | ✅ Implemented     | `module.read()`                           | ✅ test_module_read                      |
| `CWAV?`          | Check wavelength that should be calibrated | ✅ Implemented     | `module.calibration_wavelength`           | ✅ test_module_calibration_wavelengths   |
| `CWAVPO?`        | Check Power calibration value              | ✅ Implemented     | `ch{N}.calibration_power_offset`          | ✅ test_module_calibration_power_offsets |
| `MEAS`           | Command to start measuring                 | ✅ Implemented     | `meas()`                                  | ✅ test_meas_command                     |
| `STOP`           | Command to stop measuring                  | ✅ Implemented     | `stop()`                                  | ✅ test_stop_command                     |
| `STAT?`          | Check measuring status                     | ✅ Implemented     | `measurement_status()`                    | ✅ test_measurement_status               |
| `LOGN/LOGN?`     | Sets up/Reads out measurement data points  | ✅ Implemented     | `logging_points`                          | ✅ test_logging_points                   |
| `LOGG?`          | Read out logging data                      | ❌ Not Implemented | N/A                                       | N/A                                     |
| `ZERO`           | Run zeroing to remove electrical DC offset | ✅ Implemented     | `zero()`                                  | ✅ test_zero_command                     |

**Measurement Summary**: 21/22 implemented (95%)

---

## Overall Implementation Coverage

| Category    | Implemented | Total  | Percentage | Test Coverage    |
|-------------|-------------|--------|------------|------------------|
| System      | 8           | 8      | 100%       | 8/8 (100%)       |
| Measurement | 21          | 22     | 95%        | 21/21 (100%)     |
| **TOTAL**   | **29**      | **30** | **97%**    | **29/29 (100%)** |

---

## Architecture Overview

### Class Hierarchy

- **SantecMPM220** (IPInstrument)
  - Global parameters: wavelength, sweep, gain, averaging, units, range, trigger, logging
  - Methods: meas(), stop(), zero(), reset(), measurement_status(), set_sweep_parameters()
  - **modules** (ChannelList of _SantecMPMxxxModule)
    - **_SantecMPMxxxModule** (InstrumentChannel) - Base class for measurement modules
      - Module parameters: auto_range, calibration_wavelength
      - Methods: read(), get_idn()
      - **channels** (ChannelList of SantecMPMChannel)
        - **SantecMPMChannel** (InstrumentChannel) - Per-channel measurement port
          - Channel parameters: wavelength, gain (if supported), calibration_power_offset
          - Supports 1-4 channels per module depending on module type

### Module Type Support

| Module Type | Channels                     | Gain Support | Calibration Support | Status                            |
|-------------|------------------------------|--------------|---------------------|-----------------------------------|
| MPM-211     | 4 optical power              | Yes (1-5)    | Yes (20 indices)    | ✅ Fully Supported                 |
| MPM-212     | 2 optical power              | Yes (1-5)    | Yes (20 indices)    | ✅ Fully Supported                 |
| MPM-213     | 4 electrical current         | Yes (1-4)    | Yes (20 indices)    | ✅ Fully Supported                 |
| MPM-215     | 4 optical power (high range) | No           | Yes (20 indices)    | ✅ Fully Supported (gain disabled) |
| MPM-217     | 4 optical power              | Yes (1-5)    | Yes (20 indices)    | ✅ Fully Supported                 |

---

## Key Implementation Details

### Per-Channel Parameters

All channels support:
- **wavelength**: Set/get measurement wavelength via DWAV/DWAV?
- **gain**: Set/get TIA gain via DLEV/DLEV? (not available on MPM-215)
- **calibration_power_offset**: Read-only power calibration values via CWAVPO?
  - Implemented as `ParameterWithSetpoints` with 20 calibration indices
  - Retrieves calibration data for all 20 wavelength indices at once

### Sweep Parameters with Read-Back

The WSET/WSET? command sets/reads all three sweep parameters simultaneously (start, stop, step).
The driver implements this as three separate parameters with custom setter methods:

- `sweep_start`: Set/get sweep start wavelength
- `sweep_stop`: Set/get sweep stop wavelength
- `sweep_step`: Set/get sweep step

Each setter method:
1. Queries current WSET? values
2. Preserves unchanged parameters
3. Updates only the requested parameter
4. Writes the complete WSET command

Additionally, a helper method `set_sweep_parameters(start, stop, step)` is provided to set all three parameters in a single command, which is more efficient than setting them individually.

### Calibration Data Structure

- **module.calibration_wavelength**: Returns numpy array of 20 wavelength values (nm)
- **ch{N}.calibration_power_offset**: Returns numpy array of 20 power offset values (dB)
  - Linked via ParameterWithSetpoints to module.calibration_wavelength setpoints
  - Allows lookup of power offsets for specific wavelength indices

### Automatic Module Detection

During initialization, the driver:
1. Queries IDIS? to check which modules are present (0-4)
2. For each present module, queries MMVER? to get module type
3. Creates appropriate module class instance (MPM-211, MPM-212, etc.)
4. Dynamically creates channel submodules with correct parameter sets
5. Logs detected modules with serial numbers and firmware versions

---

## Test Coverage Summary

**Total Test Functions**: 30 test functions covering 29 commands/features

✅ **System Parameters** (8 tests):
- test_idn, test_module_idn, test_module_status, test_error
- test_gpib_address, test_ip_address, test_gateway_address, test_subnet_mask

✅ **Measurement Configuration** (10 tests):
- test_measurement_mode (5 modes via parametrize)
- test_wavelength
- test_sweep_parameters
- test_sweep_speed (3 speeds via parametrize)
- test_average_time (3 values via parametrize)
- test_freerun_average_time (3 values via parametrize)
- test_power_unit (2 units via parametrize)
- test_trigger_mode (2 modes via parametrize)
- test_logging_points (3 values via parametrize)

✅ **Gain and Range** (3 tests):
- test_gain
- test_auto_range_global (2 modes via parametrize)
- test_module_auto_range (2 modes via parametrize)

✅ **Per-Channel Parameters** (2 tests):
- test_module_wavelength_channels
- test_module_gain_channels

✅ **Calibration** (2 tests):
- test_module_calibration_wavelengths
- test_module_calibration_power_offsets

✅ **Control and Status** (5 tests):
- test_measurement_status
- test_module_read
- test_zero_command
- test_meas_command
- test_stop_command

✅ **Additional Features** (1 test):
- test_reset_command (bonus - *RST not in command list but implemented)

✅ **Module Detection**:
- Automatically tested via fixture initialization

---

## Not Implemented Features

| Command | Reason                                           |
|---------|--------------------------------------------------|
| `LOGG?` | Binary data format; requires specialized parsing |

---

## Notes

- All parameters include proper validators based on manual specifications
- All string responses are stripped of leading/trailing whitespace
- The driver uses native Santec command set (non-SCPI)
- Module gain control is automatically disabled for MPM-215 (no _max_gain)
- Calibration wavelength indices are 1-based in commands, internally stored as 0-19
- All measurement commands have test coverage with real hardware validation
- The `error` parameter returns a dictionary with keys: `code` (int) and `message` (str)
- The `reset()` method implements *RST command (bonus feature not in manual command list)
