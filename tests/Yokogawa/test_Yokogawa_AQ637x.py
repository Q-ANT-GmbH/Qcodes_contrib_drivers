import pytest
import math

from pygments.lexers import q

from qcodes_contrib_drivers.drivers.Yokogawa.Yokogawa_AQ637x import YokogawaAQ637x


@pytest.fixture
def driver():
    osa = YokogawaAQ637x("OSA", address="TCPIP::192.168.50.163::INSTR")
    yield osa
    osa.close()


## Common Commands

def test_idn(driver):
    idn_dict = driver.get_idn()
    assert idn_dict['model'] == 'AQ6370C'


def test_clear_status(driver):
    driver.clear_status()


def test_event_status_enable(driver):
    driver.event_status_enable(251)
    assert driver.event_status_enable() == 251


def test_event_status_register(driver):
    val = driver.event_status_register()
    assert isinstance(val, int)
    assert 0 <= val <= 255


def test_operation_complete(driver):
    driver.operation_complete()
    val = driver.operation_complete()
    assert val in (0, 1)


def test_reset(driver):
    driver.reset()


def test_service_request_enable(driver):
    driver.service_request_enable(0)
    assert driver.service_request_enable() == 0


def test_status_byte(driver):
    val = driver.status_byte()
    assert isinstance(val, int)
    assert 0 <= val <= 255


def test_trigger(driver):
    driver.trigger()


def test_wait(driver):
    driver.wait()


## Instrument specific commands
# Display Sub System Commands

def test_display_color(driver):
    for mode in range(0, 6):
        driver.display_color(mode)
        assert driver.display_color() == mode


def test_display_enabled(driver):
    driver.display_enabled(False)
    assert driver.display_enabled() is False
    driver.display_enabled(True)
    assert driver.display_enabled() is True


def test_display_overview_position(driver):
    for mode in ["off", "left", "right"]:
        driver.display_overview_position(mode)
        assert driver.display_overview_position() == mode


def test_display_overview_size(driver):
    for size in ["large", "small"]:
        driver.display_overview_size(size)
        assert driver.display_overview_size() == size


def test_display_split(driver):
    driver.display_split(True)
    assert driver.display_split() is True
    driver.display_split(False)
    assert driver.display_split() is False


def test_display_split_hold_lower(driver):
    driver.display_split(True)
    driver.display_split_hold_lower(True)
    assert driver.display_split_hold_lower() is True
    driver.display_split_hold_lower(False)
    assert driver.display_split_hold_lower() is False


def test_display_split_hold_upper(driver):
    driver.display_split(True)
    driver.display_split_hold_upper(True)
    assert driver.display_split_hold_upper() is True
    driver.display_split_hold_upper(False)
    assert driver.display_split_hold_upper() is False


def test_display_text_clear(driver):
    driver.display_text_clear()


def test_display_text_data(driver):
    text = "Optical Spectrum Analyzer"
    driver.display_text_data(text)
    assert driver.display_text_data() == text


def test_display_trace_x_center(driver):
    val = driver.display_trace_x_center()
    assert isinstance(val, float)
    driver.display_trace_x_center(val)
    assert driver.display_trace_x_center() == val


def test_display_trace_x_initialize(driver):
    driver.display_trace_x_initialize()


def test_display_trace_x_smscale(driver):
    driver.display_trace_x_smscale()


def test_display_trace_x_span(driver):
    val = driver.display_trace_x_span()
    assert isinstance(val, float)
    driver.display_trace_x_span(val)
    assert driver.display_trace_x_span() == val


def test_display_trace_x_srange(driver):
    driver.display_trace_x_srange(True)
    assert driver.display_trace_x_srange() is True
    driver.display_trace_x_srange(False)
    assert driver.display_trace_x_srange() is False


def test_display_trace_x_start(driver):
    val = driver.display_trace_x_start()
    assert isinstance(val, float)
    driver.display_trace_x_start(val)
    assert driver.display_trace_x_start() == val


def test_display_trace_x_stop(driver):
    val = driver.display_trace_x_stop()
    assert isinstance(val, float)
    driver.display_trace_x_stop(val)
    assert driver.display_trace_x_stop() == val


def test_display_trace_y_nmask(driver):
    driver.display_trace_y_nmask(-999)
    assert math.isclose(driver.display_trace_y_nmask(), -999.0, rel_tol=1e-6)
    driver.display_trace_y_nmask(-40)
    assert math.isclose(driver.display_trace_y_nmask(), -40.0, rel_tol=1e-6)


def test_display_trace_y_nmask_type(driver):
    for mode in ["vertical", "horizontal"]:
        driver.display_trace_y_nmask_type(mode)
        assert driver.display_trace_y_nmask_type() == mode


def test_display_trace_y_dnumber(driver):
    for n in (8, 10, 12):
        driver.display_trace_y_dnumber(n)
        assert driver.display_trace_y_dnumber() == n


