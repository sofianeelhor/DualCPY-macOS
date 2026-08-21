import unittest
from unittest import mock

from src.device_profile import BUILTIN_PROFILES
from src.docking.macos import MacOSDockManager
from src.scrcpy_manager import ScrcpyManager


class MacOSDockManagerTests(unittest.TestCase):
    def test_capture_geometry_tracks_arranged_canvas(self):
        manager = MacOSDockManager()
        self.assertEqual(manager.create_container(100, 100, 1152, 1214), 1)
        manager.sync_layout(0, 0, 251, 648, 1152, 648, 650, 566)
        self.assertEqual(manager.get_container_geometry(), (100, 100, 1152, 1214))


class ScrcpyMacArgumentsTests(unittest.TestCase):
    @mock.patch("src.scrcpy_manager.subprocess.run")
    def test_mdns_discovery_parses_android_wireless_services(self, run):
        run.return_value = mock.Mock(
            stdout=(
                "List of discovered mdns services\n"
                "adb-thor-pair  _adb-tls-pairing._tcp  192.168.1.42:37123\n"
                "adb-thor-live  _adb-tls-connect._tcp  192.168.1.42:38901\n"
            ),
            stderr="",
            returncode=0,
        )
        manager = ScrcpyManager(adb_bin="/opt/homebrew/bin/adb")

        services = manager.discover_wireless_services()

        self.assertEqual(len(services), 2)
        self.assertEqual(services[1]["service"], "connect")
        self.assertEqual(services[1]["ip"], "192.168.1.42")
        self.assertEqual(services[1]["port"], 38901)

    @mock.patch("src.scrcpy_manager.subprocess.run")
    def test_pairing_passes_code_without_interactive_prompt(self, run):
        run.return_value = mock.Mock(
            stdout="Successfully paired to 192.168.1.42:37123\n",
            stderr="",
            returncode=0,
        )
        manager = ScrcpyManager(adb_bin="/opt/homebrew/bin/adb")

        self.assertTrue(manager.pair_wireless("192.168.1.42", 37123, "123456"))
        self.assertEqual(
            run.call_args.args[0],
            ["/opt/homebrew/bin/adb", "pair", "192.168.1.42:37123", "123456"],
        )

    @mock.patch("src.scrcpy_manager.subprocess.run")
    def test_wireless_connect_verifies_authorized_device_state(self, run):
        run.side_effect = [
            mock.Mock(stdout="connected to 192.168.1.42:38901\n", stderr="", returncode=0),
            mock.Mock(stdout="device\n", stderr="", returncode=0),
        ]
        manager = ScrcpyManager(adb_bin="/opt/homebrew/bin/adb")

        self.assertTrue(manager.connect_wireless("192.168.1.42", 38901))
        self.assertEqual(manager.serial, "192.168.1.42:38901")
        self.assertEqual(manager.connection_mode, "wireless")
        self.assertEqual(manager.device_status, "authorized")

    @mock.patch("src.scrcpy_manager.subprocess.run")
    def test_display_probe_passes_homebrew_adb_to_scrcpy(self, run):
        run.return_value = mock.Mock(
            stdout="--display-id=0 (1920x1080)\n--display-id=4 (1240x1080)\n",
            stderr="",
        )
        manager = ScrcpyManager(
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
        )

        self.assertEqual(manager.get_displays("thor-serial"), ["0", "4"])
        probe_env = run.call_args.kwargs["env"]
        self.assertEqual(probe_env["ADB"], "/opt/homebrew/bin/adb")
        self.assertEqual(probe_env["PATH"].split(":", 1)[0], "/opt/homebrew/bin")

    @mock.patch("src.scrcpy_manager.time.sleep", return_value=None)
    @mock.patch("src.scrcpy_manager.subprocess.run")
    def test_display_probe_falls_back_to_android_dumpsys(self, run, _sleep):
        one_display = mock.Mock(
            stdout="--display-id=0 (1920x1080)\n",
            stderr="",
            returncode=0,
        )
        dumpsys = mock.Mock(
            stdout="mDisplayId=0\nDisplayViewport{displayId=4, deviceWidth=1240}",
            stderr="",
            returncode=0,
        )
        run.side_effect = [one_display, one_display, one_display, dumpsys]
        manager = ScrcpyManager(
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
        )

        self.assertEqual(manager.get_displays("thor-serial"), ["0", "4"])

    @mock.patch("src.scrcpy_manager.time.sleep", return_value=None)
    def test_thor_profile_attempts_bottom_when_probe_is_transient(self, _sleep):
        manager = ScrcpyManager(
            scale=0.6,
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
            profile=BUILTIN_PROFILES["ayn_thor"],
        )
        manager.get_displays = mock.Mock(return_value=["0"])
        commands = []

        def capture(command, label, env=None):
            commands.append((label, command))
            return mock.Mock(pid=len(commands), poll=lambda: None)

        manager._start_with_retry = capture
        processes = manager.start_scrcpy("thor-serial")

        self.assertEqual(len(processes), 2)
        self.assertEqual(commands[1][1][commands[1][1].index("--display-id") + 1], "4")

    @mock.patch("src.scrcpy_manager.time.sleep", return_value=None)
    def test_bottom_failure_cleans_up_partial_top_window(self, _sleep):
        manager = ScrcpyManager(
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
            profile=BUILTIN_PROFILES["ayn_thor"],
        )
        manager.get_displays = mock.Mock(return_value=["0", "4"])
        top_process = mock.Mock(pid=1, poll=lambda: None)
        manager._start_with_retry = mock.Mock(
            side_effect=[top_process, RuntimeError("encoder unavailable")]
        )
        manager.stop = mock.Mock()

        with self.assertRaisesRegex(RuntimeError, "Bottom display 4 failed"):
            manager.start_scrcpy("thor-serial")
        manager.stop.assert_called_once()

    def test_unauthorized_device_does_not_restart_adb(self):
        manager = ScrcpyManager(
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
        )
        manager._start_adb_server = mock.Mock()
        manager._kill_adb_server = mock.Mock()

        def unauthorized():
            manager.device_status = "unauthorized"
            return None

        manager._query_first_device = mock.Mock(side_effect=unauthorized)
        self.assertIsNone(manager.detect_device())
        manager._kill_adb_server.assert_not_called()

    @mock.patch("src.scrcpy_manager.time.sleep", return_value=None)
    @mock.patch("src.scrcpy_manager.sys.platform", "darwin")
    def test_dual_thor_windows_have_native_initial_positions(self, _sleep):
        manager = ScrcpyManager(
            scale=0.6,
            scrcpy_bin="/opt/homebrew/bin/scrcpy",
            adb_bin="/opt/homebrew/bin/adb",
            profile=BUILTIN_PROFILES["ayn_thor"],
        )
        manager.get_displays = mock.Mock(return_value=["0", "4"])
        commands = []

        def capture(command, label, env=None):
            commands.append((label, command))
            return mock.Mock(pid=len(commands), poll=lambda: None)

        manager._start_with_retry = capture
        processes = manager.start_scrcpy("thor-serial")

        self.assertEqual(len(processes), 2)
        top = commands[0][1]
        bottom = commands[1][1]
        self.assertNotIn("--render-driver", top)
        self.assertEqual(top[top.index("--display-id") + 1], "0")
        self.assertEqual(bottom[bottom.index("--display-id") + 1], "4")
        self.assertEqual(top[top.index("--window-x") + 1], "100")
        self.assertEqual(top[top.index("--window-y") + 1], "100")
        self.assertIn("--audio-codec=flac", top)
        self.assertIn("--audio-buffer=100", top)
        self.assertIn("--no-audio", bottom)
        self.assertEqual(bottom[bottom.index("--window-y") + 1], str(100 + manager.f_h1))


if __name__ == "__main__":
    unittest.main()
