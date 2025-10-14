import subprocess
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from devscape.gui_scroll import DevScapeGUI


@pytest.fixture
def mock_devscape_gui_instance(mocker):
    mock_tk = mocker.patch("tkinter.Tk")
    mock_scrolledtext = mocker.patch("tkinter.scrolledtext.ScrolledText")
    mock_button = mocker.patch("devscape.gui_scroll.tk.Button")
    mock_frame = mocker.patch("tkinter.Frame")
    mock_label = mocker.patch("tkinter.Label")
    mock_entry = mocker.patch("tkinter.Entry")
    mock_optionmenu = mocker.patch("tkinter.OptionMenu")
    mock_stringvar = mocker.patch("tkinter.StringVar")
    mock_toplevel = mocker.patch("tkinter.Toplevel")
    mock_askstring = mocker.patch("tkinter.simpledialog.askstring")
    mock_showinfo = mocker.patch("tkinter.messagebox.showinfo")
    mock_showerror = mocker.patch("tkinter.messagebox.showerror")
    mock_showwarning = mocker.patch("tkinter.messagebox.showwarning")

    mock_master = MagicMock()
    mock_tk.return_value = mock_master
    mock_scrolledtext.return_value = MagicMock()
    mock_button.return_value = MagicMock()
    mock_frame.return_value = MagicMock()
    mock_label.return_value = MagicMock()
    mock_entry.return_value = MagicMock()
    mock_optionmenu.return_value = MagicMock()
    mock_stringvar.return_value = MagicMock()
    mock_toplevel.return_value = MagicMock()

    with patch.object(DevScapeGUI, "refresh_status"):
        gui = DevScapeGUI(mock_master)

    yield {
        "gui": gui,
        "mock_tk": mock_tk,
        "mock_scrolledtext": mock_scrolledtext,
        "mock_button": mock_button,
        "mock_frame": mock_frame,
        "mock_label": mock_label,
        "mock_entry": mock_entry,
        "mock_optionmenu": mock_optionmenu,
        "mock_stringvar": mock_stringvar,
        "mock_toplevel": mock_toplevel,
        "mock_askstring": mock_askstring,
        "mock_showinfo": mock_showinfo,
        "mock_showerror": mock_showerror,
        "mock_showwarning": mock_showwarning,
    }


