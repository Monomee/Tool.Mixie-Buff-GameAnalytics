"""Desktop configuration and execution for Tool.py. Run: python ToolDesktop.py."""
import concurrent.futures
from dataclasses import dataclass
import json
import math
from pathlib import Path
import queue
import random
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import uuid

from Tool import (BASE_DIR, GAME_KEY, SECRET_KEY, LIVE_EVENTS_FILE, MAX_TOTAL_USERS,
                  ScalableAndroidTrafficGenerator)


ENGLISH = {
    'Ngôn ngữ': 'Language',
    'Cấu hình user và phiên mô phỏng gửi đến GameAnalytics.': 'Configure users and simulated sessions sent to GameAnalytics.',
    'User & phiên chơi': 'Users & sessions',
    'Chế độ user': 'User mode',
    'Tạo user mới': 'Create new users',
    'Chạy lại user đã lưu': 'Returning saved users',
    'Returning từ JSON': 'Returning from JSON',
    'Kết hợp mới / returning': 'Mixed new / returning',
    'Số user': 'Users',
    'Phiên / user': 'Sessions / user',
    'User đồng thời': 'Concurrent users',
    'Returning (%) khi kết hợp': 'Returning (%) in mixed mode',
    'Nghỉ giữa phiên (giây)': 'Pause between sessions (sec)',
    'Thời lượng tối thiểu (phút)': 'Minimum duration (min)',
    'Thời lượng tối đa (phút)': 'Maximum duration (min)',
    'Gửi sự kiện sớm nhất (giây)': 'Minimum event interval (sec)',
    'Gửi sự kiện muộn nhất (giây)': 'Maximum event interval (sec)',
    'JSON GameAnalytics': 'GameAnalytics JSON',
    'Chọn file…': 'Browse…',
    'Chế độ JSON chỉ chọn ID có trong file; chế độ kết hợp gộp JSON với user đã lưu.': 'JSON mode uses IDs from the file; mixed mode combines JSON with saved users.',
    'Project nhận dữ liệu': 'Destination project',
    'Chạy thử — không gửi mạng, không ghi trạng thái user': 'Dry run — no network requests or user state changes',
    'Bỏ chọn chạy thử sẽ gửi dữ liệu thật. Returning giữ ID và tăng số phiên; retention phụ thuộc ngày quay lại.': 'Disable dry run to send real data. Returning users keep their IDs and increment sessions; retention depends on the return date.',
    'Bắt đầu': 'Start',
    'Dừng': 'Stop',
    'Sẵn sàng • Giới hạn pool: {limit} user': 'Ready • Pool limit: {limit} users',
    'Cấu hình không hợp lệ': 'Invalid configuration',
    'Đang chạy thử…': 'Dry run in progress…',
    'Đang gửi dữ liệu thật…': 'Sending real data…',
    'CHẠY THỬ': 'DRY RUN',
    'GỬI THẬT': 'LIVE RUN',
    'Đang dừng và đóng phiên hiện tại…': 'Stopping and closing the current session…',
    'Xong {done} phiên • Lỗi {failed}': 'Completed {done} sessions • Failed {failed}',
    'Không chạy được': 'Unable to run',
    '[LỖI] ': '[ERROR] ',
    'Đã dừng': 'Stopped',
    'Hoàn tất đợt chạy': 'Run complete',
    '{label} • {completed} phiên xong • {failed} lỗi': '{label} • {completed} sessions completed • {failed} failed',
    'Chế độ user không hợp lệ.': 'Invalid user mode.',
    '{name} phải là số nguyên lớn hơn 0.': '{name} must be an integer greater than 0.',
    'Tối đa {limit} user / luồng.': 'Maximum {limit} users / workers.',
    '{name} phải là số hữu hạn.': '{name} must be a finite number.',
    'Thời lượng phải lớn hơn 0, tối thiểu ≤ tối đa.': 'Duration must be greater than 0, minimum ≤ maximum.',
    'Khoảng gửi sự kiện phải lớn hơn 0, tối thiểu ≤ tối đa.': 'Event intervals must be greater than 0, minimum ≤ maximum.',
    'Thời gian nghỉ ≥ 0 và returning nằm trong 0–100%.': 'Pause must be ≥ 0 and returning must be between 0 and 100%.',
    'Hãy chọn file JSON từ GameAnalytics.': 'Select a GameAnalytics JSON file.',
    'Thiếu Game Key hoặc Secret Key.': 'Missing Game Key or Secret Key.',
    '[THỬ] /{endpoint} — {category}': '[DRY RUN] /{endpoint} — {category}',
    'File trạng thái lỗi ở dòng {number}: {error}': 'Invalid state file at line {number}: {error}',
    'JSON phải là danh sách sự kiện GameAnalytics.': 'JSON must be a list of GameAnalytics events.',
    'Sự kiện JSON #{number} không phải object.': 'JSON event #{number} must be an object.',
    'user_id không hợp lệ ở sự kiện #{number}.': 'Invalid user_id in event #{number}.',
    'Cần {returning} returning user nhưng chỉ có {available}. Hãy giảm số lượng hoặc nhập thêm JSON.': 'Need {returning} returning users but only {available} are available. Reduce the count or import more JSON.',
    'Pool có {count} user; thêm {new_count} sẽ vượt {limit}. Hãy chọn chạy lại user đã có.': 'The pool has {count} users; adding {new_count} would exceed {limit}. Select existing users instead.',
    '[KẾ HOẠCH] {new_count} mới + {returning} returning; {sessions} phiên; {workers} luồng.': '[PLAN] {new_count} new + {returning} returning; {sessions} sessions; {workers} workers.',
    '{field} phải là số nguyên không âm.': '{field} must be a non-negative integer.',
    'client_ts / last_active không hợp lệ.': 'Invalid client_ts / last_active.',
    '{field} không hợp lệ.': 'Invalid {field}.',
    'Không khởi tạo được phiên.': 'Unable to initialize the session.',
    '[LỖI] User {user}: {error}; dừng user này.': '[ERROR] User {user}: {error}; stopping this user.',
    'Giá trị số không hợp lệ: {name}.': 'Invalid numeric value: {name}.',
}


