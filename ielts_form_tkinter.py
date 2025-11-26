#!/usr/bin/env python3
"""IELTS Answer Form implemented with tkinter (works on Windows, Linux, macOS)."""

import os
import re
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List, Optional, Sequence, Tuple
from datetime import datetime, timedelta
from pathlib import Path

NUM_QUESTIONS = 40
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(APP_DIR, "ielts_icon.png")

# Get user data directory based on platform
def get_user_data_dir() -> Path:
    """Get platform-specific user data directory for storing application data.
    
    Linux: ~/.local/share/ielts-form/
    Windows: %APPDATA%/IELTSForm/
    macOS: ~/Library/Application Support/IELTSForm/
    """
    if sys.platform == "win32":
        # Windows: Use APPDATA (roaming) or LOCALAPPDATA (local)
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "IELTSForm"
        # Fallback to user home
        return Path.home() / "AppData" / "Roaming" / "IELTSForm"
    elif sys.platform == "darwin":
        # macOS: Use Application Support
        return Path.home() / "Library" / "Application Support" / "IELTSForm"
    else:
        # Linux and other Unix-like: Use XDG Base Directory Specification
        # Prefer XDG_DATA_HOME, fallback to ~/.local/share
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / "ielts-form"
        return Path.home() / ".local" / "share" / "ielts-form"

# Set up data directory and database file
USER_DATA_DIR = get_user_data_dir()
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
FORMS_DB_FILE = USER_DATA_DIR / "forms.json"

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


def is_answer_correct(user_answer: str, key_answer: str) -> bool:
    """Check if user answer matches the key answer.
    
    The key answer may contain multiple options separated by "/" (e.g., "gardens / gardening").
    If the user provides any of these options, it's considered correct.
    """
    user_normalized = normalize_answer(user_answer)
    
    # Split key answer by "/" to get multiple acceptable options
    key_options = [opt.strip() for opt in key_answer.split("/")]
    
    # Check if user's normalized answer matches any of the key options
    for key_option in key_options:
        if user_normalized == normalize_answer(key_option):
            return True
    
    return False


def lookup_band(section_name: str, correct: int) -> float:
    table = LISTENING_BAND_TABLE if section_name.lower() == "listening" else READING_BAND_TABLE
    for threshold, band in table:
        if correct >= threshold:
            return band
    return 0.0


QUESTION_LINE_RE = re.compile(r"^(\d+(?:&\d+)*)(?:[.)-])?\s+(.*)$")


