import random

import numpy as np
import pytest
from numpy import all, array

from qcodes_contrib_drivers.drivers.Rigol.Rigol_DS8000R import RigolDS8000R


@pytest.fixture
def driver():
    rigol = RigolDS8000R("rigol", address="TCPIP::192.168.50.152::INSTR")
    yield rigol
    rigol.close()


def test_idn(driver):
    idn_dict = driver.get_idn()
    assert idn_dict["vendor"] == "RIGOL TECHNOLOGIES"


def test_reset(driver):
    driver.reset()


def test_acquire_averages(driver):
    # Required to be able to change averaging number
    driver.run()
    driver.acquire_type("averages")

    for val in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
        driver.acquire_averages(val)
        assert driver.acquire_averages() == val


def test_acquire_mdepth(driver):
    driver.acquire_type("normal")

    # Turn on only CH1 to have access to max memory depth
    driver.channels.display(False)
    driver.channels[0].display(True)

    mdepths = {1e3: "1k", 1e4: "10k", 1e5: "100k", 1e6: "1M", 1e7: "10M", 1e8: "100M", 125e6: "125M",
               250e6: "250M", 500e6: "500M"}
    driver.acquire_mdepth('AUTO')
    for key, val in mdepths.items():
        driver.acquire_mdepth(val)
        assert driver.acquire_mdepth() == key


@pytest.mark.parametrize("acquire_mode", ["normal", "averages", "peak", "high_resolution"])
def test_acquire_type(driver, acquire_mode):
    driver.acquire_type(acquire_mode)
    assert driver.acquire_type() == acquire_mode


def test_acquire_srate(driver):
    val = driver.acquire_srate()
    assert isinstance(val, float)
    assert val > 0


def test_acquire_aalias(driver):
    driver.acquire_aalias(True)
    assert driver.acquire_aalias() is True
    driver.acquire_aalias(False)
    assert driver.acquire_aalias() is False


def test_timebase_axis(driver):
    assert driver.timebase_axis() is not None


def test_timebase_delay_enable(driver):
    driver.timebase_delay_enable(True)
    assert driver.timebase_delay_enable() == True
    driver.timebase_delay_enable(False)
    assert driver.timebase_delay_enable() == False


def test_timebase_delay_offset(driver):
    # Computing allowable range from manual formula
    scale = driver.timebase_scale()
    offset = driver.timebase_offset()
    left_time = 5 * scale - offset
    right_time = 5 * scale + offset
    delay_range = 10 * scale

    val = random.uniform(-(left_time - delay_range / 2), (right_time - delay_range / 2))
    driver.timebase_delay_offset(val)
    assert driver.timebase_delay_offset() == val


def test_timebase_delay_scale(driver):
    scale = driver.timebase_scale()

    val = scale / 25
    driver.timebase_delay_scale(val)
    assert driver.timebase_delay_scale() == val


def test_timebase_offset(driver):
    val = random.random()
    driver.timebase_offset(val)
    assert driver.timebase_offset() == pytest.approx(val, rel=1e-6)


def test_timebase_scale(driver):
    val = 1e-3 * random.random()
    driver.timebase_scale(val)
    assert driver.timebase_scale() == pytest.approx(val, rel=5e-2)


@pytest.mark.parametrize("mode", ["roll", "xy", "yt"])
def test_timebase_mode(driver, mode):
    driver.timebase_mode(mode)
    assert driver.timebase_mode() == mode


@pytest.mark.parametrize("href_mode", ["center", "left_border", "right_border", "trigger", "user"])
def test_timebase_href_mode(driver, href_mode):
    driver.timebase_href_mode(href_mode)
    assert driver.timebase_href_mode() == href_mode


def test_timebase_href_position(driver):
    val = random.randint(-500, 500)
    driver.timebase_href_position(val)
    assert driver.timebase_href_position() == val


def test_timebase_vernier(driver):
    driver.timebase_vernier(True)
    assert driver.timebase_vernier() == True
    driver.timebase_vernier(False)
    assert driver.timebase_vernier() == False


def test_trigger_status(driver):
    status = driver.trigger_status()
    assert driver.trigger_status() in ("TD", "WAIT", "RUN", "AUTO", "STOP")


