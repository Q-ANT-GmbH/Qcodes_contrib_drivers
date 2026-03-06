"""Tests for Santec MPM-220 Optical Power Meter driver.

These tests require a connected MPM-220 instrument.
Update the fixture address/port for your setup.

Following the test structure from test_Santec_TSL570.py, each parameter
is tested individually to verify proper communication with the instrument.
"""

import re
import time

import pytest

from qcodes_contrib_drivers.drivers.Santec import SantecMPM220


@pytest.fixture(scope="module")
def driver():
    """Create MPM-220 instrument instance."""
    mpm = SantecMPM220("MPM220", address="192.168.50.33", port=5000)
    yield mpm
    mpm.close()


def _first_module(driver: SantecMPM220):
    """Get the first detected measurement module."""
    if len(driver.modules) == 0:
        pytest.skip("No modules detected in MPM-220 chassis.")
    return driver.modules[0]


# System/Network Parameters
def test_idn(driver):
    """Test instrument identification query (*IDN?)."""
    idn_dict = driver.get_idn()
    assert "model" in idn_dict
    assert idn_dict["model"].startswith("MPM")


def test_module_idn(driver):
    """Test module identification via get_idn()."""
    module = _first_module(driver)
    idn_dict = module.get_idn()
    assert "vendor" in idn_dict
    assert "model" in idn_dict
    assert "serial" in idn_dict
    assert "firmware" in idn_dict
    assert idn_dict["model"].startswith("MPM-")


def test_gpib_address(driver):
    """Test GPIB address parameter (ADDR/ADDR?)."""
    current = driver.gpib_address()
    driver.gpib_address(current)
    assert driver.gpib_address() == current


def test_ip_address(driver):
    """Test IP address readout (IP?)."""
    ip_addr = driver.ip_address()
    assert isinstance(ip_addr, str)
    assert re.match(r"^\d+\.\d+\.\d+\.\d+$", ip_addr)


def test_gateway_address(driver):
    """Test gateway address parameter (GW/GW?)."""
    gw_addr = driver.gateway_address()
    assert isinstance(gw_addr, str)
    # Gateway might be empty or valid IP format
    if gw_addr.strip():
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", gw_addr)


def test_subnet_mask(driver):
    """Test subnet mask parameter (SUBNET/SUBNET?)."""
    subnet_mask = driver.subnet_mask()
    assert isinstance(subnet_mask, str)
    assert re.match(r"^\d+\.\d+\.\d+\.\d+$", subnet_mask)


# Measurement Mode Parameters
def test_measurement_mode(driver):
    """Test measurement mode parameter (WMOD/WMOD?)."""
    for mode in ["CONST1", "SWEEP1", "CONST2", "SWEEP2", "FREERUN"]:
        driver.measurement_mode(mode)
        assert driver.measurement_mode() == mode


# Wavelength Parameters
def test_wavelength(driver):
    """Test global wavelength parameter (WAV/WAV?)."""
    test_wavelength = 1550.0  # nm
    driver.wavelength(test_wavelength)
    assert driver.wavelength() == pytest.approx(test_wavelength, abs=1e-3)


def test_sweep_parameters(driver):
    """Test sweep wavelength parameters (WSET/WSET?)."""
    start = 1520.0  # nm
    stop = 1570.0  # nm
    step = 0.05  # nm
    driver.set_sweep_parameters(start=start, stop=stop, step=step)
    assert driver.sweep_start() == pytest.approx(start, abs=1e-3)
    assert driver.sweep_stop() == pytest.approx(stop, abs=1e-3)
    assert driver.sweep_step() == pytest.approx(step, abs=1e-3)


def test_sweep_speed(driver):
    """Test sweep speed parameter (SPE/SPE?)."""
    for speed in [1.0, 5.0, 50.0]:
        driver.sweep_speed(speed)
        assert driver.sweep_speed() == pytest.approx(speed, abs=1e-3)


# Gain Parameters
def test_gain(driver):
    """Test global TIA gain parameter (LEV/LEV?)."""
    module = _first_module(driver)
    if module._module_type == "MPM-215":
        pytest.skip("MPM-215 does not support gain control (LEV/DLEV commands).")

    for gain in [1, 3, 5]:
        driver.gain(gain)
        assert driver.gain() == gain


def test_module_wavelength_channels(driver):
    """Test per-channel wavelength parameters (DWAV/DWAV?) for all available channels."""
    module = _first_module(driver)
    num_channels = module._num_channels

    for ch in range(1, num_channels + 1):
        test_wl = 1550.0 + ch  # nm
        channel = module.channels[ch - 1]
        channel.wavelength(test_wl)
        assert channel.wavelength() == pytest.approx(test_wl, abs=1e-3)


def test_module_gain_channels(driver):
    """Test per-channel gain parameters (DLEV/DLEV?) for all available channels."""
    module = _first_module(driver)

    if module._module_type == "MPM-215":
        pytest.skip("MPM-215 does not support gain control (DLEV).")

    num_channels = module._num_channels
    max_gain = 4 if module._module_type == "MPM-213" else 5

    for ch in range(1, num_channels + 1):
        channel = module.channels[ch - 1]
        for gain in [1, 3, max_gain]:
            channel.gain(gain)
            assert channel.gain() == gain


# Averaging Parameters
def test_average_time(driver):
    """Test averaging time parameter (AVG/AVG?)."""
    for avg_time in [0.1, 1.0, 10.0]:
        driver.average_time(avg_time)
        assert driver.average_time() == pytest.approx(avg_time, abs=1e-2)


