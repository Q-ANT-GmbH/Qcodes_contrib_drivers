import math
import random

import numpy as np
import pytest

from qcodes_contrib_drivers.drivers.Rigol.Rigol_DS8000R import RigolDS8000R


@pytest.fixture
def driver():
    rigol = RigolDS8000R(
        "rigol",
        address="TCPIP::192.168.50.77::INSTR",
    )
    yield rigol
    rigol.close()


def test_idn(driver):
    idn_dict = driver.get_idn()
    assert idn_dict["vendor"] == "RIGOL TECHNOLOGIES"


def test_reset(driver):
    driver.reset()


def test_acquire_mdepth(driver):
    mdepths = {1e3: "1k", 1e4: "10k", 1e5: "100k", 1e6: "1M", 1e7: "10M", 1e8: "100M", 125e6: "125M",
               250e6: "250M", 500e6: "500M"}
    driver.acquire_mdepth('AUTO')
    for key, val in mdepths.items():
        driver.acquire_mdepth(val)
        assert driver.acquire_mdepth() == key


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
    assert math.isclose(driver.timebase_offset(), val, rel_tol=1e-6)


def test_timebase_scale(driver):
    val = 1e-3 * random.random()
    driver.timebase_scale(val)
    assert math.isclose(driver.timebase_scale(), val, rel_tol=5e-2)


def test_timebase_mode(driver):
    driver.timebase_mode("roll")
    assert driver.timebase_mode() == "roll"
    driver.timebase_mode("xy")
    assert driver.timebase_mode() == "xy"
    driver.timebase_mode("yt")
    assert driver.timebase_mode() == "yt"


def test_timebase_href_mode(driver):
    driver.timebase_href_mode("center")
    assert driver.timebase_href_mode() == "center"
    driver.timebase_href_mode("left_border")
    assert driver.timebase_href_mode() == "left_border"
    driver.timebase_href_mode("right_border")
    assert driver.timebase_href_mode() == "right_border"
    driver.timebase_href_mode("trigger")
    assert driver.timebase_href_mode() == "trigger"
    driver.timebase_href_mode("user")
    assert driver.timebase_href_mode() == "user"


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


def test_waveform_source(driver):
    sources = ("CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH1", "MATH2", "MATH3", "MATH4")
    for source in sources:
        driver.waveform_source(source)
        assert driver.waveform_source() == source


def test_waveform_mode(driver):
    driver.waveform_mode("normal")
    assert driver.waveform_mode() == "normal"
    driver.waveform_mode("maximum")
    assert driver.waveform_mode() == "maximum"
    driver.waveform_mode("raw")
    assert driver.waveform_mode() == "raw"


def test_waveform_format(driver):
    driver.waveform_format("ascii")
    assert driver.waveform_format() == "ascii"
    driver.waveform_format("word")
    assert driver.waveform_format() == "word"
    driver.waveform_format("byte")
    assert driver.waveform_format() == "byte"


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


def test_ch_bw(driver):
    for ch in driver.ch:
        ch.bandwidth_limit("OFF")
        assert ch.bandwidth_limit() == "OFF"
        ch.bandwidth_limit("20M")
        assert ch.bandwidth_limit() == "20M"


def test_ch_coupling(driver):
    for ch in driver.ch:
        for coupling in ("AC", "DC", "GND"):
            ch.coupling(coupling)
            assert ch.coupling() == coupling


def test_ch_display(driver):
    for ch in driver.ch:
        ch.display(False)
        assert ch.display() == False
        ch.display(True)
        assert ch.display() == True


def test_ch_invert(driver):
    for ch in driver.ch:
        ch.invert(True)
        assert ch.invert() == True
        ch.invert(False)
        assert ch.invert() == False


def test_ch_offset(driver):
    for ch in driver.ch:
        offset = random.random()
        ch.offset(offset)
        assert math.isclose(ch.offset(), offset, rel_tol=1e-3)


def test_ch_delay_calibration_time(driver):
    for ch in driver.ch:
        val = random.uniform(-100e-9, 100e-9)
        ch.delay_calibration_time(val)
        assert math.isclose(ch.delay_calibration_time(), val, rel_tol=1e-4)


def test_ch_scale(driver):
    for ch in driver.ch:
        scale = random.random()
        scale = np.round(scale // 10e-3) * 10e-3

        ch.scale(scale)
        assert math.isclose(ch.scale(), scale)


def test_ch_impedance(driver):
    for ch in driver.ch:
        ch.impedance('50 Ohm')
        assert ch.impedance() == '50 Ohm'
        ch.impedance('1 MOhm')
        assert ch.impedance() == '1 MOhm'


def test_ch_probe(driver):
    vals = (0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200,
            500, 1000, 2000, 5000, 10000, 20000, 50000)
    for ch in driver.ch:
        for probe in vals:
            ch.probe(probe)
            assert ch.probe() == probe


def test_ch_units(driver):
    for ch in driver.ch:
        for unit in ("volt", "watt", "ampere", "unknown"):
            ch.units(unit)
            assert ch.units() == unit


def test_ch_vernier(driver):
    for ch in driver.ch:
        ch.vernier(True)
        assert ch.vernier() == True
        ch.vernier(False)
        assert ch.vernier() == False


def test_ch_position(driver):
    for ch in driver.ch:
        val = random.uniform(-100, 100)
        ch.position(val)
        assert math.isclose(ch.position(), val, rel_tol=1e-2)


def test_ch_calibrate(driver):
    for ch in driver.ch:
        ch.calibrate()


def test_get_trace(driver):
    ch = random.randint(1, driver.n_o_ch)
    driver.stop()
    driver.get_trace(ch)


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