def test_trigger_mode(driver):
    # Ensure all mapped modes are accepted and return the same key
    for mode in driver.trigger_mode.val_mapping.keys():
        driver.trigger_mode(mode)
        assert driver.trigger_mode() == mode


@pytest.mark.parametrize("coupling", ["ac", "dc", "lfreject", "hfreject"])
def test_trigger_coupling(driver, coupling):
    driver.trigger_coupling(coupling)
    assert driver.trigger_coupling() == coupling


@pytest.mark.parametrize("sweep", ["auto", "normal", "single"])
def test_trigger_sweep(driver, sweep):
    driver.trigger_sweep(sweep)
    assert driver.trigger_sweep() == sweep


def test_trigger_holdoff(driver):
    driver.trigger_holdoff(8e-9)
    assert driver.trigger_holdoff() == pytest.approx(8e-9, rel=1e-6)

    driver.trigger_holdoff(10)
    assert driver.trigger_holdoff() == pytest.approx(10.0, rel=1e-6)

    val = random.uniform(1e-6, 1)
    driver.trigger_holdoff(val)
    assert driver.trigger_holdoff() == pytest.approx(val, rel=1e-6)


def test_trigger_noise_reject(driver):
    driver.trigger_noise_reject(True)
    assert driver.trigger_noise_reject() is True
    driver.trigger_noise_reject(False)
    assert driver.trigger_noise_reject() is False


def test_trigger_ext_delay(driver):
    driver.trigger_edge_source("ext")

    driver.trigger_ext_delay(-500000)
    assert driver.trigger_ext_delay() == pytest.approx(-500000, rel=1e-6)
    driver.trigger_ext_delay(499990)
    assert driver.trigger_ext_delay() == pytest.approx(499990, rel=1e-6)
    val = random.uniform(-500000, 500000)
    driver.trigger_ext_delay(val)
    assert driver.trigger_ext_delay() == pytest.approx(val, abs=10.0)


@pytest.mark.parametrize("source", ["ch1", "ch2", "ch3", "ch4", "acline", "ext"])
def test_trigger_edge_source(driver, source):
    driver.trigger_edge_source(source)
    assert driver.trigger_edge_source() == source


@pytest.mark.parametrize("slope", ["positive", "negative", "rfall"])
def test_trigger_edge_slope(driver, slope):
    driver.trigger_edge_slope(slope)
    assert driver.trigger_edge_slope() == slope


@pytest.mark.parametrize("source", ["ch1", "ch2", "ch3", "ch4"])
def test_trigger_pulse_source(driver, source):
    driver.trigger_pulse_source(source)
    assert driver.trigger_pulse_source() == source


@pytest.mark.parametrize("when_mode", ["greater", "less", "gless"])
def test_trigger_pulse_when(driver, when_mode):
    driver.trigger_pulse_when(when_mode)
    assert driver.trigger_pulse_when() == when_mode


def test_trigger_pulse_uwidth(driver):
    driver.trigger_pulse_uwidth(2e-6)
    assert driver.trigger_pulse_uwidth() == pytest.approx(2e-6, rel=1e-6)
    driver.trigger_pulse_uwidth(1)
    assert driver.trigger_pulse_uwidth() == pytest.approx(1.0, rel=1e-6)
    val = random.uniform(1e-6, 0.1)
    driver.trigger_pulse_uwidth(val)
    assert driver.trigger_pulse_uwidth() == pytest.approx(val, rel=1e-6)


def test_trigger_pulse_lwidth(driver):
    driver.trigger_pulse_lwidth(1e-6)
    assert driver.trigger_pulse_lwidth() == pytest.approx(1e-6, rel=1e-6)
    driver.trigger_pulse_lwidth(1e-3)
    assert driver.trigger_pulse_lwidth() == pytest.approx(1e-3, rel=1e-6)
    val = random.uniform(1e-9, 1e-2)
    driver.trigger_pulse_lwidth(val)
    assert driver.trigger_pulse_lwidth() == pytest.approx(val, rel=1e-6)


@pytest.mark.parametrize("source", ("CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH1", "MATH2", "MATH3", "MATH4"))
def test_waveform_source(driver, source):
    driver.waveform_source(source)
    assert driver.waveform_source() == source


@pytest.mark.parametrize("mode", ["normal", "maximum", "raw"])
def test_waveform_mode(driver, mode):
    driver.waveform_mode(mode)
    assert driver.waveform_mode() == mode