def parse_answer_text(text: str) -> Tuple[Dict[int, str], Dict[int, List[int]]]:
    """Parse pasted answer text into a question->answer mapping.
    
    Returns:
        Tuple of (mapping, shared_groups):
        - mapping: Dict[int, str] - question number to answer string
        - shared_groups: Dict[int, List[int]] - question number to list of questions in same group
    
    Handles formats like:
    - "21 B" -> question 21 has answer B
    - "21&22 B, D" -> questions 21 and 22 share answers B, D (each answer can only be used once)
    - "23&24&25 A, B, C" -> questions 23, 24, 25 share answers A, B, C
    """
    mapping: Dict[int, str] = {}
    shared_groups: Dict[int, List[int]] = {}  # Maps question to list of questions in its group
    
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
        
        # Parse answers - split by comma or semicolon
        answers = [ans.strip() for ans in re.split(r",|;", answer_blob) if ans.strip()]
        if not answers:
            answers = [answer_blob]
        
        # Parse question numbers
        question_numbers = []
        for token in question_tokens:
            try:
                qnum = int(token)
            except ValueError:
                continue
            if qnum < 1 or qnum > NUM_QUESTIONS:
                continue
            question_numbers.append(qnum)
        
        if not question_numbers:
            continue
        
        # If multiple questions share answers (e.g., "21&22 B, D")
        # Store them as a shared group - answers must be matched without replacement
        if len(question_numbers) > 1:
            # Store shared group info for all questions in the group
            for qnum in question_numbers:
                shared_groups[qnum] = question_numbers.copy()
            # Store the answer options (comma-separated for shared groups)
            shared_answer = ", ".join(answers)
            for qnum in question_numbers:
                mapping[qnum] = shared_answer
        else:
            # Single question - join multiple options with " / " if multiple answers
            qnum = question_numbers[0]
            if len(answers) > 1:
                mapping[qnum] = " / ".join(answers)
            else:
                mapping[qnum] = answers[0]
    
    return mapping, shared_groups


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
        self.shared_groups: Dict[int, List[int]] = {}  # Maps question number to list of questions in same group
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
            # Create a frame for each header to center the text
            header_cell = ttk.Frame(header_frame, style="Card.TFrame")
            header_cell.grid(row=0, column=col_index, padx=8, sticky="ew", ipady=8)
            label = ttk.Label(header_cell, text=title, style="Heading.TLabel")
            label.pack(expand=True)  # Center the label in its frame
        # Configure column weights for equal spacing
        for col_index in range(len(self.groups)):
            header_frame.columnconfigure(col_index, weight=1)

        # Create columns for each group
        question_number = 1
        max_rows = max(int(count) for _, count in self.groups)
        
        # Create a grid for all questions
        questions_frame = ttk.Frame(main_container)
        questions_frame.pack(fill="both", expand=True)

        # Configure columns for equal width per group
        for col_index in range(len(self.groups)):
            # Each group takes 4 columns: number, user, key, status
            base_col = col_index * 4
            questions_frame.columnconfigure(base_col, weight=0, minsize=40)  # Number column
            questions_frame.columnconfigure(base_col + 1, weight=1, minsize=80)  # User entry
            questions_frame.columnconfigure(base_col + 2, weight=1, minsize=80)  # Key entry
            questions_frame.columnconfigure(base_col + 3, weight=0, minsize=30)  # Status

        for col_index, (_, count) in enumerate(self.groups):
            start_number = question_number
            for row in range(int(count)):
                q_num = start_number + row
                
                # Question number
                num_label = ttk.Label(questions_frame, text=f"{q_num}.", width=4, anchor="e")
                num_label.grid(row=row, column=col_index * 4, padx=2, pady=1, sticky="e")

                # User answer entry
                user_entry = ttk.Entry(questions_frame, width=10)
                user_entry.grid(row=row, column=col_index * 4 + 1, padx=2, pady=1, sticky="ew")

                # Key answer entry
                key_entry = ttk.Entry(questions_frame, width=10)
                key_entry.grid(row=row, column=col_index * 4 + 2, padx=2, pady=1, sticky="ew")

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
        """Get answer keys, returning stored text if hidden."""
        result = []
        for entry in self.key_entries:
            text = entry.get().strip()
            # If showing placeholder, get stored text instead
            if text == "HIDDEN" and hasattr(entry, '_stored_text'):
                text = entry._stored_text
            result.append(text)
        return result

    def clear(self) -> None:
        """Clear user answers and status labels."""
        for entry in self.user_entries:
            entry.delete(0, tk.END)
        for label in self.status_labels:
            label.config(text="")

    def clear_user_answers(self) -> None:
        """Clear only user answers (keep keys and status)."""
        for entry in self.user_entries:
            entry.delete(0, tk.END)

    def clear_keys(self) -> None:
        """Clear only answer keys."""
        for entry in self.key_entries:
            entry.config(state="normal")
            entry.delete(0, tk.END)
            # Clear stored text if exists
            if hasattr(entry, '_stored_text'):
                delattr(entry, '_stored_text')
            # If hidden, show placeholder
            if not self.keys_visible:
                entry.insert(0, "HIDDEN")
                entry.config(state="readonly", foreground="#cccccc")

    def clear_all(self) -> None:
        """Clear both user answers and keys, plus status labels."""
        for entry in self.user_entries:
            entry.delete(0, tk.END)
        for entry in self.key_entries:
            entry.config(state="normal")
            entry.delete(0, tk.END)
            # Clear stored text if exists
            if hasattr(entry, '_stored_text'):
                delattr(entry, '_stored_text')
            # If hidden, show placeholder
            if not self.keys_visible:
                entry.insert(0, "HIDDEN")
                entry.config(state="readonly", foreground="#cccccc")
        for label in self.status_labels:
            label.config(text="")

    def evaluate(self) -> Tuple[int, int]:
        """Evaluate answers, handling shared answer groups correctly."""
        correct = 0
        evaluated = 0
        processed_groups = set()  # Track which groups we've already processed
        
        # First, evaluate questions that are NOT in shared groups
        for idx, (user_entry, key_entry, status_label) in enumerate(
            zip(self.user_entries, self.key_entries, self.status_labels), start=1
        ):
            # Skip if this question is part of a shared group (will process groups separately)
            if idx in self.shared_groups:
                continue
            
            key_raw = key_entry.get().strip()
            if not key_raw:
                status_label.config(text="")
                continue
            evaluated += 1
            user_raw = user_entry.get().strip()
            is_correct = is_answer_correct(user_raw, key_raw)
            symbol = "✓" if is_correct else "✗"
            color = "green" if is_correct else "red"
            status_label.config(text=symbol, foreground=color)
            if is_correct:
                correct += 1
        
        # Now evaluate shared groups (e.g., "21&22 B, D")
        for qnum, group_questions in self.shared_groups.items():
            # Skip if we've already processed this group
            group_tuple = tuple(sorted(group_questions))
            if group_tuple in processed_groups:
                continue
            processed_groups.add(group_tuple)
            
            # Get all entries for this group
            group_user_answers = []
            group_key_answers = []
            group_labels = []
            group_indices = []
            
            for q in group_questions:
                if q < 1 or q > len(self.user_entries):
                    continue
                idx = q - 1  # Convert to 0-based index
                group_user_answers.append(self.user_entries[idx].get().strip())
                key_raw = self.key_entries[idx].get().strip()
                group_key_answers.append(key_raw)
                group_labels.append(self.status_labels[idx])
                group_indices.append(q)
            
            # Check if any key is empty - skip group if all keys empty
            if not any(group_key_answers):
                for label in group_labels:
                    label.config(text="")
                continue
            
            evaluated += len(group_questions)
            
            # Parse key answers - they should be comma-separated (e.g., "B, D")
            # Get the first non-empty key answer
            key_answer_str = next((k for k in group_key_answers if k), "")
            if not key_answer_str:
                for label in group_labels:
                    label.config(text="")
                continue
            
            # Parse available answer options (split by comma)
            available_options = [opt.strip() for opt in key_answer_str.split(",") if opt.strip()]
            
            # Match user answers to available options without replacement
            # This ensures each option can only be used once
            used_options = set()
            group_correct = 0
            
            for user_answer, label in zip(group_user_answers, group_labels):
                user_normalized = normalize_answer(user_answer)
                matched = False
                
                # Try to match user answer to an unused option
                for option in available_options:
                    option_normalized = normalize_answer(option)
                    if user_normalized == option_normalized and option not in used_options:
                        matched = True
                        used_options.add(option)
                        group_correct += 1
                        break
                
                # Update label
                symbol = "✓" if matched else "✗"
                color = "green" if matched else "red"
                label.config(text=symbol, foreground=color)
            
            correct += group_correct
        
        return correct, evaluated

    def reset_feedback(self) -> None:
        for label in self.status_labels:
            label.config(text="")

    def question_count(self) -> int:
        return len(self.user_entries)

    def set_keys_visible(self, visible: bool) -> None:
        self.keys_visible = visible
        HIDDEN_PLACEHOLDER = "HIDDEN"
        
        for entry in self.key_entries:
            current_text = entry.get()
            if not visible:
                # Store actual text (only if not already the placeholder)
                if current_text != HIDDEN_PLACEHOLDER:
                    entry._stored_text = current_text
                # Replace with fixed placeholder
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, HIDDEN_PLACEHOLDER)
                entry.config(state="readonly", foreground="#cccccc")
            else:
                # Restore actual text
                stored_text = getattr(entry, '_stored_text', "")
                entry.config(state="normal", foreground="black")
                entry.delete(0, tk.END)
                entry.insert(0, stored_text)
                # Clean up stored text
                if hasattr(entry, '_stored_text'):
                    delattr(entry, '_stored_text')

    def apply_answer_keys(self, mapping: Dict[int, str], shared_groups: Optional[Dict[int, List[int]]] = None) -> None:
        """Apply answer keys to entries.
        
        Args:
            mapping: Question number to answer string
            shared_groups: Question number to list of questions in same group (for shared answers)
        """
        if shared_groups:
            self.shared_groups = shared_groups
        else:
            self.shared_groups = {}
        
        for idx, entry in enumerate(self.key_entries, start=1):
            value = mapping.get(idx)
            if value:
                # Make sure entry is editable
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, value)
                # Update stored text if hidden
                if not self.keys_visible:
                    entry._stored_text = value
                    entry.delete(0, tk.END)
                    entry.insert(0, "HIDDEN")
                    entry.config(state="readonly", foreground="#cccccc")


