"""QCoDeS driver for Santec MPM-220 Optical Power Meter.

The driver uses native Santec command set (non-SCPI) and supports:
- Multiple plug-in measurement modules (MPM-211, MPM-212, MPM-213, MPM-215, MPM-217)
- Per-module wavelength and gain configuration
- Constant and sweep measurement modes
- External and internal trigger modes
"""

import logging
from typing import TYPE_CHECKING, Dict

import numpy as np
from qcodes import validators as vals
from qcodes.instrument import IPInstrument, InstrumentChannel, InstrumentBaseKWArgs
from qcodes.instrument.channel import ChannelList
from qcodes.parameters import Parameter, ParameterWithSetpoints

if TYPE_CHECKING:
    from typing_extensions import Unpack
    from qcodes.instrument import VisaInstrumentKWArgs

log = logging.getLogger(__name__)


class SantecMPMChannel(InstrumentChannel):
    """
    Channel for a single measurement port in a Santec MPM module.

    Each channel can measure optical power or electrical current depending on
    the module type, and supports configurable wavelength and gain settings.
    """

    def __init__(
            self,
            parent: "_SantecMPMxxxModule",
            name: str,
            channel: int,
            module: int,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self._parent = parent
        self.channel = channel
        self.module = module

        # Wavelength parameter
        self.add_parameter(
            name="wavelength",
            label=f"Wavelength",
            unit="nm",
            get_cmd=f"DWAV? {module},{channel}",
            set_cmd=f"DWAV {module},{channel} {{:.3f}}",
            get_parser=float,
            vals=vals.Numbers(1250, 1630),
        )
        """Measurement wavelength (nm)"""


class _SantecMPMxxxModule(InstrumentChannel):
    """
    Base class for Santec MPM measurement modules.

    Each module supports different numbers of channels depending on the module type:
    - MPM-211: 4 optical power channels
    - MPM-212: 2 optical power channels (+ 2 analog outputs)
    - MPM-213: 4 electrical current channels
    - MPM-215: 4 optical power channels (high dynamic range)
    - MPM-217: 4 optical power channels
    """

    # Lookup table for module type to class mapping
    MODULE_CLASS_LUT = {}

    # Subclasses should define _max_gain for channels with gain support
    _max_gain = None

    def __init__(
            self,
            parent: "SantecMPM220",
            name: str,
            module: int,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self._parent = parent
        self.module = module

        # Get module identification
        idn = self.get_idn()
        self._module_type = idn["model"]

        # Create channel submodules for each measurement port
        channels = ChannelList(self, "channels", SantecMPMChannel)
        for ch in range(1, self._num_channels + 1):
            channel = SantecMPMChannel(self, f"ch{ch}", ch, module)
            channels.append(channel)
            self.add_submodule(f"ch{ch}", channel)
        self.add_submodule("channels", channels)

        # Auto-range parameter
        self.auto_range: Parameter = self.add_parameter(
            name="auto_range",
            label="Auto Range Mode",
            get_cmd=f"DAUTO? {module}",
            set_cmd=f"DAUTO {module} {{:d}}",
            get_parser=lambda s: int(float(s.strip())),
            val_mapping={"MANUAL": 0, "AUTO": 1},
        )
        """Power range mode (AUTO or MANUAL)"""

        # Calibration wavelength with setpoints
        self.add_parameter(
            name="calibration_wavelength",
            label="Calibration Wavelength",
            unit="nm",
            get_raw=self._get_calibration_wavelengths,
        )
        """Calibration wavelength (nm) with index setpoint"""

        # Calibration power offset parameters for each channel
        for ch in range(1, self._num_channels + 1):
            self.add_parameter(
                parameter_class=ParameterWithSetpoints,
                name=f"calibration_power_offset_ch{ch}",
                label=f"Calibration Power Offset Ch{ch}",
                unit="dB",
                get_cmd=lambda idx=ch: self._get_calibration_power_offset(idx),
                setpoints=(self.calibration_index,),
                docstring=f"Power calibration offset (dB) for channel {ch} indexed by calibration_index",
            )

        # Create gain parameters
        self._create_gain_parameters()

    def _create_gain_parameters(self) -> None:
        """Create gain parameters for each channel. Only called if _max_gain is set."""
        if self._max_gain is None:
            return

        for ch in range(1, self._num_channels + 1):
            self.add_parameter(
                name=f"gain_ch{ch}",
                label=f"TIA Gain Channel {ch}",
                get_cmd=f"DLEV? {self.module},{ch}",
                set_cmd=f"DLEV {self.module},{ch} {{:d}}",
                get_parser=lambda s: int(float(s.strip())),
                vals=vals.Ints(1, self._max_gain),
            )

    def _get_calibration_wavelengths(self) -> float:
        """Get calibration wavelength for current index setpoint."""
        wavelengths = []
        for idx in range(1, 21):
            wl = self._parent.ask(f"CWAV? {self.module},{idx}").strip()  # Validate indices
            wavelengths.append(float(wl))
        return np.array(wl)

    def _get_calibration_power_offset(self, channel: int) -> float:
        """Get calibration power offset for specified channel and current index setpoint."""
        idx = self.calibration_index()
        if not 1 <= idx <= 20:
            raise ValueError(f"Calibration index must be 1-20, got {idx}")
        if not 1 <= channel <= self._num_channels:
            raise ValueError(f"Channel must be 1-{self._num_channels}, got {channel}")
        response = self._parent.ask(f"CWAVPO? {self.module},{channel},{idx}").strip()
        return float(response)

    def get_idn(self) -> Dict[str, str]:
        """Get module identification information."""
        response = self._parent.ask(f"MMVER? {self.module}").strip()
        parts = response.split(",")

        if len(parts) != 4:
            raise ValueError(
                f"Unexpected MMVER? response: {response!r}. "
                f"Expected: 'SANTEC,MPM-XXX,serial,Ver. x.y'"
            )

        return dict(zip(("vendor", "model", "serial", "firmware"), parts))

    def get_calibration_data(self, idx: int) -> Dict:
        """
        Get calibration wavelength and power offset values for all channels.

        Args:
            idx: Calibration wavelength index (1-20)

        Returns:
            Dictionary mapping channel number to dict with 'wavelength' and 'power_offset' keys.
            Example: {1: {'wavelength': 1550.0, 'power_offset': 0.123}, ...}

        Raises:
            ValueError: If idx is not in valid range (1-20)
        """
        if not 1 <= idx <= 20:
            raise ValueError(f"Calibration wavelength index must be 1-20, got {idx}")

        # Get calibration wavelength
        response = self._parent.ask(f"CWAV? {self.module},{idx}").strip()
        wavelength = float(response)

        # Get power offset values for each channel
        calibration_data = {}
        for ch in range(1, self._num_channels + 1):
            response = self._parent.ask(f"CWAVPO? {self.module},{ch},{idx}").strip()
            calibration_data[ch] = {
                "wavelength": wavelength,
                "power_offset": float(response),
            }

        return calibration_data

    def read(self) -> Dict[str, float]:
        """Execute optical power measurement and return results for all channels."""
        response = self._parent.ask(f"READ? {self.module}").strip()
        values = [float(v) for v in response.split(",")]
        return {f"ch{i + 1}": values[i] for i in range(min(self._num_channels, len(values)))}


class SantecMPM211(_SantecMPMxxxModule):
    """Santec MPM-211: 4 optical power channels with gain control."""
    _num_channels = 4
    _max_gain = 5


class SantecMPM212(_SantecMPMxxxModule):
    """Santec MPM-212: 2 optical power channels + 2 analog outputs, with gain control."""
    _num_channels = 2
    _max_gain = 5


class SantecMPM213(_SantecMPMxxxModule):
    """Santec MPM-213: 4 electrical current channels with gain control."""
    _num_channels = 4
    _max_gain = 4


class SantecMPM215(_SantecMPMxxxModule):
    """Santec MPM-215: 4 optical power channels, high dynamic range, no gain control."""
    _num_channels = 4


class SantecMPM217(_SantecMPMxxxModule):
    """Santec MPM-217: 4 optical power channels with gain control."""
    _num_channels = 4
    _max_gain = 5


# Populate module class lookup table
_SantecMPMxxxModule.MODULE_CLASS_LUT = {
    "MPM-211": SantecMPM211,
    "MPM-212": SantecMPM212,
    "MPM-213": SantecMPM213,
    "MPM-215": SantecMPM215,
    "MPM-217": SantecMPM217,
}


class SantecMPM220(IPInstrument):
    """
    QCoDeS driver for the Santec MPM-220 Optical Power Meter.

    Supports TCP/IP and GPIB connections. Automatically detects installed
    measurement modules and exposes them as channels (module0-module4).

    Example:
        >>> mpm = SantecMPM220("mpm", "192.168.1.161", port=5000)
        >>> mpm.measurement_mode("CONST1")
        >>> mpm.module0.ch1.wavelength(1550)
        >>> mpm.zero()
        >>> mpm.meas()
        >>> print(mpm.module0.read())
    """

    def __init__(
            self,
            name: str,
            address: str,
            **kwargs: "Unpack[VisaInstrumentKWArgs]",
    ) -> None:
        kwargs.setdefault("write_confirmation", False)
        super().__init__(name, address, **kwargs)

        # System parameters
        self.gpib_address: Parameter = self.add_parameter(
            name="gpib_address",
            label="GPIB Address",
            get_cmd="ADDR?",
            set_cmd="ADDR {:d}",
            get_parser=int,
            vals=vals.Ints(1, 31),
        )
        """GPIB address (1-31)"""

        self.ip_address: Parameter = self.add_parameter(
            name="ip_address",
            label="IP Address",
            get_cmd="IP?",
            set_cmd=None,
            get_parser=str.strip,
        )
        """Instrument IP address (read-only)"""

        self.gateway_address: Parameter = self.add_parameter(
            name="gateway_address",
            label="Gateway Address",
            get_cmd="GW?",
            set_cmd="GW {}",
            get_parser=str.strip,
        )
        """Gateway address"""

        self.subnet_mask: Parameter = self.add_parameter(
            name="subnet_mask",
            label="Subnet Mask",
            get_cmd="SUBNET?",
            set_cmd="SUBNET {}",
            get_parser=str.strip,
        )
        """Subnet mask"""

        # Measurement mode
        self.measurement_mode: Parameter = self.add_parameter(
            name="measurement_mode",
            label="Measurement Mode",
            get_cmd="WMOD?",
            set_cmd="WMOD {}",
            get_parser=str.strip,
            vals=vals.Enum("CONST1", "SWEEP1", "CONST2", "SWEEP2", "FREERUN"),
        )
        """Measurement mode"""

        # Wavelength parameters
        self.wavelength: Parameter = self.add_parameter(
            name="wavelength",
            label="Wavelength",
            unit="nm",
            get_cmd="WAV?",
            set_cmd="WAV {:.3f}",
            get_parser=float,
            vals=vals.Numbers(1250, 1630),
        )
        """Global measurement wavelength (nm)"""

        self.sweep_start: Parameter = self.add_parameter(
            name="sweep_start",
            label="Sweep Start Wavelength",
            unit="nm",
            get_cmd="WSET?",
            set_cmd=None,
            get_parser=lambda s: float(s.strip().split(",")[0]),
            vals=vals.Numbers(1250, 1630),
        )
        """Sweep start wavelength (read-only)"""

        self.sweep_stop: Parameter = self.add_parameter(
            name="sweep_stop",
            label="Sweep Stop Wavelength",
            unit="nm",
            get_cmd="WSET?",
            set_cmd=None,
            get_parser=lambda s: float(s.strip().split(",")[1]),
            vals=vals.Numbers(1250, 1630),
        )
        """Sweep stop wavelength (read-only)"""

        self.sweep_step: Parameter = self.add_parameter(
            name="sweep_step",
            label="Sweep Step",
            unit="nm",
            get_cmd="WSET?",
            set_cmd=None,
            get_parser=lambda s: float(s.strip().split(",")[2]),
            vals=vals.Numbers(0.001, 10),
        )
        """Sweep step wavelength (read-only)"""

        self.sweep_speed: Parameter = self.add_parameter(
            name="sweep_speed",
            label="Sweep Speed",
            unit="nm/s",
            get_cmd="SPE?",
            set_cmd="SPE {:.3f}",
            get_parser=float,
            vals=vals.Numbers(0.001, 200),
        )
        """Sweep speed (nm/s)"""

        # Gain and averaging
        self.gain: Parameter = self.add_parameter(
            name="gain",
            label="TIA Gain",
            get_cmd="LEV?",
            set_cmd="LEV {:d}",
            get_parser=int,
            vals=vals.Ints(1, 5),
        )
        """Global TIA Gain (1-5)"""

        self.average_time: Parameter = self.add_parameter(
            name="average_time",
            label="Average Time",
            unit="ms",
            get_cmd="AVG?",
            set_cmd="AVG {:.2f}",
            get_parser=float,
            vals=vals.Numbers(0.01, 10000),
        )
        """Averaging time (ms)"""

        self.freerun_average_time: Parameter = self.add_parameter(
            name="freerun_average_time",
            label="Freerun Average Time",
            unit="ms",
            get_cmd="FGSAVG?",
            set_cmd="FGSAVG {:.2f}",
            get_parser=float,
            vals=vals.Numbers(0.01, 10000),
        )
        """Freerun averaging time (ms)"""

        # Unit and range
        self.power_unit: Parameter = self.add_parameter(
            name="power_unit",
            label="Power Unit",
            get_cmd="UNIT?",
            set_cmd="UNIT {:d}",
            get_parser=int,
            val_mapping={"dBm": 0, "mW": 1},
        )
        """Power unit (dBm or mW)"""

        self.auto_range: Parameter = self.add_parameter(
            name="auto_range",
            label="Auto Range Mode",
            get_cmd="AUTO?",
            set_cmd="AUTO {:d}",
            get_parser=int,
            val_mapping={"MANUAL": 0, "AUTO": 1},
        )
        """Global auto-range mode"""

        # Trigger and logging
        self.trigger_mode: Parameter = self.add_parameter(
            name="trigger_mode",
            label="Trigger Mode",
            get_cmd="TRIG?",
            set_cmd="TRIG {:d}",
            get_parser=int,
            val_mapping={"INTERNAL": 0, "EXTERNAL": 1},
        )
        """Trigger mode"""

        self.logging_points: Parameter = self.add_parameter(
            name="logging_points",
            label="Logging Points",
            get_cmd="LOGN?",
            set_cmd="LOGN {:d}",
            get_parser=int,
            vals=vals.Ints(1, 1_000_000),
        )
        """Number of data points to log"""

        # Detect modules and finalize
        self._detect_modules()
        self.connect_message()

    def _detect_modules(self) -> None:
        """Detect installed measurement modules and create appropriate channel objects."""
        response = self.ask("IDIS?").strip()
        module_status = [int(x) for x in response.split(",")]

        if len(module_status) != 5:
            log.warning(f"Expected 5 modules from IDIS?, got {len(module_status)}")

        modules = ChannelList(self, "modules", _SantecMPMxxxModule)
        for idx, is_present in enumerate(module_status):
            if is_present:
                # Create temporary module to get its type
                temp_module = _SantecMPMxxxModule(self, f"temp{idx}", idx)
                idn = temp_module.get_idn()
                module_type = idn["model"]

                # Get the appropriate subclass for this module type
                module_class = _SantecMPMxxxModule.MODULE_CLASS_LUT.get(module_type)
                if module_class is None:
                    raise ValueError(
                        f"Unknown module type '{module_type}' at module {idx}. "
                        f"Supported: {', '.join(_SantecMPMxxxModule.MODULE_CLASS_LUT.keys())}"
                    )

                # Create the correctly typed module instance
                module = module_class(self, f"module{idx}", idx)
                modules.append(module)
                self.add_submodule(f"module{idx}", module)
                log.info(f"Detected {idn['model']} at module{idx} (S/N: {idn['serial']})")

        self.add_submodule("modules", modules)

    def set_sweep_parameters(self, start: float, stop: float, step: float) -> None:
        """Configure sweep mode parameters (start, stop, step in nm)."""
        self.write(f"WSET {start:.3f},{stop:.3f},{step:.3f}")

    def measurement_status(self) -> Dict[str, any]:
        """Query current measurement status."""
        response = self.ask("STAT?").strip()
        status, points = response.split(",")
        status_map = {"0": "MEASURING", "1": "COMPLETED", "-1": "STOPPED"}
        return {
            "status": status_map.get(status, status),
            "points": int(points),
        }

    def meas(self) -> None:
        """Start measurement."""
        self.write("MEAS")

    def stop(self) -> None:
        """Stop measurement."""
        self.write("STOP")

    def zero(self) -> None:
        """Run zeroing (takes ~3 seconds)."""
        self.write("ZERO")

    def reset(self) -> None:
        """Reset instrument to factory defaults."""
        self.write("*RST")
