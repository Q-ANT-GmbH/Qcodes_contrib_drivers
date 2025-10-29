import math
import random
import string
import time

import pytest

from qcodes_contrib_drivers.drivers.Rigol.Rigol_DG5000Pro import RigolDG5000Pro


@pytest.fixture
def driver():
    # Wait before opening a new connection for the next test
    time.sleep(0.2)

    rigol = RigolDG5000Pro(
        "rigol",
        address="TCPIP::192.168.50.153::INSTR",
    )

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


def test_screen_capture(driver):
    driver.screen_capture("./test.bmp")
    driver.screen_capture("./test.png")


def test_display_focus(driver):
    for i in range(len(driver.ch)):
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


def test_display_unit_pulse(driver):
    driver.display_unit_pulse("width")
    assert driver.display_unit_pulse() == "width"
    driver.display_unit_pulse("duty")
    assert driver.display_unit_pulse() == "duty"


def test_display_unit_rate(driver):
    driver.display_unit_rate("frequency")
    assert driver.display_unit_rate() == "frequency"
    driver.display_unit_rate("period")
    assert driver.display_unit_rate() == "period"


def test_display_unit_sweep(driver):
    driver.display_unit_sweep("start-stop")
    assert driver.display_unit_sweep() == "start-stop"
    driver.display_unit_sweep("center-span")
    assert driver.display_unit_sweep() == "center-span"


def test_display_unit_voltage(driver):
    driver.display_unit_voltage("amplitude-offset")
    assert driver.display_unit_voltage() == "amplitude-offset"
    driver.display_unit_voltage("high-low")
    assert driver.display_unit_voltage() == "high-low"


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
    for ch in driver.ch:
        ch.output_debounce(True)
        assert ch.output_debounce() == True
        ch.output_debounce(False)
        assert ch.output_debounce() == False


def test_output_idle(driver):
    for ch in driver.ch:
        lvl = random.randint(0, 65535)
        ch.output_idle(lvl)
        assert ch.output_idle() == lvl
        ch.output_idle("FPT")
        assert ch.output_idle() == "FPT"
        ch.output_idle("TOP")
        assert ch.output_idle() == "TOP"
        ch.output_idle("CENT")
        assert ch.output_idle() == "CENT"
        ch.output_idle("BOTT")
        assert ch.output_idle() == "BOTT"


def test_output_load(driver):
    for ch in driver.ch:
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


def test_output_polarity(driver):
    for ch in driver.ch:
        ch.output_polarity("normal")
        assert ch.output_polarity() == "normal"
        ch.output_polarity("inverted")
        assert ch.output_polarity() == "inverted"


def test_output_skew_time(driver):
    for ch in driver.ch:
        time = random.uniform(-200e-9, 200e-9)
        ch.output_skew_time(time)
        assert math.isclose(ch.output_skew_time(), time, abs_tol=1e-3)
        ch.output_skew_time("MIN")
        assert ch.output_skew_time() == -200e-9
        ch.output_skew_time("MAX")
        assert ch.output_skew_time() == 200e-9
        ch.output_skew_time("DEF")
        assert ch.output_skew_time() == 0.0


def test_output_state(driver):
    for ch in driver.ch:
        ch.output_state(True)
        assert ch.output_state() == True
        ch.output_state(False)
        assert ch.output_state() == False


def test_output_sync(driver):
    for ch in driver.ch:
        ch.output_sync(False)
        assert ch.output_sync() == False
        ch.output_sync(True)
        assert ch.output_sync() == True


def test_output_sync_mode(driver):
    for ch in driver.ch:
        # Required to enable output sync mode
        ch.source_sweep_state(True)

        ch.output_sync_mode("normal")
        assert ch.output_sync_mode() == "normal"
        ch.output_sync_mode("marker")
        assert ch.output_sync_mode() == "marker"


def test_output_sync_polarity(driver):
    for ch in driver.ch:
        ch.output_sync_polarity("normal")
        assert ch.output_sync_polarity() == "normal"
        ch.output_sync_polarity("inverted")
        assert ch.output_sync_polarity() == "inverted"


def test_output_trigger(driver):
    for ch in driver.ch:
        ch.source_burst_mode("triggered")
        ch.trigger_source("immediate")

        ch.output_trigger(True)
        assert ch.output_trigger() == True
        ch.output_trigger(False)
        assert ch.output_trigger() == False


# Source commands

def test_source_burst_state(driver):
    for ch in driver.ch:
        ch.source_burst_state(True)
        assert ch.source_burst_state() == True
        ch.source_burst_state(False)
        assert ch.source_burst_state() == False


def test_source_burst_mode(driver):
    for ch in driver.ch:
        ch.source_burst_mode("triggered")
        assert ch.source_burst_mode() == "triggered"
        ch.source_burst_mode("gated")
        assert ch.source_burst_mode() == "gated"


def test_source_sweep_state(driver):
    for ch in driver.ch:
        ch.source_sweep_state(True)
        assert ch.source_sweep_state() == True
        ch.source_sweep_state(False)
        assert ch.source_sweep_state() == False


# Trigger commands

def test_trigger_count(driver):
    for ch in driver.ch:
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
    for ch in driver.ch:
        # delay = random.uniform(0, 85)
        delay = 0.001
        ch.trigger_delay(delay)
        assert ch.trigger_delay() == delay
        ch.trigger_delay('MIN')
        assert ch.trigger_delay() == 0
        ch.trigger_delay('MAX')
        ch.trigger_delay('DEF')


def test_trigger_slope(driver):
    for ch in driver.ch:
        # Required to enable trigger slope
        ch.trigger_source("external")

        ch.trigger_slope("negative")
        assert ch.trigger_slope() == "negative"
        ch.trigger_slope("positive")
        assert ch.trigger_slope() == "positive"


def test_trigger_source(driver):
    for ch in driver.ch:
        ch.trigger_source("immediate")
        assert ch.trigger_source() == "immediate"
        ch.trigger_source("external")
        assert ch.trigger_source() == "external"
        ch.trigger_source("bus")
        assert ch.trigger_source() == "bus"
        ch.trigger_source("timer")
        assert ch.trigger_source() == "timer"  # TODO : "timer" might only be available for remote mode


def test_trigger_timer(driver):
    for ch in driver.ch:
        time = random.uniform(1e-6, 8000)
        ch.trigger_timer(time)
        assert math.isclose(ch.trigger_timer(), time)
        ch.trigger_timer("MIN")
        assert ch.trigger_timer() == 0
        ch.trigger_timer("MAX")
        assert ch.trigger_timer() == 8000


def test_ch_trigger(driver):
    for ch in driver.ch:
        ch.trigger()


def test_source_apply_ramp(driver):
    for ch in driver.ch:
        frequency = 5e6 * random.random()
        amplitude = 1
        offset = 0
        phase = 0
        ch.source_apply_ramp(frequency, amplitude, offset, phase)