def test_display_trace_y1_blevel(driver):
    val = driver.display_trace_y1_blevel()
    assert isinstance(val, float)
    driver.display_trace_y1_blevel(val)
    assert driver.display_trace_y1_blevel() == val


def test_display_trace_y1_pdivision(driver):
    val = driver.display_trace_y1_pdivision()
    assert isinstance(val, float)
    driver.display_trace_y1_pdivision(val)
    assert driver.display_trace_y1_pdivision() == val


def test_display_trace_y1_rlevel(driver):
    val = driver.display_trace_y1_rlevel()
    assert isinstance(val, float)
    driver.display_trace_y1_rlevel(val)
    assert driver.display_trace_y1_rlevel() == val


def test_display_trace_y1_rposition(driver):
    driver.display_trace_y1_rposition(10)
    assert driver.display_trace_y1_rposition() == 10


def test_display_trace_y1_spacing(driver):
    for mode in ["log", "linear"]:
        driver.display_trace_y1_spacing(mode)
        assert driver.display_trace_y1_spacing() == mode


def test_display_trace_y1_unit(driver):
    for unit in ["dbm", "w", "dbm_per_nm", "w_per_nm"]:
        driver.display_trace_y1_unit(unit)
        assert driver.display_trace_y1_unit() == unit


def test_display_trace_y2_auto(driver):
    driver.display_trace_y2_auto(True)
    assert driver.display_trace_y2_auto() is True
    driver.display_trace_y2_auto(False)
    assert driver.display_trace_y2_auto() is False


def test_display_trace_y2_length(driver):
    val = driver.display_trace_y2_length()
    assert isinstance(val, float)
    driver.display_trace_y2_length(val)
    assert driver.display_trace_y2_length() == val


def test_display_trace_y2_olevel(driver):
    val = driver.display_trace_y2_olevel()
    assert isinstance(val, float)
    driver.display_trace_y2_olevel(val)
    assert driver.display_trace_y2_olevel() == val


def test_display_trace_y2_pdivision(driver):
    val = driver.display_trace_y2_pdivision()
    assert isinstance(val, float)
    driver.display_trace_y2_pdivision(val)
    assert driver.display_trace_y2_pdivision() == val


def test_display_trace_y2_rposition(driver):
    driver.display_trace_y2_rposition(10)
    assert driver.display_trace_y2_rposition() == 10


def test_display_trace_y2_sminimum(driver):
    driver.reset()
    driver.display_trace_y2_sminimum(0.0)
    assert driver.display_trace_y2_sminimum() == 0.0


def test_display_trace_y2_unit(driver):
    for unit in ["db", "linear", "db_per_km", "percent"]:
        driver.display_trace_y2_unit(unit)
        assert driver.display_trace_y2_unit() == unit


def test_format_data(driver):
    for fmt in ["ascii", "real64", "real32"]:
        driver.format_data(fmt)
        assert driver.format_data() == fmt


def test_sense_average_count(driver):
    driver.sense_average_count(100)
    assert driver.sense_average_count() == 100


def test_sense_bandwidth_resolution(driver):
    val = driver.sense_bandwidth_resolution()
    assert isinstance(val, float)
    driver.sense_bandwidth_resolution(val)
    assert driver.sense_bandwidth_resolution() == val


def test_sense_chopper(driver):
    for mode in ["off", "switch"]:
        driver.sense_chopper(mode)
        assert driver.sense_chopper() == mode


def test_sense_correction_level_shift(driver):
    val = driver.sense_correction_level_shift()
    assert isinstance(val, float)
    driver.sense_correction_level_shift(val)
    assert driver.sense_correction_level_shift() == val


def test_sense_correction_rvelocity_medium(driver):
    for medium in ["air", "vacuum"]:
        driver.sense_correction_rvelocity_medium(medium)
        assert driver.sense_correction_rvelocity_medium() == medium


def test_sense_correction_wavelength_shift(driver):
    val = driver.sense_correction_wavelength_shift()
    assert isinstance(val, float)
    driver.sense_correction_wavelength_shift(val)
    assert driver.sense_correction_wavelength_shift() == val


def test_sense_sensitivity(driver):
    for mode in ["normal_hold", "normal_auto", "mid", "high1", "high2", "high3", "normal"]:
        driver.sense_sensitivity(mode)
        assert driver.sense_sensitivity() == mode


def test_sense_setting_correction(driver):
    driver.sense_setting_correction("off")
    assert driver.sense_setting_correction() == "off"
    driver.sense_setting_correction("on_mode1")
    assert driver.sense_setting_correction() == "on_mode1"


def test_sense_setting_fconnector(driver):
    for mode in ["normal", "angled"]:
        driver.sense_setting_fconnector(mode)
        assert driver.sense_setting_fconnector() == mode