@pytest.mark.parametrize("fmt", ["ascii", "word", "byte"])
def test_waveform_format(driver, fmt):
    driver.waveform_format(fmt)
    assert driver.waveform_format() == fmt


def test_waveform_points(driver):
    # Required to change waveform_points
    driver.reset()
    driver.waveform_mode("raw")

    pts = random.randint(1, 1000)
    driver.waveform_points(pts)
    assert driver.waveform_points() == pts


def test_waveform_start(driver):
    start = random.randint(1, 1000)
    driver.waveform_start(start)
    assert driver.waveform_start() == start


def test_waveform_stop(driver):
    stop = random.randint(1, 1000)
    driver.waveform_stop(stop)
    assert driver.waveform_stop() == stop


def test_waveform_preamble(driver):
    preample = driver.get_waveform_preamble()
    print(preample)


@pytest.mark.parametrize("bw_limit", ["OFF", "20M"])
def test_ch_bw(driver, bw_limit):
    driver.channels.bandwidth_limit(bw_limit)
    assert all(array(driver.channels.bandwidth_limit()) == bw_limit)


@pytest.mark.parametrize("coupling", ("AC", "DC", "GND"))
def test_ch_coupling(driver, coupling):
    driver.channels.coupling(coupling)
    assert all(array(driver.channels.coupling()) == coupling)


def test_ch_display(driver):
    driver.channels.display(False)
    assert all(array(driver.channels.display()) == False)
    driver.channels.display(True)
    assert all(array(driver.channels.display()) == True)


def test_ch_invert(driver):
    driver.channels.invert(True)
    assert all(array(driver.channels.invert()) == True)
    driver.channels.invert(False)
    assert all(array(driver.channels.invert()) == False)


def test_ch_offset(driver):
    offset = np.random.random(len(driver.channels))
    driver.channels.offset(offset)
    assert all(np.isclose(array(driver.channels.offset()), offset, rtol=1e-3))


def test_ch_delay_calibration_time(driver):
    val = np.random.uniform(-100e-9, 100e-9, (len(driver.channels),))
    driver.channels.delay_calibration_time(val)
    assert all(np.isclose(array(driver.channels.delay_calibration_time()), val, rtol=1e-3))


def test_ch_scale(driver):
    scale = np.random.random(len(driver.channels))
    driver.channels.scale(scale)
    assert all(np.isclose(array(driver.channels.scale()), scale, atol=0.01))


@pytest.mark.parametrize("impedance", ['50 Ohm', '1 MOhm'])
def test_ch_impedance(driver, impedance):
    driver.channels.impedance(impedance)
    assert all(array(driver.channels.impedance()) == impedance)


def test_ch_probe(driver):
    vals = (0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200,
            500, 1000, 2000, 5000, 10000, 20000, 50000)

    for v in vals:
        driver.channels.probe(v)
        assert all(array(driver.channels.probe()) == v)


@pytest.mark.parametrize("unit", ("volt", "watt", "ampere", "unknown"))
def test_ch_units(driver, unit):
    driver.channels.units(unit)
    assert all(array(driver.channels.units()) == unit)


def test_ch_vernier(driver):
    driver.channels.vernier(True)
    assert all(array(driver.channels.vernier()) == True)
    driver.channels.vernier(False)
    assert all(array(driver.channels.vernier()) == False)


def test_ch_position(driver):
    val = np.random.uniform(-100, 100, (len(driver.channels),))
    driver.channels.position(val)
    assert all(np.isclose(array(driver.channels.position()), val, atol=0.05))


def test_ch_calibrate(driver):
    driver.channels.calibrate()


def test_ch_trace_raw(driver):
    driver.stop()
    assert array(driver.channels.trace_raw()).shape == (4, *driver.timebase_axis().shape)


def test_ch_trace(driver):
    driver.stop()
    assert array(driver.channels.trace()).shape == (4, *driver.timebase_axis().shape)


def test_autoscale(driver):
    driver.autoscale()


def test_clear(driver):
    driver.clear()


def test_run(driver):
    driver.run()


def test_stop(driver):
    driver.stop()


def test_single(driver):
    driver.single()


def test_trigger_force(driver):
    driver.trigger_force()
