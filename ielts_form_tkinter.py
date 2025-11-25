#!/usr/bin/env python3
"""IELTS Answer Form implemented with tkinter (works on Windows, Linux, macOS)."""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List, Sequence, Tuple

NUM_QUESTIONS = 40
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(APP_DIR, "ielts_icon.png")

GroupSpec = Tuple[str, int]

LISTENING_BAND_TABLE: List[Tuple[int, float]] = [
    (39, 9.0),
    (37, 8.5),
    (35, 8.0),
    (32, 7.5),
    (30, 7.0),
    (26, 6.5),
    (23, 6.0),
    (18, 5.5),
    (16, 5.0),
    (13, 4.5),
    (11, 4.0),
    (8, 3.5),
    (6, 3.0),
    (4, 2.5),
    (0, 2.0),
]

READING_BAND_TABLE: List[Tuple[int, float]] = [
    (39, 9.0),
    (37, 8.5),
    (35, 8.0),
    (33, 7.5),
    (30, 7.0),
    (27, 6.5),
    (23, 6.0),
    (19, 5.5),
    (15, 5.0),
    (13, 4.5),
    (10, 4.0),
    (8, 3.5),
    (6, 3.0),
    (4, 2.5),
    (0, 2.0),
]


def normalize_answer(answer: str) -> str:
    """Normalize answers for comparison (case/spacing insensitive)."""
    cleaned = re.sub(r"[\s\-]+", "", answer.strip().lower())
    return cleaned


def lookup_band(section_name: str, correct: int) -> float:
    table = LISTENING_BAND_TABLE if section_name.lower() == "listening" else READING_BAND_TABLE
    for threshold, band in table:
        if correct >= threshold:
            return band
    return 0.0


QUESTION_LINE_RE = re.compile(r"^(\d+(?:&\d+)*)(?:[.)-])?\s+(.*)$")


def parse_answer_text(text: str) -> Dict[int, str]:
    """Parse pasted answer text into a question->answer mapping."""
    mapping: Dict[int, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(part|passage)\b", line, re.IGNORECASE):
            continue
        if line.startswith("("):
            continue
        match = QUESTION_LINE_RE.match(line)
        if not match:
            continue
        question_tokens = match.group(1).split("&")
        answer_blob = match.group(2).strip()
        if not answer_blob:
            continue
        answers = [ans.strip() for ans in re.split(r",|;", answer_blob) if ans.strip()]
        if not answers:
            answers = [answer_blob]
        for idx, token in enumerate(question_tokens):
            try:
                qnum = int(token)
            except ValueError:
                continue
            if qnum < 1 or qnum > NUM_QUESTIONS:
                continue
            answer_value = answers[idx] if idx < len(answers) else answers[-1]
            mapping[qnum] = answer_value
    return mapping


class SectionFrame(ttk.Frame):
    """Scrollable list of question entry rows."""

    def __init__(self, parent, section_name: str, groups: Sequence[GroupSpec]):
        super().__init__(parent)
        self.section_name = section_name
        self.groups: List[GroupSpec] = list(groups)
        self.keys_visible = True

        # Create scrollable frame
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.scrollable_frame.bind("<Configure>", on_frame_configure)

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas.find_all()[0], width=canvas_width)

        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.user_entries: List[ttk.Entry] = []
        self.key_entries: List[ttk.Entry] = []
        self.status_labels: List[ttk.Label] = []
        self._build_groups()

    def _build_groups(self) -> None:
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.user_entries.clear()
        self.key_entries.clear()
        self.status_labels.clear()

        # Create main container with columns
        main_container = ttk.Frame(self.scrollable_frame)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Create header row
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=(0, 10))
        for col_index, (title, _) in enumerate(self.groups):
            label = ttk.Label(header_frame, text=title, font=("TkDefaultFont", 10, "bold"))
            label.grid(row=0, column=col_index, padx=12, sticky="w")

        # Create columns for each group
        question_number = 1
        max_rows = max(int(count) for _, count in self.groups)
        
        # Create a grid for all questions
        questions_frame = ttk.Frame(main_container)
        questions_frame.pack(fill="both", expand=True)

        for col_index, (_, count) in enumerate(self.groups):
            start_number = question_number
            for row in range(int(count)):
                q_num = start_number + row
                
                # Question number
                num_label = ttk.Label(questions_frame, text=f"{q_num}.", width=4, anchor="e")
                num_label.grid(row=row, column=col_index * 4, padx=2, pady=1, sticky="e")

                # User answer entry
                user_entry = ttk.Entry(questions_frame, width=10)
                user_entry.grid(row=row, column=col_index * 4 + 1, padx=2, pady=1)

                # Key answer entry
                key_entry = ttk.Entry(questions_frame, width=10, show="" if self.keys_visible else "•")
                key_entry.grid(row=row, column=col_index * 4 + 2, padx=2, pady=1)

                # Status label
                status_label = ttk.Label(questions_frame, text="", width=3)
                status_label.grid(row=row, column=col_index * 4 + 3, padx=2, pady=1)

                self.user_entries.append(user_entry)
                self.key_entries.append(key_entry)
                self.status_labels.append(status_label)
            question_number += int(count)

    def set_groups(self, groups: Sequence[GroupSpec]) -> None:
        self.groups = list(groups)
        self._build_groups()

    def get_answers(self) -> List[str]:
        return [entry.get().strip() for entry in self.user_entries]

    def get_answer_keys(self) -> List[str]:
        return [entry.get().strip() for entry in self.key_entries]

    def clear(self) -> None:
        for entry in self.user_entries:
            entry.delete(0, tk.END)
        for label in self.status_labels:
            label.config(text="")

    def clear_keys(self) -> None:
        for entry in self.key_entries:
            entry.delete(0, tk.END)

    def evaluate(self) -> Tuple[int, int]:
        correct = 0
        evaluated = 0
        for user_entry, key_entry, status_label in zip(
            self.user_entries, self.key_entries, self.status_labels
        ):
            key_raw = key_entry.get().strip()
            if not key_raw:
                status_label.config(text="")
                continue
            evaluated += 1
            user_raw = user_entry.get().strip()
            is_correct = normalize_answer(user_raw) == normalize_answer(key_raw)
            symbol = "✓" if is_correct else "✗"
            color = "green" if is_correct else "red"
            status_label.config(text=symbol, foreground=color)
            if is_correct:
                correct += 1
        return correct, evaluated

    def reset_feedback(self) -> None:
        for label in self.status_labels:
            label.config(text="")

    def question_count(self) -> int:
        return len(self.user_entries)

    def set_keys_visible(self, visible: bool) -> None:
        self.keys_visible = visible
        for entry in self.key_entries:
            entry.config(show="" if visible else "•")

    def apply_answer_keys(self, mapping: Dict[int, str]) -> None:
        for idx, entry in enumerate(self.key_entries, start=1):
            value = mapping.get(idx)
            if value:
                entry.delete(0, tk.END)
                entry.insert(0, value)


class IELTSApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("IELTS Answer Form")
        self.root.geometry("600x700")
        if os.path.exists(ICON_PATH):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=ICON_PATH))
            except Exception:
                pass  # Icon loading is optional

        # Main container
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        self.back_button = ttk.Button(header_frame, text="← Back", command=self.on_change_test_clicked)
        self.back_button.pack(side="left", padx=(0, 10))
        self.back_button.state(["disabled"])

        title_label = ttk.Label(header_frame, text="IELTS Answer Form", font=("TkDefaultFont", 14, "bold"))
        title_label.pack(side="left")

        # Stack frame for different views
        self.stack_frame = ttk.Frame(main_frame)
        self.stack_frame.pack(fill="both", expand=True)

        # Landing page
        self.landing_frame = ttk.Frame(self.stack_frame)
        landing_content = ttk.Frame(self.landing_frame)
        landing_content.pack(expand=True)

        heading = ttk.Label(landing_content, text="Choose a test to start filling in answers.", font=("TkDefaultFont", 12, "bold"))
        heading.pack(pady=10)

        subtext = ttk.Label(
            landing_content,
            text="You can work on Listening or Reading separately.\nPick one below to load its answer sheet.",
            justify="center"
        )
        subtext.pack(pady=5)

        button_frame = ttk.Frame(landing_content)
        button_frame.pack(pady=20)

        listening_button = tk.Button(
            button_frame,
            text="Listening",
            bg="#27ae60",
            fg="white",
            font=("TkDefaultFont", 14, "bold"),
            width=15,
            height=6,
            command=lambda: self.switch_to_section("listening")
        )
        listening_button.pack(side="left", padx=10)

        reading_button = tk.Button(
            button_frame,
            text="Reading",
            bg="#c0392b",
            fg="white",
            font=("TkDefaultFont", 14, "bold"),
            width=15,
            height=6,
            command=lambda: self.switch_to_section("reading")
        )
        reading_button.pack(side="left", padx=10)

        # Section frames
        listening_groups = [
            (f"Listening Part {idx} (Q{(idx - 1) * 10 + 1}-{idx * 10})", 10)
            for idx in range(1, 5)
        ]
        self.listening_box = SectionFrame(self.stack_frame, "Listening", listening_groups)

        reading_groups = [
            ("Reading Passage 1 (Q1-13)", 13),
            ("Reading Passage 2 (Q14-26)", 13),
            ("Reading Passage 3 (Q27-40)", 14),
        ]
        self.reading_box = SectionFrame(self.stack_frame, "Reading", reading_groups)

        # Show landing page initially
        self.landing_frame.pack(fill="both", expand=True)

        # Score label
        self.score_label = ttk.Label(main_frame, text="", font=("TkDefaultFont", 10))
        self.score_label.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)

        ttk.Button(button_frame, text="Submit", command=self.on_submit_clicked).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Paste Right Answer", command=self.on_paste_answers_clicked).pack(side="left", padx=2)
        self.hide_button = ttk.Button(button_frame, text="Hide Answers", command=self.on_toggle_hide_answers)
        self.hide_button.pack(side="left", padx=2)
        ttk.Button(button_frame, text="Preview", command=self.on_preview_clicked).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Clear All", command=self.on_clear_clicked).pack(side="left", padx=2)
        ttk.Button(button_frame, text="Save Answers", command=self.on_save_clicked).pack(side="left", padx=2)

        self.answers_hidden = False
        self.current_section = None

    def get_active_section(self) -> Tuple[str, SectionFrame] | None:
        if self.current_section == "listening":
            return "Listening", self.listening_box
        if self.current_section == "reading":
            return "Reading", self.reading_box
        return None

    def require_active_section(self) -> Tuple[str, SectionFrame] | None:
        active = self.get_active_section()
        if active:
            return active
        messagebox.showinfo("Select a test first", "Choose Listening or Reading on the start screen before entering answers.")
        return None

    def collect_active_answers(self) -> Tuple[str, List[str]] | None:
        active = self.require_active_section()
        if not active:
            return None
        section_name, section_box = active
        return section_name, section_box.get_answers()

    def switch_to_section(self, target: str) -> None:
        if target not in {"listening", "reading"}:
            return
        self.current_section = target

        # Hide all frames
        self.landing_frame.pack_forget()
        self.listening_box.pack_forget()
        self.reading_box.pack_forget()

        # Show selected section
        if target == "listening":
            self.listening_box.pack(fill="both", expand=True)
        else:
            self.reading_box.pack(fill="both", expand=True)

        self.root.title(f"IELTS Answer Form · {target.capitalize()}")
        self.back_button.state(["!disabled"])
        self.apply_key_visibility()
        self.update_score_label("")

    def on_change_test_clicked(self) -> None:
        self.current_section = None
        self.landing_frame.pack(fill="both", expand=True)
        self.listening_box.pack_forget()
        self.reading_box.pack_forget()
        self.root.title("IELTS Answer Form")
        self.back_button.state(["disabled"])
        self.apply_key_visibility()
        self.update_score_label("")

    def on_clear_clicked(self) -> None:
        active = self.require_active_section()
        if not active:
            return
        _, section_box = active
        section_box.clear()
        self.update_score_label("")

    def on_paste_answers_clicked(self) -> None:
        active = self.require_active_section()
        if not active:
            return
        section_name, section_box = active

        dialog = tk.Toplevel(self.root)
        dialog.title("Paste Right Answer")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        info_label = ttk.Label(
            dialog,
            text="Paste the official answers below.\nLines like '21&22   A, E' will be split automatically.",
            justify="left"
        )
        info_label.pack(pady=10, padx=10, anchor="w")

        text_widget = scrolledtext.ScrolledText(dialog, height=15, width=60)
        text_widget.pack(fill="both", expand=True, padx=10, pady=5)

        result = {"text": ""}

        def apply_answers():
            result["text"] = text_widget.get("1.0", tk.END)
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Apply", command=apply_answers).pack(side="left", padx=5)

        dialog.wait_window()

        text = result["text"]
        if not text.strip():
            return

        mapping = parse_answer_text(text)
        if not mapping:
            messagebox.showinfo("No answers detected", "Make sure the text includes numbered lines.")
            return

        section_box.apply_answer_keys(mapping)
        section_box.reset_feedback()
        self.update_score_label("")

    def on_toggle_hide_answers(self) -> None:
        self.answers_hidden = not self.answers_hidden
        self.apply_key_visibility()

    def on_submit_clicked(self) -> None:
        active = self.require_active_section()
        if not active:
            return
        section_name, section_box = active
        missing_keys = [
            idx + 1 for idx, value in enumerate(section_box.get_answer_keys()) if not value
        ]
        if missing_keys:
            messagebox.showinfo(
                "Add answer keys",
                "Please fill the correct-answer boxes before submitting so we can compare."
            )
            return
        correct, _evaluated = section_box.evaluate()
        total = section_box.question_count()
        band = lookup_band(section_name, correct)
        self.update_score_label(f"{section_name}: {correct}/{total} correct · Band {band:.1f}")

    def on_preview_clicked(self) -> None:
        result = self.collect_active_answers()
        if not result:
            return
        section_name, answers = result
        preview_lines = [section_name]
        preview_lines.extend(
            [f"  Q{idx:02d}: {answer}" for idx, answer in enumerate(answers, start=1)]
        )
        messagebox.showinfo("Preview Answers", "\n".join(preview_lines))

    def update_score_label(self, text: str) -> None:
        self.score_label.config(text=text)

    def apply_key_visibility(self) -> None:
        visible = not self.answers_hidden
        self.hide_button.config(text="Show Answers" if not visible else "Hide Answers")
        if hasattr(self, "listening_box"):
            self.listening_box.set_keys_visible(visible)
        if hasattr(self, "reading_box"):
            self.reading_box.set_keys_visible(visible)

    def on_save_clicked(self) -> None:
        result = self.collect_active_answers()
        if not result:
            return
        section_name, answers = result
        default_name = f"ielts_{section_name.lower()}_answers.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(f"{section_name}\n")
                for idx, answer in enumerate(answers, start=1):
                    handle.write(f"{idx},{answer}\n")


def main() -> None:
    root = tk.Tk()
    app = IELTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

