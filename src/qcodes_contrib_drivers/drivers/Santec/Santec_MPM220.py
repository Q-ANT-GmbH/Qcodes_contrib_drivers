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
from qcodes.validators import Arrays, Anything

if TYPE_CHECKING:
    from typing_extensions import Unpack
    from qcodes.instrument import VisaInstrumentKWArgs

log = logging.getLogger(__name__)


class SantecMPMChannel(InstrumentChannel):
    """Channel for a single measurement port in a Santec MPM module."""

    def __init__(
            self,
            parent: "_SantecMPMxxxModule",
            name: str,
            channel: int,
            module: int,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self.channel = channel
        self.module = module

        self.wavelength: Parameter = self.add_parameter(
            name="wavelength",
            label="Wavelength",
            unit="nm",
            get_cmd=f"DWAV? {module},{channel}",
            set_cmd=f"DWAV {module},{channel} {{:.3f}}",
            get_parser=float,
            vals=vals.Numbers(1250, 1630),
        )
        """Measurement wavelength (nm)"""

        if parent._max_gain is not None:
            self.gain: Parameter = self.add_parameter(
                name="gain",
                label="TIA Gain",
                get_cmd=f"DLEV? {module},{channel}",
                set_cmd=f"DLEV {module},{channel} {{:d}}",
                get_parser=lambda s: int(float(s.strip())),
                vals=vals.Ints(1, parent._max_gain),
            )
            """TIA Gain setting for this channel"""

        self.calibration_power_offset: Parameter = self.add_parameter(
            name="calibration_power_offset",
            label="Calibration power offset",
            unit="dB",
            get_cmd=self._get_calibration_power_offset,
            setpoints=(parent.calibration_wavelength,),
            parameter_class=ParameterWithSetpoints,
            vals=Arrays(shape=(20,), valid_types=(float,)),
            snapshot_get=True,
            snapshot_value=True
        )
        """Power calibration offset (dB) - requires wavelength index parameter (1-20)"""

    def _get_calibration_power_offset(self) -> np.ndarray:
        """Get calibration power offset for all wavelength indices."""
        return np.array([
            float(self.root_instrument.ask(f"CWAVPO? {self.module},{self.channel},{i + 1}").strip())
            for i in range(20)
        ])


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

    # Class variables: subclasses must define _num_channels and optionally _max_gain
    _max_gain = None
    _num_channels = None

    def __init__(
            self,
            parent: "SantecMPM220",
            name: str,
            module: int,
            **kwargs: "Unpack[InstrumentBaseKWArgs]",
    ) -> None:
        super().__init__(parent, name, **kwargs)
        self.module = module

        self.IDN = self.add_parameter("IDN", get_cmd=self.get_idn, vals=Anything())

        self.auto_range: Parameter = self.add_parameter(
            name="auto_range",
            label="Auto Range Mode",
            get_cmd=f"DAUTO? {module}",
            set_cmd=f"DAUTO {module} {{:d}}",
            get_parser=lambda s: int(float(s.strip())),
            val_mapping={"MANUAL": 0, "AUTO": 1},
        )
        """Power range mode (AUTO or MANUAL)"""

        self.calibration_wavelength: Parameter = self.add_parameter(
            name="calibration_wavelength",
            label="Calibration Wavelength",
            unit="nm",
            get_cmd=self._get_calibration_wavelengths,
            vals=Arrays(shape=(20,), valid_types=(float,))
        )
        """Calibration wavelength (nm) with index setpoint"""

        channels = ChannelList(self, "channels", SantecMPMChannel)
        for ch in range(1, self._num_channels + 1):
            channel = SantecMPMChannel(self, f"ch{ch}", ch, module)
            # self.add_submodule(f"ch{ch}", cha
            channels.append(channel)
        self.channels = self.add_submodule("channels", channels.to_channel_tuple())

    def _get_calibration_wavelengths(self) -> np.ndarray:
        """Get calibration wavelengths for all indices."""
        return np.array([
            float(self._parent.ask(f"CWAV? {self.module},{i + 1}").strip())
            for i in range(20)
        ])

    def get_idn(self) -> Dict[str, str]:
        """Get module identification information."""
        response = self._parent.ask(f"MMVER? {self.module}").strip()
        parts = response.split(",")
        if len(parts) != 4:
            raise ValueError(f"Unexpected MMVER? response: {response!r}")
        return dict(zip(("vendor", "model", "serial", "firmware"), parts))

    def read(self) -> Dict[str, float]:
        """Execute optical power measurement and return results for all channels."""
        response = self._parent.ask(f"READ? {self.module}").strip()
        values = [float(v) for v in response.split(",")]
        return {f"ch{i + 1}": values[i] for i in range(min(self._num_channels, len(values)))}


class SantecMPM211Module(_SantecMPMxxxModule):
    """Santec MPM-211: 4 optical power channels with gain control."""
    _num_channels = 4
    _max_gain = 5


class SantecMPM212Module(_SantecMPMxxxModule):
    """Santec MPM-212: 2 optical power channels + 2 analog outputs, with gain control."""
    _num_channels = 2
    _max_gain = 5


class SantecMPM213Module(_SantecMPMxxxModule):
    """Santec MPM-213: 4 electrical current channels with gain control."""
    _num_channels = 4
    _max_gain = 4


class SantecMPM215Module(_SantecMPMxxxModule):
    """Santec MPM-215: 4 optical power channels, high dynamic range, no gain control."""
    _num_channels = 4


class SantecMPM217Module(_SantecMPMxxxModule):
    """Santec MPM-217: 4 optical power channels with gain control."""
    _num_channels = 4
    _max_gain = 5


# Populate module class lookup table
_SantecMPMxxxModule.MODULE_CLASS_LUT = {
    "MPM-211": SantecMPM211Module,
    "MPM-212": SantecMPM212Module,
    "MPM-213": SantecMPM213Module,
    "MPM-215": SantecMPM215Module,
    "MPM-217": SantecMPM217Module,
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

        self.error: Parameter = self.add_parameter(
            name="error",
            label="Error queue",
            get_cmd="ERR?",
            get_parser=lambda s: dict(code=int(s.strip().split(",")[0]), message=s.strip().split(",")[1].strip('"'))
        )
        """Read and clear error from error queue (read-only, returns error number)"""

        self.measurement_mode: Parameter = self.add_parameter(
            name="measurement_mode",
            label="Measurement Mode",
            get_cmd="WMOD?",
            set_cmd="WMOD {}",
            get_parser=str.strip,
            vals=vals.Enum("CONST1", "SWEEP1", "CONST2", "SWEEP2", "FREERUN"),
        )
        """Measurement mode"""

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
            set_cmd=self._set_sweep_start,
            get_parser=lambda s: float(s.strip().split(",")[0]),
            vals=vals.Numbers(1250, 1630),
        )
        """Sweep start wavelength (read-only)"""

        self.sweep_stop: Parameter = self.add_parameter(
            name="sweep_stop",
            label="Sweep Stop Wavelength",
            unit="nm",
            get_cmd="WSET?",
            set_cmd=self._set_sweep_stop,
            get_parser=lambda s: float(s.strip().split(",")[1]),
            vals=vals.Numbers(1250, 1630),
        )
        """Sweep stop wavelength (read-only)"""

        self.sweep_step: Parameter = self.add_parameter(
            name="sweep_step",
            label="Sweep Step",
            unit="nm",
            get_cmd="WSET?",
            set_cmd=self._set_sweep_step,
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

        self.measurement_status: Parameter = self.add_parameter(
            name="measurement_status",
            label="Measurement Status",
            get_cmd="STAT?",
            set_cmd=None,
            get_parser=self._parse_measurement_status,
        )
        """Current measurement status (dict with 'status' and 'points' keys)"""

        self.module_status: Parameter = self.add_parameter(
            name="module_status",
            label="Module Status",
            get_cmd="IDIS?",
            set_cmd=None,
            get_parser=lambda s: [bool(int(x)) for x in s.split(",")],
        )
        """Module status (dict mapping slot to boolean presence)"""

        self._detect_modules()
        self.connect_message()

    @staticmethod
    def _parse_measurement_status(response: str) -> Dict[str, any]:
        """Parse STAT? response into a dictionary."""
        status, points = response.strip().split(",")
        status_map = {"0": "MEASURING", "1": "COMPLETED", "-1": "STOPPED"}
        return {"status": status_map.get(status, status), "points": int(points)}

    def _set_sweep_start(self, value: float) -> None:
        """Set sweep start wavelength while preserving stop and step."""
        params = self.ask("WSET?").strip().split(",")
        self.write(f"WSET {value:.3f},{params[1]},{params[2]}")

    def _set_sweep_stop(self, value: float) -> None:
        """Set sweep stop wavelength while preserving start and step."""
        params = self.ask("WSET?").strip().split(",")
        self.write(f"WSET {params[0]},{value:.3f},{params[2]}")

    def _set_sweep_step(self, value: float) -> None:
        """Set sweep step while preserving start and stop."""
        params = self.ask("WSET?").strip().split(",")
        self.write(f"WSET {params[0]},{params[1]},{value:.3f}")

    def _detect_modules(self) -> None:
        """Detect installed measurement modules and create appropriate channel objects."""
        modules = ChannelList(self, "modules", _SantecMPMxxxModule)

        for idx, is_present in enumerate(self.module_status()):
            if not is_present:
                continue

            module_type = self.ask(f"MMVER? {idx}").strip().split(",")[1]
            module_class = _SantecMPMxxxModule.MODULE_CLASS_LUT.get(module_type)

            if module_class is None:
                raise ValueError(
                    f"Unknown module type '{module_type}' at slot {idx}. "
                    f"Supported: {', '.join(_SantecMPMxxxModule.MODULE_CLASS_LUT.keys())}"
                )

            module = module_class(self, f"module{idx}", idx)
            modules.append(module)
            # self.add_submodule(f"module{idx}", module)

        self.add_submodule("modules", modules)

    def set_sweep_parameters(self, start: float, stop: float, step: float) -> None:
        """Configure sweep mode parameters (start, stop, step in nm)."""
        self.write(f"WSET {start:.3f},{stop:.3f},{step:.3f}")

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