def tr(text, language='vi', **values):
    return (ENGLISH.get(text, text) if language == 'en' else text).format(**values)


@dataclass
class RunConfig:
    mode: str = 'new'
    users: int = 1
    sessions: int = 1
    workers: int = 1
    returning_percent: float = 60
    duration_min: float = 6
    duration_max: float = 10
    action_min: float = 30
    action_max: float = 75
    pause_seconds: float = 0
    json_path: str = ''
    dry_run: bool = True
    game_key: str = GAME_KEY
    secret_key: str = SECRET_KEY
    language: str = 'vi'

    def validate(self):
        if self.mode not in ('new', 'saved', 'json', 'mixed'):
            raise ValueError(tr('Chế độ user không hợp lệ.', self.language))
        for name in ('users', 'sessions', 'workers'):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 1:
                raise ValueError(tr('{name} phải là số nguyên lớn hơn 0.', self.language, name=name))
        if self.users > MAX_TOTAL_USERS or self.workers > MAX_TOTAL_USERS:
            raise ValueError(tr('Tối đa {limit} user / luồng.', self.language, limit=MAX_TOTAL_USERS))
        for name in ('duration_min', 'duration_max', 'action_min', 'action_max',
                     'pause_seconds', 'returning_percent'):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(tr('{name} phải là số hữu hạn.', self.language, name=name))
        if not 0 < self.duration_min <= self.duration_max:
            raise ValueError(tr('Thời lượng phải lớn hơn 0, tối thiểu ≤ tối đa.', self.language))
        if not 0 < self.action_min <= self.action_max:
            raise ValueError(tr('Khoảng gửi sự kiện phải lớn hơn 0, tối thiểu ≤ tối đa.', self.language))
        if self.pause_seconds < 0 or not 0 <= self.returning_percent <= 100:
            raise ValueError(tr('Thời gian nghỉ ≥ 0 và returning nằm trong 0–100%.', self.language))
        if self.mode == 'json' and not self.json_path:
            raise ValueError(tr('Hãy chọn file JSON từ GameAnalytics.', self.language))
        if not self.dry_run and (not self.game_key.strip() or not self.secret_key.strip()):
            raise ValueError(tr('Thiếu Game Key hoặc Secret Key.', self.language))