def test_run_cli_command_success(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    with patch("subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(
            stdout="CLI Output", stderr="", returncode=0
        )
        output = gui.run_cli_command(["status"])
        assert output == "CLI Output"
        mock_subprocess_run.assert_called_once()


def test_run_cli_command_error(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showerror = mock_devscape_gui_instance["mock_showerror"]
    with patch("subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, "cmd", stderr="Error Output"
        )
        output = gui.run_cli_command(["invalid"])
        assert "Error running command: Error Output" in output
        mock_showerror.assert_called_once()


def test_run_cli_command_file_not_found(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showerror = mock_devscape_gui_instance["mock_showerror"]
    with patch("subprocess.run") as mock_subprocess_run:
        mock_subprocess_run.side_effect = FileNotFoundError
        output = gui.run_cli_command(["status"])
        assert "Python executable not found" in output
        mock_showerror.assert_called_once()


def test_get_current_state_success(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_cli_output = """
--- Heart's Pulse (Current State) ❤️ ---
{"player": {"name": "TestPlayer"}}
--- Lineage Archive (Recent Entries) 📜 ---
"""
    with patch.object(gui, "run_cli_command", return_value=mock_cli_output):
        state = gui.get_current_state()
        assert state == {"player": {"name": "TestPlayer"}}


def test_get_current_state_no_state_section(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_cli_output = """
Some other output
--- Lineage Archive (Recent Entries) 📜 ---
"""
    with patch.object(gui, "run_cli_command", return_value=mock_cli_output):
        state = gui.get_current_state()
        assert state is None


def test_get_current_state_json_decode_error(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showwarning = mock_devscape_gui_instance["mock_showwarning"]
    mock_cli_output = """
--- Heart's Pulse (Current State) ❤️ ---
Invalid JSON
--- Lineage Archive (Recent Entries) 📜 ---
"""
    with patch.object(gui, "run_cli_command", return_value=mock_cli_output):
        state = gui.get_current_state()
        assert state is None
        mock_showwarning.assert_called_once()


def test_get_current_state_cli_error(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showerror = mock_devscape_gui_instance["mock_showerror"]
    with patch.object(gui, "run_cli_command", side_effect=Exception("CLI Error")):
        state = gui.get_current_state()
        assert state is None
        mock_showerror.assert_called_once()


def test_refresh_status(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_cli_output = "Refreshed Status Output"
    with patch.object(gui, "run_cli_command", return_value=mock_cli_output):
        gui.refresh_status()
        gui.status_display.delete.assert_called_once_with(1.0, tk.END)
        gui.status_display.insert.assert_called_once_with(tk.END, mock_cli_output)


def test_start_quest_success(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_askstring = mock_devscape_gui_instance["mock_askstring"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    mock_askstring.side_effect = ["quest1", "user1"]
    with patch.object(
        gui, "run_cli_command", return_value="Quest Started"
    ) as mock_run_cli_command:
        with patch.object(gui, "refresh_status") as mock_refresh_status:
            gui.start_quest()
            mock_run_cli_command.assert_called_once_with(
                ["quest", "start", "quest1", "--contributor", "user1"]
            )
            mock_refresh_status.assert_called_once()
            mock_showinfo.assert_called_once_with("Start Quest", "Quest Started")


def test_start_quest_no_quest_id(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_askstring = mock_devscape_gui_instance["mock_askstring"]
    mock_askstring.return_value = None
    with patch.object(gui, "run_cli_command") as mock_run_cli_command:
        gui.start_quest()
        mock_run_cli_command.assert_not_called()


def test_start_quest_no_contributor(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_askstring = mock_devscape_gui_instance["mock_askstring"]
    mock_askstring.side_effect = ["quest1", None]
    with patch.object(gui, "run_cli_command") as mock_run_cli_command:
        gui.start_quest()
        mock_run_cli_command.assert_not_called()


def test_evolve_trait_dialog_no_traits(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    with patch.object(gui, "get_current_state", return_value={"traits": []}):
        gui.evolve_trait_dialog()
        mock_showinfo.assert_called_once_with(
            "Evolve Trait", "No traits available to evolve."
        )


def test_evolve_trait_dialog_initial_setup(mock_devscape_gui_instance, mocker):
    gui = mock_devscape_gui_instance["gui"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_state = {"traits": [{"trait_id": "trait1"}, {"trait_id": "trait2"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        # Mock the Toplevel and its internal components to get the on_ok function
        mock_toplevel_instance = MagicMock()
        mock_toplevel_class.return_value = mock_toplevel_instance

        mock_string_var_instance = MagicMock()
        mock_string_var_instance.get.return_value = "trait1"
        mock_stringvar_class.return_value = mock_string_var_instance

        mock_level_entry_instance = MagicMock()
        mock_level_entry_instance.get.return_value = "2"
        mock_contributor_entry_instance = MagicMock()
        mock_contributor_entry_instance.get.return_value = "GUI User"

        mock_entry_class.side_effect = [
            mock_level_entry_instance,
            mock_contributor_entry_instance,
        ]
        gui.evolve_trait_dialog()
        mock_toplevel_class.assert_called_once_with(gui.master)
        mock_toplevel_instance.title.assert_called_once_with("Evolve Trait")


def test_evolve_trait_dialog_on_ok_logic_success(mock_devscape_gui_instance, mocker):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_state = {"traits": [{"trait_id": "trait1"}, {"trait_id": "trait2"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        # Mock the Toplevel and its internal components to get the on_ok function
        mock_toplevel_instance = MagicMock()
        mock_toplevel_class.return_value = mock_toplevel_instance

        mock_string_var_instance = MagicMock()
        mock_string_var_instance.get.return_value = "trait1"
        mock_stringvar_class.return_value = mock_string_var_instance

        mock_level_entry_instance = MagicMock()
        mock_level_entry_instance.get.return_value = "2"
        mock_contributor_entry_instance = MagicMock()
        mock_contributor_entry_instance.get.return_value = "GUI User"

        mock_entry_class.side_effect = [
            mock_level_entry_instance,
            mock_contributor_entry_instance,
        ]

        mock_button_class = mock_devscape_gui_instance["mock_button"]
        mock_button_instance = MagicMock()
        mock_button_class.return_value = mock_button_instance

        with patch.object(
            gui, "run_cli_command", return_value="Trait Evolved"
        ) as mock_run_cli_command:
            with patch.object(gui, "refresh_status") as mock_refresh_status:
                gui.evolve_trait_dialog()
                # Find the call to Button that creates the 'OK' button
                ok_button_call = None
                for call_args, call_kwargs in mock_button_class.call_args_list:
                    if call_kwargs.get("text") == "OK":
                        ok_button_call = call_kwargs
                        break
                assert ok_button_call is not None
                on_ok_func = ok_button_call["command"]
                on_ok_func()

                mock_run_cli_command.assert_called_once_with(
                    ["evolve", "trait1", "2", "--contributor", "GUI User"]
                )
                mock_refresh_status.assert_called_once()
                mock_showinfo.assert_called_once_with("Evolve Trait", "Trait Evolved")


def test_evolve_trait_dialog_on_ok_logic_invalid_level(
    mock_devscape_gui_instance, mocker
):
    gui = mock_devscape_gui_instance["gui"]
    mock_showerror = mock_devscape_gui_instance["mock_showerror"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_state = {"traits": [{"trait_id": "trait1"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        mock_toplevel_instance = MagicMock()
        mock_toplevel_class.return_value = mock_toplevel_instance

        mock_string_var_instance = MagicMock()
        mock_string_var_instance.get.return_value = "trait1"
        mock_level_entry_instance = MagicMock()
        mock_level_entry_instance.get.return_value = "0"  # Invalid level
        mock_contributor_entry_instance = MagicMock()
        mock_contributor_entry_instance.get.return_value = "GUI User"

        mock_entry_class.side_effect = [
            mock_level_entry_instance,
            mock_contributor_entry_instance,
        ]
        mock_button_class = mock_devscape_gui_instance["mock_button"]
        mock_button_instance = MagicMock()
        mock_button_class.return_value = mock_button_instance
        with patch.object(
            gui, "run_cli_command", return_value=""
        ) as mock_run_cli_command:
            gui.evolve_trait_dialog()
            # Find the call to Button that creates the 'OK' button
            ok_button_call = None
            for call_args, call_kwargs in mock_button_class.call_args_list:
                if call_kwargs.get("text") == "OK":
                    ok_button_call = call_kwargs
                    break
            assert ok_button_call is not None
            on_ok_func = ok_button_call["command"]
            on_ok_func()
            mock_showerror.assert_called_once_with(
                "Input Error", "Level must be a positive integer."
            )


def test_evolve_trait_dialog_on_ok_logic_non_integer_level(
    mock_devscape_gui_instance, mocker
):
    gui = mock_devscape_gui_instance["gui"]
    mock_showerror = mock_devscape_gui_instance["mock_showerror"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_state = {"traits": [{"trait_id": "trait1"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        mock_toplevel_instance = MagicMock()
        mock_toplevel_class.return_value = mock_toplevel_instance

        mock_string_var_instance = MagicMock()
        mock_string_var_instance.get.return_value = "trait1"
        mock_stringvar_class.return_value = mock_string_var_instance

        mock_entry_instance = MagicMock()
        mock_entry_instance.get.return_value = "abc"  # Non-integer level
        mock_contributor_entry_instance = MagicMock()
        mock_contributor_entry_instance.get.return_value = "GUI User"

        mock_entry_class.side_effect = [
            mock_entry_instance,
            mock_contributor_entry_instance,
        ]

        mock_button_class = mock_devscape_gui_instance["mock_button"]
        mock_button_instance = MagicMock()
        mock_button_class.return_value = mock_button_instance
        with patch.object(
            gui, "run_cli_command", return_value=""
        ) as mock_run_cli_command:
            gui.evolve_trait_dialog()
            # Find the call to Button that creates the 'OK' button
            ok_button_call = None
            for call_args, call_kwargs in mock_button_class.call_args_list:
                if call_kwargs.get("text") == "OK":
                    ok_button_call = call_kwargs
                    break
            assert ok_button_call is not None
            on_ok_func = ok_button_call["command"]
            on_ok_func()
            mock_showerror.assert_called_once_with(
                "Input Error", "Level must be an integer."
            )


def test_complete_quest_dialog_no_quests(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    with patch.object(gui, "get_current_state", return_value={"quests": []}):
        gui.complete_quest_dialog()
        mock_showinfo.assert_called_once_with(
            "Complete Quest", "No active quests to complete."
        )


def test_complete_quest_dialog_no_active_quests(mock_devscape_gui_instance):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    mock_state = {"quests": [{"quest_id": "quest1", "status": "completed"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        gui.complete_quest_dialog()
        mock_showinfo.assert_called_once_with(
            "Complete Quest", "No active quests to complete."
        )


def test_complete_quest_dialog_on_ok_logic_success(mock_devscape_gui_instance, mocker):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_state = {"quests": [{"quest_id": "quest1", "status": "active"}]}
    with patch.object(gui, "get_current_state", return_value=mock_state):
        mock_toplevel_instance = MagicMock()
        mock_toplevel_class.return_value = mock_toplevel_instance

        mock_string_var_instance = MagicMock()
        mock_string_var_instance.get.return_value = "quest1"
        mock_stringvar_class.return_value = mock_string_var_instance

        mock_contributor_entry_instance = MagicMock()
        mock_contributor_entry_instance.get.return_value = "GUI User"
        mock_entry_class.return_value = mock_contributor_entry_instance

        mock_button_class = mock_devscape_gui_instance["mock_button"]
        mock_button_instance = MagicMock()
        mock_button_class.return_value = mock_button_instance

        with patch.object(
            gui, "run_cli_command", return_value="Quest Completed"
        ) as mock_run_cli_command:
            with patch.object(gui, "refresh_status") as mock_refresh_status:
                gui.complete_quest_dialog()
                # Find the call to Button that creates the 'OK' button
                ok_button_call = None
                for call_args, call_kwargs in mock_button_class.call_args_list:
                    if call_kwargs.get("text") == "OK":
                        ok_button_call = call_kwargs
                        break
                assert ok_button_call is not None
                on_ok_func = ok_button_call["command"]
                on_ok_func()

                mock_run_cli_command.assert_called_once_with(
                    ["quest", "complete", "quest1", "--contributor", "GUI User"]
                )
                mock_refresh_status.assert_called_once()
                mock_showinfo.assert_called_once_with(
                    "Complete Quest", "Quest Completed"
                )


def test_log_feedback_dialog_on_ok_logic_success(mock_devscape_gui_instance, mocker):
    gui = mock_devscape_gui_instance["gui"]
    mock_showinfo = mock_devscape_gui_instance["mock_showinfo"]
    mock_toplevel_class = mock_devscape_gui_instance["mock_toplevel"]
    mock_stringvar_class = mock_devscape_gui_instance["mock_stringvar"]
    mock_entry_class = mock_devscape_gui_instance["mock_entry"]

    mock_toplevel_instance = MagicMock()
    mock_toplevel_class.return_value = mock_toplevel_instance

    mock_mood_var_instance = MagicMock()
    mock_mood_var_instance.get.return_value = "calm"
    mock_stringvar_class.return_value = mock_mood_var_instance

    mock_contributor_entry_instance = MagicMock()
    mock_contributor_entry_instance.get.return_value = "GUI User"
    mock_entry_class.return_value = mock_contributor_entry_instance

    mock_button_class = mock_devscape_gui_instance["mock_button"]
    mock_button_instance = MagicMock()
    mock_button_class.return_value = mock_button_instance

    with patch.object(
        gui, "run_cli_command", return_value="Feedback Logged"
    ) as mock_run_cli_command:
        with patch.object(gui, "refresh_status") as mock_refresh_status:
            gui.log_feedback_dialog()
            # Find the call to Button that creates the 'OK' button
            ok_button_call = None
            for call_args, call_kwargs in mock_button_class.call_args_list:
                if call_kwargs.get("text") == "OK":
                    ok_button_call = call_kwargs
                    break
            assert ok_button_call is not None
            on_ok_func = ok_button_call["command"]
            on_ok_func()

            mock_run_cli_command.assert_called_once_with(
                ["feedback", "calm", "--contributor", "GUI User"]
            )
            mock_refresh_status.assert_called_once()
            mock_showinfo.assert_called_once_with("Log Feedback", "Feedback Logged")
