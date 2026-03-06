import random
import string

import numpy as np
import pytest
from numpy import all, array

from qcodes_contrib_drivers.drivers.Rigol.Rigol_DG5000Pro import RigolDG5000Pro


@pytest.fixture
def driver():
    rigol = RigolDG5000Pro("rigol", address="TCPIP::192.168.50.158::INSTR")
    yield rigol
    rigol.close()


def test_idn(driver):
    idn_dict = driver.get_idn()
    assert idn_dict["vendor"] == "RIGOL TECHNOLOGIES"


def test_all(driver):
    driver.all(False)
    driver.all(True)


def test_display_brightness(driver):
    driver.display_brightness(42)
    assert driver.display_brightness() == 42


@pytest.mark.parametrize("format_type", ["bmp", "png"])
def test_screen_capture_format(driver, format_type):
    driver.screen_capture_format(format_type)
    assert driver.screen_capture_format() == format_type


def test_screen_capture_png(driver):
    driver.screen_capture("./test.png")


def test_screen_capture_bmp(driver):
    driver.screen_capture("./test.bmp")


def test_display_focus(driver):
    for i in range(len(driver.channels)):
        driver.display_focus(i + 1)
        # assert driver.display_focus() == i + 1    # TODO : Seems to be a bug on the instrument side when reading ch > 2


def test_display_state(driver):
    driver.display_state(False)
    assert driver.display_state() == False
    driver.display_state(True)
    assert driver.display_state() == True


def test_display_text(driver):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    driver.display_text(random_string)
    assert driver.display_text() == random_string
    driver.display_clear_text()


@pytest.mark.parametrize("unit_type,expected", [
    ("width", "width"),
    ("duty", "duty")
])
def test_display_unit_pulse(driver, unit_type, expected):
    driver.display_unit_pulse(unit_type)
    assert driver.display_unit_pulse() == expected


@pytest.mark.parametrize("unit_type,expected", [
    ("frequency", "frequency"),
    ("period", "period")
])
def test_display_unit_rate(driver, unit_type, expected):
    driver.display_unit_rate(unit_type)
    assert driver.display_unit_rate() == expected


@pytest.mark.parametrize("unit_type,expected", [
    ("start-stop", "start-stop"),
    ("center-span", "center-span")
])
def test_display_unit_sweep(driver, unit_type, expected):
    driver.display_unit_sweep(unit_type)
    assert driver.display_unit_sweep() == expected


@pytest.mark.parametrize("unit_type,expected", [
    ("amplitude-offset", "amplitude-offset"),
    ("high-low", "high-low")
])
def test_display_unit_voltage(driver, unit_type, expected):
    driver.display_unit_voltage(unit_type)
    assert driver.display_unit_voltage() == expected


def test_display_view(driver):
    driver.display_view("auto")
    assert driver.display_view() == "auto"
    driver.display_view(2)
    assert driver.display_view() == 2
    driver.display_view(4)
    assert driver.display_view() == 4
    driver.display_view(8)
    assert driver.display_view() == 8


def test_clear(driver):
    driver.clear()


def test_options(driver):
    driver.options()


# TODO : Seems to mess up the following tests...
# def test_reset(driver):
#     driver.reset()


def test_wait(driver):
    driver.wait()


def test_trigger(driver):
    driver.trigger()


def test_opc(driver):
    driver.opc()


# Channel specific commands
def test_output_debounce(driver):
    driver.channels.output_debounce(True)
    assert all(array(driver.channels.output_debounce()) == True)
    driver.channels.output_debounce(False)
    assert all(array(driver.channels.output_debounce()) == False)


def test_output_idle(driver):
    lvl = np.random.randint(0, 65535, size=len(driver.channels))
    driver.channels.output_idle(lvl)
    assert all(array(driver.channels.output_idle()) == lvl)
    driver.channels.output_idle("FPT")
    assert all(array(driver.channels.output_idle()) == "FPT")
    driver.channels.output_idle("TOP")
    assert all(array(driver.channels.output_idle()) == "TOP")
    driver.channels.output_idle("CENT")
    assert all(array(driver.channels.output_idle()) == "CENT")
    driver.channels.output_idle("BOTT")
    assert all(array(driver.channels.output_idle()) == "BOTT")


def test_output_load(driver):
    for ch in driver.channels:
        lvl = random.randint(1, 10000)
        ch.output_load(lvl)
        assert ch.output_load() == lvl
        ch.output_load("MIN")
        assert ch.output_load() == 1.0
        ch.output_load("MAX")
        assert ch.output_load() == 10000.0
        ch.output_load("INF")
        assert ch.output_load() == 9.9e37
        ch.output_load("DEF")
        assert ch.output_load() == 50.0


@pytest.mark.parametrize("polarity", ["normal", "inverted"])
def test_output_polarity(driver, polarity):
    driver.channels.output_polarity(polarity)
    assert all(array(driver.channels.output_polarity()) == polarity)


