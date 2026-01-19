import logging
import numpy as np

from typing import TYPE_CHECKING

from qcodes.instrument import VisaInstrument, VisaInstrumentKWArgs, InstrumentChannel, InstrumentBaseKWArgs, Instrument, \
    ChannelList
from qcodes.parameters import Parameter, create_on_off_val_mapping, ParamRawDataType
from qcodes.validators import Enum, Ints, Strings

if TYPE_CHECKING:
    from typing_extensions import Unpack

log = logging.getLogger(__name__)


class YokogawaData(Parameter):
    def __init__(self, name: str, format: str = 'real64', get_cmd: str = None, **kwargs) -> None:
        super().__init__(name, **kwargs)

        if format not in ['real64', 'real32']:
            raise NotImplementedError

        self.format = format
        self.get_cmd = get_cmd

    def get_raw(self) -> ParamRawDataType:
        # Set data format
        self.root_instrument.format_data(self.format)

        # Read data
        self.root_instrument.write(self.get_cmd)
        bytestream = self.root_instrument.visa_handle.read_raw()
        n = int(bytestream[1:2].decode("ascii"))
        l = int(bytestream[2:2 + n].decode("ascii"))
        data = bytestream[2 + n:].strip()

        # Convert to ndarray
        if self.format == 'real64':
            data = np.frombuffer(data, dtype=np.float64, count=l // 8)
        elif self.format == 'real32':
            data = np.frombuffer(data, dtype=np.float32, count=l // 4)

        return data


class YokogawaAQ637xChannel(InstrumentChannel):
    def __init__(
            self,
            parent: Instrument,
            name: str,
            trace: str,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self.model = self._parent.model
        self.trace = trace

        self.state: Parameter = self.add_parameter(
            "state",
            set_cmd=f":TRACe:STATe:{trace} {{}}",
            get_cmd=f":TRACe:STATe:{trace}?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        "Sets/queries the display status of the specified trace"

        self.attribute: Parameter = self.add_parameter(
            "attribute",
            set_cmd=f":TRACe:ATTRibute:{trace} {{}}",
            get_cmd=f":TRACe:ATTRibute:{trace}?",
            val_mapping={
                "write": 0,
                "fix": 1,
                "max hold": 2,
                "min hold": 3,
                "rolling average": 4,
                "calculate": 5
            },
        )
        """Trace Attribute"""

        self.roll_avg: Parameter = self.add_parameter(
            "roll_avg",
            set_cmd=f":TRACe:ATTRibute:RAVG:{trace} {{}}",
            get_cmd=f":TRACe:ATTRibute:RAVG:{trace}?",
            get_parser=int,
            vals=Ints(2, 100)
        )
        """ROLL AVG averaging count for the specified trace"""

        self.data_sample_number: Parameter = self.add_parameter(
            "data_sample_number",
            get_cmd=f":TRACe:DATA:SNUMber? {trace}",
            get_parser=int,
        )
        """Number of sampled data points for this trace."""

        self.data_x: YokogawaData = self.add_parameter(
            "data_x",
            get_cmd=f":TRACe:DATA:X? {trace}",
            parameter_class=YokogawaData,
            snapshot_value=False
        )
        """Wavelength axis data for this trace."""

        self.data_y: YokogawaData = self.add_parameter(
            "data_y",
            get_cmd=f":TRACe:DATA:Y? {trace}",
            parameter_class=YokogawaData,
            snapshot_value=False
        )
        """Level axis data for this trace."""

    def active(self) -> None:
        """Set trace in ACTIVE mode"""
        self.write(f":TRACe:ACTive {self.trace}")

    def delete(self) -> None:
        """Delete the data of this trace."""
        self.write(f":TRACe:DELete {self.trace}")

    def write_mode(self) -> None:
        """Set trace in WRITE mode"""
        self.write(f":TRACe:ATTRibute:{self.trace} WRITe")

    def fix(self) -> None:
        """Set trace in FIX mode"""
        self.write(f":TRACe:ATTRibute:{self.trace} FIX")

    def max_hold(self) -> None:
        """Set trace in MAX HOLD mode"""
        self.write(f":TRACe:ATTRibute:{self.trace} MAX")

    def min_hold(self) -> None:
        """Set trace in MIN HOLD mode"""
        self.write(f":TRACe:ATTRibute:{self.trace} MIN")


class YokogawaAQ637x(VisaInstrument):
    """
    Driver for the Yokogawa AQ6370C/AQ6370D/AQ6373/AQ6373B/AQ6375/AQ6375B Optical Spectrum Analyzer.
    """

    default_terminator = "\n"

    MODELS = [
        "AQ6370C",
        "AQ6370D",
        "AQ6373",
        "AQ6373B",
        "AQ6375",
        "AQ6375B",
    ]
    """List of support Optical Spectrum Analyzer"""

    def __init__(
            self,
            name: str,
            address: str,
            **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ):
        super().__init__(name, address, **kwargs)

        self.model = self.get_idn()["model"]
        if self.model is None:
            raise KeyError("Could not determine model")
        elif self.model not in self.MODELS:
            raise KeyError("Model code " + self.model + " is not recognized")

        # Create channels (called traces for OSA)
        traces = ChannelList(self, "ch", YokogawaAQ637xChannel)
        for tr in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
            traces.append(YokogawaAQ637xChannel(self, f"TR{tr}", f"TR{tr}"))
        self.traces = traces.to_channel_tuple()
        """Instrument traces (aka channels)"""

        ## Common Commands

        self.event_status_enable: Parameter = self.add_parameter(
            "event_status_enable",
            set_cmd="*ESE {}",
            get_cmd="*ESE?",
            vals=Ints(0, 255),
            get_parser=int,
        )
        """Standard event status enable register (0–255)"""

        self.event_status_register: Parameter = self.add_parameter(
            "event_status_register",
            get_cmd="*ESR?",
            get_parser=int,
        )
        """Standard event status register (read and clear)"""

        self.operation_complete: Parameter = self.add_parameter(
            "operation_complete",
            set_cmd="*OPC",
            get_cmd="*OPC?",
            get_parser=int,
        )
        """Operation complete flag (sets/queries OPC bit in ESR)"""

        self.service_request_enable: Parameter = self.add_parameter(
            "service_request_enable",
            set_cmd="*SRE {}",
            get_cmd="*SRE?",
            vals=Ints(0, 255),
            get_parser=int,
        )
        """Service request enable register (0–255)"""

        self.status_byte: Parameter = self.add_parameter(
            "status_byte",
            get_cmd="*STB?",
            get_parser=int,
        )
        """Status byte register (read-only)"""

        self.self_test: Parameter = self.add_parameter(
            "self_test",
            get_cmd="*TST?",
            get_parser=int,
        )
        """Run instrument self-test and return status code"""

        ## Instrument specific commands
        # Display Sub System Commands

        self.display_color: Parameter = self.add_parameter(
            "display_color",
            set_cmd=":DISPlay:COLor {}",
            get_cmd=":DISPlay:COLor?",
            vals=Ints(0, 5),
            get_parser=int,
        )
        """Screen color mode (0 = B/W, 1–5 = color modes)"""

        self.display_enabled: Parameter = self.add_parameter(
            "display_enabled",
            set_cmd=":DISPlay {}",
            get_cmd=":DISPlay?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enable or disable the display"""

        self.display_overview_position: Parameter = self.add_parameter(
            "display_overview_position",
            set_cmd=":DISPlay:OVIew:POSition {}",
            get_cmd=":DISPlay:OVIew:POSition?",
            val_mapping={
                "off": 0,
                "left": 1,
                "right": 2,
            },
        )
        """Overview display position (off, left, right)"""

        self.display_overview_size: Parameter = self.add_parameter(
            "display_overview_size",
            set_cmd=":DISPlay:OVIew:SIZE {}",
            get_cmd=":DISPlay:OVIew:SIZE?",
            val_mapping={
                "large": 0,
                "small": 1,
            },
        )
        """Overview display size (large or small)"""

        self.display_split: Parameter = self.add_parameter(
            "display_split",
            set_cmd=":DISPlay:SPLit {}",
            get_cmd=":DISPlay:SPLit?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enable or disable split screen display"""

        self.display_split_hold_lower: Parameter = self.add_parameter(
            "display_split_hold_lower",
            set_cmd=":DISPlay:SPLit:HOLD:LOWer {}",
            get_cmd=":DISPlay:SPLit:HOLD:LOWer?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Hold the lower trace in split-screen mode"""

        self.display_split_hold_upper: Parameter = self.add_parameter(
            "display_split_hold_upper",
            set_cmd=":DISPlay:SPLit:HOLD:UPPer {}",
            get_cmd=":DISPlay:SPLit:HOLD:UPPer?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Hold the upper trace in split-screen mode"""

        self.display_text_data: Parameter = self.add_parameter(
            "display_text_data",
            set_cmd=':DISPlay:TEXT:DATA "{}"',
            get_cmd=":DISPlay:TEXT:DATA?",
            vals=Strings(max_length=56),
            get_parser=str,
        )
        """Display text label (max 56 characters)"""

        self.display_trace_x_center: Parameter = self.add_parameter(
            "display_trace_x_center",
            set_cmd=":DISPlay:TRACe:X:SCALe:CENTer {}",
            get_cmd=":DISPlay:TRACe:X:SCALe:CENTer?",
            get_parser=float,
        )
        """Center value of the display X-axis"""

        self.display_trace_x_span: Parameter = self.add_parameter(
            "display_trace_x_span",
            set_cmd=":DISPlay:TRACe:X:SCALe:SPAN {}",
            get_cmd=":DISPlay:TRACe:X:SCALe:SPAN?",
            get_parser=float,
        )
        """Span of the display X-axis"""

        self.display_trace_x_srange: Parameter = self.add_parameter(
            "display_trace_x_srange",
            set_cmd=":DISPlay:TRACe:X:SCALe:SRANge {}",
            get_cmd=":DISPlay:TRACe:X:SCALe:SRANge?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Limit analytical range to the display X-axis scale"""

        self.display_trace_x_start: Parameter = self.add_parameter(
            "display_trace_x_start",
            set_cmd=":DISPlay:TRACe:X:SCALe:STARt {}",
            get_cmd=":DISPlay:TRACe:X:SCALe:STARt?",
            get_parser=float,
        )
        """Start value of the display X-axis"""

        self.display_trace_x_stop: Parameter = self.add_parameter(
            "display_trace_x_stop",
            set_cmd=":DISPlay:TRACe:X:SCALe:STOP {}",
            get_cmd=":DISPlay:TRACe:X:SCALe:STOP?",
            get_parser=float,
        )
        """Stop value of the display X-axis"""

        self.display_trace_y_nmask: Parameter = self.add_parameter(
            "display_trace_y_nmask",
            set_cmd=":DISPlay:TRACe:Y:NMASk {}",
            get_cmd=":DISPlay:TRACe:Y:NMASk?",
            unit="dB",
            get_parser=float,
        )
        """Y-axis display mask threshold in dB (-999 disables masking)"""

        self.display_trace_y_nmask_type: Parameter = self.add_parameter(
            "display_trace_y_nmask_type",
            set_cmd=":DISPlay:TRACe:Y:NMASk:TYPE {}",
            get_cmd=":DISPlay:TRACe:Y:NMASk:TYPE?",
            val_mapping={
                "vertical": 0,
                "horizontal": 1,
            },
        )
        """Y-axis mask display type (vertical or horizontal)"""

        self.display_trace_y_dnumber: Parameter = self.add_parameter(
            "display_trace_y_dnumber",
            set_cmd=":DISPlay:TRACe:Y:SCALe:DNUMber {}",
            get_cmd=":DISPlay:TRACe:Y:SCALe:DNUMber?",
            vals=Enum(8, 10, 12),
            get_parser=int,
        )
        """Number of Y-axis display divisions (8, 10, or 12)"""

        self.display_trace_y1_blevel: Parameter = self.add_parameter(
            "display_trace_y1_blevel",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:BLEVel {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:BLEVel?",
            unit="W",
            get_parser=float,
        )
        """Y1-axis base level for linear scale in watts"""

        self.display_trace_y1_pdivision: Parameter = self.add_parameter(
            "display_trace_y1_pdivision",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:PDIVision {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:PDIVision?",
            unit="dB",
            get_parser=float,
        )
        """Y1-axis level scale per division in dB"""

        self.display_trace_y1_rlevel: Parameter = self.add_parameter(
            "display_trace_y1_rlevel",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:RLEVel {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:RLEVel?",
            get_parser=float,
        )
        """Y1-axis reference level (log or linear mode dependent)"""

        self.display_trace_y1_rposition: Parameter = self.add_parameter(
            "display_trace_y1_rposition",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:RPOSition {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:RPOSition?",
            unit="DIV",
            vals=Ints(0, 12),
            get_parser=int,
        )
        """Y1-axis reference level position in divisions"""

        self.display_trace_y1_spacing: Parameter = self.add_parameter(
            "display_trace_y1_spacing",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:SPACing {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:SPACing?",
            val_mapping={
                "log": 0,
                "linear": 1,
            },
        )
        """Y1-axis scale spacing (logarithmic or linear)"""

        self.display_trace_y1_unit: Parameter = self.add_parameter(
            "display_trace_y1_unit",
            set_cmd=":DISPlay:TRACe:Y1:SCALe:UNIT {}",
            get_cmd=":DISPlay:TRACe:Y1:SCALe:UNIT?",
            val_mapping={
                "dbm": 0,
                "w": 1,
                "dbm_per_nm": 2,
                "w_per_nm": 3,
            },
        )
        """Y1-axis unit (dBm, W, dBm/nm, or W/nm)"""

        self.display_trace_y2_auto: Parameter = self.add_parameter(
            "display_trace_y2_auto",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:AUTO {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:AUTO?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enable or disable automatic scaling of the Y2-axis"""

        self.display_trace_y2_length: Parameter = self.add_parameter(
            "display_trace_y2_length",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:LENGth {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:LENGth?",
            unit="km",
            get_parser=float,
        )
        """Optical fiber length for Y2-axis when unit is dB/km"""

        self.display_trace_y2_olevel: Parameter = self.add_parameter(
            "display_trace_y2_olevel",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:OLEVel {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:OLEVel?",
            get_parser=float,
        )
        """Y2-axis offset level (dB or dB/km, unit depends on subscale)"""

        self.display_trace_y2_pdivision: Parameter = self.add_parameter(
            "display_trace_y2_pdivision",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:PDIVision {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:PDIVision?",
            get_parser=float,
        )
        """Y2-axis scale per division (unit depends on subscale)"""

        self.display_trace_y2_rposition: Parameter = self.add_parameter(
            "display_trace_y2_rposition",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:RPOSition {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:RPOSition?",
            unit="DIV",
            vals=Ints(0, 12),
            get_parser=int,
        )
        """Y2-axis reference level position in divisions"""

        self.display_trace_y2_sminimum: Parameter = self.add_parameter(
            "display_trace_y2_sminimum",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:SMINimum {}%",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:SMINimum?",
            unit="%",
            get_parser=float,
        )
        """Y2-axis scale minimum value (linear or % mode)"""

        self.display_trace_y2_unit: Parameter = self.add_parameter(
            "display_trace_y2_unit",
            set_cmd=":DISPlay:TRACe:Y2:SCALe:UNIT {}",
            get_cmd=":DISPlay:TRACe:Y2:SCALe:UNIT?",
            val_mapping={
                "db": 0,
                "linear": 1,
                "db_per_km": 2,
                "percent": 3,
            },
        )
        """Y2-axis unit (dB, linear, dB/km, or %)"""

        # FORMat Sub System Commands

        self.format_data: Parameter = self.add_parameter(
            "format_data",
            set_cmd=":FORMat:DATA {}",
            get_cmd=":FORMat:DATA?",
            val_mapping={
                "ascii": "ASCII",
                "real64": "REAL,64",
                "real32": "REAL,32",
            },
        )
        """Data transfer format (ASCII, REAL 64-bit, or REAL 32-bit)"""

        # INITiate Sub System Command

        self.sweep_mode: Parameter = self.add_parameter(
            "sweep_mode",
            set_cmd=":INITiate:SMODe {}",
            get_cmd=":INITiate:SMODe?",
            val_mapping={
                "single": 1,
                "repeat": 2,
                "auto": 3,
                "segment": 4
            }
        )
        """Sets/queries the sweep mode"""

        # SENSe Sub System Commands

        self.sense_average_count: Parameter = self.add_parameter(
            "sense_average_count",
            set_cmd=":SENSe:AVERage:COUNt {}",
            get_cmd=":SENSe:AVERage:COUNt?",
            vals=Ints(),
            get_parser=int,
        )
        """Number of averages per measured point"""

        self.sense_bandwidth_resolution: Parameter = self.add_parameter(
            "sense_bandwidth_resolution",
            set_cmd=":SENSe:BANDwidth:RESolution {}",
            get_cmd=":SENSe:BANDwidth:RESolution?",
            get_parser=float,
        )
        """Measurement resolution (bandwidth)"""

        self.sense_chopper: Parameter = self.add_parameter(
            "sense_chopper",
            set_cmd=":SENSe:CHOPper {}",
            get_cmd=":SENSe:CHOPper?",
            val_mapping={
                "off": 0,
                "switch": 2,
            },
        )
        """Chopper mode (off or switch)"""

        self.sense_correction_level_shift: Parameter = self.add_parameter(
            "sense_correction_level_shift",
            set_cmd=":SENSe:CORRection:LEVel:SHIFt {}",
            get_cmd=":SENSe:CORRection:LEVel:SHIFt?",
            unit="dB",
            get_parser=float,
        )
        """Level correction offset in dB"""

        self.sense_correction_rvelocity_medium: Parameter = self.add_parameter(
            "sense_correction_rvelocity_medium",
            set_cmd=":SENSe:CORRection:RVELocity:MEDium {}",
            get_cmd=":SENSe:CORRection:RVELocity:MEDium?",
            val_mapping={
                "air": 0,
                "vacuum": 1,
            },
        )
        """Wavelength reference medium (air or vacuum)"""

        self.sense_correction_wavelength_shift: Parameter = self.add_parameter(
            "sense_correction_wavelength_shift",
            set_cmd=":SENSe:CORRection:WAVelength:SHIFt {}",
            get_cmd=":SENSe:CORRection:WAVelength:SHIFt?",
            unit="m",
            get_parser=float,
        )
        """Wavelength correction offset in meters"""

        self.sense_sensitivity: Parameter = self.add_parameter(
            "sense_sensitivity",
            set_cmd=":SENSe:SENSe {}",
            get_cmd=":SENSe:SENSe?",
            val_mapping={
                "normal_hold": 0,
                "normal_auto": 1,
                "mid": 2,
                "high1": 3,
                "high2": 4,
                "high3": 5,
                "normal": 6,
            },
        )
        """Measurement sensitivity setting"""

        self.sense_setting_correction: Parameter = self.add_parameter(
            "sense_setting_correction",
            set_cmd=":SENSe:SETTing:CORRection {}",
            get_cmd=":SENSe:SETTing:CORRection?",
            val_mapping={
                "off": 0,
                "on_mode1": 1,
                "on_mode2": 2,
            },
        )
        """Resolution correction function setting"""

        self.sense_setting_fconnector: Parameter = self.add_parameter(
            "sense_setting_fconnector",
            set_cmd=":SENSe:SETTing:FCONnector {}",
            get_cmd=":SENSe:SETTing:FCONnector?",
            val_mapping={
                "normal": 0,
                "angled": 1,
            },
        )
        """Fiber connector mode (normal or angled)"""

        if self.model in ("AQ6373", "AQ6373B"):
            self.sense_setting_fiber: Parameter = self.add_parameter(
                "sense_setting_fiber",
                set_cmd=":SENSe:SETTing:FIBer {}",
                get_cmd=":SENSe:SETTing:FIBer?",
                val_mapping={
                    "small": 0,
                    "large": 1,
                },
            )
            """Fiber core size mode (small or large)"""

        self.sense_setting_smoothing: Parameter = self.add_parameter(
            "sense_setting_smoothing",
            set_cmd=":SENSe:SETTing:SMOothing {}",
            get_cmd=":SENSe:SETTing:SMOothing?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Enable or disable smoothing"""

        self.sense_sweep_points: Parameter = self.add_parameter(
            "sense_sweep_points",
            set_cmd=":SENSe:SWEep:POINts {}",
            get_cmd=":SENSe:SWEep:POINts?",
            vals=Ints(),
            get_parser=int,
        )
        """Number of samples measured per sweep"""

        self.sense_sweep_points_auto: Parameter = self.add_parameter(
            "sense_sweep_points_auto",
            set_cmd=":SENSe:SWEep:POINts:AUTO {}",
            get_cmd=":SENSe:SWEep:POINts:AUTO?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Automatically set the number of sweep points"""

        self.sense_sweep_segment_points: Parameter = self.add_parameter(
            "sense_sweep_segment_points",
            set_cmd=":SENSe:SWEep:SEGMent:POINts {}",
            get_cmd=":SENSe:SWEep:SEGMent:POINts?",
            vals=Ints(1, 2 ** 31 - 1),
            get_parser=int,
        )
        """Number of sampling points per segment sweep"""

        self.sense_sweep_speed: Parameter = self.add_parameter(
            "sense_sweep_speed",
            set_cmd=":SENSe:SWEep:SPEed {}",
            get_cmd=":SENSe:SWEep:SPEed?",
            val_mapping={
                "1x": 0,
                "2x": 1,
            },
        )
        """Sweep speed (1x = standard, 2x = fast)"""

        self.sense_sweep_step: Parameter = self.add_parameter(
            "sense_sweep_step",
            set_cmd=":SENSe:SWEep:STEP {}",
            get_cmd=":SENSe:SWEep:STEP?",
            unit="m",
            get_parser=float,
        )
        """Sampling interval for sweep measurements"""

        self.sense_sweep_time_0nm: Parameter = self.add_parameter(
            "sense_sweep_time_0nm",
            set_cmd=":SENSe:SWEep:TIME:0NM {}",
            get_cmd=":SENSe:SWEep:TIME:0NM?",
            unit="s",
            vals=Ints(0, 2 ** 31 - 1),
            get_parser=int,
        )
        """Measurement time for 0-nm sweep mode (0 = minimum)"""

        self.sense_sweep_time_interval: Parameter = self.add_parameter(
            "sense_sweep_time_interval",
            set_cmd=":SENSe:SWEep:TIME:INTerval {}",
            get_cmd=":SENSe:SWEep:TIME:INTerval?",
            unit="s",
            vals=Ints(0, 2 ** 31 - 1),
            get_parser=int,
        )
        """Time between consecutive sweeps (0 = minimum)"""

        if self.model not in ("AQ6370D", "AQ6373B", "AQ6375B"):
            self.sense_sweep_tlssync: Parameter = self.add_parameter(
                "sense_sweep_tlssync",
                set_cmd=":SENSe:SWEep:TLSSync {}",
                get_cmd=":SENSe:SWEep:TLSSync?",
                val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
            )
            """Enable or disable synchronous TLS sweep"""

        self.sense_wavelength_center: Parameter = self.add_parameter(
            "sense_wavelength_center",
            set_cmd=":SENSe:WAVelength:CENTer {}",
            get_cmd=":SENSe:WAVelength:CENTer?",
            get_parser=float,
        )
        """Measurement center wavelength"""

        self.sense_wavelength_span: Parameter = self.add_parameter(
            "sense_wavelength_span",
            set_cmd=":SENSe:WAVelength:SPAN {}",
            get_cmd=":SENSe:WAVelength:SPAN?",
            get_parser=float,
        )
        """Measurement wavelength span"""

        self.sense_wavelength_srange: Parameter = self.add_parameter(
            "sense_wavelength_srange",
            set_cmd=":SENSe:WAVelength:SRANge {}",
            get_cmd=":SENSe:WAVelength:SRANge?",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Limit wavelength sweep range to marker L1–L2 spacing"""

        self.sense_wavelength_start: Parameter = self.add_parameter(
            "sense_wavelength_start",
            set_cmd=":SENSe:WAVelength:STARt {}",
            get_cmd=":SENSe:WAVelength:STARt?",
            get_parser=float,
        )
        """Measurement start wavelength"""

        self.sense_wavelength_stop: Parameter = self.add_parameter(
            "sense_wavelength_stop",
            set_cmd=":SENSe:WAVelength:STOP {}",
            get_cmd=":SENSe:WAVelength:STOP?",
            get_parser=float,
        )
        """Measurement stop wavelength"""

    # Common Commands

    def clear_status(self) -> None:
        """Clear all event status registers and queues except the output queue"""
        self.write("*CLS")

    def reset(self) -> None:
        """Reset the instrument to its default state"""
        self.write("*RST")

    def trigger(self) -> None:
        """Force a single trigger sweep regardless of trigger mode"""
        self.write("*TRG")

    def wait(self) -> None:
        """Wait until all previously issued commands have completed"""
        self.write("*WAI")

    ## Instrument specific commands
    # Replicating button commands

    def immediate(self):
        """Makes a sweep"""
        self.write(":INITIATE")

    def stop(self) -> None:
        """Stops operations such as measurements and calibration"""
        self.write(":ABORt")

    def auto(self):
        self.sweep_mode("auto")
        self.immediate()

    def repeat(self):
        self.sweep_mode("repeat")
        self.immediate()

    def single(self):
        self.sweep_mode("single")
        self.immediate()

    # Display Sub System Commands

    def display_text_clear(self) -> None:
        """Clear all display text labels"""
        self.write(":DISPlay:TEXT:CLEar")

    def display_trace_x_initialize(self) -> None:
        """Initialize the display X-axis scale parameters"""
        self.write(":DISPlay:TRACe:X:SCALe:INITialize")

    def display_trace_x_smscale(self) -> None:
        """Sets parameters of the current display scale to the measurement scale"""
        self.write(":DISPLAY:TRACE:X:SMSCALE")

    def delete_all_traces(self) -> None:
        """Delete the data of all traces."""
        self.write(":TRACe:DELete:ALL")