class DesktopRunner:
    def __init__(self, config, state_path=None, log=None, progress=None, stop=None):
        config.validate()
        self.config = config
        self.state_path = Path(state_path or Path(BASE_DIR) / 'android_retention_keys.txt')
        self.log = log or (lambda message: None)
        self.progress = progress or (lambda completed, failed: None)
        self.stop = stop or threading.Event()
        self.generator = ScalableAndroidTrafficGenerator(config.game_key, config.secret_key)
        self.generator.stop_event = self.stop
        self.generator.duration_range = (config.duration_min, config.duration_max)
        self.generator.action_range = (config.action_min, config.action_max)
        self.generator.strict_session_end = True
        self.generator.log = self.log
        if config.dry_run:
            self.generator._send = lambda endpoint, payload: self.log(
                tr('[THỬ] /{endpoint} — {category}', config.language, endpoint=endpoint,
                   category=payload[0]["category"] if isinstance(payload, list) else 'init'))

    def prepare(self):
        roster = {}
        if self.state_path.exists():
            for number, line in enumerate(self.state_path.read_text(encoding='utf-8').splitlines(), 1):
                if not line.strip():
                    continue
                parts = line.split(',')
                try:
                    uid, session, last_active = parts[:3]
                    account = dict(user_id=uid, session_num=int(session), last_active=float(last_active),
                                   manufacturer=parts[3] if len(parts) > 3 else 'samsung',
                                   device=parts[4] if len(parts) > 4 else 'SM-G781N',
                                   os_version=parts[5] if len(parts) > 5 else 'android 13',
                                   lifetime_session_length=int(parts[6]) if len(parts) > 6 else 0,
                                   from_live_file=False)
                    self._validate_account(account)
                    roster[uid] = account
                except (ValueError, IndexError) as error:
                    raise ValueError(tr('File trạng thái lỗi ở dòng {number}: {error}',
                                        self.config.language, number=number, error=error)) from error

        imported = set()
        if self.config.mode in ('json', 'mixed') and self.config.json_path:
            events = json.loads(Path(self.config.json_path).read_text(encoding='utf-8-sig'))
            if not isinstance(events, list):
                raise ValueError(tr('JSON phải là danh sách sự kiện GameAnalytics.', self.config.language))
            for number, event in enumerate(events, 1):
                if not isinstance(event, dict):
                    raise ValueError(tr('Sự kiện JSON #{number} không phải object.', self.config.language, number=number))
                uid = event.get('user_id')
                if not uid:
                    continue
                if not isinstance(uid, str) or any(c in uid for c in ',\r\n'):
                    raise ValueError(tr('user_id không hợp lệ ở sự kiện #{number}.', self.config.language, number=number))
                account = dict(user_id=uid, session_num=event.get('session_num', 1),
                               last_active=event.get('client_ts', 0),
                               lifetime_session_length=event.get('lifetime_session_length', 0),
                               manufacturer=event.get('manufacturer', 'samsung'),
                               device=event.get('device', 'SM-G781N'),
                               os_version=event.get('os_version', 'android 13'), from_live_file=True)
                self._validate_account(account)
                if uid in roster:
                    for field in ('session_num', 'last_active', 'lifetime_session_length'):
                        account[field] = max(account[field], roster[uid][field])
                roster[uid] = account
                imported.add(uid)

        config = self.config
        candidates = [p for uid, p in roster.items()
                      if (config.mode != 'json' or uid in imported) and p['session_num'] > 0]
        returning = (config.users if config.mode in ('saved', 'json') else
                     round(config.users * config.returning_percent / 100) if config.mode == 'mixed' else 0)
        if len(candidates) < returning:
            raise ValueError(tr('Cần {returning} returning user nhưng chỉ có {available}. Hãy giảm số lượng hoặc nhập thêm JSON.',
                                config.language, returning=returning, available=len(candidates)))
        new_count = config.users - returning
        if len(roster) + new_count > MAX_TOTAL_USERS:
            raise ValueError(tr('Pool có {count} user; thêm {new_count} sẽ vượt {limit}. Hãy chọn chạy lại user đã có.',
                                config.language, count=len(roster), new_count=new_count, limit=MAX_TOTAL_USERS))
        active = random.sample(candidates, returning)
        for _ in range(new_count):
            profile = random.choice(self.generator.device_profiles)
            account = dict(user_id=str(uuid.uuid4()), session_num=0, last_active=time.time(),
                           **profile, os_version=random.choice(self.generator.os_versions),
                           lifetime_session_length=0, from_live_file=False)
            roster[account['user_id']] = account
            active.append(account)
        self.log(tr('[KẾ HOẠCH] {new_count} mới + {returning} returning; {sessions} phiên; {workers} luồng.',
                    config.language, new_count=new_count, returning=returning,
                    sessions=config.users * config.sessions, workers=min(config.users, config.workers)))
        return active, roster

    def _validate_account(self, account):
        for field in ('session_num', 'lifetime_session_length'):
            value = account[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(tr('{field} phải là số nguyên không âm.', self.config.language, field=field))
        timestamp = account['last_active']
        if not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or timestamp < 0:
            raise ValueError(tr('client_ts / last_active không hợp lệ.', self.config.language))
        for field in ('user_id', 'manufacturer', 'device', 'os_version'):
            value = account[field]
            if not isinstance(value, str) or not value or any(c in value for c in ',\r\n'):
                raise ValueError(tr('{field} không hợp lệ.', self.config.language, field=field))

    def _save(self, roster):
        # Replace atomically so an interrupted write cannot truncate the user pool.
        temp = self.state_path.with_suffix(self.state_path.suffix + '.tmp')
        fields = ('user_id', 'session_num', 'last_active', 'manufacturer', 'device',
                  'os_version', 'lifetime_session_length')
        temp.write_text(''.join(','.join(str(p[f]) for f in fields) + '\n'
                                for p in roster.values()), encoding='utf-8')
        temp.replace(self.state_path)

    def run(self):
        if self.stop.is_set():
            return dict(completed=0, failed=0)
        active, roster = self.prepare()
        completed = failed = 0
        lock = threading.Lock()

        def play(account):
            nonlocal completed, failed
            for index in range(self.config.sessions):
                if self.stop.is_set():
                    break
                try:
                    result = self.generator.simulate_dynamic_session(account)
                    if result['session_num'] != account['session_num'] + 1:
                        raise RuntimeError(tr('Không khởi tạo được phiên.', self.config.language))
                    with lock:
                        roster[result['user_id']] = result
                        if not self.config.dry_run:
                            self._save(roster)
                        completed += 1
                        self.progress(completed, failed)
                    account = result
                except Exception as error:
                    with lock:
                        failed += 1
                        self.progress(completed, failed)
                    self.log(tr('[LỖI] User {user}: {error}; dừng user này.', self.config.language,
                                user=account['user_id'][:8], error=error))
                    break
                if index + 1 < self.config.sessions and self.stop.wait(self.config.pause_seconds):
                    break

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.config.users, self.config.workers)) as pool:
            futures = [pool.submit(play, account) for account in active]
            for future in concurrent.futures.as_completed(futures):
                future.result()
        return dict(completed=completed, failed=failed)


