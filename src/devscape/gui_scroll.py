import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, simpledialog

# Assuming the engine script is runnable via python -m
ENGINE_PATH = str(Path(__file__).parent.parent / "devscape" / "engine.py")


class DevScapeGUI:
    def __init__(self, master):
        self.master = master
        master.title("DevScape Ritual Dashboard")

        self.status_display = scrolledtext.ScrolledText(master, width=80, height=30)
        self.status_display.pack(pady=10)

        self.refresh_button = tk.Button(
            master, text="Refresh Status", command=self.refresh_status
        )
        self.refresh_button.pack(pady=5)

        self.ritual_frame = tk.Frame(master)
        self.ritual_frame.pack(pady=10)

        self.evolve_button = tk.Button(
            self.ritual_frame, text="Evolve Trait", command=self.evolve_trait_dialog
        )
        self.evolve_button.grid(row=0, column=0, padx=5)

        self.start_quest_button = tk.Button(
            self.ritual_frame, text="Start Quest", command=self.start_quest
        )
        self.start_quest_button.grid(row=0, column=1, padx=5)

        self.complete_quest_button = tk.Button(
            self.ritual_frame, text="Complete Quest", command=self.complete_quest_dialog
        )
        self.complete_quest_button.grid(row=0, column=2, padx=5)

        self.log_feedback_button = tk.Button(
            self.ritual_frame, text="Log Feedback", command=self.log_feedback_dialog
        )
        self.log_feedback_button.grid(row=0, column=3, padx=5)

        self.refresh_status()

    def run_cli_command(self, command_args):
        try:
            # Use python -m to run the engine module
            cmd = ["python", "-m", "src.devscape.engine"] + command_args
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8"
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            messagebox.showerror("CLI Error", f"Error running command: {e.stderr}")
            return f"Error running command: {e.stderr}"
        except FileNotFoundError:
            messagebox.showerror(
                "System Error",
                "Error: Python executable not found. Make sure Python is in your PATH.",
            )
            return (
                "Error: Python executable not found. Make sure Python is in your PATH."
            )

    def get_current_state(self):
        try:
            status_output = self.run_cli_command(["status"])
            # Extract JSON part from the status output
            start_marker = "--- Heart's Pulse (Current State) ❤️ ---"
            end_marker = "--- Lineage Archive (Recent Entries) 📜 ---"

            state_json_str = ""
            in_state_section = False
            for line in status_output.splitlines():
                if start_marker in line:
                    in_state_section = True
                    continue
                if end_marker in line:
                    in_state_section = False
                    break
                if in_state_section and line.strip():
                    state_json_str += line + "\n"

            # Clean up the JSON string (remove leading/trailing whitespace, etc.)
            state_json_str = state_json_str.strip()

            # The status output might include extra lines or formatting that makes direct json.loads fail.
            # A more robust way would be to have the engine's status command output raw JSON for the state.
            # For now, we'll try to parse the pretty-printed JSON.
            # This is a brittle approach and should be improved by having the CLI output machine-readable JSON.

            # Attempt to parse the JSON. This might fail if the pretty-printing adds non-JSON elements.
            # A safer approach would be to have a dedicated CLI command to get raw state JSON.
            # For this prototype, we'll assume the pretty-printed JSON is parsable after stripping.

            # Fallback to a simpler parsing if direct json.loads fails due to formatting
            try:
                # This is a hacky way to get the JSON part, ideally the CLI would have a raw JSON output option
                # For now, we'll rely on the pretty-printed output being somewhat parsable
                # This will likely need refinement if the status output format changes significantly
                state_data = json.loads(state_json_str)
                return state_data
            except json.JSONDecodeError as e:
                messagebox.showwarning(
                    "State Parsing Warning",
                    f"Could not parse state JSON from status output. Error: {e}\nRaw string: {state_json_str}",
                )
                return None

        except Exception as e:  # pylint: disable=broad-except
            messagebox.showerror("Error", f"Failed to get current state: {e}")
            return None

    def refresh_status(self):
        status_output = self.run_cli_command(["status"])
        self.status_display.delete(1.0, tk.END)
        self.status_display.insert(tk.END, status_output)

    def evolve_trait_dialog(self):
        current_state = self.get_current_state()
        if not current_state or not current_state.get("traits"):
            messagebox.showinfo("Evolve Trait", "No traits available to evolve.")
            return

        traits = [t["trait_id"] for t in current_state["traits"]]

        dialog = tk.Toplevel(self.master)
        dialog.title("Evolve Trait")

        tk.Label(dialog, text="Select Trait:").pack()
        trait_var = tk.StringVar(dialog)
        trait_var.set(traits[0])  # set the default option
        trait_menu = tk.OptionMenu(dialog, trait_var, *traits)
        trait_menu.pack()

        tk.Label(dialog, text="Enter New Level:").pack()
        level_entry = tk.Entry(dialog)
        level_entry.pack()
        level_entry.insert(0, "1")  # Default level

        tk.Label(dialog, text="Enter Contributor Name:").pack()
        contributor_entry = tk.Entry(dialog)
        contributor_entry.pack()
        contributor_entry.insert(0, "GUI User")

        def on_ok():
            selected_trait = trait_var.get()
            new_level = level_entry.get()
            contributor = contributor_entry.get()
            dialog.destroy()

            try:
                new_level = int(new_level)
                if new_level < 1:
                    messagebox.showerror(
                        "Input Error", "Level must be a positive integer."
                    )
                    return
            except ValueError:
                messagebox.showerror("Input Error", "Level must be an integer.")
                return

            command_args = [
                "evolve",
                selected_trait,
                str(new_level),
                "--contributor",
                contributor,
            ]
            output = self.run_cli_command(command_args)
            self.refresh_status()
            messagebox.showinfo("Evolve Trait", output)

        tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def evolve_trait(self):
        # This function is replaced by evolve_trait_dialog
        pass

    def start_quest(self):
        quest_id = simpledialog.askstring("Start Quest", "Enter Quest ID:")
        if not quest_id:
            return
        contributor = simpledialog.askstring(
            "Start Quest", "Enter Contributor Name:", initialvalue="GUI User"
        )
        if not contributor:
            return

        command_args = ["quest", "start", quest_id, "--contributor", contributor]
        output = self.run_cli_command(command_args)
        self.refresh_status()
        messagebox.showinfo("Start Quest", output)

    def complete_quest_dialog(self):
        current_state = self.get_current_state()
        if not current_state or not current_state.get("quests"):
            messagebox.showinfo("Complete Quest", "No active quests to complete.")
            return

        active_quests = [
            q["quest_id"] for q in current_state["quests"] if q["status"] == "active"
        ]
        if not active_quests:
            messagebox.showinfo("Complete Quest", "No active quests to complete.")
            return

        dialog = tk.Toplevel(self.master)
        dialog.title("Complete Quest")

        tk.Label(dialog, text="Select Quest:").pack()
        quest_var = tk.StringVar(dialog)
        quest_var.set(active_quests[0])  # set the default option
        quest_menu = tk.OptionMenu(dialog, quest_var, *active_quests)
        quest_menu.pack()

        tk.Label(dialog, text="Enter Contributor Name:").pack()
        contributor_entry = tk.Entry(dialog)
        contributor_entry.pack()
        contributor_entry.insert(0, "GUI User")

        def on_ok():
            selected_quest = quest_var.get()
            contributor = contributor_entry.get()
            dialog.destroy()

            command_args = [
                "quest",
                "complete",
                selected_quest,
                "--contributor",
                contributor,
            ]
            output = self.run_cli_command(command_args)
            self.refresh_status()
            messagebox.showinfo("Complete Quest", output)

        tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def complete_quest(self):
        # This function is replaced by complete_quest_dialog
        pass

    def log_feedback_dialog(self):
        moods = ["calm", "unrest", "joy", "mysterious", "chaotic"]

        dialog = tk.Toplevel(self.master)
        dialog.title("Log Feedback")

        tk.Label(dialog, text="Select Mood:").pack()
        mood_var = tk.StringVar(dialog)
        mood_var.set(moods[0])  # set the default option
        mood_menu = tk.OptionMenu(dialog, mood_var, *moods)
        mood_menu.pack()

        tk.Label(dialog, text="Enter Contributor Name:").pack()
        contributor_entry = tk.Entry(dialog)
        contributor_entry.pack()
        contributor_entry.insert(0, "GUI User")

        def on_ok():
            selected_mood = mood_var.get()
            contributor = contributor_entry.get()
            dialog.destroy()

            command_args = ["feedback", selected_mood, "--contributor", contributor]
            output = self.run_cli_command(command_args)
            self.refresh_status()
            messagebox.showinfo("Log Feedback", output)

        tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def log_feedback(self):
        # This function is replaced by log_feedback_dialog
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = DevScapeGUI(root)
    root.mainloop()
