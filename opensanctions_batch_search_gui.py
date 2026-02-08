#!/usr/bin/env python3
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


SCRIPT_NAME = "opensanctions_batch_search.py"


class OpenSanctionsBatchGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OpenSanctions Batch Search GUI")
        self.root.geometry("960x760")

        self.running = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(self.script_dir, SCRIPT_NAME)

        self.input_txt_var = tk.StringVar()
        self.input_csv_var = tk.StringVar()
        self.output_var = tk.StringVar(
            value=os.path.join(self.script_dir, "opensanctions_results.csv")
        )
        self.name_column_var = tk.StringVar(value="")
        self.first_name_column_var = tk.StringVar(value="Vorname")
        self.last_name_column_var = tk.StringVar(value="Nachname")

        self.max_links_var = tk.StringVar(value="3")
        self.timeout_var = tk.StringVar(value="20")
        self.sleep_var = tk.StringVar(value="0.5")
        self.limit_var = tk.StringVar(value="0")
        self.no_dedupe_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="Ready")
        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            main, text="OpenSanctions Batch Search", font=("TkDefaultFont", 12, "bold")
        )
        title.pack(anchor="w")

        manual_frame = ttk.LabelFrame(main, text="Manual Names (one per line)")
        manual_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 8))
        self.names_text = tk.Text(manual_frame, height=8, wrap="word")
        self.names_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        files_frame = ttk.LabelFrame(main, text="Input Files")
        files_frame.pack(fill=tk.X, expand=False, pady=8)
        files_frame.columnconfigure(1, weight=1)

        ttk.Label(files_frame, text="TXT").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(files_frame, textvariable=self.input_txt_var).grid(
            row=0, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(files_frame, text="Browse", command=self._pick_txt).grid(
            row=0, column=2, sticky="e", padx=8, pady=6
        )

        ttk.Label(files_frame, text="CSV").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(files_frame, textvariable=self.input_csv_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(files_frame, text="Browse", command=self._pick_csv).grid(
            row=1, column=2, sticky="e", padx=8, pady=6
        )

        cols_frame = ttk.LabelFrame(main, text="CSV Column Mapping")
        cols_frame.pack(fill=tk.X, expand=False, pady=8)
        for i in range(4):
            cols_frame.columnconfigure(i, weight=1)

        ttk.Label(cols_frame, text="Name column").grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )
        ttk.Entry(cols_frame, textvariable=self.name_column_var).grid(
            row=0, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Label(cols_frame, text="First name column").grid(
            row=1, column=0, sticky="w", padx=8, pady=6
        )
        ttk.Entry(cols_frame, textvariable=self.first_name_column_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Label(cols_frame, text="Last name column").grid(
            row=1, column=2, sticky="w", padx=8, pady=6
        )
        ttk.Entry(cols_frame, textvariable=self.last_name_column_var).grid(
            row=1, column=3, sticky="ew", padx=8, pady=6
        )

        opts_frame = ttk.LabelFrame(main, text="Options")
        opts_frame.pack(fill=tk.X, expand=False, pady=8)
        for i in range(8):
            opts_frame.columnconfigure(i, weight=1)

        ttk.Label(opts_frame, text="Max links").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_frame, textvariable=self.max_links_var, width=8).grid(
            row=0, column=1, sticky="w", padx=8, pady=6
        )
        ttk.Label(opts_frame, text="Timeout").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_frame, textvariable=self.timeout_var, width=8).grid(
            row=0, column=3, sticky="w", padx=8, pady=6
        )
        ttk.Label(opts_frame, text="Sleep").grid(row=0, column=4, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_frame, textvariable=self.sleep_var, width=8).grid(
            row=0, column=5, sticky="w", padx=8, pady=6
        )
        ttk.Label(opts_frame, text="Limit").grid(row=0, column=6, sticky="w", padx=8, pady=6)
        ttk.Entry(opts_frame, textvariable=self.limit_var, width=8).grid(
            row=0, column=7, sticky="w", padx=8, pady=6
        )

        ttk.Checkbutton(
            opts_frame, text="No dedupe", variable=self.no_dedupe_var
        ).grid(row=1, column=0, sticky="w", padx=8, pady=6)

        out_frame = ttk.LabelFrame(main, text="Output")
        out_frame.pack(fill=tk.X, expand=False, pady=8)
        out_frame.columnconfigure(1, weight=1)

        ttk.Label(out_frame, text="CSV").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(out_frame, textvariable=self.output_var).grid(
            row=0, column=1, sticky="ew", padx=8, pady=6
        )
        ttk.Button(out_frame, text="Browse", command=self._pick_output).grid(
            row=0, column=2, sticky="e", padx=8, pady=6
        )

        actions = ttk.Frame(main)
        actions.pack(fill=tk.X, expand=False, pady=(4, 8))
        ttk.Button(actions, text="Run Search", command=self.run_search).pack(side=tk.LEFT)
        ttk.Button(actions, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=8)
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(main, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, height=12, wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _pick_txt(self) -> None:
        path = filedialog.askopenfilename(
            title="Select TXT file", filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.input_txt_var.set(path)

    def _pick_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV file", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.input_csv_var.set(path)

    def _pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save output CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.output_var.set(path)

    def _append_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def _build_command(self) -> list[str]:
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Missing script: {self.script_path}")

        cmd = [sys.executable, self.script_path]

        names_raw = self.names_text.get("1.0", tk.END)
        for line in names_raw.splitlines():
            name = line.strip()
            if name:
                cmd.extend(["--name", name])

        input_txt = self.input_txt_var.get().strip()
        if input_txt:
            cmd.extend(["--input-txt", input_txt])

        input_csv = self.input_csv_var.get().strip()
        if input_csv:
            cmd.extend(["--input-csv", input_csv])

        name_col = self.name_column_var.get().strip()
        if name_col:
            cmd.extend(["--name-column", name_col])

        first_col = self.first_name_column_var.get().strip()
        if first_col:
            cmd.extend(["--first-name-column", first_col])

        last_col = self.last_name_column_var.get().strip()
        if last_col:
            cmd.extend(["--last-name-column", last_col])

        output = self.output_var.get().strip()
        if output:
            cmd.extend(["--output", output])

        max_links = int(self.max_links_var.get().strip())
        timeout = float(self.timeout_var.get().strip())
        sleep = float(self.sleep_var.get().strip())
        limit = int(self.limit_var.get().strip())

        cmd.extend(["--max-links", str(max_links)])
        cmd.extend(["--timeout", str(timeout)])
        cmd.extend(["--sleep", str(sleep)])
        cmd.extend(["--limit", str(limit)])

        if self.no_dedupe_var.get():
            cmd.append("--no-dedupe")

        return cmd

    def run_search(self) -> None:
        if self.running:
            messagebox.showinfo("Info", "A search is already running.")
            return

        try:
            cmd = self._build_command()
        except ValueError:
            messagebox.showerror(
                "Input error",
                "Check numeric fields (max links, timeout, sleep, limit).",
            )
            return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.running = True
        self.status_var.set("Running...")
        self._append_log("")
        self._append_log("Executing command:")
        self._append_log(" ".join(f'"{part}"' if " " in part else part for part in cmd))

        thread = threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True)
        thread.start()

    def _run_subprocess(self, cmd: list[str]) -> None:
        proc = subprocess.Popen(
            cmd,
            cwd=self.script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate()
        code = proc.returncode

        def finish() -> None:
            if stdout.strip():
                self._append_log("")
                self._append_log("[stdout]")
                self._append_log(stdout.rstrip())
            if stderr.strip():
                self._append_log("")
                self._append_log("[stderr]")
                self._append_log(stderr.rstrip())

            self._append_log("")
            self._append_log(f"Exit code: {code}")
            self.running = False
            self.status_var.set("Done" if code == 0 else "Failed")

        self.root.after(0, finish)


def main() -> int:
    root = tk.Tk()
    OpenSanctionsBatchGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