MODE_LABELS = {'Tạo user mới': 'new', 'Chạy lại user đã lưu': 'saved',
               'Returning từ JSON': 'json', 'Kết hợp mới / returning': 'mixed'}


class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.closing = False
        self.messages = queue.Queue()
        self.stop = threading.Event()
        self.inputs = []
        self.lang = 'vi'
        root.title('GameAnalytics • Android Session Tool')
        root.geometry('980x860')
        root.minsize(820, 740)
        style = ttk.Style(root)
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        outer = ttk.Frame(root, padding=18)
        outer.pack(fill='both', expand=True)
        language_row = ttk.Frame(outer)
        language_row.pack(fill='x', pady=(0, 6))
        ttk.Label(language_row, text='Ngôn ngữ').pack(side='left', padx=(0, 8))
        self.language = tk.StringVar(value='Tiếng Việt')
        language_selector = ttk.Combobox(language_row, textvariable=self.language,
                                         values=('Tiếng Việt', 'English'), state='readonly', width=14)
        language_selector.pack(side='left')
        language_selector.bind('<<ComboboxSelected>>', self.change_language)
        self.inputs.append((language_selector, 'readonly'))
        ttk.Label(outer, text='Android Session Tool', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Cấu hình user và phiên mô phỏng gửi đến GameAnalytics.').pack(anchor='w', pady=(0, 10))
        form = ttk.LabelFrame(outer, text='User & phiên chơi', padding=12)
        form.pack(fill='x')
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        self.values = {}

        def field(label, key, default, row, column=0, options=None, secret=False):
            ttk.Label(form, text=label).grid(row=row, column=column, sticky='w', padx=4, pady=5)
            variable = tk.StringVar(value=str(default))
            self.values[key] = variable
            widget = (ttk.Combobox(form, textvariable=variable, values=options, state='readonly')
                      if options else ttk.Entry(form, textvariable=variable, show='•' if secret else ''))
            widget.grid(row=row, column=column + 1, sticky='ew', padx=4, pady=5)
            self.inputs.append((widget, 'readonly' if options else 'normal'))
            return widget

        self.mode_combo = field('Chế độ user', 'mode', 'Tạo user mới', 0, options=list(MODE_LABELS))
        field('Số user', 'users', 1, 0, 2)
        field('Phiên / user', 'sessions', 1, 1)
        field('User đồng thời', 'workers', 1, 1, 2)
        field('Returning (%) khi kết hợp', 'returning_percent', 60, 2)
        field('Nghỉ giữa phiên (giây)', 'pause_seconds', 0, 2, 2)
        field('Thời lượng tối thiểu (phút)', 'duration_min', 6, 3)
        field('Thời lượng tối đa (phút)', 'duration_max', 10, 3, 2)
        field('Gửi sự kiện sớm nhất (giây)', 'action_min', 30, 4)
        field('Gửi sự kiện muộn nhất (giây)', 'action_max', 75, 4, 2)
        file_row = ttk.Frame(outer)
        file_row.pack(fill='x', pady=10)
        ttk.Label(file_row, text='JSON GameAnalytics').pack(side='left', padx=(0, 8))
        local_json = Path(LIVE_EVENTS_FILE)
        self.json_path = tk.StringVar(value=str(local_json) if local_json.exists() else '')
        entry = ttk.Entry(file_row, textvariable=self.json_path)
        entry.pack(side='left', fill='x', expand=True)
        browse = ttk.Button(file_row, text='Chọn file…', command=self.browse)
        browse.pack(side='left', padx=(8, 0))
        self.inputs.extend([(entry, 'normal'), (browse, 'normal')])
        ttk.Label(outer, text='Chế độ JSON chỉ chọn ID có trong file; chế độ kết hợp gộp JSON với user đã lưu.').pack(anchor='w')
        credentials = ttk.LabelFrame(outer, text='Project nhận dữ liệu', padding=10)
        credentials.pack(fill='x', pady=10)
        credentials.columnconfigure(1, weight=1)
        self.game_key = tk.StringVar(value=GAME_KEY)
        self.secret_key = tk.StringVar(value=SECRET_KEY)
        for row, (label, variable) in enumerate((('Game Key', self.game_key), ('Secret Key', self.secret_key))):
            ttk.Label(credentials, text=label).grid(row=row, column=0, padx=5, pady=3)
            entry = ttk.Entry(credentials, textvariable=variable, show='•' if row else '')
            entry.grid(row=row, column=1, sticky='ew', pady=3)
            self.inputs.append((entry, 'normal'))
        self.dry_run = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(outer, text='Chạy thử — không gửi mạng, không ghi trạng thái user', variable=self.dry_run)
        check.pack(anchor='w')
        self.inputs.append((check, 'normal'))
        ttk.Label(outer, text='Bỏ chọn chạy thử sẽ gửi dữ liệu thật. Returning giữ ID và tăng số phiên; retention phụ thuộc ngày quay lại.',
                  wraplength=870).pack(anchor='w', pady=(4, 8))
        controls = ttk.Frame(outer)
        controls.pack(fill='x')
        self.start_button = ttk.Button(controls, text='Bắt đầu', command=self.start)
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(controls, text='Dừng', command=self.request_stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        self.status = tk.StringVar()
        self.set_status('Sẵn sàng • Giới hạn pool: {limit} user', limit=MAX_TOTAL_USERS)
        ttk.Label(controls, textvariable=self.status).pack(side='left', padx=8)
        self.bar = ttk.Progressbar(outer)
        self.bar.pack(fill='x', pady=8)
        self.log_box = ScrolledText(outer, height=10, state='disabled', font=('Consolas', 10))
        self.log_box.pack(fill='both', expand=True)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.after(100, self.poll)

    def set_status(self, text, **values):
        self.status_text = text
        self.status_values = values
        self.status.set(tr(text, self.lang, **values))

    def change_language(self, event=None):
        labels = {tr(label, self.lang): mode for label, mode in MODE_LABELS.items()}
        selected_mode = labels[self.values['mode'].get()]
        self.lang = 'en' if self.language.get() == 'English' else 'vi'
        originals = {translated: source for source, translated in ENGLISH.items()}

        def update_widgets(parent):
            for widget in parent.winfo_children():
                if 'text' in widget.keys():
                    text = widget.cget('text')
                    source = originals.get(text, text)
                    if source in ENGLISH and '{' not in source:
                        widget.configure(text=tr(source, self.lang))
                update_widgets(widget)

        update_widgets(self.root)
        self.mode_combo.configure(values=[tr(label, self.lang) for label in MODE_LABELS])
        self.values['mode'].set(next(tr(label, self.lang) for label, mode in MODE_LABELS.items()
                                     if mode == selected_mode))
        # Terminal status labels are stored in the previous language.
        values = dict(self.status_values)
        if 'label' in values:
            values['label'] = tr(originals.get(values['label'], values['label']), self.lang)
        self.set_status(self.status_text, **values)

    def browse(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[('GameAnalytics JSON', '*.json')])
        if path:
            self.json_path.set(path)

    def start(self):
        if self.running:
            return
        try:
            values = {key: variable.get().strip() for key, variable in self.values.items()}
            values['mode'] = {tr(label, self.lang): mode for label, mode in MODE_LABELS.items()}[values['mode']]
            for keys, convert in ((('users', 'sessions', 'workers'), int),
                                  (('returning_percent', 'pause_seconds', 'duration_min', 'duration_max',
                                    'action_min', 'action_max'), float)):
                for key in keys:
                    try:
                        values[key] = convert(values[key])
                    except ValueError:
                        raise ValueError(tr('Giá trị số không hợp lệ: {name}.', self.lang, name=key)) from None
            config = RunConfig(**values, json_path=self.json_path.get().strip(), dry_run=self.dry_run.get(),
                               game_key=self.game_key.get().strip(), secret_key=self.secret_key.get().strip(),
                               language=self.lang)
            config.validate()
        except (ValueError, KeyError) as error:
            messagebox.showerror(tr('Cấu hình không hợp lệ', self.lang), str(error), parent=self.root)
            return
        self.stop.clear()
        self.running = True
        self.bar.configure(maximum=config.users * config.sessions, value=0)
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        for widget, _ in self.inputs:
            widget.configure(state='disabled')
        self.set_status('Đang chạy thử…' if config.dry_run else 'Đang gửi dữ liệu thật…')
        self.append_log('\n=== ' + tr('CHẠY THỬ' if config.dry_run else 'GỬI THẬT', self.lang) + ' ===')

        def work():
            try:
                runner = DesktopRunner(config, log=lambda msg: self.messages.put(('log', msg)), stop=self.stop,
                                       progress=lambda done, failed: self.messages.put(('progress', (done, failed))))
                result = runner.run()
                self.messages.put(('done', result))
            except Exception as error:
                self.messages.put(('error', str(error)))

        threading.Thread(target=work, daemon=True).start()

    def append_log(self, message):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', message + '\n')
        if int(self.log_box.index('end-1c').split('.')[0]) > 2000:
            self.log_box.delete('1.0', '201.0')
        self.log_box.see('end')
        self.log_box.configure(state='disabled')

    def request_stop(self):
        self.stop.set()
        self.stop_button.configure(state='disabled')
        self.set_status('Đang dừng và đóng phiên hiện tại…')

    def close(self):
        if self.running:
            self.closing = True
            self.request_stop()
        else:
            self.root.destroy()

    def poll(self):
        # Bound each batch so event-heavy runs cannot monopolize the Tk event loop.
        for _ in range(200):
            try:
                kind, value = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == 'log':
                self.append_log(value)
            elif kind == 'progress':
                done, failed = value
                self.bar.configure(value=done + failed)
                if self.stop.is_set():
                    self.set_status('Đang dừng và đóng phiên hiện tại…')
                else:
                    self.set_status('Xong {done} phiên • Lỗi {failed}', done=done, failed=failed)
            else:
                self.running = False
                self.start_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
                for widget, state in self.inputs:
                    widget.configure(state=state)
                if kind == 'error':
                    self.set_status('Không chạy được')
                    self.append_log(tr('[LỖI] ', self.lang) + value)
                    if not self.closing:
                        messagebox.showerror(tr('Không chạy được', self.lang), value, parent=self.root)
                else:
                    label = tr('Đã dừng' if self.stop.is_set() else 'Hoàn tất đợt chạy', self.lang)
                    self.set_status('{label} • {completed} phiên xong • {failed} lỗi', label=label,
                                    completed=value['completed'], failed=value['failed'])
                    self.append_log(self.status.get())
                if self.closing:
                    self.root.destroy()
                    return
        self.root.after(100, self.poll)


if __name__ == '__main__':
    DesktopApp(tk.Tk()).root.mainloop()
