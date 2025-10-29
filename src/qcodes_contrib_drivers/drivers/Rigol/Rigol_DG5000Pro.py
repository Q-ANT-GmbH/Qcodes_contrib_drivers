from typing import TYPE_CHECKING, Union

from qcodes.instrument import VisaInstrument, VisaInstrumentKWArgs, InstrumentChannel, InstrumentBaseKWArgs, Instrument
from qcodes.parameters import Parameter
from qcodes.parameters import create_on_off_val_mapping
from qcodes.validators import Enum, Ints, MultiType, Numbers, Strings

if TYPE_CHECKING:
    from typing_extensions import Unpack


class RigolDG5000ProChannel(InstrumentChannel):

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

        # 3.10 :OUTPut Commands

        self.output_debounce: Parameter = self.add_parameter(
            "output_debounce",
            get_cmd=f":OUTPut{channel}:DEBounce:STATe?",
            set_cmd=f":OUTPut{channel}:DEBounce {{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """on/off status of the debounce function for the specified channel"""

        self.output_idle: Parameter = self.add_parameter(
            "output_idle",
            get_cmd=f":OUTPut{channel}:IDLE?",
            set_cmd=f":OUTPut{channel}:IDLE {{}}",
            vals=MultiType(
                Ints(0, 65535),
                Enum("FPT", "TOP", "CENT", "BOTT")
            ),
            get_parser=lambda x: int(x) if x.isdigit() else x,
        )
        """Idle level position of the burst mode for the specified channel"""

        self.output_load: Parameter = self.add_parameter(
            "output_load",
            get_cmd=f":OUTPut{channel}:LOAD?",
            set_cmd=f":OUTPut{channel}:LOAD {{}}",
            vals=MultiType(
                Ints(1, 10000),  # Ohms
                Enum("INF", "MIN", "MAX", "DEF")),
            get_parser=float
        )
        """Output impedance for the specified channel"""

        self.output_polarity: Parameter = self.add_parameter(
            "output_polarity",
            get_cmd=f":OUTPut{channel}:POLarity?",
            set_cmd=f":OUTPut{channel}:POLarity {{}}",
            val_mapping={"normal": "NORM ", "inverted": "INV "}
        )
        """Output polarity for the specified channel"""

        self.output_skew_time: Parameter = self.add_parameter(
            "output_skew_time",
            get_cmd=f":OUTPut{channel}:SKEW:TIME?",
            set_cmd=f":OUTPut{channel}:SKEW:TIME {{}}",
            vals=MultiType(
                Numbers(-200e-9, 200e-9),
                Enum("MIN", "MAX", "DEF")
            ),
            get_parser=float
        )
        """Channel-to-channel skew (relative timing of the analog output)"""

        self.output_state: Parameter = self.add_parameter(
            "output_state",
            get_cmd=f":OUTPut{channel}:STATe?",
            set_cmd=f":OUTPut{channel}:STATe {{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Output on/off status for the specified channel"""

        self.output_sync: Parameter = self.add_parameter(
            "output_sync",
            get_cmd=f":OUTPut{channel}:SYNC?",
            set_cmd=f":OUTPut{channel}:SYNC {{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Output on/off state of the sync signal"""

        self.output_sync_mode: Parameter = self.add_parameter(
            "output_sync_mode",
            get_cmd=f":OUTPut{channel}:SYNC:MODE?",
            set_cmd=f":OUTPut{channel}:SYNC:MODE {{}}",
            val_mapping={"normal": "NORM", "marker": "MARK"},
            get_parser=str.strip
        )
        """Frequency mark function for the specified channel"""

        self.output_sync_polarity: Parameter = self.add_parameter(
            "output_sync_polarity",
            get_cmd=f":OUTPut{channel}:SYNC:POLarity?",
            set_cmd=f":OUTPut{channel}:SYNC:POLarity? {{}}",
            val_mapping={"normal": "NORM", "inverted": "INV"},
            get_parser=str.strip
        )
        """Polarity of sync signal for the specified channel"""

        self.output_trigger: Parameter = self.add_parameter(
            "output_trigger",
            get_cmd=f":OUTPut{channel}:TRIGger?",
            set_cmd=f":OUTPut{channel}:TRIGger {{}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Trigger on/off state for Sweep or Burst mode"""

        self.output_trigger_slope: Parameter = self.add_parameter(
            "output_trigger_slope",
            get_cmd=f":OUTPut{channel}:TRIGger:SLOPe?",
            set_cmd=f":OUTPut{channel}:TRIGger:SLOPe? {{}}",
            val_mapping={"positive": "POS", "negative": "NEG"},
        )
        """Slope of the trigger output signal for the specified channel"""

        # 3.12 :SOURce Commands

        self.source_am_depth: Parameter = self.add_parameter(
            "source_am_depth",
            get_cmd=f":SOURce{channel}:AM:DEPTh?",
            set_cmd=f":SOURce{channel}:AM:DEPTh {{}}",
            vals=MultiType(
                Ints(0, 120),
                Enum("MIN", "MAX")
            ),
            get_parser=float
        )
        """AM modulation depth for the specified channel"""

        self.source_am_dssc: Parameter = self.add_parameter(
            "source_am_dssc",
            get_cmd=f":SOURce{channel}:AM:DSSC?",
            set_cmd=f":SOURce{channel}:AM:DSSC {{}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """On/off status of the AM DSSC function for the specified channel"""

        self.source_am_frequency: Parameter = self.add_parameter(
            "source_am_frequency",
            get_cmd=f":SOURce{channel}:AM:INTernal:FREQuency?",
            set_cmd=f":SOURce{channel}:AM:INTernal:FREQuency {{}}",
            vals=MultiType(
                Numbers(2e-3, 1e6),
                Enum("MIN", "MAX", "DEF")
            )
        )

        self.source_burst_state: Parameter = self.add_parameter(
            "source_burst_state",
            get_cmd=f":SOURce{channel}:BURSt:STATe?",
            set_cmd=f":SOURce{channel}:BURSt:STATe {{}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """On/off status of the burst mode for the specified channel"""

        self.source_burst_mode: Parameter = self.add_parameter(
            "source_burst_mode",
            get_cmd=f":SOURce{channel}:BURSt:MODE?",
            set_cmd=f":SOURce{channel}:BURSt:MODE {{}}",
            val_mapping={"triggered": "TRIG ", "gated": "GAT "},
        )
        """Burst type for the specified channel"""

        self.source_sweep_state: Parameter = self.add_parameter(
            "source_sweep_state",
            get_cmd=f":SOURce{channel}:SWEep:STATe?",
            set_cmd=f":SOURce{channel}:SWEep:STATe {{}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """On/off status of the Sweep function for the specified channel"""

        # 3.14 :TRIGer Commands

        self.trigger_count: Parameter = self.add_parameter(
            "trigger_count",
            get_cmd=f":TRIGger{channel}:COUNt?",
            set_cmd=f":TRIGger{channel}:COUNt {{}}",
            vals=MultiType(
                Ints(1, 1000000),
                Enum("MIN", "MAX", "DEF")
            ),
            get_parser=lambda x: int(x) if x.isdigit() else x,
        )
        """Trigger count for the specified channel"""

        self.trigger_delay: Parameter = self.add_parameter(
            "trigger_delay",
            get_cmd=f":TRIGger{channel}:DELay?",
            set_cmd=f":TRIGger{channel}:DElay {{}}",
            vals=MultiType(
                Numbers(0, 85),
                Enum("MIN", "MAX", "DEF")
            ),
            get_parser=float
        )
        """Trigger delay for the specified channel"""

        self.trigger_slope: Parameter = self.add_parameter(
            "trigger_slope",
            get_cmd=f":TRIGger{channel}:SLOPe?",
            set_cmd=f":TRIGger{channel}:SLOPe {{}}",
            val_mapping={"positive": "POS", "negative": "NEG"},
        )
        """Edge type of the external trigger signal for the specified channel"""

        self.trigger_source: Parameter = self.add_parameter(
            "trigger_source",
            get_cmd=f":TRIGger{channel}:SOURce?",
            set_cmd=f":TRIGger{channel}:SOURce {{}}",
            val_mapping={"immediate": "IMM", "external": "EXT", "bus": "BUS", "timer": "TIM"},
        )
        """Trigger type for the specified channel"""

        self.trigger_timer: Parameter = self.add_parameter(
            "trigger_timer",
            get_cmd=f":TRIGger{channel}:TIMer?",
            set_cmd=f":TRIGger{channel}:TIMer {{}}",
            vals=MultiType(
                Numbers(1e-6, 8000),
                Enum("MIN", "MAX")
            ),
            get_parser=float
        )
        """Trigger timer for the specified channel"""

    def trigger(self) -> None:
        """Generate trigger event for the specified channel"""
        self.write(f":TRIGger{self.channel}")

    def source_apply_ramp(self, frequency: float, amplitude: float, offset: float, phase: float) -> None:
        """Sets the specified channel to output a ramp

        Sets the specified channel to output a ramp (with the maximum symmetry available at the current frequency)
        with the specified frequency, amplitude, offset, and phase.

        Args:
            frequency:
            amplitude:
            offset:
            phase:
        """
        # TODO : Add validators to the input
        self.write(f":SOURce{self.channel}:APPLy:RAMP {frequency},{amplitude},{offset},{phase}")


class RigolDG5000Pro(VisaInstrument):
    """
    Driver for the Rigol DG5000 Pro series arbitrary waveform generator.
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

        models = ["DG5258 Pro",
                  "DG5358 Pro",
                  "DG5508 Pro",
                  "DG5254 Pro",
                  "DG5354 Pro",
                  "DG5504 Pro",
                  "DG5252 Pro",
                  "DG5352 Pro",
                  "DG5502 Pro"]

        if self.model in models:
            i = models.index(self.model)
            n_o_ch = [8, 8, 8, 4, 4, 4, 2, 2, 2][i]
        elif self.model is None:
            raise KeyError("Could not determine model")
        else:
            raise KeyError("Model code " + self.model + " is not recognized")

        self.ch = []
        """Instrument channels"""

        for i in range(1, n_o_ch + 1):
            channel = RigolDG5000ProChannel(self, f"ch{i}", i)
            self.ch += [self.add_submodule(f"ch{i}", channel)]

        self.add_function(
            "abort",
            call_cmd=":ABORt",
            docstring="Stops any operation that is triggered"
        )

        # :DISPlay commands are used to set or query the status of the current channel and
        # display, and select the method to specify the voltage range, frequency sweep range,
        # and pulse duration.

        self.display_brightness: Parameter = self.add_parameter(
            "display_brightness",
            get_cmd=":DISPlay:BRIGhtness?",
            set_cmd=":DISPlay:BRIGhtness {:d}",
            vals=Ints(0, 100),
            get_parser=int,
        )
        """Display brightness (between 0 and 100)"""

        self.display_focus: Parameter = self.add_parameter(
            "display_focus",
            get_cmd=":DISPlay:FOCus?",
            set_cmd=":DISPlay:FOCus {}",
            val_mapping={1: "CH1", 2: "CH2", 3: "CH3", 4: "CH4", 5: "CH5", 6: "CH6", 7: "CH7", 8: "CH8"},
        )
        """Current channel"""

        self.display_state: Parameter = self.add_parameter(
            "display_state",
            get_cmd=":DISPlay:STATe?",
            set_cmd=":DISPlay:STATe {:d}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """State of the front-panel screen (on or off)"""

        self.display_text = self.add_parameter(
            "display_text",
            get_cmd=":DISPlay:TEXT?",
            set_cmd=":DISPlay:TEXT \"{:s}\"",
            vals=Strings(max_length=40)
        )
        """Text message displayed on the front-panel screen"""

        self.display_unit_pulse: Parameter = self.add_parameter(
            "display_unit_pulse",
            get_cmd=":DISPlay:UNIT:PULSe?",
            set_cmd=":DISPlay:UNIT:PULSE {:s}",
            val_mapping={"width": "WIDT", "duty": "DUTY"},
        )
        """Method used to specify the pulse width"""

        self.display_unit_rate: Parameter = self.add_parameter(
            "display_unit_rate",
            get_cmd=":DISPlay:UNIT:RATE?",
            set_cmd=":DISPlay:UNIT:RATE {:s}",
            val_mapping={"frequency": "FREQ", "period": "PER"},
        )
        """Rate unit for Sine, Square, Ramp, Pulse, Arb, and Harmonic"""

        self.display_unit_sweep: Parameter = self.add_parameter(
            "display_unit_sweep",
            get_cmd=":DISPlay:UNIT:SWEep?",
            set_cmd=":DISPlay:UNIT:SWEep {:s}",
            val_mapping={"start-stop": "STAR", "center-span": "CENT"},
        )
        """Method used to specify the frequency sweep range"""

        self.display_unit_voltage: Parameter = self.add_parameter(
            "display_unit_voltage",
            get_cmd=":DISPlay:UNIT:VOLTage?",
            set_cmd=":DISPlay:UNIT:VOLTage {:s}",
            val_mapping={"amplitude-offset": "AMPL", "high-low": "HIGH"},
        )
        """Method used to specify the voltage sweep range"""

        self.display_view: Parameter = self.add_parameter(
            "display_view",
            get_cmd=":DISPlay:VIEW?",
            set_cmd=":DISPlay:VIEW {:s}",
            val_mapping={"auto": "AUTO", 2: "DUAL", 4: "FOUR", 8: "EIGH"},
        )
        """Multi-window mode"""

        # :HCOPy commands are used to set or query the image format and execute the
        # screenshot operation.
        # TODO: Implement :HCOPy commands

        self.screen_capture_format: Parameter = self.add_parameter(
            "screen_capture_format",
            get_cmd=":HCOPy:SDUMp:DATA:FORMat?",
            set_cmd=":HCOPy:SDUMp:DATA:FORMat? {}",
            val_mapping={"png": "PNG", "bmp": "BMP"},
        )
        """Format of the screen capture image"""

        # :INITiate commands are used to set or query the "wait-for-trigger" state of the
        # instrument.

    def all(self, state: Union[bool, str]) -> None:
        val_mapping = create_on_off_val_mapping(on_val=1, off_val=0)
        self.write(f":ALL {val_mapping[state]}")

    def display_clear_text(self):
        """Clears the text message displayed on the front-panel screen"""
        self.write(":DISPlay:TEXT:CLEar")

    def screen_capture(self, fname: str) -> None:
        """Captures the current screen"""

        if fname.endswith(".png"):
            self.screen_capture_format("png")
        elif fname.endswith(".bmp"):
            self.screen_capture_format("bmp")
        else:
            raise ValueError("Invalid file format (only .bmp or .png is supported)")

        # Read screen capture from device
        self.write(":HCOPy:SDUMp:DATA?")
        bytestream = self.root_instrument.visa_handle.read_raw()
        n = int(bytestream[1:2].decode("ascii"))
        l = int(bytestream[2:2 + n].decode("ascii"))
        img = bytestream[2 + n:].strip()

        assert len(img) == l

        with open(file=fname, mode="wb") as f:
            f.write(img)

    # IEEE488.2 Common Commands

    def opc(self) -> int:
        """
        Queries whether all the previous commands are executed.

        The query returns 1 to the output buffer after the command is executed.
        """
        ret_val = self.ask("*OPC?")
        return int(ret_val)

    def clear(self) -> None:
        """Clears all the event registers, and also clears the error queue"""
        self.write("*CLS")

    def options(self) -> tuple[str, ...]:
        """Queries the options installed in your instrument"""
        options_raw = self.ask("*OPT?")
        return tuple(options_raw.split(","))

    def reset(self) -> None:
        """Resets the instrument to its factory default state"""
        self.write("*RST")

    def save(self, slot=0) -> None:
        """Stores the current instrument state to a specified location in non-volatile memory"""
        Enum(0, 1, 2, 3, 4, 5).validate(slot)
        self.write(f"*SAVE {slot:d}")

    def trigger(self):
        """Generates a trigger event"""
        self.write("*TRG")

    def wait(self) -> None:
        """Waits for the operation to complete"""
        self.write("*WAI")  # TODO: Test this, self.ask(...) might be required instead