def test_output_skew_time(driver):
    for ch in driver.channels:
        time = random.uniform(-200e-9, 200e-9)
        ch.output_skew_time(time)
        assert ch.output_skew_time() == pytest.approx(time, abs=1e-3)
        ch.output_skew_time("MIN")
        assert ch.output_skew_time() == -200e-9
        ch.output_skew_time("MAX")
        assert ch.output_skew_time() == 200e-9
        ch.output_skew_time("DEF")
        assert ch.output_skew_time() == 0.0


def test_output_state(driver):
    driver.channels.output_state(True)
    assert all(array(driver.channels.output_state()) == True)
    driver.channels.output_state(False)
    assert all(array(driver.channels.output_state()) == False)


def test_output_sync(driver):
    driver.channels.output_sync(True)
    assert all(array(driver.channels.output_sync()) == True)
    driver.channels.output_sync(False)
    assert all(array(driver.channels.output_sync()) == False)


@pytest.mark.parametrize("sync_mode", ["normal", "marker"])
def test_output_sync_mode(driver, sync_mode):
    driver.channels.source_sweep_state(True)  # Required to enable output sync mode
    driver.channels.output_sync(True)
    driver.channels.output_sync_mode(sync_mode)
    assert all(array(driver.channels.output_sync_mode()) == sync_mode)


@pytest.mark.parametrize("polarity", ["normal", "inverted"])
def test_output_sync_polarity(driver, polarity):
    driver.channels.output_sync_polarity(polarity)
    assert all(array(driver.channels.output_sync_polarity()) == polarity)


def test_output_trigger(driver):
    driver.channels.source_burst_mode("triggered")  # Required to enable output trigger
    driver.channels.trigger_source("immediate")

    for ch in driver.channels:
        ch.output_trigger(True)
        assert ch.output_trigger() == True
        ch.output_trigger(False)
        assert ch.output_trigger() == False


# Source commands

def test_source_burst_state(driver):
    for ch in driver.channels:
        ch.source_burst_state(True)
        assert ch.source_burst_state() == True
        ch.source_burst_state(False)
        assert ch.source_burst_state() == False


@pytest.mark.parametrize("burst_mode", ["gated", "triggered"])
def test_source_burst_mode(driver, burst_mode):
    for ch in driver.channels:
        ch.source_burst_mode(burst_mode)
        assert ch.source_burst_mode() == burst_mode


def test_source_sweep_state(driver):
    driver.channels.source_sweep_state(True)
    assert all(array(driver.channels.source_sweep_state()) == True)
    driver.channels.source_sweep_state(False)
    assert all(array(driver.channels.source_sweep_state()) == False)


# Trigger commands

def test_trigger_count(driver):
    for ch in driver.channels:
        count = random.randint(1, 1000000)
        ch.trigger_count(count)
        assert ch.trigger_count() == count
        ch.trigger_count("MIN")
        assert ch.trigger_count() == 1
        ch.trigger_count("MAX")
        assert ch.trigger_count() == 1000000
        ch.trigger_count("DEF")
        assert ch.trigger_count() == 1


def test_trigger_delay(driver):
    for ch in driver.channels:
        # delay = random.uniform(0, 85)
        delay = 0.001
        ch.trigger_delay(delay)
        assert ch.trigger_delay() == delay
        ch.trigger_delay('MIN')
        assert ch.trigger_delay() == 0
        ch.trigger_delay('MAX')
        ch.trigger_delay('DEF')


@pytest.mark.parametrize("slope", ["negative", "positive"])
def test_trigger_slope(driver, slope):
    driver.channels.trigger_source("external")  # Required to enable trigger slope
    for ch in driver.channels:
        ch.trigger_slope(slope)
        assert ch.trigger_slope() == slope


@pytest.mark.parametrize("source", ["immediate", "external", "bus", "timer"])
def test_trigger_source(driver, source):
    driver.channels.source_burst_state(True)  # Required to enable trigger all possible trigger sources
    for ch in driver.channels:
        ch.trigger_source(source)
        assert ch.trigger_source() == source


def test_trigger_timer(driver):
    driver.channels.source_burst_state(True)  # Required to enable trigger all possible trigger sources
    driver.channels.trigger_source("timer")
    for ch in driver.channels:
        time = random.uniform(1e-6, 8000)
        ch.trigger_timer(time)
        assert ch.trigger_timer() == pytest.approx(time)
        ch.trigger_timer("MIN")
        assert ch.trigger_timer() == 0
        ch.trigger_timer("MAX")
        assert ch.trigger_timer() == 8000


def test_ch_trigger(driver):
    for ch in driver.channels:
        ch.trigger()


def test_source_apply_ramp(driver):
    for ch in driver.channels:
        frequency = 5e6 * random.random()
        amplitude = 1
        offset = 0
        phase = 0
        ch.source_apply_ramp(frequency, amplitude, offset, phase)
