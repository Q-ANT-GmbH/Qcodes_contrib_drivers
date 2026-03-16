from typing import TYPE_CHECKING, Union

from qcodes.instrument import VisaInstrument, VisaInstrumentKWArgs, InstrumentChannel, InstrumentBaseKWArgs, Instrument, \
    ChannelList, find_or_create_instrument
from qcodes.parameters import Parameter
from qcodes.parameters import create_on_off_val_mapping
from qcodes.validators import Enum, Ints, MultiType, Numbers, Strings

import numpy as np
import time

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
            vals=MultiType(Ints(0, 65535), Enum("FPT", "TOP", "CENT", "BOTT")),
            get_parser=lambda x: int(x) if x.isdigit() else x,
        )
        """Idle level position of the burst mode for the specified channel"""

        self.output_load: Parameter = self.add_parameter(
            "output_load",
            get_cmd=f":OUTPut{channel}:LOAD?",
            set_cmd=f":OUTPut{channel}:LOAD {{}}",
            vals=MultiType(Ints(1, 10000), Enum("INF", "MIN", "MAX", "DEF")),  # Ohms
            get_parser=float,
        )
        """Output impedance for the specified channel"""

        self.output_polarity: Parameter = self.add_parameter(
            "output_polarity",
            get_cmd=f":OUTPut{channel}:POLarity?",
            set_cmd=f":OUTPut{channel}:POLarity {{}}",
            val_mapping={"normal": "NORM ", "inverted": "INV "},
        )
        """Output polarity for the specified channel"""

        self.output_skew_time: Parameter = self.add_parameter(
            "output_skew_time",
            get_cmd=f":OUTPut{channel}:SKEW:TIME?",
            set_cmd=f":OUTPut{channel}:SKEW:TIME {{}}",
            vals=MultiType(Numbers(-200e-9, 200e-9), Enum("MIN", "MAX", "DEF")),
            get_parser=float,
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
            get_parser=str.strip,
        )
        """Frequency mark function for the specified channel"""

        self.output_sync_polarity: Parameter = self.add_parameter(
            "output_sync_polarity",
            get_cmd=f":OUTPut{channel}:SYNC:POLarity?",
            set_cmd=f":OUTPut{channel}:SYNC:POLarity {{}}",
            val_mapping={"normal": "NORM", "inverted": "INV"},
            get_parser=str.strip,
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
            set_cmd=f":OUTPut{channel}:TRIGger:SLOPe {{}}",
            val_mapping={"positive": "POS", "negative": "NEG"},
        )
        """Slope of the trigger output signal for the specified channel"""

        # 3.12 :SOURce Commands

        self.source_am_depth: Parameter = self.add_parameter(
            "source_am_depth",
            get_cmd=f":SOURce{channel}:AM:DEPTh?",
            set_cmd=f":SOURce{channel}:AM:DEPTh {{}}",
            vals=MultiType(Ints(0, 120), Enum("MIN", "MAX")),
            get_parser=float,
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
            vals=MultiType(Numbers(2e-3, 1e6), Enum("MIN", "MAX", "DEF")),
        )

        self.source_burst_mode: Parameter = self.add_parameter(
            "source_burst_mode",
            get_cmd=f":SOURce{channel}:BURSt:MODE?",
            set_cmd=f":SOURce{channel}:BURSt:MODE {{}}",
            val_mapping={"triggered": "TRIG", "gated": "GAT"},
            get_parser=str.strip,
        )
        """Burst type for the specified channel"""

        self.source_burst_state: Parameter = self.add_parameter(
            "source_burst_state",
            get_cmd=f":SOURce{channel}:BURSt:STATe?",
            set_cmd=f":SOURce{channel}:BURSt:STATe {{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Burst mode on/off state for the specified channel"""

        self.source_sweep_state: Parameter = self.add_parameter(
            "source_sweep_state",
            get_cmd=f":SOURce{channel}:SWEep:STATe?",
            set_cmd=f":SOURce{channel}:SWEep:STATe {{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        """Sweep function on/off state for the specified channel"""

        # 3.14 :TRIGer Commands

        self.trigger_count: Parameter = self.add_parameter(
            "trigger_count",
            get_cmd=f":TRIGger{channel}:COUNt?",
            set_cmd=f":TRIGger{channel}:COUNt {{}}",
            vals=MultiType(Ints(1, 1000000), Enum("MIN", "MAX", "DEF")),
            get_parser=lambda x: int(x) if x.isdigit() else x,
        )
        """Trigger count for the specified channel"""

        self.trigger_delay: Parameter = self.add_parameter(
            "trigger_delay",
            get_cmd=f":TRIGger{channel}:DELay?",
            set_cmd=f":TRIGger{channel}:DElay {{}}",
            vals=MultiType(Numbers(0, 85), Enum("MIN", "MAX", "DEF")),
            get_parser=float,
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
            vals=MultiType(Numbers(1e-6, 8000), Enum("MIN", "MAX")),
            get_parser=float,
        )
        """Trigger timer for the specified channel"""

    def trigger(self) -> None:
        """Generate trigger event for the specified channel"""
        self.write(f":TRIGger{self.channel}")

    def source_apply_ramp(
            self,
            frequency: float,
            amplitude: float,
            offset: float,
            phase: float,
            symmetry: Union[float, None] = None,
    ) -> None:
        """Sets the specified channel to output a ramp

        Sets the specified channel to output a ramp with the specified frequency,
        amplitude, offset, and phase. When symmetry is supplied, ramp symmetry is
        explicitly set in percent.

        Args:
                frequency: Frequency in Hz
                amplitude: Amplitude in Vpp
                offset: DC offset in V
                phase: Phase in degrees
                symmetry: Ramp symmetry in percent (0 to 100). Optional.
        """
        Numbers(*self.root_instrument.frequency_range["ramp"]).validate(frequency)
        Numbers(-360, 360).validate(phase)
        self.write(f":SOURce{self.channel}:APPLy:RAMP {frequency},{amplitude},{offset},{phase}")

        if symmetry is not None:
            Numbers(0, 100).validate(symmetry)
            self.write(f":SOURce{self.channel}:FUNCtion:RAMP:SYMMetry {symmetry}")

    def source_apply_sinusoid(self, frequency: float, amplitude: float, offset: float, phase: float) -> None:
        """Sets the specified channel to output a sine wave

        Sets the specified channel to output a sine wave with the specified frequency, amplitude, offset, and phase.

        Args:
                frequency: Frequency in Hz
                amplitude: Amplitude in Vpp
                offset: DC offset in V
                phase: Phase in degrees
        """
        Numbers(*self.root_instrument.frequency_range["sine"]).validate(frequency)
        Numbers(-360, 360).validate(phase)
        self.write(f":SOURce{self.channel}:APPLy:SINusoid {frequency},{amplitude},{offset},{phase}")

    def source_apply_square(self, frequency: float, amplitude: float, offset: float, phase: float) -> None:
        """Sets the specified channel to output a square wave

        Sets the specified channel to output a square wave with the specified frequency, amplitude, offset, and phase.

        Args:
                frequency: Frequency in Hz
                amplitude: Amplitude in Vpp
                offset: DC offset in V
                phase: Phase in degrees
        """
        Numbers(*self.root_instrument.frequency_range["square_ft_off"]).validate(frequency)
        Numbers(-360, 360).validate(phase)
        self.write(f":SOURce{self.channel}:APPLy:SQUare {frequency},{amplitude},{offset},{phase}")

    def source_apply_pulse(self, frequency: float, amplitude: float, offset: float) -> None:
        """Sets the specified channel to output a pulse

        Sets the specified channel to output a pulse with the specified frequency, amplitude, and offset.

        Args:
                frequency: Frequency in Hz
                amplitude: Amplitude in Vpp
                offset: DC offset in V
        """
        Numbers(*self.root_instrument.frequency_range["pulse"]).validate(frequency)
        self.write(f":SOURce{self.channel}:APPLy:PULSe {frequency},{amplitude},{offset}")

    def source_apply_arb(self, frequency: float, amplitude: float, offset: float, phase: float) -> None:
        """Sets the specified channel to output an arbitrary waveform

        Sets the specified channel to output an arbitrary waveform with the specified frequency, amplitude, offset, and phase.

        Args:
                frequency: Frequency in Hz
                amplitude: Amplitude in Vpp
                offset: DC offset in V
                phase: Phase in degrees
        """
        Numbers(*self.root_instrument.frequency_range["arb"]).validate(frequency)
        Numbers(-360, 360).validate(phase)
        self.write(f":SOURce{self.channel}:APPLy:ARB {frequency},{amplitude},{offset},{phase}")


class RigolDG5000Pro(VisaInstrument):
    """
    Driver for the Rigol DG5000 Pro series arbitrary waveform generator.
    """

    default_terminator = "\n"

    MODELS = [
        "DG5258 Pro",
        "DG5358 Pro",
        "DG5508 Pro",
        "DG5254 Pro",
        "DG5354 Pro",
        "DG5504 Pro",
        "DG5252 Pro",
        "DG5352 Pro",
        "DG5502 Pro",
    ]

    NUM_CHANNELS = {
        "DG5258 Pro": 8,
        "DG5358 Pro": 8,
        "DG5508 Pro": 8,
        "DG5254 Pro": 4,
        "DG5354 Pro": 4,
        "DG5504 Pro": 4,
        "DG5252 Pro": 2,
        "DG5352 Pro": 2,
        "DG5502 Pro": 2,
    }

    FREQ_RANGE = {
        "DG52": {
            "sine": (1e-6, 250e6),
            "square_ft_on": (1e-6, 170e6),
            "square_ft_off": (1e-6, 120e6),
            "ramp": (1e-6, 5e6),
            "pulse": (1e-6, 120e6),
            "arb": (1e-6, 100e6),
            "harmonic": (1e-6, 125e6),
        },
        "DG53": {
            "sine": (1e-6, 350e6),
            "square_ft_on": (1e-6, 170e6),
            "square_ft_off": (1e-6, 120e6),
            "ramp": (1e-6, 5e6),
            "pulse": (1e-6, 120e6),
            "arb": (1e-6, 100e6),
            "harmonic": (1e-6, 175e6),
        },
        "DG55": {
            "sine": (1e-6, 500e6),
            "square_ft_on": (1e-6, 170e6),
            "square_ft_off": (1e-6, 120e6),
            "ramp": (1e-6, 5e6),
            "pulse": (1e-6, 120e6),
            "arb": (1e-6, 100e6),
            "harmonic": (1e-6, 250e6),
        },
    }

    def __init__(
            self,
            name: str,
            address: str,
            **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ):
        super().__init__(name, address, **kwargs)

        self.model = self.get_idn()["model"]

        if self.model in self.MODELS:
            self.frequency_range = self.FREQ_RANGE[self.model[:4]]
        elif self.model is None:
            raise KeyError("Could not determine model")
        else:
            raise KeyError("Model code " + self.model + " is not recognized")

        channels = ChannelList(self, "ch", RigolDG5000ProChannel)
        for i in range(1, self.NUM_CHANNELS[self.model] + 1):
            channels.append(RigolDG5000ProChannel(self, f"ch{i}", i))
        self.channels = channels.to_channel_tuple()
        """Instrument channels"""

        self.add_function("abort", call_cmd=":ABORt", docstring="Stops any operation that is triggered")

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
            "display_text", get_cmd=":DISPlay:TEXT?", set_cmd=':DISPlay:TEXT "{:s}"', vals=Strings(max_length=40)
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
            set_cmd=":HCOPy:SDUMp:DATA:FORMat {}",
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

        if len(img) != l:
            raise ValueError(f"Screen capture data length mismatch: expected {l}, got {len(img)}")

        with open(file=fname, mode="wb") as f:
            f.write(img)

    # IEEE488.2 Common Commands

    def options(self) -> tuple[str, ...]:
        """Queries the options installed in your instrument"""
        options_raw = self.ask("*OPT?")
        return tuple(options_raw.split(","))


    def save(self, slot=0) -> None:
        """Stores the current instrument state to a specified location in non-volatile memory"""
        Enum(0, 1, 2, 3, 4, 5).validate(slot)
        self.write(f"*SAVE {slot:d}")


    def clear(self):
        """Clears all the event registers, and also clears the error queue"""
        self.write("*CLS")


    def opc(self):
        """Queries whether all the previous commands are executed (operation complete)"""
        assert self.ask("*OPC?") == "1"


    def reset(self):
        """Resets the instrument to its factory default settings"""
        self.write("*RST")


    def trigger(self):
        """Generates a trigger event"""
        self.write("*TRG")


    def wait(self):
        """Waits for all the pending operations to complete"""
        self.write("*WAI")


def connect_awg_scope(devices: dict):
    from qcodes_contrib_drivers.drivers.Rigol.Rigol_DS8000R import RigolDS8000R

    def _close_existing(name: str) -> None:
        try:
            existing = Instrument.find_instrument(name)
        except KeyError:
            return

        try:
            existing.close()
        except Exception:
            try:
                Instrument.remove_instance(existing)
            except Exception:
                pass

    awg_ip = devices["rigol_awg"]["ip"]
    scope_ip = devices["rigol_oscilloscope"]["ip"]

    # Reloading driver modules in notebooks creates a new class object, which can
    # confuse find_or_create_instrument when an older instance with the same name
    # is still registered. Drop any stale instances before recreating them.
    _close_existing("my_awg")
    _close_existing("my_scope")

    awg = find_or_create_instrument(
        RigolDG5000Pro,
        "my_awg",
        address=f"TCPIP::{awg_ip}::INSTR",
        recreate=True,
    )
    scope = find_or_create_instrument(
        RigolDS8000R,
        "my_scope",
        address=f"TCPIP::{scope_ip}::INSTR",
        recreate=True,
    )

    try:
        scope.timeout(5.0)
    except Exception:
        pass

    return awg, scope


def turn_off_awg_channels(awg):
    for ch in awg.channels:
        ch.output_state("off")


def _apply_dc_level(awg, ch_idx: int, dc_voltage: float):
    ch_num = int(ch_idx) + 1
    ch = awg.channels[ch_idx]

    ch.source_apply_square(
        frequency=1.0,
        amplitude=0.0,
        offset=float(dc_voltage),
        phase=0.0,
    )
    try:
        awg.write(f":SOURce{ch_num}:FUNC:SQU:DCYC 100")
    except Exception:
        pass
    ch.output_polarity("normal")


def _normalize_awg_trigger_source(trigger_source: str) -> str:
    src = str(trigger_source).strip().lower()
    if src in ("ext", "external"):
        return "external"
    if src in ("imm", "immediate", "int", "internal"):
        return "immediate"
    if src == "bus":
        return "bus"
    if src in ("tim", "timer"):
        return "timer"
    raise ValueError(f"Unsupported AWG trigger_source={trigger_source!r}")


def _normalize_awg_trigger_edge(trigger_edge: str) -> str:
    edge = str(trigger_edge).strip().lower()
    if edge in ("leading", "rising", "rise", "positive", "pos"):
        return "positive"
    if edge in ("trailing", "falling", "fall", "negative", "neg"):
        return "negative"
    raise ValueError(f"Unsupported AWG trigger_edge={trigger_edge!r}")


def _normalize_awg_idle_level(idle_level):
    if isinstance(idle_level, (int, float)):
        return int(idle_level)

    idle = str(idle_level).strip().upper().replace(" ", "")
    if idle in ("FPT", "FIRSTPOINT", "FIRSTPT", "1STPT"):
        return "FPT"
    if idle in ("TOP", "CENT", "BOTT"):
        return idle

    raise ValueError(f"Unsupported AWG idle_level={idle_level!r}")


def _set_awg_burst_cycles(awg, ch_idx: int, burst_cycles):
    ch_num = int(ch_idx) + 1
    cyc = str(burst_cycles).strip().upper()

    if cyc in ("INF", "INFINITE", "INFINITY"):
        cmds = [
            f":SOURce{ch_num}:BURSt:NCYCles INF",
            f":SOURce{ch_num}:BURSt:NCYCles INFinity",
        ]
    else:
        cyc_val = int(burst_cycles)
        if cyc_val < 1:
            raise ValueError("AWG burst cycles must be >= 1 or INF.")
        cmds = [f":SOURce{ch_num}:BURSt:NCYCles {cyc_val}"]

    last_exc = None
    for cmd in cmds:
        try:
            awg.write(cmd)
            return
        except Exception as exc:
            last_exc = exc

    if last_exc is not None:
        raise last_exc


def _normalize_awg_burst_mode(burst_mode: str) -> str:
    mode = str(burst_mode).strip().lower()
    if mode in ("trig", "triggered", "burst"):
        return "triggered"
    if mode in ("gat", "gated", "gate"):
        return "gated"
    if mode in ("inf", "infinity", "infinite"):
        return "infinity"
    raise ValueError(f"Unsupported AWG burst_mode={burst_mode!r}")


def _configure_awg_ramp_trigger(
    awg,
    ch_idx: int,
    trigger_source="external",
    trigger_edge="leading",
    burst_mode="burst",
    burst_cycles="INF",
    idle_level="FPT",
):
    ch_num = int(ch_idx) + 1
    ch = awg.channels[ch_idx]

    src = _normalize_awg_trigger_source(trigger_source)
    edge = _normalize_awg_trigger_edge(trigger_edge)
    idle = _normalize_awg_idle_level(idle_level)
    mode = _normalize_awg_burst_mode(burst_mode)

    try:
        ch.source_burst_state(True)
    except Exception:
        awg.write(f":SOURce{ch_num}:BURSt:STATe ON")

    mode_scpi = {"triggered": "TRIG", "gated": "GAT", "infinity": "INF"}[mode]
    try:
        ch.source_burst_mode(mode)
    except Exception:
        awg.write(f":SOURce{ch_num}:BURSt:MODE {mode_scpi}")

    src_scpi = {
        "immediate": "IMM",
        "external": "EXT",
        "bus": "BUS",
        "timer": "TIM",
    }[src]
    try:
        ch.trigger_source(src)
    except Exception:
        awg.write(f":TRIGger{ch_num}:SOURce {src_scpi}")

    edge_scpi = {"positive": "POS", "negative": "NEG"}[edge]
    try:
        ch.trigger_slope(edge)
    except Exception:
        awg.write(f":TRIGger{ch_num}:SLOPe {edge_scpi}")

    try:
        ch.output_idle(idle)
    except Exception:
        awg.write(f":OUTPut{ch_num}:IDLE {idle}")

    if mode == "triggered":
        _set_awg_burst_cycles(awg=awg, ch_idx=ch_idx, burst_cycles=burst_cycles)


def _configure_awg_constant_dc_hold(awg, ch_idx: int):
    ch_num = int(ch_idx) + 1
    ch = awg.channels[ch_idx]

    try:
        ch.source_burst_state(False)
    except Exception:
        awg.write(f":SOURce{ch_num}:BURSt:STATe OFF")

    try:
        ch.trigger_source("immediate")
    except Exception:
        awg.write(f":TRIGger{ch_num}:SOURce IMM")

    try:
        awg.write(f":SYNChro:BUNDle CH{ch_num},OFF")
    except Exception:
        pass


def _readback_awg_trigger_config(ch):
    out = {}
    for key, getter in (
        ("burst_state", ch.source_burst_state),
        ("burst_mode", ch.source_burst_mode),
        ("trigger_source", ch.trigger_source),
        ("trigger_slope", ch.trigger_slope),
        ("output_idle", ch.output_idle),
    ):
        try:
            out[key] = getter()
        except Exception:
            out[key] = "N/A"
    return out


def _sync_awg_channels(awg, channel_indices):
    if not channel_indices:
        return

    channel_numbers = sorted({idx + 1 for idx in channel_indices})
    benchmark = channel_numbers[0]
    awg.write(f":SYNChro:BENChmark CH{benchmark}")

    for ch_num in channel_numbers[1:]:
        awg.write(f":SYNChro:BUNDle CH{ch_num},ON")

    awg.write(f":SOURce{benchmark}:PHASe:SYNChronize")
    awg.ask("*OPC?")
    time.sleep(0.1)


def configure_awg_for_mzm(
    awg,
    active_mzm: int,
    mzm_awg_map: dict,
    ramp_frequency_hz: float,
    volt_min: float,
    volt_max: float,
    bias_lookup: dict,
    output_load="INF",
    ramp_trigger_source="external",
    ramp_trigger_edge="leading",
    ramp_burst_mode="burst",
    ramp_cycles="INF",
    ramp_idle_level="FPT",
    ramp_symmetry_pct=0.0,
):
    amplitude = abs(float(volt_max) - float(volt_min))
    if amplitude == 0:
        raise ValueError("volt_min and volt_max cannot be equal.")

    offset = 0.5 * (float(volt_max) + float(volt_min))

    for _, (ch_pos_idx, ch_neg_idx) in mzm_awg_map.items():
        ch_pos = awg.channels[ch_pos_idx]
        ch_neg = awg.channels[ch_neg_idx]
        ch_pos.output_state("off")
        ch_neg.output_state("off")
        ch_pos.output_load(output_load)
        ch_neg.output_load(output_load)
    awg.ask("*OPC?")

    for mzm_num, (ch_pos_idx, ch_neg_idx) in mzm_awg_map.items():
        if mzm_num == active_mzm:
            continue

        ch_pos = awg.channels[ch_pos_idx]
        ch_neg = awg.channels[ch_neg_idx]

        bias_v = float(bias_lookup.get(mzm_num, 0.0))
        _apply_dc_level(awg=awg, ch_idx=ch_pos_idx, dc_voltage=+bias_v)
        _apply_dc_level(awg=awg, ch_idx=ch_neg_idx, dc_voltage=-bias_v)
        _configure_awg_constant_dc_hold(awg=awg, ch_idx=ch_pos_idx)
        _configure_awg_constant_dc_hold(awg=awg, ch_idx=ch_neg_idx)

        ch_pos.output_state("on")
        ch_neg.output_state("on")

    awg.ask("*OPC?")

    ch_pos_idx, ch_neg_idx = mzm_awg_map[active_mzm]
    ch_pos = awg.channels[ch_pos_idx]
    ch_neg = awg.channels[ch_neg_idx]

    ch_pos.source_apply_ramp(
        frequency=ramp_frequency_hz,
        amplitude=amplitude,
        offset=offset,
        phase=0.0,
        symmetry=ramp_symmetry_pct,
    )
    ch_pos.output_polarity("inverted")
    _configure_awg_ramp_trigger(
        awg=awg,
        ch_idx=ch_pos_idx,
        trigger_source=ramp_trigger_source,
        trigger_edge=ramp_trigger_edge,
        burst_mode=ramp_burst_mode,
        burst_cycles=ramp_cycles,
        idle_level=ramp_idle_level,
    )

    ch_neg.source_apply_ramp(
        frequency=ramp_frequency_hz,
        amplitude=amplitude,
        offset=offset,
        phase=0.0,
        symmetry=ramp_symmetry_pct,
    )
    ch_neg.output_polarity("normal")
    _configure_awg_ramp_trigger(
        awg=awg,
        ch_idx=ch_neg_idx,
        trigger_source=ramp_trigger_source,
        trigger_edge=ramp_trigger_edge,
        burst_mode=ramp_burst_mode,
        burst_cycles=ramp_cycles,
        idle_level=ramp_idle_level,
    )

    awg.ask("*OPC?")

    ch_pos.output_state("on")
    ch_neg.output_state("on")

    awg.ask("*OPC?")

    print(f"    AWG CH{ch_pos_idx + 1} trigger cfg: {_readback_awg_trigger_config(ch_pos)}")
    print(f"    AWG CH{ch_neg_idx + 1} trigger cfg: {_readback_awg_trigger_config(ch_neg)}")

    _sync_awg_channels(awg, [ch_pos_idx, ch_neg_idx])


def _upload_arb_staircase(awg, ch_idx, n_steps, samples_per_step=1):
    """Build a normalized staircase waveform and upload it to volatile memory.

    The staircase has *n_steps* levels linearly spaced from -1 to +1.
    Each level is repeated *samples_per_step* times (default 1, which is
    sufficient when the AWG uses zero-order-hold / step interpolation).

        Prefers the built-in ``STAIRUP`` arb shape on DG5000 Pro firmware, which
        avoids vendor-specific raw upload commands that may be unsupported.

        If built-in selection fails, tries multiple SCPI upload variants:
            1. Binary DAC  — ``:TRACe<n>:DATA:DAC VOLATILE,END,#...``
            2. ASCII float — ``:TRACe<n>:DATA VOLATILE,<csv>``
            3. ASCII float — ``:SOURce<n>:DATA VOLATILE,<csv>``
        After each attempt the error queue is checked; the first variant that
        succeeds is used.
    """
    ch_num = int(ch_idx) + 1
    n_steps = int(n_steps)

    levels = np.linspace(-1.0, 1.0, n_steps)
    waveform = np.repeat(levels, int(samples_per_step)) if samples_per_step > 1 else levels

    # ---------- helpers ----------
    def _drain_errors():
        """Read all queued errors and return the first non-zero one (or None)."""
        first_err = None
        for _ in range(20):
            err = awg.ask(':SYSTem:ERRor?')
            if err.startswith('0,') or err.startswith('+0,'):
                break
            if first_err is None:
                first_err = err
        return first_err

    def _try_binary_dac():
        """Binary 16-bit signed upload via :TRACe<n>:DATA:DAC."""
        dac_values = np.clip(
            np.round(waveform * 32767), -32768, 32767
        ).astype(np.int16)
        data_bytes = dac_values.tobytes()
        byte_count_str = str(len(data_bytes))
        block_header = f'#{len(byte_count_str)}{byte_count_str}'
        cmd_prefix = f':TRACe{ch_num}:DATA:DAC VOLATILE,END,'
        raw_cmd = (
            cmd_prefix.encode('ascii')
            + block_header.encode('ascii')
            + data_bytes
        )
        awg.visa_handle.write_raw(raw_cmd)
        awg.ask('*OPC?')
        return _drain_errors()

    def _try_ascii(prefix):
        """ASCII float upload (values in -1..+1)."""
        data_str = ','.join(f'{v:.6f}' for v in waveform)
        awg.write(f'{prefix}{ch_num}:DATA VOLATILE,{data_str}')
        awg.ask('*OPC?')
        return _drain_errors()

    # ---------- prefer built-in staircase arb first ----------
    awg.write("*CLS")
    _drain_errors()
    try:
        awg.write(f":SOURce{ch_num}:FUNCtion:ARBitrary STAIRUP")
        awg.ask("*OPC?")
        err = _drain_errors()
        if err is None:
            print("  _upload_arb_staircase: using built-in arb 'STAIRUP'")
            try:
                awg.write(f':SOURce{ch_num}:FUNCtion:ARBitrary:INTerpolation STEP')
            except Exception:
                pass
            return
    except Exception:
        pass

    # ---------- attempt each upload variant ----------
    awg.write('*CLS')
    _drain_errors()

    attempts = [
        ('binary :TRACe:DATA:DAC', _try_binary_dac),
        ('ASCII  :TRACe:DATA',     lambda: _try_ascii(':TRACe')),
        ('ASCII  :SOURce:DATA',    lambda: _try_ascii(':SOURce')),
    ]

    last_err = None
    upload_ok = False
    for label, fn in attempts:
        awg.write('*CLS')
        _drain_errors()
        try:
            err = fn()
        except Exception as exc:
            last_err = f'{label}: {exc}'
            continue
        if err is None:
            print(f'  _upload_arb_staircase: succeeded with {label}')
            upload_ok = True
            break
        last_err = f'{label}: {err}'
    if upload_ok:
        # Select the uploaded volatile waveform.
        awg.write(f':SOURce{ch_num}:FUNCtion:ARBitrary VOLATILE')
    else:
        # Some DG5000 Pro firmware variants do not expose SCPI upload commands
        # for volatile arb data. Fall back to a built-in staircase arb shape.
        fallback_candidates = (
            "STAIRUP",
            "STAIR",
            "RAMPUP",
            "UPSTAIR",
        )
        fallback_used = None
        for name in fallback_candidates:
            awg.write("*CLS")
            _drain_errors()
            try:
                awg.write(f":SOURce{ch_num}:FUNCtion:ARBitrary {name}")
                awg.ask("*OPC?")
                err = _drain_errors()
            except Exception:
                continue
            if err is None:
                fallback_used = name
                break

        if fallback_used is None:
            raise RuntimeError(
                f"All upload methods failed for CH{ch_num}. Last error: {last_err}. "
                "Also failed to select any built-in staircase arb waveform."
            )

        print(
            f"  _upload_arb_staircase: upload unsupported; using built-in arb '{fallback_used}'"
        )

    # Use step (sample-hold) interpolation so each level is flat.
    try:
        awg.write(f':SOURce{ch_num}:FUNCtion:ARBitrary:INTerpolation STEP')
    except Exception:
        pass


def configure_awg_for_mzm_staircase(
    awg,
    active_mzm: int,
    mzm_awg_map: dict,
    ramp_frequency_hz: float,
    volt_min: float,
    volt_max: float,
    bias_lookup: dict,
    time_bins_per_period: int = 128,
    samples_per_step: int = 1,
    output_load="INF",
    ramp_trigger_source="external",
    ramp_trigger_edge="leading",
    ramp_burst_mode="burst",
    ramp_cycles=1,
    ramp_idle_level="FPT",
    **kwargs,
):
    """Configure AWG with a staircase (stepped) arb waveform for MZM calibration.

    Replaces the continuous ramp used by :func:`configure_awg_for_mzm` with
    *time_bins_per_period* discrete voltage steps spanning
    [*volt_min*, *volt_max*].  The arb waveform plays at *ramp_frequency_hz*
    so one complete staircase occupies ``1 / ramp_frequency_hz`` seconds and
    each step lasts ``1 / (ramp_frequency_hz * time_bins_per_period)`` seconds.

    Non-active MZMs are held at their DC bias levels, identical to the
    continuous-ramp variant.
    """
    amplitude = abs(float(volt_max) - float(volt_min))
    if amplitude == 0:
        raise ValueError("volt_min and volt_max cannot be equal.")

    offset = 0.5 * (float(volt_max) + float(volt_min))
    n_steps = int(time_bins_per_period)

    # --- Turn off all channels and set output impedance ---
    for _, (ch_pos_idx, ch_neg_idx) in mzm_awg_map.items():
        ch_pos = awg.channels[ch_pos_idx]
        ch_neg = awg.channels[ch_neg_idx]
        ch_pos.output_state("off")
        ch_neg.output_state("off")
        ch_pos.output_load(output_load)
        ch_neg.output_load(output_load)
    awg.ask("*OPC?")

    # --- Non-active MZMs: hold at DC bias ---
    for mzm_num, (ch_pos_idx, ch_neg_idx) in mzm_awg_map.items():
        if mzm_num == active_mzm:
            continue

        ch_pos = awg.channels[ch_pos_idx]
        ch_neg = awg.channels[ch_neg_idx]

        bias_v = float(bias_lookup.get(mzm_num, 0.0))
        _apply_dc_level(awg=awg, ch_idx=ch_pos_idx, dc_voltage=+bias_v)
        _apply_dc_level(awg=awg, ch_idx=ch_neg_idx, dc_voltage=-bias_v)
        _configure_awg_constant_dc_hold(awg=awg, ch_idx=ch_pos_idx)
        _configure_awg_constant_dc_hold(awg=awg, ch_idx=ch_neg_idx)

        ch_pos.output_state("on")
        ch_neg.output_state("on")

    awg.ask("*OPC?")

    # --- Active MZM: staircase arb waveform ---
    ch_pos_idx, ch_neg_idx = mzm_awg_map[active_mzm]
    ch_pos = awg.channels[ch_pos_idx]
    ch_neg = awg.channels[ch_neg_idx]

    # Upload the staircase to both channels.
    _upload_arb_staircase(awg, ch_pos_idx, n_steps, samples_per_step)
    _upload_arb_staircase(awg, ch_neg_idx, n_steps, samples_per_step)

    # Configure arb output parameters.
    ch_pos.source_apply_arb(
        frequency=ramp_frequency_hz,
        amplitude=amplitude,
        offset=offset,
        phase=0.0,
    )
    ch_pos.output_polarity("inverted")
    _configure_awg_ramp_trigger(
        awg=awg,
        ch_idx=ch_pos_idx,
        trigger_source=ramp_trigger_source,
        trigger_edge=ramp_trigger_edge,
        burst_mode=ramp_burst_mode,
        burst_cycles=ramp_cycles,
        idle_level=ramp_idle_level,
    )

    ch_neg.source_apply_arb(
        frequency=ramp_frequency_hz,
        amplitude=amplitude,
        offset=offset,
        phase=0.0,
    )
    ch_neg.output_polarity("normal")
    _configure_awg_ramp_trigger(
        awg=awg,
        ch_idx=ch_neg_idx,
        trigger_source=ramp_trigger_source,
        trigger_edge=ramp_trigger_edge,
        burst_mode=ramp_burst_mode,
        burst_cycles=ramp_cycles,
        idle_level=ramp_idle_level,
    )

    awg.ask("*OPC?")

    ch_pos.output_state("on")
    ch_neg.output_state("on")

    awg.ask("*OPC?")

    print(f"    AWG CH{ch_pos_idx + 1} trigger cfg: {_readback_awg_trigger_config(ch_pos)}")
    print(f"    AWG CH{ch_neg_idx + 1} trigger cfg: {_readback_awg_trigger_config(ch_neg)}")
    print(
        f"    Staircase: {n_steps} steps, arb freq={ramp_frequency_hz:.2f} Hz, "
        f"step duration={1.0 / (ramp_frequency_hz * n_steps):.3e} s"
    )

    _sync_awg_channels(awg, [ch_pos_idx, ch_neg_idx])