def test_freerun_average_time(driver):
    """Test freerun averaging time parameter (FGSAVG/FGSAVG?)."""
    for avg_time in [0.1, 1.0, 10.0]:
        driver.freerun_average_time(avg_time)
        assert driver.freerun_average_time() == pytest.approx(avg_time, abs=1e-2)


# Power Unit Parameter
def test_power_unit(driver):
    """Test power unit selection parameter (UNIT/UNIT?)."""
    for unit in ["dBm", "mW"]:
        driver.power_unit(unit)
        assert driver.power_unit() == unit


# Auto-Range Parameters
def test_auto_range_global(driver):
    """Test global auto-range mode parameter (AUTO/AUTO?)."""
    for mode in ["AUTO", "MANUAL"]:
        driver.auto_range(mode)
        assert driver.auto_range() == mode


def test_module_auto_range(driver):
    """Test per-module auto-range parameter (DAUTO/DAUTO?)."""
    module = _first_module(driver)
    for mode in ["AUTO", "MANUAL"]:
        module.auto_range(mode)
        assert module.auto_range() == mode


def test_module_calibration_wavelengths(driver):
    """Test calibration wavelength readout (CWAV?) using setpoints."""
    module = _first_module(driver)

    # Query first few calibration wavelengths (indices 1-5) using setpoint
    for idx in range(1, 6):
        module.calibration_index(idx)
        wavelength = module.calibration_wavelength()
        assert isinstance(wavelength, float)
        assert 1250 <= wavelength <= 1630


def test_module_calibration_power_offsets(driver):
    """Test calibration power offset readout (CWAVPO?) using setpoints."""
    module = _first_module(driver)
    num_channels = module._num_channels

    # Query calibration data for index 1 using setpoint
    module.calibration_index(1)

    for ch in range(1, num_channels + 1):
        param_name = f"calibration_power_offset_ch{ch}"
        power_offset = getattr(module, param_name)()

        # Power offset should be a reasonable dB value
        assert isinstance(power_offset, float)
        assert -50 <= power_offset <= 50  # Reasonable dB range


def test_module_calibration_data(driver):
    """Test combined calibration data readout (CWAV? and CWAVPO?)."""
    module = _first_module(driver)
    num_channels = module._num_channels

    # Query calibration data for index 1 using legacy method
    calib_data = module.get_calibration_data(1)

    # Verify structure: should have one entry per channel
    assert len(calib_data) == num_channels

    for ch in range(1, num_channels + 1):
        assert ch in calib_data
        assert "wavelength" in calib_data[ch]
        assert "power_offset" in calib_data[ch]

        # Validate wavelength is in valid range
        assert 1250 <= calib_data[ch]["wavelength"] <= 1630

        # Power offset should be a reasonable dB value
        assert isinstance(calib_data[ch]["power_offset"], float)
        assert -50 <= calib_data[ch]["power_offset"] <= 50  # Reasonable dB range


# Trigger Mode Parameter
def test_trigger_mode(driver):
    """Test trigger mode parameter (TRIG/TRIG?)."""
    for mode in ["INTERNAL", "EXTERNAL"]:
        driver.trigger_mode(mode)
        assert driver.trigger_mode() == mode


# Logging Parameters
def test_logging_points(driver):
    """Test logging points parameter (LOGN/LOGN?)."""
    for points in [10, 100, 1000]:
        driver.logging_points(points)
        assert driver.logging_points() == points


# Status and Measurement Commands
def test_measurement_status(driver):
    """Test measurement status query (STAT?)."""
    driver.meas()
    time.sleep(0.2)
    status = driver.measurement_status()
    assert "status" in status
    assert "points" in status
    assert status["status"] in ["MEASURING", "COMPLETED", "STOPPED"]
    driver.stop()


# Module Readout
def test_module_read(driver):
    """Test module readout (READ?)."""
    module = _first_module(driver)
    num_channels = module._num_channels

    driver.measurement_mode("CONST1")
    driver.zero()
    time.sleep(3.1)  # Wait for zeroing
    driver.meas()
    time.sleep(0.5)  # Allow measurement to complete

    result = module.read()
    assert isinstance(result, dict)
    # Verify only the expected channels are present
    expected_keys = {f"ch{i}" for i in range(1, num_channels + 1)}
    assert set(result.keys()) == expected_keys
    assert all(isinstance(v, float) for v in result.values())

    driver.stop()


# Control Commands
def test_zero_command(driver):
    """Test zeroing command (ZERO)."""
    driver.zero()
    # Zeroing takes ~3 seconds; just verify command executes without error
    time.sleep(3.1)


def test_meas_command(driver):
    """Test start measurement command (MEAS)."""
    driver.measurement_mode("CONST1")
    driver.meas()
    time.sleep(0.2)
    status = driver.measurement_status()
    assert status["status"] in ["MEASURING", "COMPLETED"]
    driver.stop()


def test_stop_command(driver):
    """Test stop measurement command (STOP)."""
    driver.meas()
    time.sleep(0.2)
    driver.stop()
    time.sleep(0.1)
    status = driver.measurement_status()
    assert status["status"] == "STOPPED"


def test_reset_command(driver):
    """Test instrument reset command (*RST)."""
    driver.reset()
    time.sleep(0.5)  # Allow time for reset to complete