def test_sense_setting_smoothing(driver):
    driver.sense_setting_smoothing(True)
    assert driver.sense_setting_smoothing() is True
    driver.sense_setting_smoothing(False)
    assert driver.sense_setting_smoothing() is False


def test_sense_sweep_points(driver):
    driver.sense_sweep_points(20001)
    assert driver.sense_sweep_points() == 20001


def test_sense_sweep_points_auto(driver):
    driver.sense_sweep_points_auto(True)
    assert driver.sense_sweep_points_auto() is True
    driver.sense_sweep_points_auto(False)
    assert driver.sense_sweep_points_auto() is False


def test_sense_sweep_segment_points(driver):
    driver.sense_sweep_segment_points(100)
    assert driver.sense_sweep_segment_points() == 100


def test_sense_sweep_speed(driver):
    driver.reset()
    for speed in ["1x", "2x"]:
        driver.sense_sweep_speed(speed)
        assert driver.sense_sweep_speed() == speed


def test_sense_sweep_step(driver):
    val = driver.sense_sweep_step()
    assert isinstance(val, float)
    driver.sense_sweep_step(val)
    assert driver.sense_sweep_step() == val


def test_sense_sweep_time_0nm(driver):
    driver.sense_sweep_time_0nm(10)
    assert driver.sense_sweep_time_0nm() == 10


def test_sense_sweep_time_interval(driver):
    driver.sense_sweep_time_interval(100)
    assert driver.sense_sweep_time_interval() == 100


def test_sense_sweep_tlssync(driver):
    driver.reset()
    driver.sense_sweep_tlssync(True)
    assert driver.sense_sweep_tlssync() is True
    driver.sense_sweep_tlssync(False)
    assert driver.sense_sweep_tlssync() is False


def test_sense_wavelength_center(driver):
    val = driver.sense_wavelength_center()
    assert isinstance(val, float)
    driver.sense_wavelength_center(val)
    assert driver.sense_wavelength_center() == val


def test_sense_wavelength_span(driver):
    val = driver.sense_wavelength_span()
    assert isinstance(val, float)
    driver.sense_wavelength_span(val)
    assert driver.sense_wavelength_span() == val


def test_sense_wavelength_srange(driver):
    driver.sense_wavelength_srange(True)
    assert driver.sense_wavelength_srange() is True
    driver.sense_wavelength_srange(False)
    assert driver.sense_wavelength_srange() is False


def test_sense_wavelength_start(driver):
    val = driver.sense_wavelength_start()
    assert isinstance(val, float)
    driver.sense_wavelength_start(val)
    assert driver.sense_wavelength_start() == val


def test_sense_wavelength_stop(driver):
    val = driver.sense_wavelength_stop()
    assert isinstance(val, float)
    driver.sense_wavelength_stop(val)
    assert driver.sense_wavelength_stop() == val


def test_trace_state(driver):
    for tr in driver.traces:
        tr.state(False)
        assert tr.state() is False
        tr.state(True)
        assert tr.state() is True


def test_trace_active(driver):
    for tr in driver.traces:
        tr.active()


def test_trace_attribute(driver):
    for tr in driver.traces:
        for attribute in ('write', 'fix', 'max hold', 'min hold', 'rolling average', 'calculate'):
            tr.attribute(attribute)
            assert tr.attribute() == attribute


def test_trace_roll_avg(driver):
    for tr in driver.traces:
        tr.roll_avg(10)
        assert tr.roll_avg() == 10
        tr.roll_avg(2)
        assert tr.roll_avg() == 2


def test_trace_data_sample_number(driver):
    for tr in driver.traces:
        val = tr.data_sample_number()
        assert isinstance(val, int)
        assert val >= 0


def test_trace_delete(driver):
    for tr in driver.traces:
        tr.delete()


def test_trace_delete_all(driver):
    driver.delete_all_traces()


def test_trace_write(driver):
    for tr in driver.traces:
        tr.write_mode()
        assert tr.attribute() == 'write'


def test_trace_fix(driver):
    for tr in driver.traces:
        tr.fix()
        assert tr.attribute() == 'fix'


def test_trace_max_hold(driver):
    for tr in driver.traces:
        tr.max_hold()
        assert tr.attribute() == 'max hold'


def test_trace_min_hold(driver):
    for tr in driver.traces:
        tr.min_hold()
        assert tr.attribute() == 'min hold'


def test_sweep_mode(driver):
    for mode in ("single", "repeat", "auto", "segment"):
        driver.sweep_mode(mode)
        assert driver.sweep_mode() == mode


def test_auto(driver):
    driver.auto()
    assert driver.sweep_mode() is "auto"


def test_single(driver):
    driver.single()
    assert driver.sweep_mode() is "single"


def test_repeat(driver):
    driver.repeat()
    assert driver.sweep_mode() is "repeat"