class FormWindow:
    """Popup window for a single IELTS form."""
    
    def __init__(self, parent: tk.Tk, form_name: str, section_name: str, groups: Sequence[GroupSpec], 
                 default_width: int = 1000, default_height: int = 700, min_width: int = 1000, min_height: int = 700):
        self.window = tk.Toplevel(parent)
        self.window.title(f"{form_name} - {section_name}")
        self.window.configure(bg="#f5f5f5")
        self.form_name = form_name
        self.section_name = section_name
        self.answers_hidden = False
        self.default_width = default_width
        self.default_height = default_height
        self.min_width = min_width
        self.min_height = min_height
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill="both", expand=True)
        
        # Header with form name and timer
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        title_label = ttk.Label(header_frame, text=form_name, style="Heading.TLabel")
        title_label.pack(side="left")
        
        # Timer section
        timer_frame = ttk.Frame(header_frame)
        timer_frame.pack(side="right")
        
        # Set timer duration based on section
        timer_minutes = 30 if section_name == "Listening" else 60
        self.timer_seconds = timer_minutes * 60
        self.timer_running = False
        self.timer_end_time = None
        
        self.timer_label = ttk.Label(timer_frame, text=f"⏱️ {self.format_time(self.timer_seconds)}", 
                                     font=("Segoe UI", 12, "bold"), foreground="#2c3e50")
        self.timer_label.pack(side="left", padx=5)
        
        self.timer_button = ttk.Button(timer_frame, text="▶ Start", style="TButton", 
                                      command=self.toggle_timer, width=8)
        self.timer_button.pack(side="left", padx=2)
        
        reset_button = ttk.Button(timer_frame, text="🔄 Reset", style="TButton", 
                                 command=self.reset_timer, width=8)
        reset_button.pack(side="left", padx=2)
        
        # Start timer update after window is fully initialized
        self.window.after(100, self.update_timer)
        
        # Section frame
        self.section_box = SectionFrame(main_frame, section_name, groups)
        self.section_box.pack(fill="both", expand=True)
        
        # Score label
        self.score_label = ttk.Label(main_frame, text="", style="Heading.TLabel")
        self.score_label.pack(pady=8)
        
        # Buttons with icons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="✓ Submit", style="TButton", command=self.on_submit_clicked).pack(side="left", padx=3)
        ttk.Button(button_frame, text="📋 Paste Right Answer", style="TButton", command=self.on_paste_answers_clicked).pack(side="left", padx=3)
        self.hide_button = ttk.Button(button_frame, text="👁️ Hide Answers", style="TButton", command=self.on_toggle_hide_answers)
        self.hide_button.pack(side="left", padx=3)
        ttk.Button(button_frame, text="👀 Preview", style="TButton", command=self.on_preview_clicked).pack(side="left", padx=3)
        ttk.Button(button_frame, text="🗑️ Clear All", style="TButton", command=self.on_clear_clicked).pack(side="left", padx=3)
        ttk.Button(button_frame, text="💾 Save Answers", style="TButton", command=self.on_save_clicked).pack(side="left", padx=3)
        
        # Auto-size window to fit content
        # NOTE: To manually adjust popup window size, modify the default_width/default_height
        # parameters when creating FormWindow (in on_form_clicked method)
        self.window.update_idletasks()
        width = max(self.window.winfo_reqwidth() + 40, self.default_width)
        height = max(self.window.winfo_reqheight() + 40, self.default_height)
        self.window.geometry(f"{width}x{height}")
        self.window.minsize(self.min_width, self.min_height)
    
    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def toggle_timer(self) -> None:
        """Start or pause the timer."""
        if not self.timer_running:
            # Start timer
            if self.timer_end_time is None:
                self.timer_end_time = datetime.now() + timedelta(seconds=self.timer_seconds)
            else:
                # Resume from where we left off
                remaining = (self.timer_end_time - datetime.now()).total_seconds()
                if remaining <= 0:
                    self.timer_end_time = datetime.now() + timedelta(seconds=self.timer_seconds)
                else:
                    self.timer_end_time = datetime.now() + timedelta(seconds=remaining)
            self.timer_running = True
            self.timer_button.config(text="⏸ Pause")
        else:
            # Pause timer
            self.timer_running = False
            self.timer_button.config(text="▶ Start")
    
    def reset_timer(self) -> None:
        """Reset timer to initial value."""
        timer_minutes = 30 if self.section_name == "Listening" else 60
        self.timer_seconds = timer_minutes * 60
        self.timer_running = False
        self.timer_end_time = None
        self.timer_label.config(text=f"⏱️ {self.format_time(self.timer_seconds)}", foreground="#2c3e50")
        self.timer_button.config(text="▶ Start")
    
    def update_timer(self) -> None:
        """Update timer display every second."""
        # Check if window still exists by trying to access a widget property
        try:
            # Try to access window title - if window is destroyed, this will raise TclError
            _ = self.window.title()
        except (tk.TclError, AttributeError, RuntimeError):
            # Window was destroyed
            return
        
        if self.timer_running and self.timer_end_time:
            remaining = int((self.timer_end_time - datetime.now()).total_seconds())
            if remaining <= 0:
                # Time's up!
                self.timer_running = False
                try:
                    self.timer_label.config(text="⏱️ 00:00", foreground="#e74c3c")
                    self.timer_button.config(text="▶ Start")
                    # Show alarm
                    self.window.bell()  # System beep
                    messagebox.showwarning("Time's Up!", f"Your {self.section_name} test time has ended!")
                except tk.TclError:
                    return  # Window was destroyed
            else:
                self.timer_seconds = remaining
                # Change color when less than 5 minutes remaining
                color = "#e74c3c" if remaining < 300 else "#2c3e50"
                try:
                    self.timer_label.config(text=f"⏱️ {self.format_time(remaining)}", foreground=color)
                except tk.TclError:
                    return  # Window was destroyed
        else:
            # Show current time if paused
            if self.timer_end_time:
                remaining = int((self.timer_end_time - datetime.now()).total_seconds())
                if remaining > 0:
                    self.timer_seconds = remaining
                    try:
                        self.timer_label.config(text=f"⏱️ {self.format_time(remaining)}", foreground="#2c3e50")
                    except tk.TclError:
                        return  # Window was destroyed
        
        # Schedule next update only if window still exists
        try:
            self.window.after(1000, self.update_timer)
        except tk.TclError:
            pass  # Window was destroyed
    
    def on_submit_clicked(self) -> None:
        # Evaluate only questions that have answer keys (optional)
        correct, evaluated = self.section_box.evaluate()
        total = self.section_box.question_count()
        if evaluated == 0:
            self.score_label.config(text="No answer keys provided. Fill in answer keys to get a score.")
            return
        band = lookup_band(self.section_name, correct)
        self.score_label.config(text=f"{self.section_name}: {correct}/{evaluated} correct (out of {evaluated} with keys) · Band {band:.1f}")
    
    def on_paste_answers_clicked(self) -> None:
        dialog = tk.Toplevel(self.window)
        dialog.title("Paste Right Answer")
        dialog.geometry("500x400")
        dialog.transient(self.window)
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
        
        mapping, shared_groups = parse_answer_text(text)
        if not mapping:
            messagebox.showinfo("No answers detected", "Make sure the text includes numbered lines.")
            return
        
        self.section_box.apply_answer_keys(mapping, shared_groups)
        self.section_box.reset_feedback()
        self.score_label.config(text="")
    
    def on_toggle_hide_answers(self) -> None:
        self.answers_hidden = not self.answers_hidden
        self.hide_button.config(text="👁️ Show Answers" if not self.answers_hidden else "👁️ Hide Answers")
        self.section_box.set_keys_visible(not self.answers_hidden)
    
    def on_preview_clicked(self) -> None:
        answers = self.section_box.get_answers()
        preview_lines = [self.form_name]
        preview_lines.extend(
            [f"  Q{idx:02d}: {answer}" for idx, answer in enumerate(answers, start=1)]
        )
        messagebox.showinfo("Preview Answers", "\n".join(preview_lines))
    
    def on_clear_clicked(self) -> None:
        """Show dialog with clear options."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Clear Answers")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg="#f5f5f5")
        
        # Title
        title_label = ttk.Label(dialog, text="What would you like to clear?", style="Heading.TLabel")
        title_label.pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        result = {"action": None}
        
        def clear_user_only():
            result["action"] = "user"
            dialog.destroy()
        
        def clear_keys_only():
            result["action"] = "keys"
            dialog.destroy()
        
        def clear_all():
            result["action"] = "all"
            dialog.destroy()
        
        def cancel():
            result["action"] = "cancel"
            dialog.destroy()
        
        # Option buttons
        ttk.Button(button_frame, text="Clear Only User Answers", style="TButton", 
                  command=clear_user_only).pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Clear Only Right Answers", style="TButton", 
                  command=clear_keys_only).pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Clear All Answers", style="TButton", 
                  command=clear_all).pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Cancel", style="TButton", 
                  command=cancel).pack(fill="x", pady=5)
        
        dialog.wait_window()
        
        action = result["action"]
        if action == "user":
            self.section_box.clear_user_answers()
            self.score_label.config(text="")
        elif action == "keys":
            self.section_box.clear_keys()
            self.section_box.reset_feedback()
            self.score_label.config(text="")
        elif action == "all":
            self.section_box.clear_all()
            self.score_label.config(text="")
        # If cancel, do nothing
    
    def save_state(self) -> Dict:
        """Save current form state (answers, keys, score, etc.)."""
        return {
            "user_answers": self.section_box.get_answers(),
            "answer_keys": self.section_box.get_answer_keys(),
            "score_text": self.score_label.cget("text"),
            "answers_hidden": self.answers_hidden,
        }
    
    def load_state(self, state: Dict) -> None:
        """Load saved form state."""
        if not state:
            return
        
        # Restore user answers
        user_answers = state.get("user_answers", [])
        for idx, entry in enumerate(self.section_box.user_entries):
            if idx < len(user_answers):
                entry.delete(0, tk.END)
                entry.insert(0, user_answers[idx])
        
        # Restore answer keys
        answer_keys = state.get("answer_keys", [])
        for idx, entry in enumerate(self.section_box.key_entries):
            if idx < len(answer_keys) and answer_keys[idx]:
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, answer_keys[idx])
        
        # Restore score
        score_text = state.get("score_text", "")
        if score_text:
            self.score_label.config(text=score_text)
        
        # Restore hide state (this will handle hiding keys if needed)
        answers_hidden = state.get("answers_hidden", False)
        if answers_hidden != self.answers_hidden:
            self.on_toggle_hide_answers()
    
    def on_save_clicked(self) -> None:
        answers = self.section_box.get_answers()
        default_name = f"ielts_{self.form_name.replace(' ', '_')}_answers.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(f"{self.form_name}\n")
                handle.write(f"{self.section_name}\n")
                for idx, answer in enumerate(answers, start=1):
                    handle.write(f"{idx},{answer}\n")


class FormListFrame(ttk.Frame):
    """Frame showing list of forms for a section with simple button-based UI."""
    
    def __init__(self, parent, section_name: str, on_form_clicked, get_form_state=None, save_callback=None, delete_callback=None):
        super().__init__(parent)
        self.section_name = section_name
        self.on_form_clicked = on_form_clicked
        self.get_form_state = get_form_state  # Function to get form state for status
        self.save_callback = save_callback  # Function to save database
        self.delete_callback = delete_callback  # Function to delete form state from database
        self.forms: List[str] = []
        self._click_in_progress = False  # Flag to prevent rapid double-clicks
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=15, padx=15)
        
        title_label = ttk.Label(header_frame, text=f"{section_name} Forms", style="Heading.TLabel")
        title_label.pack(side="left")
        
        # Button frame for actions
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side="right")
        
        delete_button = ttk.Button(button_frame, text="🗑️ Delete", style="Danger.TButton", command=self.on_delete_form)
        delete_button.pack(side="right", padx=(0, 5))
        
        add_button = ttk.Button(button_frame, text="➕ New", style="TButton", command=self.on_add_form)
        add_button.pack(side="right")
        
        # Simple listbox with scrollbar (most stable approach)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 12),
            yscrollcommand=scrollbar.set,
            bg="white",
            fg="#2c3e50",
            selectbackground="#3498db",
            selectforeground="white",
            borderwidth=0,
            highlightthickness=1,
            highlightcolor="#3498db",
            relief="flat",
            activestyle="none"  # Remove underline on selection
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bind events - only double-click opens forms
        self.listbox.bind("<Double-Button-1>", self.on_form_double_click)
        self.listbox.bind("<Return>", self.on_form_double_click)
    
    def suggest_next_form_name(self) -> str:
        """Suggest the next form name based on existing forms."""
        # Pattern to match: "Practice Cam XX Listening Test YY" or "Practice Cam XX Reading Test YY"
        pattern = re.compile(r"Practice Cam (\d+) (Listening|Reading) Test (\d+)")
        
        max_cam = 0
        cam_test_map = {}  # Map of cam_number -> max_test_number
        
        # Parse all existing forms
        for form_name in self.forms:
            match = pattern.match(form_name)
            if match:
                cam_num = int(match.group(1))
                test_num = int(match.group(3))
                
                max_cam = max(max_cam, cam_num)
                
                if cam_num not in cam_test_map:
                    cam_test_map[cam_num] = test_num
                else:
                    cam_test_map[cam_num] = max(cam_test_map[cam_num], test_num)
        
        # Determine next form name
        if not cam_test_map:
            # No existing forms, start with Cam 10 Test 01
            next_cam = 10
            next_test = 1
        else:
            # Find the highest Cam number and its max test
            highest_cam = max(cam_test_map.keys())
            max_test = cam_test_map[highest_cam]
            
            if max_test < 4:
                # Increment test number
                next_cam = highest_cam
                next_test = max_test + 1
            else:
                # Max test reached, increment Cam and reset test to 01
                next_cam = highest_cam + 1
                next_test = 1
        
        # Generate suggested name (2-digit format for consistency)
        section_type = "Listening" if self.section_name == "Listening" else "Reading"
        return f"Practice Cam {next_cam} {section_type} Test {next_test:02d}"
    
    def on_add_form(self) -> None:
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("New Form")
        dialog.geometry("500x150")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter form name:", font=("TkDefaultFont", 10)).pack(pady=10)
        
        # Auto-suggest next form name
        suggested_name = self.suggest_next_form_name()
        
        entry = ttk.Entry(dialog, width=50, font=("TkDefaultFont", 10))
        entry.pack(pady=5, padx=20, fill="x")
        entry.insert(0, suggested_name)
        
        # Select all text for easy editing
        entry.select_range(0, tk.END)
        
        entry.focus()
        
        result = {"name": ""}
        
        def create_form():
            name = entry.get().strip()
            if name:
                result["name"] = name
                dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Create", command=create_form).pack(side="left", padx=5)
        
        entry.bind("<Return>", lambda e: create_form())
        dialog.wait_window()
        
        name = result["name"]
        if name:
            self.add_form(name)
            # Save database after adding form
            if self.save_callback:
                self.save_callback()
    
    def on_delete_form(self) -> None:
        """Delete the selected form from the list."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a form to delete.")
            return
        
        idx = selection[0]
        if idx >= len(self.forms):
            return
        
        form_name = self.forms[idx]
        
        # Confirmation dialog
        result = messagebox.askyesno(
            "Delete Form",
            f"Are you sure you want to delete '{form_name}'?\n\nThis will remove the form and all its saved data.",
            icon="warning"
        )
        
        if result:
            # Remove from list
            self.forms.remove(form_name)
            self.refresh_list()
            
            # Delete form state from database
            if self.delete_callback:
                self.delete_callback(form_name)
            
            # Save database
            if self.save_callback:
                self.save_callback()
    
    def get_form_status(self, form_name: str) -> str:
        """Get status of a form: 'completed', 'in-progress', or 'not-started'."""
        if self.get_form_state:
            form_key = f"{self.section_name.lower()}:{form_name}"
            state = self.get_form_state(form_key)
            if state and state.get("score_text"):
                return "completed"
            elif state and (state.get("user_answers") or state.get("answer_keys")):
                return "in-progress"
        return "not-started"
    
    def format_listbox_item(self, form_name: str) -> str:
        """Format form name for listbox (no status icons)."""
        return form_name
    
    def on_form_double_click(self, event=None) -> None:
        """Handle double click on listbox item - opens the form."""
        # Prevent rapid successive clicks
        if self._click_in_progress:
            return
        
        try:
            selection = self.listbox.curselection()
            if not selection:
                return
            
            idx = selection[0]
            if idx >= len(self.forms):
                return
            
            form_name = self.forms[idx]
            
            # Set flag to prevent rapid clicks
            self._click_in_progress = True
            
            # Schedule the actual form opening to avoid blocking
            def open_form():
                try:
                    self.on_form_clicked(form_name)
                except Exception as e:
                    print(f"Error opening form: {e}")
                finally:
                    # Reset flag after a delay
                    self.winfo_toplevel().after(300, lambda: setattr(self, '_click_in_progress', False))
            
            # Use after_idle to ensure it runs after current event processing
            self.winfo_toplevel().after_idle(open_form)
            
        except (tk.TclError, AttributeError, IndexError) as e:
            # Reset flag on error
            self._click_in_progress = False
            print(f"Error in double-click handler: {e}")
    
    def add_form(self, form_name: str) -> None:
        if form_name not in self.forms:
            self.forms.append(form_name)
            self.refresh_list()
    
    def refresh_list(self) -> None:
        """Refresh the listbox with current forms."""
        self.listbox.delete(0, tk.END)
        for form_name in self.forms:
            self.listbox.insert(tk.END, form_name)


