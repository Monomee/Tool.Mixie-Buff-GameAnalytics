import base64
import concurrent.futures
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
import random
import math
import requests
import threading

# Ensure console supports utf-8 safely on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Local configuration is deliberately excluded from Git.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(BASE_DIR, "android_retention_keys.txt")
MAX_TOTAL_USERS = 150

try:
    with open(os.path.join(BASE_DIR, "config.local.json"), encoding="utf-8-sig") as config_file:
        CONFIG = json.load(config_file)
except FileNotFoundError:
    CONFIG = {}
except json.JSONDecodeError:
    raise ValueError("config.local.json must contain valid JSON.") from None
if not isinstance(CONFIG, dict) or not all(isinstance(value, str) for value in CONFIG.values()):
    raise ValueError("config.local.json must be an object with string values.")

GAME_KEY = CONFIG.get("game_key", "").strip()
SECRET_KEY = CONFIG.get("secret_key", "").strip()
LIVE_EVENTS_FILE = os.path.join(BASE_DIR, CONFIG.get("live_events_file", "live-events.json"))

class ScalableAndroidTrafficGenerator:
    def __init__(self, game_key: str, secret_key: str, live_events_path: str = LIVE_EVENTS_FILE):
        self.game_key = game_key
        self.secret_key = secret_key.encode('utf-8')
        self.base_url = f"https://api.gameanalytics.com/v2/{game_key}"
        self.live_events_path = live_events_path
        self.stop_event = threading.Event()
        self.duration_range = (6.0, 10.0)
        self.action_range = (30.0, 75.0)
        self.log = print
        self.strict_session_end = False
        
        self.sdk_version = CONFIG.get("sdk_version", "unity 0.0.0")
        self.engine_version = CONFIG.get("engine_version", "unity 0.0.0")
        self.build = CONFIG.get("build", "0.0.0")
        self.platform = CONFIG.get("platform", "android")
        self.android_bundle_id = CONFIG.get("android_bundle_id", "com.example.game")
        self.android_app_version = CONFIG.get("android_app_version", "0.0.0")
        self.android_app_build = CONFIG.get("android_app_build", "1")
        self.android_app_signature = CONFIG.get("android_app_signature", "")
        self.android_channel_id = CONFIG.get("android_channel_id", "com.google.android.packageinstaller")
        self.connection_type = CONFIG.get("connection_type", "wwan")

        # Default devices
        self.device_profiles = [
            {"manufacturer": "samsung", "device": "SM-G781N"},
            {"manufacturer": "google", "device": "Pixel 8"},
            {"manufacturer": "xiaomi", "device": "23127PN0CG"},
            {"manufacturer": "oneplus", "device": "CPH2581"}
        ]
        self.os_versions = ["android 13", "android 14", "android 15"]
        self.game_actions = [
            "Gameplay:Match:Started",
            "Shop:View:DailyDeals",
            "Inventory:Equip:Skin",
            "Social:Leaderboard:View"
        ]

    def get_target_player_count(self) -> int:
        """Calculates player targets dynamically based on the current hour."""
        current_hour = time.localtime().tm_hour
        wave = math.sin((current_hour - 15) * math.pi / 12)  
        
        min_players = 1
        max_players = 3
        target = int(min_players + (max_players - min_players) * ((wave + 1) / 2))
        
        print(f"[TIME] Current Hour: {current_hour}:00 | Scaling Target Concurrency to: {target} players")
        return target

    def load_live_events_players(self, file_path: str) -> dict:
        """Extracts unique players and their highest session numbers from live-events JSON."""
        if not os.path.exists(file_path):
            print(f"[INFO] No live events file found at: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                events = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to read {file_path}: {e}")
            return {}

        players = {}
        for event in events:
            uid = event.get("user_id")
            if not uid:
                continue

            session_num = event.get("session_num", 1)
            client_ts = event.get("client_ts", time.time())
            device = event.get("device", "SM-G781N")
            manufacturer = event.get("manufacturer", "samsung")
            os_ver = event.get("os_version", "android 13")
            lifetime_len = event.get("lifetime_session_length", 0)

            if uid not in players:
                players[uid] = {
                    "user_id": uid,
                    "session_num": session_num,
                    "last_active": client_ts,
                    "manufacturer": manufacturer,
                    "device": device,
                    "os_version": os_ver,
                    "lifetime_session_length": lifetime_len,
                    "from_live_file": True
                }
            else:
                if session_num > players[uid]["session_num"]:
                    players[uid]["session_num"] = session_num
                if client_ts > players[uid]["last_active"]:
                    players[uid]["last_active"] = client_ts
                if lifetime_len > players[uid].get("lifetime_session_length", 0):
                    players[uid]["lifetime_session_length"] = lifetime_len

        print(f"[IMPORT] Loaded {len(players)} unique existing players from live-events JSON.")
        return players

    def load_and_scale_roster(self, target_count: int, retention_rate: float = 0.6) -> tuple[list, list]:
        """
        Builds the active player roster, strictly capping total accounts around MAX_TOTAL_USERS (150).
        Reuses existing accounts for returning sessions rather than infinitely minting new ones.
        """
        master_roster = {}

        # 1. Load historical retention accounts from file if present
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split(",")
                        if len(parts) >= 3:
                            uid = parts[0]
                            master_roster[uid] = {
                                "user_id": uid,
                                "session_num": int(parts[1]),
                                "last_active": float(parts[2]),
                                "manufacturer": parts[3] if len(parts) > 3 else "samsung",
                                "device": parts[4] if len(parts) > 4 else "SM-G781N",
                                "os_version": parts[5] if len(parts) > 5 else "android 13",
                                "lifetime_session_length": int(parts[6]) if len(parts) > 6 else 0,
                                "from_live_file": False
                            }

        # 2. Ingest players from the downloaded live-events file
        live_players = self.load_live_events_players(self.live_events_path)
        for uid, pdata in live_players.items():
            if uid not in master_roster:
                master_roster[uid] = pdata
            else:
                if pdata["session_num"] > master_roster[uid]["session_num"]:
                    master_roster[uid]["session_num"] = pdata["session_num"]
                master_roster[uid]["manufacturer"] = pdata["manufacturer"]
                master_roster[uid]["device"] = pdata["device"]
                master_roster[uid]["os_version"] = pdata["os_version"]
                master_roster[uid]["from_live_file"] = True

        # Safety trim: if the roster ever exceeds MAX_TOTAL_USERS, keep only the top MAX_TOTAL_USERS
        if len(master_roster) > MAX_TOTAL_USERS:
            sorted_accounts = sorted(
                master_roster.values(),
                key=lambda a: (1 if a.get("from_live_file") else 0, a.get("last_active", 0)),
                reverse=True
            )
            master_roster = {a["user_id"]: a for a in sorted_accounts[:MAX_TOTAL_USERS]}

        # 3. Select returning players from the existing roster
        live_uids = [uid for uid, p in master_roster.items() if p.get("from_live_file")]
        other_uids = [uid for uid, p in master_roster.items() if not p.get("from_live_file")]

        num_returning = min(len(master_roster), int(target_count * retention_rate))
        selected_batch = []
        selected_uids = set()

        # Prioritize live-imported players first
        num_live_pick = min(len(live_uids), int(num_returning * 0.75))
        if num_live_pick > 0:
            chosen_live = random.sample(live_uids, num_live_pick)
            for uid in chosen_live:
                selected_batch.append(master_roster[uid])
                selected_uids.add(uid)

        # Fill remaining returning slots from other existing accounts
        remaining_ret_slots = num_returning - len(selected_batch)
        available_other = [uid for uid in other_uids if uid not in selected_uids]
        if remaining_ret_slots > 0 and available_other:
            chosen_other = random.sample(available_other, min(len(available_other), remaining_ret_slots))
            for uid in chosen_other:
                selected_batch.append(master_roster[uid])
                selected_uids.add(uid)

        if selected_batch:
            next_sample = [p["session_num"] + 1 for p in selected_batch[:4]]
            print(f"[RETENTION] Selected {len(selected_batch)} returning players (next sessions: {next_sample}...)")

        # 4. Fill remaining slots:
        # ONLY mint new accounts if we haven't reached the 150-user cap!
        needed = target_count - len(selected_batch)
        can_mint = max(0, MAX_TOTAL_USERS - len(master_roster))
        to_mint = min(needed, can_mint)

        if to_mint > 0:
            print(f"[GROWTH] Minting {to_mint} new players (pool: {len(master_roster) + to_mint}/{MAX_TOTAL_USERS})")
            for _ in range(to_mint):
                new_uid = str(uuid.uuid4())
                dev_prof = random.choice(self.device_profiles)
                new_account = {
                    "user_id": new_uid,
                    "session_num": 0,
                    "last_active": time.time(),
                    "manufacturer": dev_prof["manufacturer"],
                    "device": dev_prof["device"],
                    "os_version": random.choice(self.os_versions),
                    "lifetime_session_length": 0,
                    "from_live_file": False
                }
                master_roster[new_uid] = new_account
                selected_batch.append(new_account)
                selected_uids.add(new_uid)

        # If we still need players to hit target_count (cap reached or not enough to mint),
        # fill by recycling remaining unselected players in the 150 pool
        still_needed = target_count - len(selected_batch)
        if still_needed > 0:
            unselected = [p for uid, p in master_roster.items() if uid not in selected_uids]
            if unselected:
                fill_pick = random.sample(unselected, min(len(unselected), still_needed))
                selected_batch.extend(fill_pick)

        print(f"[POOL] Active batch: {len(selected_batch)} | Total user pool: {len(master_roster)}/{MAX_TOTAL_USERS}")
        return selected_batch, list(master_roster.values())

    def _save_all_accounts(self, master_roster: list):
        """Saves states securely back into flat text layout formatting."""
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            for acct in master_roster:
                mfr = acct.get("manufacturer", "samsung")
                dev = acct.get("device", "SM-G781N")
                os_ver = acct.get("os_version", "android 13")
                life = acct.get("lifetime_session_length", 0)
                f.write(f"{acct['user_id']},{acct['session_num']},{acct['last_active']},{mfr},{dev},{os_ver},{life}\n")

    def _generate_signature(self, body_bytes: bytes) -> str:
        digest = hmac.new(self.secret_key, body_bytes, hashlib.sha256).digest()
        return base64.b64encode(digest).decode('utf-8')

    def _send(self, endpoint: str, payload: list | dict):
        url = f"{self.base_url}/{endpoint}"
        body_bytes = json.dumps(payload).encode('utf-8')
        headers = {
            "Authorization": self._generate_signature(body_bytes),
            "Content-Type": "application/json"
        }
        resp = requests.post(url, data=body_bytes, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"[ERROR] [{endpoint.upper()}] HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        return resp

    def _create_event_payload(self, category: str, account: dict, session_id: str, next_session_num: int,
                              current_length: int = 0, lifetime_length: int = 0, extra_fields: dict = None) -> list:
        """Constructs an event JSON matching the exact GA Unity/Android SDK schema."""
        now = int(time.time())
        event = {
            "v": 2,
            "user_id": account["user_id"],
            "event_uuid": str(uuid.uuid4()),
            "client_ts": now,
            "sdk_version": self.sdk_version,
            "os_version": account.get("os_version", "android 13"),
            "manufacturer": account.get("manufacturer", "samsung"),
            "device": account.get("device", "SM-G781N"),
            "platform": self.platform,
            "session_id": session_id,
            "session_num": next_session_num,
            "current_session_length": current_length,
            "lifetime_session_length": lifetime_length,
            "connection_type": self.connection_type,
            "android_bundle_id": self.android_bundle_id,
            "android_app_version": self.android_app_version,
            "android_app_build": self.android_app_build,
            "android_app_signature": self.android_app_signature,
            "android_channel_id": self.android_channel_id,
            "engine_version": self.engine_version,
            "build": self.build,
            "category": category
        }
        if extra_fields:
            event.update(extra_fields)
        return [event]

    def simulate_dynamic_session(self, account: dict) -> dict:
        """Simulates an organic player session lasting anywhere between 6 to 10 minutes."""
        user_id = account["user_id"]
        next_session_num = account["session_num"] + 1
        session_id = str(uuid.uuid4())
        
        manufacturer = account.get("manufacturer", "samsung")
        device = account.get("device", "SM-G781N")
        os_ver = account.get("os_version", "android 13")
        is_new_install = (account["session_num"] == 0 and not account.get("from_live_file"))
        is_returning = (next_session_num > 1)
        lifetime_start = account.get("lifetime_session_length", 0)

        # Real player variable lengths: 6 to 10 minutes randomized per-profile
        session_duration_minutes = random.uniform(*self.duration_range)
        target_seconds = session_duration_minutes * 60
        
        try:
            # 1. Initialize session
            init_payload = {
                "platform": self.platform,
                "os_version": os_ver,
                "sdk_version": self.sdk_version,
                "build": self.build,
                "session_num": next_session_num,
                "user_id": user_id
            }
            self._send("init", init_payload)

            # 2. Send user session start event
            # CRITICAL: GameAnalytics requires 'install: True' on session 1 to count the user as a New User
            user_extra = {}
            if is_new_install:
                user_extra["install"] = True

            user_event = self._create_event_payload(
                category="user",
                account=account,
                session_id=session_id,
                next_session_num=next_session_num,
                current_length=0,
                lifetime_length=lifetime_start,
                extra_fields=user_extra
            )
            self._send("events", user_event)
            tag = "RETURNING" if is_returning else "NEW INSTALL"
            self.log(f"[START] [{tag} User {user_id[:8]}] Session #{next_session_num} on {device} ({os_ver})")
        except Exception as e:
            self.log(f"[WARN] [User {user_id[:8]}] Init/Start failed: {e}")
            return account

        start_time = time.time()
        elapsed = 0

        while elapsed < target_seconds and not self.stop_event.is_set():
            # Jagged intervals to look like true human pacing
            sleep_step = random.uniform(*self.action_range)
            remaining = target_seconds - elapsed
            if self.stop_event.wait(min(sleep_step, remaining)):
                break
            
            elapsed = time.time() - start_time
            chosen_action = random.choice(self.game_actions)

            design_payload = self._create_event_payload(
                category="design",
                account=account,
                session_id=session_id,
                next_session_num=next_session_num,
                current_length=int(elapsed),
                lifetime_length=lifetime_start + int(elapsed),
                extra_fields={"event_id": chosen_action}
            )
            try:
                self._send("events", design_payload)
                self.log(f"[ACTION] [User {user_id[:8]}] Event: {chosen_action}")
            except Exception as e:
                self.log(f"[WARN] [User {user_id[:8]}] Event send failed: {e}")

        # 3. Send session_end event so GameAnalytics calculates session length and retention cleanly
        session_length = int(time.time() - start_time)
        session_end_payload = self._create_event_payload(
            category="session_end",
            account=account,
            session_id=session_id,
            next_session_num=next_session_num,
            current_length=session_length,
            lifetime_length=lifetime_start + session_length,
            extra_fields={"length": session_length}
        )
        try:
            self._send("events", session_end_payload)
            self.log(f"[FINISH] [User {user_id[:8]}] Completed Session #{next_session_num} ({session_length}s)")
        except Exception as e:
            self.log(f"[WARN] [User {user_id[:8]}] Session end send failed: {e}")
            if self.strict_session_end:
                raise

        # Return updated metrics to persist returning player state
        return {
            "user_id": user_id,
            "session_num": next_session_num,
            "last_active": time.time(),
            "manufacturer": manufacturer,
            "device": device,
            "os_version": os_ver,
            "lifetime_session_length": lifetime_start + session_length,
            "from_live_file": account.get("from_live_file", False)
        }

# --- Deployment Execution Loop ---
if __name__ == "__main__":
    if not GAME_KEY or not SECRET_KEY:
        sys.exit("Set game_key and secret_key in config.local.json before sending data.")
    generator = ScalableAndroidTrafficGenerator(GAME_KEY, SECRET_KEY, LIVE_EVENTS_FILE)
    
    # 1. Dynamically figure out target player volumes based on current time
    target_players = generator.get_target_player_count()
    
    # 2. Build roster mixing returning live players (retention) and new installs
    active_batch, full_roster = generator.load_and_scale_roster(target_players, retention_rate=0.6)
    
    print(f"[EXEC] Spawning {len(active_batch)} asynchronous workers. Each profile stays online for 6-10 minutes.")

    # 3. Spin up concurrent thread pool allocation
    updated_profiles_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=target_players) as executor:
        futures = {executor.submit(generator.simulate_dynamic_session, profile): profile for profile in active_batch}
        
        for future in concurrent.futures.as_completed(futures):
            res_profile = future.result()
            if res_profile:
                updated_profiles_map[res_profile["user_id"]] = res_profile

    # 4. Sync session tracking progress back into master roster
    for idx, acct in enumerate(full_roster):
        uid = acct["user_id"]
        if uid in updated_profiles_map:
            full_roster[idx] = updated_profiles_map[uid]

    generator._save_all_accounts(full_roster)
    print("\n[COMPLETE] All active profiles finished and retention records have been updated.")

