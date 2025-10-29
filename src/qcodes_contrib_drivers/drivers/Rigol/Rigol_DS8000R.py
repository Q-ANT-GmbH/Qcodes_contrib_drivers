from typing import TYPE_CHECKING

import numpy as np
from qcodes.instrument import VisaInstrument, VisaInstrumentKWArgs, InstrumentChannel, InstrumentBaseKWArgs, Instrument
from qcodes.parameters import Parameter
from qcodes.parameters import create_on_off_val_mapping
from qcodes.validators import Enum, Ints, Numbers

if TYPE_CHECKING:
    from typing_extensions import Unpack
    from numpy.typing import NDArray
    from typing import Optional


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
            set_cmd=f":CHANnel{channel}:OFFSet {{:f}}",
            get_cmd=f":CHANnel{channel}:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Vertical offset of the specified channel in (V)"""

        self.delay_calibration_time: Parameter = self.add_parameter(
            "delay_calibration_time",
            set_cmd=f":CHANnel{channel}:TCALibrate {{}}",
            get_cmd=f":CHANnel{channel}:TCALibrate?",
            vals=Numbers(-100e-9, 100e-9),
            get_parser=float
        )
        """Delay calibration time (used to calibrate the zero offset of the corresponding channel) of the specified channel in (s)"""

        self.scale: Parameter = self.add_parameter(
            "scale",
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
            set_cmd=f":CHANnel{channel}:PROBe:DELay {{}}",
            get_cmd=f":CHANnel{channel}:PROBe:DELay?",
            vals=Numbers(-100e-9, 100e-9),
            get_parser=float
        )
        """Probe delay time of the specified channel in (s)"""

        self.probe_bias: Parameter = self.add_parameter(
            "probe_bias",
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

    def calibrate(self) -> None:
        """Starts calibration of the active probe connected to the specified channel"""
        self.write(f":CHANnel{self.channel}:CSTart")


class RigolDS8000R(VisaInstrument):
    """
    Driver for the Rigol DS8000-R series of Oscilloscopes
    """

    default_terminator = "\n"

    def __init__(
            self,
            name: str,
            address: str,
            **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ):
        super().__init__(name, address, **kwargs)

        self.model = self.get_idn()["model"]

        models = [
            "DS8104-R",
            "DS8204-R",
            "DS8034-R",
        ]

        if self.model in models:
            i = models.index(self.model)
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

        self.ch = []
        """Instrument channels"""

        for i in range(1, self.n_o_ch + 1):
            channel = RigolDS8000RChannel(self, f"ch{i}", i)
            self.ch += [self.add_submodule(f"ch{i}", channel)]

        self.acquire_mdepth: Parameter = self.add_parameter(
            "acquire_mdepth",
            set_cmd=":ACQuire:MDEPth {:s}",
            get_cmd=":ACQuire:MDEPth?",
            vals=Enum("AUTO", "1k", "10k", "100k", "1M", "10M", "100M", "125M", "250M", "500M"),
            get_parser=float
        )
        """Memory depth of the oscilloscope"""

        self.timebase_delay_enable: Parameter = self.add_parameter(
            "timebase_delay_enable",
            set_cmd=f":TIMebase:DELay:ENABle {{}}",
            get_cmd=f":TIMebase:DELay:ENABLe?",
            val_mapping=create_on_off_val_mapping(1, 0),
        )
        """On/off status of the delayed sweep"""

        self.timebase_delay_offset: Parameter = self.add_parameter(
            "timebase_delay_offset",
            set_cmd=f":TIMebase:DElay:OFFSet {{}}",
            get_cmd=f":TIMebase:DElay:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Offset of the delayed timebase in (s)"""

        self.timebase_delay_scale: Parameter = self.add_parameter(
            "timebase_delay_scale",
            set_cmd=f":TIMebase:DElay:SCALe {{}}",
            get_cmd=f":TIMebase:DElay:SCALe?",
            vals=Numbers(),
            get_parser=float
        )
        """Scale of the delayed timebase in (s/div)"""

        self.timebase_offset: Parameter = self.add_parameter(
            "timebase_offset",
            set_cmd=f":TIMebase:OFFSet {{}}",
            get_cmd=f":TIMebase:OFFSet?",
            vals=Numbers(),
            get_parser=float
        )
        """Offset of the main time base in (s)"""

        self.timebase_scale: Parameter = self.add_parameter(
            "timebase_scale",
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

    def get_trace(self, source: int | str, fmt: str = "byte", pts: Optional[int] = None) -> NDArray[np.uint8]:
        """
        Reads a waveform from the oscilloscope in STOP state.

        Args:
            source: channel like 1..n or SCPI source string (e.g. "CHAN1", "MATH3", etc)
            fmt: "byte" (8-bit) or "word" (16-bit)
            pts: optional number of points to request

        Returns:
            ndarray of dtype uint8 (byte) or uint16 (word)
        """

        # Ensure STOP
        if self.trigger_status() != "STOP":
            raise RuntimeError("Waveform data can only be read when the oscilloscope is in the STOP state.")

        # Waveform source
        if isinstance(source, int) and (0 < source <= self.n_o_ch):
            self.waveform_source(f"CHAN{source}")
        else:
            self.waveform_source(source)

        # Set format and mode
        fmt = fmt.lower()
        if fmt not in {"byte", "word"}:
            raise ValueError('format must be "byte" or "word"')

        self.waveform_format(fmt)
        self.waveform_mode("raw")

        if pts is not None:
            self.waveform_points(int(pts))

        # Read data
        self.write(":WAVeform:DATA?")
        bytestream = self.visa_handle.read_raw()
        n = int(bytestream[1:2].decode("ascii"))
        l = int(bytestream[2:2 + n].decode("ascii"))
        waveform = bytestream[2 + n:].strip()

        # Check that all data is present
        assert len(waveform) == l

        # Convert to ndarray
        if fmt == "byte":
            return np.frombuffer(waveform, dtype=np.uint8, count=l)
        else:
            return np.frombuffer(waveform, dtype=np.uint16, count=l)

    def autoscale(self) -> None:
        self.write(":AUToscale")

    def clear(self) -> None:
        self.write(":CLEar")

    def run(self) -> None:
        self.write(":RUN")

    def stop(self) -> None:
        self.write(":STOP")

    def single(self) -> None:
        self.write(":SINGle")

    def trigger_force(self) -> None:
        self.write(":TFORce")

    def reset(self):
        """Resets the instrument to its factory default settings"""
        self.write("*RST")
