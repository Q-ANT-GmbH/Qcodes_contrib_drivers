import logging
from typing import TYPE_CHECKING

import numpy as np
from qcodes.instrument import VisaInstrument, VisaInstrumentKWArgs, InstrumentChannel, InstrumentBaseKWArgs, Instrument
from qcodes.parameters import Parameter, ParameterWithSetpoints, ParamRawDataType, create_on_off_val_mapping
from qcodes.validators import Enum, Ints, Numbers, Arrays

if TYPE_CHECKING:
    from typing_extensions import Unpack

log = logging.getLogger(__name__)


class ParameterTimeAxis(Parameter):

    def get_raw(self):
        p = self.instrument.get_waveform_preamble()
        return np.linspace(p["xorigin"], p["xorigin"] + p["xincrement"] * p["points"], p["points"])


class ScopeArrayRaw(Parameter):
    def get_raw(self) -> ParamRawDataType:

        # Ensure STOP
        if self.root_instrument.trigger_status() != "STOP":
            raise RuntimeError("Waveform data can only be read when the oscilloscope is in the STOP state.")

        # Ensure RAW
        if self.root_instrument.waveform_mode() != 'raw':
            raise RuntimeError("Only raw mode is supported for now.")

        # Waveform source
        self.root_instrument.waveform_source(f"CHAN{self.instrument.channel}")

        # Read data
        self.root_instrument.write(":WAVeform:DATA?")
        bytestream = self.root_instrument.visa_handle.read_raw()
        n = int(bytestream[1:2].decode("ascii"))
        l = int(bytestream[2:2 + n].decode("ascii"))
        waveform = bytestream[2 + n:].strip()

        # Convert to ndarray
        if self.root_instrument.waveform_format() == "byte":
            waveform = np.frombuffer(waveform, dtype=np.uint8, count=l)
        else:
            waveform = np.frombuffer(waveform, dtype=np.uint16, count=l)

        return waveform


class ScopeArray(ParameterWithSetpoints):

    def get_raw(self) -> ParamRawDataType:
        trace_raw = self.instrument.trace_raw()

        # Covert from ADC values to Voltage
        p = self.root_instrument.get_waveform_preamble()
        return (trace_raw - p["yreference"] - p["yorigin"]) * p["yincrement"]


