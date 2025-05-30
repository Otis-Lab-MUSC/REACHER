import panel as pn
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Any, Dict
from .dashboard import Dashboard

class HardwareTab(Dashboard):
    """A class to manage the Hardware tab UI for controlling wireless REACHER hardware, inheriting from Dashboard."""

    def __init__(self) -> None:
        """Initialize the HardwareTab with inherited Dashboard components and tab-specific UI.

        **Description:**
        - Sets up controls for arming and configuring hardware components like levers, cues, and lasers.
        - Includes a real-time square wave plot for laser stimulation.
        """
        super().__init__()
        self.hardware_components: Dict[str, callable] = {
            "LH Lever": self.arm_lh_lever,
            "RH Lever": self.arm_rh_lever,
            "Cue": self.arm_cs,
            "Pump": self.arm_pump,
            "Lick Circuit": self.arm_lick_circuit,
            "Laser": self.arm_laser,
            "Imaging Timestamp Receptor": self.arm_frames    
        }
        self.active_lever_button: pn.widgets.MenuButton = pn.widgets.MenuButton(
            name="Active Lever", items=[("LH Lever", "LH Lever"), ("RH Lever", "RH Lever")], button_type="primary"
        )
        self.active_lever_button.on_click(self.set_active_lever)
        self.rh_lever_armed: bool = False
        self.arm_rh_lever_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm RH Lever",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_rh_lever_button.param.watch(self.arm_rh_lever, 'value')
        self.lh_lever_armed: bool = False
        self.arm_lh_lever_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm LH Lever",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_lh_lever_button.param.watch(self.arm_lh_lever, 'value')
        self.cue_armed: bool = False
        self.arm_cue_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm Cue",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_cue_button.param.watch(self.arm_cs, 'value')
        self.send_cue_configuration_button: pn.widgets.Button = pn.widgets.Button(
            name="Send",
            icon="upload",
            button_type="primary"
        )
        self.send_cue_configuration_button.on_click(self.send_cue_configuration)
        self.cue_frequency_intslider: pn.widgets.IntInput = pn.widgets.IntInput(
            name="Cue Frequency (Hz)",
            start=0,
            end=20000,
            value=8000,
            step=50
        )
        self.cue_duration_intslider: pn.widgets.IntInput = pn.widgets.IntInput(
            name="Cue Duration (ms)",
            start=0,
            end=10000,
            value=1600,
            step=50
        )
        self.pump_armed: bool = False
        self.arm_pump_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm Pump",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_pump_button.param.watch(self.arm_pump, 'value')
        self.lick_circuit_armed: bool = False
        self.arm_lick_circuit_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm Lick Circuit",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_lick_circuit_button.param.watch(self.arm_lick_circuit, 'value')
        self.microscope_armed: bool = False
        self.arm_microscope_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm Scope",
            icon="lock",
            value=False,
            button_type="danger"
        )
        self.arm_microscope_button.param.watch(self.arm_frames, 'value')
        self.laser_armed: bool = False
        self.arm_laser_button: pn.widgets.Toggle = pn.widgets.Toggle(
            name="Arm Laser",
            button_type="danger",
            value=False,
            icon="lock",
            disabled=False
        )
        self.arm_laser_button.param.watch(self.arm_laser, 'value')
        self.stim_mode_widget: pn.widgets.Select = pn.widgets.Select(
            name="Stim Mode",
            options=["Cycle", "Active-Press"],
            value="Cycle"
        )
        self.stim_frequency_slider: pn.widgets.IntInput = pn.widgets.IntInput(
            name="Frequency (Hz)",
            start=1,
            end=100,
            step=1,
            value=20
        )
        self.stim_duration_slider: pn.widgets.IntInput = pn.widgets.IntInput(
            name="Stim Duration (s)",
            start=1,
            end=60,
            step=5,
            value=30
        )
        self.send_laser_config_button: pn.widgets.Button = pn.widgets.Button(
            name="Send",
            button_type="primary",
            icon="upload",
            disabled=False
        )
        self.send_laser_config_button.on_click(self.send_laser_configuration)
        self.interactive_plot = pn.bind(
            self.plot_square_wave, 
            frequency=self.stim_frequency_slider, 
        )

    def set_active_lever(self, event: Any) -> None:
        """Set the active lever for the experiment via the API.

        **Description:**
        - Designates either the left-hand or right-hand lever as active.

        **Args:**
        - `event (Any)`: The event object containing the new lever selection.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        if event.new == "LH Lever":
            data = {'command': 'ACTIVE_LEVER_LH'}
        elif event.new == "RH Lever":
            data = {'command': 'ACTIVE_LEVER_RH'}
        try:
            import requests
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to set active lever", str(e))

    def arm_rh_lever(self, _: Any) -> None:
        """Arm or disarm the right-hand lever via the API.

        **Description:**
        - Toggles the arming state of the right-hand lever and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.rh_lever_armed:
                data = {'command': 'ARM_LEVER_RH'}
                self.rh_lever_armed = True
                self.arm_rh_lever_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_LEVER_RH'}
                self.rh_lever_armed = False
                self.arm_rh_lever_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm RH lever", str(e))

    def arm_lh_lever(self, _: Any) -> None:
        """Arm or disarm the left-hand lever via the API.

        **Description:**
        - Toggles the arming state of the left-hand lever and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.lh_lever_armed:
                data = {'command': 'ARM_LEVER_LH'}
                self.lh_lever_armed = True
                self.arm_lh_lever_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_LEVER_LH'}
                self.lh_lever_armed = False
                self.arm_lh_lever_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm LH lever", str(e))

    def arm_cs(self, _: Any) -> None:
        """Arm or disarm the cue stimulus via the API.

        **Description:**
        - Toggles the arming state of the cue stimulus and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.cue_armed:
                data = {'command': 'ARM_CS'}
                self.cue_armed = True
                self.arm_cue_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_CS'}
                self.cue_armed = False
                self.arm_cue_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm CS", str(e))

    def send_cue_configuration(self, _: Any) -> None:
        """Send cue configuration to the API.

        **Description:**
        - Transmits frequency and duration settings for the cue.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            data = {'command': f"SET_FREQUENCY_CS:{self.cue_frequency_intslider.value}"}
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
            data = {'command': f"SET_DURATION_CS:{self.cue_duration_intslider.value}"}
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to send CS configuration", str(e))

    def arm_pump(self, _: Any) -> None:
        """Arm or disarm the pump via the API.

        **Description:**
        - Toggles the arming state of the pump and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.pump_armed:
                data = {'command': 'ARM_PUMP'}
                self.pump_armed = True
                self.arm_pump_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_PUMP'}
                self.pump_armed = False
                self.arm_pump_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm pump", str(e))

    def arm_lick_circuit(self, _: Any) -> None:
        """Arm or disarm the lick circuit via the API.

        **Description:**
        - Toggles the arming state of the lick circuit and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.lick_circuit_armed:
                data = {'command': 'ARM_LICK_CIRCUIT'}
                self.lick_circuit_armed = True
                self.arm_lick_circuit_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_LICK_CIRCUIT'}
                self.lick_circuit_armed = False
                self.arm_lick_circuit_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm lick circuit", str(e))

    def arm_frames(self, _: Any) -> None:
        """Arm or disarm the imaging timestamp receptor via the API.

        **Description:**
        - Toggles the arming state of the imaging timestamp receptor and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.microscope_armed:
                data = {'command': 'ARM_FRAME'}
                self.microscope_armed = True
                self.arm_microscope_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_FRAME'}
                self.microscope_armed = False
                self.arm_microscope_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm 2P", str(e))

    def arm_laser(self, _: Any) -> None:
        """Arm or disarm the laser via the API.

        **Description:**
        - Toggles the arming state of the laser and updates the UI.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            if not self.laser_armed:
                data = {'command': 'ARM_LASER'}
                self.laser_armed = True
                self.arm_laser_button.icon = "unlock"
            else:
                data = {'command': 'DISARM_LASER'}
                self.laser_armed = False
                self.arm_laser_button.icon = "lock"
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to arm or disarm laser", str(e))

    def send_laser_configuration(self, _: Any) -> None:
        """Send laser configuration to the API.

        **Description:**
        - Transmits mode, duration, and frequency settings for the laser.

        **Args:**
        - `_ (Any)`: Unused event argument.
        """
        if not self.api_connected:
            self.add_response("Please connect to the API first.")
            return
        api_config = self.get_api_config()
        try:
            import requests
            data = {'command': f"LASER_STIM_MODE_{str(self.stim_mode_widget.value).upper()}"}
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
            data = {'command': f"LASER_DURATION:{str(self.stim_duration_slider.value)}"}
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
            data = {'command': f"LASER_FREQUENCY:{str(self.stim_frequency_slider.value)}"}
            response = requests.post(timeout=5, url=f"http://{api_config['host']}:{api_config['port']}/serial/command", json=data)
            response.raise_for_status()
        except Exception as e:
            self.add_error("Failed to send laser configuration", str(e))

    def plot_square_wave(self, frequency: int) -> plt.Figure:
        """Plot a square wave for one second based on the given frequency.

        **Description:**
        - Generates a visual representation of a square wave for laser stimulation.

        **Args:**
        - `frequency (int)`: Number of pulses per second.

        **Returns:**
        - `plt.Figure`: The matplotlib figure object.
        """
        total_duration = 1
        t = np.linspace(0, total_duration, 1000)
        square_wave = np.zeros_like(t)
        if frequency == 1:
            square_wave[1:999] = 1
        else:
            period = 1 / frequency
            for i, time_point in enumerate(t):
                if (time_point % period) < (period / 2):
                    square_wave[i] = 1
        plt.figure(figsize=(5, 2))
        plt.plot(t, square_wave, drawstyle='steps-pre')
        plt.title(f'Square Wave - {frequency} Hz')
        plt.xlabel('Time [s]')
        plt.ylabel('Amplitude')
        plt.ylim([-0.1, 1.1])
        plt.grid(True)
        return plt.gcf()

    def arm_devices(self, devices: List[str]) -> None:
        """Arm the specified devices via the API.

        **Description:**
        - Arms a list of hardware components using their respective arming methods.

        **Args:**
        - `devices (List[str])`: List of device names to arm.
        """
        for device in devices:
            arm_device = self.hardware_components.get(device)
            if arm_device:
                arm_device(None)

    def layout(self) -> pn.Row:
        """Construct the layout for the HardwareTab.

        **Description:**
        - Assembles the UI with sections for levers, cues, pumps, and optogenetics controls.

        **Returns:**
        - `pn.Row`: The HardwareTab layout.
        """
        levers_area = pn.Column(
            pn.pane.Markdown("### Levers"),
            self.active_lever_button,
            self.arm_rh_lever_button,
            self.arm_lh_lever_button,
        )
        cue_area = pn.Column(
            pn.pane.Markdown("### Cue"),
            self.arm_cue_button,
            self.cue_duration_intslider,
            self.cue_frequency_intslider,
            self.send_cue_configuration_button
        )
        reward_area = pn.Column(
            pn.pane.Markdown("### Pump"),
            self.arm_pump_button,
            pn.Spacer(height=50),
            pn.pane.Markdown("### Lick Circuit"),
            self.arm_lick_circuit_button,
        )
        opto_area = pn.Column(
            pn.pane.Markdown("### Scope"),
            self.arm_microscope_button,
            pn.Spacer(height=50),
            pn.pane.Markdown("### Laser"),
            self.arm_laser_button,
            self.stim_mode_widget,
            self.stim_frequency_slider,
            self.stim_duration_slider,
            self.send_laser_config_button,
            pn.pane.Matplotlib(self.interactive_plot, width=500, height=200)
        )
        return pn.Row(
            pn.Column(
                levers_area,
                pn.Spacer(height=50),
                cue_area,
                pn.Spacer(height=50),
                reward_area
            ),
            pn.Spacer(width=100),
            opto_area
        )

    """
    **Contact:**
    - For inquiries or support, please email: [thejoshbq@proton.me](mailto:thejoshbq@proton.me).
    """