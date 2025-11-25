#!/usr/bin/env python3
"""IELTS Answer Form implemented with PyGObject (GTK 3)."""

import os
import re
from typing import Dict, List, Sequence, Tuple

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, Gtk  # noqa: E402

NUM_QUESTIONS = 40
APP_ID = "com.example.IELTSAnswerForm"
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


def load_css() -> None:
    screen = Gdk.Screen.get_default()
    if not screen:
        return
    css = b"""
    .landing-button {
        font-weight: bold;
        font-size: 16px;
        padding: 30px 40px;
        border-radius: 12px;
        color: #ffffff;
    }
    .landing-button.listening {
        background: #27ae60;
    }
    .landing-button.reading {
        background: #c0392b;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


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


class SectionBox(Gtk.ScrolledWindow):
    """Scrollable list of question entry rows."""

    def __init__(self, section_name: str, groups: Sequence[GroupSpec]):
        super().__init__()
        self.section_name = section_name
        self.groups: List[GroupSpec] = list(groups)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_hexpand(True)
        self.set_vexpand(True)

        viewport = Gtk.Viewport()
        self.add(viewport)

        self.section_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
        self.section_box.set_margin_top(12)
        self.section_box.set_margin_bottom(12)
        self.section_box.set_margin_start(12)
        self.section_box.set_margin_end(12)
        viewport.add(self.section_box)

        self.user_entries: List[Gtk.Entry] = []
        self.key_entries: List[Gtk.Entry] = []
        self.status_labels: List[Gtk.Label] = []
        self.keys_visible = True
        self._build_groups()

    def _build_groups(self) -> None:
        for child in self.section_box.get_children():
            self.section_box.remove(child)
        self.user_entries.clear()
        self.key_entries.clear()
        self.status_labels.clear()

        grid = Gtk.Grid()
        grid.set_column_spacing(24)
        grid.set_row_spacing(6)
        self.section_box.pack_start(grid, False, False, 0)

        question_number = 1
        for col_index, (title, count) in enumerate(self.groups):
            header = Gtk.Label(label=title, xalign=0)
            header.set_markup(f"<b>{title}</b>")
            grid.attach(header, col_index, 0, 1, 1)

            start_number = question_number
            for row in range(int(count)):
                q_num = start_number + row
                cell = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 4)
                number_label = Gtk.Label(label=f"{q_num}.", xalign=1)
                number_label.set_width_chars(3)

                user_entry = Gtk.Entry()
                user_entry.set_width_chars(8)
                user_entry.set_max_length(32)

                key_entry = Gtk.Entry()
                key_entry.set_width_chars(8)
                key_entry.set_max_length(32)
                key_entry.set_placeholder_text("Answer")
                key_entry.set_visibility(True)
                key_entry.set_invisible_char("•")

                status_label = Gtk.Label(label="", xalign=0)

                cell.pack_start(number_label, False, False, 0)
                cell.pack_start(user_entry, False, False, 4)
                cell.pack_start(key_entry, False, False, 4)
                cell.pack_start(status_label, False, False, 4)
                grid.attach(cell, col_index, row + 1, 1, 1)

                self.user_entries.append(user_entry)
                self.key_entries.append(key_entry)
                self.status_labels.append(status_label)
            question_number += int(count)

    def set_groups(self, groups: Sequence[GroupSpec]) -> None:
        self.groups = list(groups)
        self._build_groups()

    def get_answers(self) -> List[str]:
        return [entry.get_text().strip() for entry in self.user_entries]

    def get_answer_keys(self) -> List[str]:
        return [entry.get_text().strip() for entry in self.key_entries]

    def clear(self) -> None:
        for entry in self.user_entries:
            entry.set_text("")
        for label in self.status_labels:
            label.set_text("")

    def clear_keys(self) -> None:
        for entry in self.key_entries:
            entry.set_text("")

    def evaluate(self) -> Tuple[int, int]:
        correct = 0
        evaluated = 0
        for user_entry, key_entry, status_label in zip(
            self.user_entries, self.key_entries, self.status_labels
        ):
            key_raw = key_entry.get_text().strip()
            if not key_raw:
                status_label.set_text("")
                continue
            evaluated += 1
            user_raw = user_entry.get_text().strip()
            is_correct = normalize_answer(user_raw) == normalize_answer(key_raw)
            symbol = "✓" if is_correct else "✗"
            color = "green" if is_correct else "red"
            status_label.set_markup(f'<span foreground="{color}" weight="bold">{symbol}</span>')
            if is_correct:
                correct += 1
        return correct, evaluated

    def reset_feedback(self) -> None:
        for label in self.status_labels:
            label.set_text("")

    def question_count(self) -> int:
        return len(self.user_entries)

    def set_keys_visible(self, visible: bool) -> None:
        self.keys_visible = visible
        for entry in self.key_entries:
            entry.set_visibility(visible)

    def apply_answer_keys(self, mapping: Dict[int, str]) -> None:
        for idx, entry in enumerate(self.key_entries, start=1):
            value = mapping.get(idx)
            if value:
                entry.set_text(value)



class IELTSWindow(Gtk.ApplicationWindow):
    """Main window hosting the two sections and control buttons."""

    def __init__(self, app: Gtk.Application):
        super().__init__(application=app, title="IELTS Answer Form")
        load_css()
        self.set_default_size(520, 650)
        if os.path.exists(ICON_PATH):
            self.set_icon_from_file(ICON_PATH)

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
        for setter in (
            main_box.set_margin_top,
            main_box.set_margin_bottom,
            main_box.set_margin_start,
            main_box.set_margin_end,
        ):
            setter(12)
        self.add(main_box)

        header_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        header_box.set_hexpand(True)
        main_box.pack_start(header_box, False, False, 0)

        self.back_button = Gtk.Button()
        back_image = Gtk.Image.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON)
        self.back_button.set_image(back_image)
        self.back_button.set_relief(Gtk.ReliefStyle.NONE)
        self.back_button.set_tooltip_text("Back to test selection")
        self.back_button.connect("clicked", self.on_change_test_clicked)
        header_box.pack_start(self.back_button, False, False, 0)

        header_label = Gtk.Label(
            label="<b>IELTS Answer Form</b>",
            xalign=0,
        )
        header_label.set_use_markup(True)
        header_box.pack_start(header_label, True, True, 0)

        self.stack = Gtk.Stack.new()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)

        landing_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
        for setter in (
            landing_box.set_margin_top,
            landing_box.set_margin_bottom,
            landing_box.set_margin_start,
            landing_box.set_margin_end,
        ):
            setter(24)
        landing_box.set_valign(Gtk.Align.CENTER)
        landing_box.set_halign(Gtk.Align.CENTER)

        heading = Gtk.Label(label="Choose a test to start filling in answers.")
        heading.set_use_markup(True)
        heading.set_markup("<b>Choose a test to start filling in answers.</b>")
        heading.set_halign(Gtk.Align.CENTER)

        subtext = Gtk.Label(
            label="You can work on Listening or Reading separately. "
            "Pick one below to load its answer sheet.",
        )
        subtext.set_halign(Gtk.Align.CENTER)
        subtext.set_line_wrap(True)
        landing_box.pack_start(heading, False, False, 0)
        landing_box.pack_start(subtext, False, False, 0)

        button_row = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 24)
        button_row.set_halign(Gtk.Align.CENTER)
        landing_box.pack_start(button_row, False, False, 12)

        listening_button = Gtk.Button(label="Listening")
        listening_button.get_style_context().add_class("landing-button")
        listening_button.get_style_context().add_class("listening")
        listening_button.set_size_request(180, 140)
        listening_button.connect("clicked", lambda *_: self.switch_to_section("listening"))
        button_row.pack_start(listening_button, False, False, 0)

        reading_button = Gtk.Button(label="Reading")
        reading_button.get_style_context().add_class("landing-button")
        reading_button.get_style_context().add_class("reading")
        reading_button.set_size_request(180, 140)
        reading_button.connect("clicked", lambda *_: self.switch_to_section("reading"))
        button_row.pack_start(reading_button, False, False, 0)

        listening_groups = [
            (f"Listening Part {idx} (Q{(idx - 1) * 10 + 1}-{idx * 10})", 10)
            for idx in range(1, 5)
        ]
        self.listening_box = SectionBox("Listening", listening_groups)
        reading_groups = [
            ("Reading Passage 1 (Q1-13)", 13),
            ("Reading Passage 2 (Q14-26)", 13),
            ("Reading Passage 3 (Q27-40)", 14),
        ]
        self.reading_box = SectionBox("Reading", reading_groups)

        self.stack.add_named(landing_box, "landing")
        self.stack.add_named(self.listening_box, "listening")
        self.stack.add_named(self.reading_box, "reading")
        self.stack.set_visible_child_name("landing")
        self.back_button.set_sensitive(False)

        main_box.pack_start(self.stack, True, True, 0)

        self.score_label = Gtk.Label(label="")
        self.score_label.set_halign(Gtk.Align.END)
        self.score_label.set_xalign(1.0)
        main_box.pack_start(self.score_label, False, False, 0)

        self.answers_hidden = False

        button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        main_box.pack_start(button_box, False, False, 0)

        submit_button = Gtk.Button(label="Submit")
        submit_button.connect("clicked", self.on_submit_clicked)
        button_box.pack_start(submit_button, False, False, 0)

        paste_button = Gtk.Button(label="Paste Right Answer")
        paste_button.connect("clicked", self.on_paste_answers_clicked)
        button_box.pack_start(paste_button, False, False, 0)

        self.hide_button = Gtk.Button(label="Hide Answers")
        self.hide_button.connect("clicked", self.on_toggle_hide_answers)
        button_box.pack_start(self.hide_button, False, False, 0)

        preview_button = Gtk.Button(label="Preview")
        preview_button.connect("clicked", self.on_preview_clicked)
        button_box.pack_start(preview_button, False, False, 0)

        clear_button = Gtk.Button(label="Clear All")
        clear_button.connect("clicked", self.on_clear_clicked)
        button_box.pack_start(clear_button, False, False, 0)

        save_button = Gtk.Button(label="Save Answers")
        save_button.connect("clicked", self.on_save_clicked)
        button_box.pack_start(save_button, False, False, 0)

        self.apply_key_visibility()

    def get_active_section(self) -> Tuple[str, SectionBox] | None:
        visible = self.stack.get_visible_child_name()
        if visible == "listening":
            return "Listening", self.listening_box
        if visible == "reading":
            return "Reading", self.reading_box
        return None

    def require_active_section(self) -> Tuple[str, SectionBox] | None:
        active = self.get_active_section()
        if active:
            return active
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Select a test first",
        )
        dialog.format_secondary_text(
            "Choose Listening or Reading on the start screen before entering answers."
        )
        dialog.run()
        dialog.destroy()
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
        self.stack.set_visible_child_name(target)
        self.set_title(f"IELTS Answer Form · {target.capitalize()}")
        self.back_button.set_sensitive(True)
        self.apply_key_visibility()
        self.update_score_label("")

    def on_change_test_clicked(self, _button: Gtk.Button) -> None:
        self.stack.set_visible_child_name("landing")
        self.set_title("IELTS Answer Form")
        self.back_button.set_sensitive(False)
        self.apply_key_visibility()
        self.update_score_label("")

    def on_clear_clicked(self, _button: Gtk.Button) -> None:
        active = self.require_active_section()
        if not active:
            return
        _, section_box = active
        section_box.clear()
        self.update_score_label("")

    def on_paste_answers_clicked(self, _button: Gtk.Button) -> None:
        active = self.require_active_section()
        if not active:
            return
        section_name, section_box = active

        dialog = Gtk.Dialog(
            title="Paste Right Answer",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
        )
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Apply", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        content.set_spacing(6)

        info_label = Gtk.Label(
            label="Paste the official answers below. "
            "Lines like '21&22   A, E' will be split automatically.",
            xalign=0,
        )
        info_label.set_line_wrap(True)
        content.pack_start(info_label, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_min_content_height(200)
        text_view = Gtk.TextView()
        scroller.add(text_view)
        content.pack_start(scroller, True, True, 0)

        dialog.show_all()
        response = dialog.run()
        text = ""
        if response == Gtk.ResponseType.OK:
            buffer = text_view.get_buffer()
            start, end = buffer.get_start_iter(), buffer.get_end_iter()
            text = buffer.get_text(start, end, True)
        dialog.destroy()

        if not text.strip():
            return

        mapping = parse_answer_text(text)
        if not mapping:
            self.show_message("No answers detected", "Make sure the text includes numbered lines.")
            return

        section_box.apply_answer_keys(mapping)
        section_box.reset_feedback()
        self.update_score_label("")

    def on_toggle_hide_answers(self, _button: Gtk.Button) -> None:
        self.answers_hidden = not self.answers_hidden
        self.apply_key_visibility()

    def on_submit_clicked(self, _button: Gtk.Button) -> None:
        active = self.require_active_section()
        if not active:
            return
        section_name, section_box = active
        missing_keys = [
            idx + 1 for idx, value in enumerate(section_box.get_answer_keys()) if not value
        ]
        if missing_keys:
            self.show_message(
                "Add answer keys",
                "Please fill the correct-answer boxes before submitting so we can compare.",
            )
            return
        correct, _evaluated = section_box.evaluate()
        total = section_box.question_count()
        band = lookup_band(section_name, correct)
        self.update_score_label(
            f"{section_name}: {correct}/{total} correct · Band {band:.1f}"
        )

    def on_preview_clicked(self, _button: Gtk.Button) -> None:
        result = self.collect_active_answers()
        if not result:
            return
        section_name, answers = result
        preview_lines = [section_name]
        preview_lines.extend(
            [f"  Q{idx:02d}: {answer}" for idx, answer in enumerate(answers, start=1)]
        )
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Preview Answers",
        )
        dialog.format_secondary_text("\n".join(preview_lines))
        dialog.run()
        dialog.destroy()

    def show_message(self, title: str, body: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(body)
        dialog.run()
        dialog.destroy()

    def update_score_label(self, text: str) -> None:
        self.score_label.set_text(text)

    def apply_key_visibility(self) -> None:
        visible = not getattr(self, "answers_hidden", False)
        if hasattr(self, "hide_button"):
            self.hide_button.set_label("Show Answers" if not visible else "Hide Answers")
        if hasattr(self, "listening_box"):
            self.listening_box.set_keys_visible(visible)
        if hasattr(self, "reading_box"):
            self.reading_box.set_keys_visible(visible)

    def on_save_clicked(self, _button: Gtk.Button) -> None:
        result = self.collect_active_answers()
        if not result:
            return
        section_name, answers = result
        dialog = Gtk.FileChooserNative.new(
            "Save IELTS Answers",
            self,
            Gtk.FileChooserAction.SAVE,
            None,
            None,
        )
        default_name = f"ielts_{section_name.lower()}_answers.txt"
        dialog.set_current_name(default_name)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_filename()
            if file_path:
                with open(file_path, "w", encoding="utf-8") as handle:
                    handle.write(f"{section_name}\n")
                    for idx, answer in enumerate(answers, start=1):
                        handle.write(f"{idx},{answer}\n")
        dialog.destroy()
        dialog.destroy()


class IELTSApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            window = IELTSWindow(self)
        window.show_all()
        window.present()


def main() -> None:
    app = IELTSApp()
    app.run()


if __name__ == "__main__":
    main()