class RigolDS8000RChannel(InstrumentChannel):

    def __init__(
            self,
            parent: Instrument,
            name: str,
            channel: int,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self.model = self._parent.model
        self.channel = channel

        self.bandwidth_limit: Parameter = self.add_parameter(
            "bandwidth_limit",
            set_cmd=f":CHANnel{channel}:BWLimit {{}}",
            get_cmd=f":CHANnel{channel}:BWLimit?",
            vals=Enum("20M", "OFF"),
        )
        """Bandwidth limit of the specified channel"""

        self.coupling: Parameter = self.add_parameter(
            "coupling",
            set_cmd=f":CHANnel{channel}:COUPling {{}}",
            get_cmd=f":CHANnel{channel}:COUPling?",
            vals=Enum("AC", "DC", "GND"),
        )
        """Coupling mode of the specified channel"""

        self.display: Parameter = self.add_parameter(
            "display",
            set_cmd=f":CHANnel{channel}:DISPlay {{}}",
            get_cmd=f":CHANnel{channel}:DISPlay?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0)
        )
        """Whether the specified channel is displayed or not"""

        self.invert: Parameter = self.add_parameter(
            "invert",
            set_cmd=f":CHANnel{channel}:INVert {{}}",
            get_cmd=f":CHANnel{channel}:INVert?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0)
        )
        """Whether the specified channel is inverted or not"""

        self.offset: Parameter = self.add_parameter(
            "offset",
            unit="V",
            set_cmd=f":CHANnel{channel}:OFFSet {{:f}}",
            get_cmd=f":CHANnel{channel}:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Vertical offset of the specified channel in (V)"""

        self.delay_calibration_time: Parameter = self.add_parameter(
            "delay_calibration_time",
            unit="s",
            set_cmd=f":CHANnel{channel}:TCALibrate {{}}",
            get_cmd=f":CHANnel{channel}:TCALibrate?",
            vals=Numbers(-100e-9, 100e-9),
            get_parser=float
        )
        """Delay calibration time (used to calibrate the zero offset of the corresponding channel) of the specified channel in (s)"""

        self.scale: Parameter = self.add_parameter(
            "scale",
            unit="V",
            set_cmd=f":CHANnel{channel}:SCALe {{:f}}",
            get_cmd=f":CHANnel{channel}:SCAle?",
            vals=Numbers(1e-3, 10),
            get_parser=float
        )
        """Vertical scale of the specified channel in (V)"""

        self.impedance: Parameter = self.add_parameter(
            "impedance",
            set_cmd=f":CHANnel{channel}:IMPedance {{}}",
            get_cmd=f":CHANnel{channel}:IMPedance?",
            val_mapping={"50 Ohm": "FIFT", "1 MOhm": "OMEG"},
        )
        """Input impedance of the specified channel"""

        self.probe: Parameter = self.add_parameter(
            "probe",
            set_cmd=f":CHANnel{channel}:PROBe {{}}",
            get_cmd=f":CHANnel{channel}:PROBe?",
            vals=Enum(0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5,
                      1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000),
            get_parser=float
        )
        """Probe ratio of the specified channel"""

        self.probe_delay: Parameter = self.add_parameter(
            "probe_delay",
            unit="s",
            set_cmd=f":CHANnel{channel}:PROBe:DELay {{}}",
            get_cmd=f":CHANnel{channel}:PROBe:DELay?",
            vals=Numbers(-100e-9, 100e-9),
            get_parser=float
        )
        """Probe delay time of the specified channel in (s)"""

        self.probe_bias: Parameter = self.add_parameter(
            "probe_bias",
            unit="V",
            set_cmd=f":CHANnel{channel}:PROBe:BIAS {{}}",
            get_cmd=f":CHANnel{channel}:PROBe:BIAS?",
            vals=Numbers(-5, 5),
            get_parser=float
        )
        """Probe bias voltage of the specified channel in (V)"""

        self.units: Parameter = self.add_parameter(
            "units",
            set_cmd=f":CHANnel{channel}:UNITs {{}}",
            get_cmd=f":CHANnel{channel}:UNITs?",
            val_mapping={"volt": "VOLT", "watt": "WATT", "ampere": "AMP", "unknown": "UNKN"},
        )
        """Amplitude display unit of the specified channel"""

        self.vernier: Parameter = self.add_parameter(
            "vernier",
            set_cmd=f":CHANnel{channel}:VERNier {{}}",
            get_cmd=f":CHANnel{channel}:VERNier?",
            val_mapping=create_on_off_val_mapping(1, 0)
        )
        """On/off status of the fine adjustment function of the vertical scale of the specified channel"""

        self.position: Parameter = self.add_parameter(
            "position",
            set_cmd=f":CHANnel{channel}:POSition {{:f}}",
            get_cmd=f":CHANnel{channel}:POSition?",
            vals=Numbers(-100, 100),
            get_parser=float
        )
        """Offset calibration voltage for calibrating the zero point of the specified channel in (V)"""

        self.trace_raw: Parameter = self.add_parameter(
            "trace_raw",
            parameter_class=ScopeArrayRaw,
            vals=Arrays(shape=(self.root_instrument.waveform_points.get,)),
            snapshot_value=False
        )
        """Trace of the specified channel in ADC units"""

        self.trace: ParameterWithSetpoints = self.add_parameter(
            "trace",
            unit="V",
            parameter_class=ScopeArray,
            setpoints=(self.parent.timebase_axis,),
            vals=Arrays(shape=(self.root_instrument.waveform_points.get,)),
            snapshot_value=False
        )
        """Trace of the specified channel in (V)"""

    def calibrate(self) -> None:
        """Starts calibration of the active probe connected to the specified channel"""
        self.write(f":CHANnel{self.channel}:CSTart")


class RigolDS8000R(VisaInstrument):
    """
    Driver for the Rigol DS8000-R series of Oscilloscopes
    """

    default_terminator = "\n"

    MODELS = [
        "DS8104-R",
        "DS8204-R",
        "DS8034-R",
    ]
    """Models part of the Rigol DS8000-R series of Oscilloscopes """

    def __init__(
            self,
            name: str,
            address: str,
            **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ):
        super().__init__(name, address, **kwargs)

        self.model = self.get_idn()["model"]

        if self.model in self.MODELS:
            i = self.MODELS.index(self.model)
            self.n_o_ch = [4, 4, 4][i]
            self.bw_limit = [
                ('20M', '250M', '500M', 'OFF'),
                ('20M', '250M', '500M', 'OFF'),
                ('20M', '250M', 'OFF'),
            ][i]
        elif self.model is None:
            raise KeyError("Could not determine model")
        else:
            raise KeyError("Model code " + self.model + " is not recognized")

        self.acquire_averages = self.add_parameter(
            "acquire_averages",
            set_cmd=":ACQuire:AVERages {}",
            get_cmd=":ACQuire:AVERages?",
            vals=Enum(*2 ** np.arange(1, 17)),
            get_parser=int,
        )
        """Number of averages in average acquisition mode (2–65536, power of 2)."""

        self.acquire_mdepth: Parameter = self.add_parameter(
            "acquire_mdepth",
            set_cmd=":ACQuire:MDEPth {:s}",
            get_cmd=":ACQuire:MDEPth?",
            vals=Enum("AUTO", "1k", "10k", "100k", "1M", "10M", "100M", "125M", "250M", "500M"),
            get_parser=float
        )
        """Memory depth of the oscilloscope"""

        self.acquire_type = self.add_parameter(
            "acquire_type",
            set_cmd=":ACQuire:TYPE {}",
            get_cmd=":ACQuire:TYPE?",
            val_mapping={
                "normal": "NORM",
                "averages": "AVER",
                "peak": "PEAK",
                "high_resolution": "HRES",
            },
        )
        """Acquisition mode (NORMal, AVERages, PEAK, HRESolution)."""

        self.acquire_srate = self.add_parameter(
            "acquire_srate",
            get_cmd=":ACQuire:SRATe?",
            unit="1/s",
            get_parser=float,
        )
        """Current sample rate in samples per second."""

        self.acquire_aalias = self.add_parameter(
            "acquire_aalias",
            set_cmd=":ACQuire:AALias {}",
            get_cmd=":ACQuire:AALias?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enable or disable anti-aliasing."""

        self.timebase_delay_enable: Parameter = self.add_parameter(
            "timebase_delay_enable",
            set_cmd=f":TIMebase:DELay:ENABle {{}}",
            get_cmd=f":TIMebase:DELay:ENABLe?",
            val_mapping=create_on_off_val_mapping(1, 0),
        )
        """On/off status of the delayed sweep"""

        self.timebase_delay_offset: Parameter = self.add_parameter(
            "timebase_delay_offset",
            unit="s",
            set_cmd=f":TIMebase:DElay:OFFSet {{}}",
            get_cmd=f":TIMebase:DElay:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Offset of the delayed timebase in (s)"""

        self.timebase_delay_scale: Parameter = self.add_parameter(
            "timebase_delay_scale",
            unit="s/div",
            set_cmd=f":TIMebase:DElay:SCALe {{}}",
            get_cmd=f":TIMebase:DElay:SCALe?",
            vals=Numbers(),
            get_parser=float
        )
        """Scale of the delayed timebase in (s/div)"""

        self.timebase_offset: Parameter = self.add_parameter(
            "timebase_offset",
            unit="s",
            set_cmd=f":TIMebase:OFFSet {{}}",
            get_cmd=f":TIMebase:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Offset of the main time base in (s)"""

        self.timebase_scale: Parameter = self.add_parameter(
            "timebase_scale",
            unit="s/div",
            set_cmd=f":TIMebase:SCALe {{}}",
            get_cmd=f":TIMebase:SCALe?",
            vals=Numbers(),
            get_parser=float
        )
        """Scale of the main time base in (s/div)"""

        self.timebase_mode: Parameter = self.add_parameter(
            "timebase_mode",
            set_cmd=f":TIMebase:MODE {{}}",
            get_cmd=f":TIMebase:MODE?",
            val_mapping={"yt": "MAIN", "xy": "XY", "roll": "ROLL"},
        )
        """Horizontal timebase mode"""

        self.timebase_href_mode: Parameter = self.add_parameter(
            "timebase_href_mode",
            set_cmd=f":TIMebase:HREFerence:MODE {{}}",
            get_cmd=f":TIMebase:HREFerence:MODE?",
            val_mapping={
                "center": "CENT",
                "left_border": "LB",
                "right_border": "RB",
                "trigger": "TRIG",
                "user": "USER",
            },
        )
        """Horizontal reference mode"""

        self.timebase_href_position: Parameter = self.add_parameter(
            "timebase_href_position",
            set_cmd=f":TIMebase:HREFerence:POSition {{}}",
            get_cmd=f":TIMebase:HREFerence:POSition?",
            vals=Ints(-500, 500),
            get_parser=int
        )
        """Reference position when the waveforms are expanded or compressed horizontally"""

        self.timebase_vernier: Parameter = self.add_parameter(
            "timebase_vernier",
            set_cmd=f":TIMebase:VERNier {{}}",
            get_cmd=f":TIMebase:VERNier?",
            val_mapping=create_on_off_val_mapping(1, 0),
        )
        """On/off status of the fine adjustment function of the horizontal scale"""

        self.trigger_mode = self.add_parameter(
            "trigger_mode",
            set_cmd=":TRIGger:MODE {}",
            get_cmd=":TRIGger:MODE?",
            val_mapping={
                "edge": "EDGE",
                "pulse": "PULS",
                "slope": "SLOP",
                "video": "VID",
                "pattern": "PATT",
                "duration": "DUR",
                "timeout": "TIM",
                "runt": "RUNT",
                "window": "WIND",
                "delay": "DEL",
                "setup": "SET",
                "nedge": "NEDG",
                "rs232": "RS232",
                "iic": "IIC",
                "spi": "SPI",
                "can": "CAN",
                "flexray": "FLEX",
                "lin": "LIN",
                "iis": "IIS",
                "m1553": "M1553",
            },
        )
        """Trigger type"""

        self.trigger_coupling = self.add_parameter(
            "trigger_coupling",
            set_cmd=":TRIGger:COUPling {}",
            get_cmd=":TRIGger:COUPling?",
            val_mapping={
                "ac": "AC",
                "dc": "DC",
                "lfreject": "LFR",
                "hfreject": "HFR",
            },
        )
        """Trigger coupling type (AC, DC, LFReject, HFReject)."""

        self.trigger_sweep = self.add_parameter(
            "trigger_sweep",
            set_cmd=":TRIGger:SWEep {}",
            get_cmd=":TRIGger:SWEep?",
            val_mapping={
                "auto": "AUTO",
                "normal": "NORM",
                "single": "SING",
            },
        )
        """Trigger sweep mode (AUTO, NORMal, SINGle)."""

        self.trigger_holdoff = self.add_parameter(
            "trigger_holdoff",
            unit="s",
            set_cmd=":TRIGger:HOLDoff {}",
            get_cmd=":TRIGger:HOLDoff?",
            vals=Numbers(8e-9, 10),
            get_parser=float,
        )
        """Trigger holdoff time in seconds (8 ns – 10 s)."""

        self.trigger_noise_reject = self.add_parameter(
            "trigger_noise_reject",
            set_cmd=":TRIGger:NREJect {}",
            get_cmd=":TRIGger:NREJect?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enables or disables trigger noise rejection."""

        self.trigger_ext_delay = self.add_parameter(
            "trigger_ext_delay",
            unit="s",
            set_cmd=":TRIGger:EXTDelay {:f}",
            get_cmd=":TRIGger:EXTDelay?",
            vals=Numbers(-500000, 500000),
            get_parser=float,
        )
        """External trigger delay in seconds (-500 ns – 500 ns)."""

        self.trigger_edge_source = self.add_parameter(
            "trigger_edge_source",
            set_cmd=":TRIGger:EDGE:SOURce {}",
            get_cmd=":TRIGger:EDGE:SOURce?",
            val_mapping={
                "ch1": "CHAN1",
                "ch2": "CHAN2",
                "ch3": "CHAN3",
                "ch4": "CHAN4",
                "acline": "ACL",
                "ext": "EXT",
            },
        )
        """Edge trigger source (CHAN1–4, ACLine, EXT)."""

        self.trigger_edge_slope = self.add_parameter(
            "trigger_edge_slope",
            set_cmd=":TRIGger:EDGE:SLOPe {}",
            get_cmd=":TRIGger:EDGE:SLOPe?",
            val_mapping={
                "positive": "POS",
                "negative": "NEG",
                "rfall": "RFAL",
            },
        )
        """Edge trigger slope (POSitive, NEGative, RFALl)."""

        self.trigger_edge_level = self.add_parameter(
            "trigger_edge_level",
            set_cmd=":TRIGger:EDGE:LEVel {}",
            get_cmd=":TRIGger:EDGE:LEVel?",
            unit="V",
            vals=Numbers(-5, 5),
            get_parser=float,
        )
        """Edge trigger level in volts."""

        self.trigger_pulse_source = self.add_parameter(
            "trigger_pulse_source",
            set_cmd=":TRIGger:PULSe:SOURce {}",
            get_cmd=":TRIGger:PULSe:SOURce?",
            val_mapping={
                "ch1": "CHAN1",
                "ch2": "CHAN2",
                "ch3": "CHAN3",
                "ch4": "CHAN4",
            },
        )
        """Pulse trigger source (CHAN1–4)."""

        self.trigger_pulse_when = self.add_parameter(
            "trigger_pulse_when",
            set_cmd=":TRIGger:PULSe:WHEN {}",
            get_cmd=":TRIGger:PULSe:WHEN?",
            val_mapping={
                "greater": "GRE",
                "less": "LESS",
                "gless": "GLES",
            },
        )
        """Pulse trigger condition (GREater, LESS, GLESs)."""

        self.trigger_pulse_uwidth = self.add_parameter(
            "trigger_pulse_uwidth",
            set_cmd=":TRIGger:PULSe:UWIDth {}",
            get_cmd=":TRIGger:PULSe:UWIDth?",
            unit="s",
            vals=Numbers(0, 10),
            get_parser=float,
        )
        """Pulse trigger upper width limit in seconds (up to 10 s)."""

        self.trigger_pulse_lwidth = self.add_parameter(
            "trigger_pulse_lwidth",
            set_cmd=":TRIGger:PULSe:LWIDth {}",
            get_cmd=":TRIGger:PULSe:LWIDth?",
            unit="s",
            vals=Numbers(800e-12, 10),
            get_parser=float,
        )
        """Pulse trigger lower width limit in seconds (≥ 800 ps)."""

        self.trigger_pulse_level = self.add_parameter(
            "trigger_pulse_level",
            set_cmd=":TRIGger:PULSe:LEVel {}",
            get_cmd=":TRIGger:PULSe:LEVel?",
            unit="V",
            vals=Numbers(-5, 5),
            get_parser=float,
        )
        """Pulse trigger level in volts."""

        self.waveform_source: Parameter = self.add_parameter(
            "waveform_source",
            set_cmd=f":WAVeform:SOURce {{}}",
            get_cmd=f":WAVeform:SOURce?",
            vals=Enum("CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH1", "MATH2", "MATH3", "MATH4"),
        )
        """Source channel of waveform data reading"""

        self.waveform_mode: Parameter = self.add_parameter(
            "waveform_mode",
            set_cmd=f":WAVeform:MODE {{}}",
            get_cmd=f":WAVeform:MODE?",
            val_mapping={"normal": "NORM", "maximum": "MAX", "raw": "RAW"},
        )
        """Mode of the waveform_data command in reading data"""

        self.waveform_format: Parameter = self.add_parameter(
            "waveform_format",
            set_cmd=f":WAVeform:FORMat {{}}",
            get_cmd=f":WAVeform:FORMat?",
            val_mapping={"word": "WORD", "byte": "BYTE", "ascii": "ASC"},
        )
        """Return format of the waveform data points to be read"""

        self.waveform_points: Parameter = self.add_parameter(
            "waveform_points",
            set_cmd=":WAVeform:POINts {:d}",
            get_cmd=":WAVeform:POINts?",
            vals=Ints(),
            get_parser=int
        )
        """Number of waveform points to be read"""

        self.waveform_start: Parameter = self.add_parameter(
            "waveform_start",
            set_cmd=f":WAVeform:STARt {{}}",
            get_cmd=f":WAVeform:STARt?",
            vals=Ints(),
            get_parser=int
        )
        """Start position of the waveform data reading"""

        self.waveform_stop: Parameter = self.add_parameter(
            "waveform_stop",
            set_cmd=f":WAVeform:STOP {{}}",
            get_cmd=f":WAVeform:STOP?",
            vals=Ints(),
            get_parser=int
        )
        """Stop position of the waveform data reading"""

        self.timebase_axis: ParameterTimeAxis = self.add_parameter(
            "timebase_axis",
            unit="s",
            parameter_class=ParameterTimeAxis,
            vals=Arrays(shape=(self.waveform_points.get,)),
            snapshot_value=False
        )
        """Array of values corresponding to the time axes (w.r.t to trigger point)"""

        self.ch = []
        """Instrument channels"""

        for i in range(1, self.n_o_ch + 1):
            channel = RigolDS8000RChannel(self, f"ch{i}", i)
            self.ch += [self.add_submodule(f"ch{i}", channel)]

    def trigger_status(self):
        """Queries the current trigger status"""
        return self.ask(":TRIGger:STATus?")

    def get_waveform_preamble(self):
        """Returns 10 waveform parameters seperated by comma"""
        preample = self.ask(":WAVeform:PREamble?")
        preample = preample.split(",")
        preample_dict = {
            "format": ["BYTE", "WORD", "ASC"][int(preample[0])],
            "type": ["NORM", "MAX", "RAW"][int(preample[1])],
            "points": int(preample[2]),
            "count": int(preample[3]),
            "xincrement": float(preample[4]),
            "xorigin": float(preample[5]),
            "xreference": float(preample[6]),
            "yincrement": float(preample[7]),
            "yorigin": float(preample[8]),
            "yreference": float(preample[9]),
        }
        return preample_dict

    def autoscale(self) -> None:
        """Enables the waveform auto setting function"""
        self.write(":AUToscale")

    def clear(self) -> None:
        """Clears all the waveforms on the screen"""
        self.write(":CLEar")

    def run(self) -> None:
        """Start the oscilloscope"""
        self.write(":RUN")

    def stop(self) -> None:
        """Stop the oscilloscope"""
        self.write(":STOP")

    def single(self) -> None:
        """Sets the trigger mode of the oscilloscope to 'Single' """
        self.write(":SINGle")

    def trigger_force(self) -> None:
        """Generates a trigger signal forcibly"""
        self.write(":TFORce")

    def reset(self):
        """Resets the instrument to its factory default settings"""
        self.write("*RST")