class IELTSApp:
    """Main application window."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("IELTS Answer Form")
        self.root.minsize(600, 500)
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

        self.back_button = ttk.Button(header_frame, text="← Back", style="TButton", command=self.on_back_clicked)
        self.back_button.pack(side="left", padx=(0, 10))
        self.back_button.state(["disabled"])

        title_label = ttk.Label(header_frame, text="IELTS Answer Form", style="Title.TLabel")
        title_label.pack(side="left")

        # Stack frame for different views
        self.stack_frame = ttk.Frame(main_frame)
        self.stack_frame.pack(fill="both", expand=True)

        # Landing page
        self.landing_frame = ttk.Frame(self.stack_frame)
        landing_content = ttk.Frame(self.landing_frame)
        landing_content.pack(expand=True)

        heading = ttk.Label(landing_content, text="Choose a test to start filling in answers.", style="Heading.TLabel")
        heading.pack(pady=10)

        subtext = ttk.Label(
            landing_content,
            text="You can work on Listening or Reading separately.\nPick one below to load its answer sheet.",
            justify="center",
            style="Subtitle.TLabel"
        )
        subtext.pack(pady=5)

        button_frame = ttk.Frame(landing_content)
        button_frame.pack(pady=20)

        listening_button = tk.Button(
            button_frame,
            text="Listening",
            bg="#27ae60",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            width=18,
            height=4,
            relief="flat",
            bd=0,
            cursor="hand2",
            activebackground="#229954",
            activeforeground="white",
            command=lambda: self.switch_to_section("listening")
        )
        listening_button.pack(side="left", padx=15, pady=10)

        reading_button = tk.Button(
            button_frame,
            text="Reading",
            bg="#e74c3c",
            fg="white",
            font=("Segoe UI", 16, "bold"),
            width=18,
            height=4,
            relief="flat",
            bd=0,
            cursor="hand2",
            activebackground="#c0392b",
            activeforeground="white",
            command=lambda: self.switch_to_section("reading")
        )
        reading_button.pack(side="left", padx=15, pady=10)

        # Form list frames
        self.listening_list = FormListFrame(self.stack_frame, "Listening", self.on_form_clicked,
                                           get_form_state=lambda key: self.form_states.get(key),
                                           save_callback=self.save_database,
                                           delete_callback=lambda name: self.delete_form_state("listening", name))
        self.reading_list = FormListFrame(self.stack_frame, "Reading", self.on_form_clicked,
                                         get_form_state=lambda key: self.form_states.get(key),
                                         save_callback=self.save_database,
                                         delete_callback=lambda name: self.delete_form_state("reading", name))

        # Show landing page initially
        self.landing_frame.pack(fill="both", expand=True)

        self.current_section = None
        self.open_windows: Dict[str, FormWindow] = {}
        # Store form states (persists across window open/close)
        self.form_states: Dict[str, Dict] = {}
        
        # Save database when app closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)
        
        # Load saved data from JSON database (after form lists are created)
        self.load_database()
        
        # Auto-size window
        self.root.update_idletasks()
        width = max(self.root.winfo_reqwidth() + 20, 600)
        height = max(self.root.winfo_reqheight() + 20, 500)
        self.root.geometry(f"{width}x{height}")

    def switch_to_section(self, target: str) -> None:
        if target not in {"listening", "reading"}:
            return
        self.current_section = target

        # Hide all frames
        self.landing_frame.pack_forget()
        self.listening_list.pack_forget()
        self.reading_list.pack_forget()

        # Show selected section list
        if target == "listening":
            self.listening_list.pack(fill="both", expand=True)
            self.listening_list.refresh_list()  # Refresh to show updated status
        else:
            self.reading_list.pack(fill="both", expand=True)
            self.reading_list.refresh_list()  # Refresh to show updated status

        self.root.title(f"IELTS Answer Form · {target.capitalize()}")
        self.back_button.state(["!disabled"])
        
        # Auto-resize window
        self.root.update_idletasks()
        width = max(self.root.winfo_reqwidth() + 20, 600)
        height = max(self.root.winfo_reqheight() + 20, 500)
        self.root.geometry(f"{width}x{height}")

    def on_back_clicked(self) -> None:
        self.current_section = None
        self.landing_frame.pack(fill="both", expand=True)
        self.listening_list.pack_forget()
        self.reading_list.pack_forget()
        self.root.title("IELTS Answer Form")
        self.back_button.state(["disabled"])
        
        # Auto-resize window
        self.root.update_idletasks()
        width = max(self.root.winfo_reqwidth() + 20, 600)
        height = max(self.root.winfo_reqheight() + 20, 500)
        self.root.geometry(f"{width}x{height}")

    def load_database(self) -> None:
        """Load form states and form lists from JSON database."""
        try:
            if FORMS_DB_FILE.exists():
                with open(FORMS_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Load form states
                self.form_states = data.get("form_states", {})
                
                # Load form lists
                listening_forms = data.get("listening_forms", [])
                reading_forms = data.get("reading_forms", [])
                
                # Restore form lists
                for form_name in listening_forms:
                    if form_name not in self.listening_list.forms:
                        self.listening_list.add_form(form_name)
                
                for form_name in reading_forms:
                    if form_name not in self.reading_list.forms:
                        self.reading_list.add_form(form_name)
        except (json.JSONDecodeError, IOError, Exception) as e:
            # If file is corrupted or doesn't exist, start fresh
            print(f"Warning: Could not load database: {e}")
            self.form_states = {}
    
    def save_database(self) -> None:
        """Save form states and form lists to JSON database."""
        try:
            # Save all open windows' states before saving
            for form_key, form_window in list(self.open_windows.items()):
                try:
                    self.form_states[form_key] = form_window.save_state()
                except (tk.TclError, AttributeError):
                    pass  # Window was destroyed
            
            data = {
                "form_states": self.form_states,
                "listening_forms": self.listening_list.forms,
                "reading_forms": self.reading_list.forms
            }
            
            # Write to temporary file first, then rename (atomic write)
            temp_file = FORMS_DB_FILE.with_suffix(".json.tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic replace (cross-platform, Python 3.3+)
            os.replace(str(temp_file), str(FORMS_DB_FILE))
        except (IOError, Exception) as e:
            print(f"Warning: Could not save database: {e}")
    
    def delete_form_state(self, section: str, form_name: str) -> None:
        """Delete form state from database."""
        form_key = f"{section}:{form_name}"
        
        # Remove from form_states
        if form_key in self.form_states:
            del self.form_states[form_key]
        
        # Close window if it's open
        if form_key in self.open_windows:
            try:
                self.open_windows[form_key].window.destroy()
            except (tk.TclError, AttributeError):
                pass
            del self.open_windows[form_key]
    
    def on_app_close(self) -> None:
        """Handle app close - save database before exiting."""
        self.save_database()
        self.root.destroy()

    def on_form_clicked(self, form_name: str) -> None:
        """Open or focus a form window."""
        if not self.current_section:
            return
        
        # Create unique key for this form
        form_key = f"{self.current_section}:{form_name}"
        
        # If window already exists, focus it
        if form_key in self.open_windows:
            try:
                window = self.open_windows[form_key].window
                # Check if window still exists
                if window.winfo_exists():
                    window.lift()
                    window.focus()
                    return
                else:
                    # Window was destroyed, remove from dict
                    del self.open_windows[form_key]
            except (tk.TclError, AttributeError):
                # Window was closed, remove from dict
                if form_key in self.open_windows:
                    del self.open_windows[form_key]
        
        # Create groups based on section and set appropriate window sizes
        if self.current_section == "listening":
            groups = [
                (f"Listening Part {idx} (Q{(idx - 1) * 10 + 1}-{idx * 10})", 10)
                for idx in range(1, 5)
            ]
            section_name = "Listening"
            # Listening has 4 columns, needs wider window
            default_width = 1200
            default_height = 700
            min_width = 1000
            min_height = 600
        else:
            groups = [
                ("Reading Passage 1 (Q1-13)", 13),
                ("Reading Passage 2 (Q14-26)", 13),
                ("Reading Passage 3 (Q27-40)", 14),
            ]
            section_name = "Reading"
            # Reading has 3 columns, can be narrower
            default_width = 1000
            default_height = 700
            min_width = 900
            min_height = 600
        
        # Create new form window with section-specific sizes
        try:
            form_window = FormWindow(
                self.root, 
                form_name, 
                section_name, 
                groups,
                default_width=default_width,
                default_height=default_height,
                min_width=min_width,
                min_height=min_height
            )
            self.open_windows[form_key] = form_window
            
            # Load saved state if exists
            if form_key in self.form_states:
                try:
                    form_window.load_state(self.form_states[form_key])
                except Exception as e:
                    print(f"Warning: Could not load state for {form_name}: {e}")
            
            # Clean up when window closes
            def on_close():
                try:
                    # Save state before closing
                    if form_key in self.open_windows:
                        try:
                            self.form_states[form_key] = form_window.save_state()
                        except Exception:
                            pass  # Ignore save errors on close
                        del self.open_windows[form_key]
                        # Refresh the form list to update status
                        if self.current_section == "listening":
                            self.listening_list.refresh_list()
                        elif self.current_section == "reading":
                            self.reading_list.refresh_list()
                        # Save to database
                        self.save_database()
                    try:
                        form_window.window.destroy()
                    except (tk.TclError, AttributeError):
                        pass  # Window already destroyed
                except Exception as e:
                    print(f"Error in window close handler: {e}")
            
            form_window.window.protocol("WM_DELETE_WINDOW", on_close)
        except Exception as e:
            print(f"Error creating form window: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Could not open form '{form_name}': {e}")


def setup_modern_theme(root: tk.Tk) -> None:
    """Apply modern theme styling to the application."""
    style = ttk.Style()
    
    # Try to use a modern theme, fallback to default
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    
    # Modern color palette
    bg_color = "#f5f5f5"
    fg_color = "#2c3e50"
    accent_green = "#27ae60"
    accent_red = "#e74c3c"
    accent_blue = "#3498db"
    border_color = "#bdc3c7"
    hover_green = "#229954"
    hover_red = "#c0392b"
    
    # Configure root background
    root.configure(bg=bg_color)
    
    # Configure Frame styles
    style.configure("TFrame", background=bg_color)
    style.configure("Card.TFrame", background="white", relief="flat")
    
    # Configure Label styles
    style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
    style.configure("Title.TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 16, "bold"))
    style.configure("Heading.TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 12, "bold"))
    style.configure("Subtitle.TLabel", background=bg_color, foreground="#7f8c8d", font=("Segoe UI", 9))
    
    # Configure Button styles
    style.configure("TButton", 
                    font=("Segoe UI", 10),
                    padding=8,
                    relief="flat",
                    borderwidth=0,
                    focuscolor="none")
    style.map("TButton",
              background=[("active", "#ecf0f1"), ("!active", "white")],
              foreground=[("active", fg_color), ("!active", fg_color)])
    
    # Custom button styles
    style.configure("Primary.TButton",
                    background=accent_blue,
                    foreground="white",
                    font=("Segoe UI", 10, "bold"),
                    padding=10)
    style.map("Primary.TButton",
              background=[("active", "#2980b9"), ("!active", accent_blue)])
    
    style.configure("Success.TButton",
                    background=accent_green,
                    foreground="white",
                    font=("Segoe UI", 10, "bold"),
                    padding=10)
    style.map("Success.TButton",
              background=[("active", hover_green), ("!active", accent_green)])
    
    style.configure("Danger.TButton",
                    background=accent_red,
                    foreground="white",
                    font=("Segoe UI", 10, "bold"),
                    padding=10)
    style.map("Danger.TButton",
              background=[("active", hover_red), ("!active", accent_red)])
    
    # Configure Entry styles
    style.configure("TEntry",
                    fieldbackground="white",
                    foreground=fg_color,
                    borderwidth=1,
                    relief="solid",
                    padding=5,
                    font=("Segoe UI", 10))
    style.map("TEntry",
              bordercolor=[("focus", accent_blue), ("!focus", border_color)])
    
    # Configure Listbox style (custom styling for listbox)
    style.configure("TListbox",
                    background="white",
                    foreground=fg_color,
                    selectbackground=accent_blue,
                    selectforeground="white",
                    font=("Segoe UI", 11),
                    borderwidth=1,
                    relief="solid")
    
    # Configure Scrollbar style
    style.configure("TScrollbar",
                    background=bg_color,
                    troughcolor=bg_color,
                    borderwidth=0,
                    arrowcolor=fg_color,
                    darkcolor=bg_color,
                    lightcolor=bg_color)
    style.map("TScrollbar",
              background=[("active", "#d5dbdb"), ("!active", bg_color)])


def main() -> None:
    root = tk.Tk()
    setup_modern_theme(root)
    app = IELTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

