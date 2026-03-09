"""Tests for Santec MPM-220 Optical Power Meter driver.

These tests require a connected MPM-220 instrument.
Update the fixture address/port for your setup.
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


@pytest.fixture
def first_module(driver):
    """Get the first detected measurement module."""
    if not driver.modules:
        pytest.skip("No modules detected")
    return driver.modules[0]


# System/Network Parameters
def test_idn(driver):
    """Test instrument identification query (*IDN?)."""
    idn_dict = driver.get_idn()
    assert isinstance(idn_dict, dict)
    assert "model" in idn_dict
    assert idn_dict["model"].startswith("MPM")


def test_module_idn(first_module):
    """Test module identification via get_idn()."""
    idn = first_module.get_idn()
    assert isinstance(idn, dict)
    assert idn["model"].startswith("MPM-")


def test_gpib_address(driver):
    """Test GPIB address parameter (ADDR/ADDR?)."""
    current = driver.gpib_address()
    driver.gpib_address(current)
    assert driver.gpib_address() == current


def test_ip_address(driver):
    """Test IP address readout (IP?)."""
    ip_addr = driver.ip_address()
    assert re.match(r"^\d+\.\d+\.\d+\.\d+$", ip_addr)


def test_gateway_address(driver):
    """Test gateway address parameter (GW/GW?)."""
    gw_addr = driver.gateway_address()
    if gw_addr.strip():
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", gw_addr)


def test_subnet_mask(driver):
    """Test subnet mask parameter (SUBNET/SUBNET?)."""
    subnet_mask = driver.subnet_mask()
    assert re.match(r"^\d+\.\d+\.\d+\.\d+$", subnet_mask)


def test_module_status(driver):
    """Test module status parameter (IDIS?)."""
    status = driver.module_status()
    assert isinstance(status, list)
    assert len(status) == 5
    assert all(isinstance(present, bool) for present in status)


def test_error(driver):
    """Test error query (ERR?)."""
    err = driver.error()
    assert isinstance(err, dict)
    assert "code" in err
    assert "message" in err
    assert isinstance(err["code"], int)
    assert isinstance(err["message"], str)


# Measurement Mode Parameters
@pytest.mark.parametrize("mode", ["CONST1", "SWEEP1", "CONST2", "SWEEP2", "FREERUN"])
def test_measurement_mode(driver, mode):
    """Test measurement mode parameter (WMOD/WMOD?)."""
    driver.measurement_mode(mode)
    assert driver.measurement_mode() == mode


# Wavelength Parameters
def test_wavelength(driver):
    """Test global wavelength parameter (WAV/WAV?)."""
    driver.wavelength(1550.0)
    assert driver.wavelength() == pytest.approx(1550.0, abs=1e-3)


def test_sweep_parameters(driver):
    """Test sweep wavelength parameters (WSET/WSET?)."""
    driver.set_sweep_parameters(start=1520.0, stop=1570.0, step=0.05)
    assert driver.sweep_start() == pytest.approx(1520.0, abs=1e-3)
    assert driver.sweep_stop() == pytest.approx(1570.0, abs=1e-3)
    assert driver.sweep_step() == pytest.approx(0.05, abs=1e-3)


@pytest.mark.parametrize("speed", [1.0, 5.0, 50.0])
def test_sweep_speed(driver, speed):
    """Test sweep speed parameter (SPE/SPE?)."""
    driver.sweep_speed(speed)
    assert driver.sweep_speed() == pytest.approx(speed, abs=1e-3)


# Gain Parameters
def test_gain(driver, first_module):
    """Test global TIA gain parameter (LEV/LEV?)."""
    if first_module._max_gain is None:
        pytest.skip("Module does not support gain control (MPM-215).")

    driver.gain(1)
    assert driver.gain() == 1


def test_module_wavelength_channels(first_module):
    """Test per-channel wavelength parameters (DWAV/DWAV?)."""
    for i, ch in enumerate(first_module.channels, 1):
        test_wl = 1550.0 + i
        ch.wavelength(test_wl)
        assert ch.wavelength() == pytest.approx(test_wl, abs=1e-3)


def test_module_gain_channels(first_module):
    """Test per-channel gain parameters (DLEV/DLEV?)."""
    if first_module._max_gain is None:
        pytest.skip("Module does not support gain control (MPM-215).")

    for ch in first_module.channels:
        ch.gain(1)
        assert ch.gain() == 1


# Averaging Parameters
@pytest.mark.parametrize("avg_time", [0.1, 1.0, 10.0])
def test_average_time(driver, avg_time):
    """Test averaging time parameter (AVG/AVG?)."""
    driver.average_time(avg_time)
    assert driver.average_time() == pytest.approx(avg_time, abs=1e-2)


@pytest.mark.parametrize("avg_time", [0.1, 1.0, 10.0])
def test_freerun_average_time(driver, avg_time):
    """Test freerun averaging time parameter (FGSAVG/FGSAVG?)."""
    driver.freerun_average_time(avg_time)
    assert driver.freerun_average_time() == pytest.approx(avg_time, abs=1e-2)


# Power Unit Parameter
@pytest.mark.parametrize("unit", ["dBm", "mW"])
def test_power_unit(driver, unit):
    """Test power unit selection parameter (UNIT/UNIT?)."""
    driver.power_unit(unit)
    assert driver.power_unit() == unit


# Auto-Range Parameters
@pytest.mark.parametrize("mode", ["AUTO", "MANUAL"])
def test_auto_range_global(driver, mode):
    """Test global auto-range mode parameter (AUTO/AUTO?)."""
    driver.auto_range(mode)
    assert driver.auto_range() == mode


@pytest.mark.parametrize("mode", ["AUTO", "MANUAL"])
def test_module_auto_range(first_module, mode):
    """Test per-module auto-range parameter (DAUTO/DAUTO?)."""
    first_module.auto_range(mode)
    assert first_module.auto_range() == mode


# Calibration Parameters
def test_module_calibration_wavelengths(first_module):
    """Test calibration wavelength readout (CWAV?)."""
    wavelengths = first_module.calibration_wavelength()
    assert all(1250 <= wl <= 1630 for wl in wavelengths[:5])


def test_module_calibration_power_offsets(first_module):
    """Test calibration power offset readout (CWAVPO?)."""
    for ch in first_module.channels:
        offsets = ch.calibration_power_offset()
        assert all(-50 <= offset <= 50 for offset in offsets[:5])


# Trigger Mode Parameter# Trigger Mode Parameter
@pytest.mark.parametrize("mode", ["INTERNAL", "EXTERNAL"])
def test_trigger_mode(driver, mode):
    """Test trigger mode parameter (TRIG/TRIG?)."""
    driver.trigger_mode(mode)
    assert driver.trigger_mode() == mode


# Logging Parameters
@pytest.mark.parametrize("points", [10, 100, 1000])
def test_logging_points(driver, points):
    """Test logging points parameter (LOGN/LOGN?)."""
    driver.logging_points(points)
    assert driver.logging_points() == points


# Status and Measurement Commands
def test_measurement_status(driver):
    """Test measurement status query (STAT?)."""
    driver.meas()
    time.sleep(0.2)
    status = driver.measurement_status()
    assert status["status"] in ["MEASURING", "COMPLETED", "STOPPED"]
    driver.stop()


def test_module_read(driver, first_module):
    """Test module readout (READ?)."""
    driver.measurement_mode("CONST1")
    driver.zero()
    time.sleep(3.1)
    driver.meas()
    time.sleep(0.5)

    result = first_module.read()
    assert len(result) == first_module._num_channels
    assert all(isinstance(v, float) for v in result.values())

    driver.stop()


# Control Commands
def test_zero_command(driver):
    """Test zeroing command (ZERO)."""
    driver.zero()
    time.sleep(3.1)


def test_meas_command(driver):
    """Test start measurement command (MEAS)."""
    driver.measurement_mode("CONST1")
    driver.meas()
    time.sleep(0.2)
    assert driver.measurement_status()["status"] in ["MEASURING", "COMPLETED"]
    driver.stop()


def test_stop_command(driver):
    """Test stop measurement command (STOP)."""
    driver.meas()
    time.sleep(0.2)
    driver.stop()
    time.sleep(0.1)
    assert driver.measurement_status()["status"] == "STOPPED"


def test_reset_command(driver):
    """Test instrument reset command (*RST)."""
    driver.reset()
    time.sleep(0.5)
