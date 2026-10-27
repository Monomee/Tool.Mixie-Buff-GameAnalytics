# Android Session Tool

[Tiếng Việt](#tiếng-việt) · [English](#english)

## Tiếng Việt

### 1. Giới thiệu và mục đích

Android Session Tool là công cụ Python có giao diện desktop để tạo ID user giả lập, mô phỏng phiên chơi Android và gửi sự kiện lên **GameAnalytics**. Công cụ giúp học cách analytics ghi nhận user mới, user quay lại, số phiên, sự kiện gameplay và thời gian hoạt động.

Theo cách gọi thông thường, tool có thể được dùng để “buff user / thời gian”: tạo dữ liệu tổng hợp làm tăng số user, phiên và thời lượng được gửi đến project. Đây là **dữ liệu mô phỏng**, không chứng minh có người chơi thật hay tăng trưởng thật. Gửi sự kiện thành công cũng không bảo đảm mọi chỉ số trên dashboard tăng tương ứng.

Tool **không khởi tạo máy ảo Android, không chạy APK và không điều khiển điện thoại thật**. Mỗi user mới là UUID ngẫu nhiên kèm thông tin thiết bị mô phỏng; chương trình gửi request HTTP theo cấu trúc sự kiện GameAnalytics. ID nhập từ JSON được giữ nguyên, nên có thể đến từ dữ liệu thật hoặc lần mô phỏng trước đó.

Nên dùng project kiểm thử riêng mà bạn sở hữu hoặc được phép gửi dữ liệu. Dữ liệu tổng hợp gửi vào project đang vận hành có thể làm sai lệch báo cáo và quyết định dựa trên analytics.

### 2. Chức năng

- **Tạo user mới:** sinh UUID và chọn hãng, model thiết bị, phiên bản Android từ danh sách mô phỏng trong code.
- **Chạy lại user đã lưu:** dùng lại ID và trạng thái của user có phiên trước đó.
- **Returning từ JSON:** nhập bản export sự kiện, nhóm theo `user_id`, lấy số phiên, thời gian hoạt động cuối và tổng thời lượng lớn nhất giữa JSON và trạng thái đã lưu. Chế độ này chỉ chọn ID có trong JSON.
- **Kết hợp mới / returning:** chọn một phần user cũ theo tỷ lệ cấu hình, phần còn lại tạo mới.
- **Cấu hình lượt chạy:** số user, phiên/user, user đồng thời, thời lượng phiên, khoảng gửi sự kiện và thời gian nghỉ giữa phiên.
- **Mô phỏng sự kiện:** khởi tạo, bắt đầu phiên, sự kiện gameplay/design và kết thúc phiên, kèm metadata thiết bị/build, số phiên và thời lượng.
- **Chạy thử:** hiển thị log theo thời gian mô phỏng, không gửi request analytics và không ghi trạng thái user.
- **Theo dõi và dừng:** log, tiến độ và nút dừng; giao diện cố gắng đóng phiên đang chạy trước khi kết thúc.
- **Tiếng Việt / English:** đổi nhãn, trạng thái và thông báo kiểm tra dữ liệu trên giao diện.
- **Cấu hình riêng:** tách khóa và thông tin build/project khỏi mã nguồn dùng để chia sẻ.

Giới hạn pool hiện tại là **150 user**, không phải 150 máy ảo đang chạy. Giao diện báo lỗi nếu thêm user sẽ vượt giới hạn; không tự xóa user cũ để tạo chỗ.

### 3. Yêu cầu và cài đặt

- Python **3.10 trở lên**, có `pip` và Tkinter.
- Windows nếu muốn dùng `.bat`. Các lệnh dưới đây dùng PowerShell.
- Internet và khóa project hợp lệ khi gửi thật.
- Quyền ghi vào thư mục dự án để lưu trạng thái sau phiên gửi thật.

Tải hoặc clone dự án, mở PowerShell trong thư mục chứa `Tool.py`, rồi chạy:

```powershell
python --version
python -m pip install -r requirements.txt
python -m tkinter
```

`requirements.txt` hiện cài `requests>=2.31,<3`. Tkinter đi cùng bộ cài Python phù hợp, không cài bằng `pip install tkinter`. Lệnh cuối chỉ mở cửa sổ kiểm tra Tkinter; đóng cửa sổ đó trước khi chạy tool.

Nếu muốn tách thư viện khỏi Python dùng chung, có thể dùng môi trường ảo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ToolDesktop.py
```

Không cần kích hoạt môi trường ảo khi gọi interpreter trực tiếp như trên. Các lệnh `python ...` còn lại trong tài liệu phải dùng đúng interpreter đã cài thư viện.

### 4. Cấu hình khóa và thông tin project

Không cần khóa để mở giao diện và chạy thử. Để gửi thật, tạo cấu hình riêng **nếu chưa có**:

```powershell
Copy-Item config.example.json config.local.json
```

Không ghi đè cấu hình đang dùng. Mở `config.local.json` bằng trình soạn thảo, điền thông tin của project bạn được phép kiểm thử:

| Trường | Ý nghĩa |
| --- | --- |
| `game_key`, `secret_key` | Khóa GameAnalytics của project nhận sự kiện. Không chia sẻ giá trị thật. |
| `live_events_file` | File export để nhập user; đường dẫn tương đối tính từ thư mục chứa `Tool.py`. Mặc định `live-events.json`. |
| `sdk_version`, `engine_version` | Phiên bản SDK và engine được gửi trong sự kiện. |
| `build` | Nhãn build của game. |
| `platform` | Nền tảng, mặc định `android`. |
| `android_bundle_id` | Package/bundle ID của ứng dụng. |
| `android_app_version`, `android_app_build` | Phiên bản và số build của ứng dụng. |
| `android_app_signature` | Metadata chữ ký ứng dụng; không phải file khóa ký riêng. |
| `android_channel_id`, `connection_type` | Metadata kênh cài đặt và loại kết nối mô phỏng. |

Mọi giá trị phải là **chuỗi JSON**, kể cả số build. `0.0.0` và `com.example.game` trong bản mẫu chỉ là minh họa; thay bằng metadata phù hợp trước khi gửi thật. Không thêm comment hoặc dấu phẩy cuối vào JSON. Với đường dẫn Windows, dùng `/` hoặc escape dấu `\` thành `\\`.

Khởi động lại ứng dụng sau khi sửa file. Giao diện cho phép nhập Game Key/Secret Key khác trong phiên sử dụng hiện tại nhưng không ghi thay đổi đó vào file. Khi đổi project, cần dùng trạng thái user riêng như lưu ý bên dưới.

### 5. Cách chạy

#### Cách A — file `.bat` trên Windows

Sau khi cài thư viện, nhấp đúp `StartDesktop.bat`, hoặc chạy:

```powershell
.\StartDesktop.bat
```

File chuyển về thư mục dự án rồi gọi `python ToolDesktop.py`; nếu lỗi, nó giữ console để đọc thông báo. File không tự cài Python hay thư viện và dùng lệnh `python` trong môi trường hiện tại. Nếu chỉ cài thư viện trong `.venv`, dùng interpreter trực tiếp ở phần cài đặt hoặc chạy `.bat` từ môi trường đã kích hoạt `.venv`.

#### Cách B — kiểm tra code và chạy Python trực tiếp

Nếu không yên tâm với `.bat`, có thể mở và đọc `StartDesktop.bat`, `ToolDesktop.py`, `Tool.py` và `requirements.txt` trước khi chạy:

```powershell
python ToolDesktop.py
```

Lệnh này mở **cùng giao diện** mà `.bat` sử dụng. Chạy trực tiếp giúp bạn chủ động chọn interpreter và đọc mã nguồn, nhưng không tự bảo đảm mã nguồn an toàn nếu chưa kiểm tra.

#### Cách C — chế độ dòng lệnh cũ

```powershell
python Tool.py
```

**Lệnh này gửi thật ngay khi có đủ khóa trong `config.local.json`; không có hộp chọn chạy thử.** Nó không đọc các giá trị đang nhập trên giao diện. Logic mặc định chọn mục tiêu 1–3 user theo giờ máy, mỗi user một phiên khoảng 6–10 phút, sự kiện cách nhau khoảng 30–75 giây, tỷ lệ returning mục tiêu 60% tùy pool sẵn có.

CLI lưu pool ở cuối lượt chạy và xử lý lỗi khác giao diện. Nên dùng giao diện khi cần kiểm soát số phiên, chạy thử và dừng có điều phối.

### 6. Sử dụng giao diện

1. Chọn **Tiếng Việt** hoặc **English** ở đầu cửa sổ. Mặc định mỗi lần mở là Tiếng Việt; đổi ngôn ngữ giữ nguyên các giá trị đã nhập. Bộ chọn tạm khóa khi đang chạy.
2. Chọn chế độ user. Với returning từ JSON, dùng **Chọn file… / Browse…** để chọn bản export dạng danh sách sự kiện.
3. Nhập số user, phiên/user và user đồng thời. **Tổng phiên dự kiến = số user × phiên/user**. Mỗi user chạy các phiên của mình lần lượt.
4. Nhập thời lượng tối thiểu/tối đa bằng **phút**; khoảng gửi sự kiện và nghỉ giữa phiên bằng **giây**. Thời lượng và khoảng sự kiện phải lớn hơn 0; tối thiểu không vượt tối đa.
5. Giữ **Chạy thử / Dry run** cho lần kiểm tra đầu. Ví dụ: 1 user, 1 phiên, thời lượng 0.01–0.02 phút, sự kiện mỗi 0.1–0.2 giây. Chạy thử vẫn chờ theo thời gian đã chọn.
6. Sau khi kiểm tra log và project đích, bỏ chọn chạy thử nếu muốn gửi thật, rồi nhấn **Bắt đầu / Start**.
7. Nhấn **Dừng / Stop** để ngừng chờ, đóng phiên hiện tại và bỏ các phiên tiếp theo. Đóng cửa sổ khi đang chạy cũng yêu cầu dừng và chờ xử lý phiên.

Trong chế độ kết hợp, số returning là `round(số user × tỷ lệ / 100)` theo quy tắc làm tròn của Python. Thiếu returning user thì báo lỗi, không tự tạo ID mới để thay phần thiếu đó.

### 7. File dữ liệu và bảo mật

| File | Vai trò | Đưa lên Git? |
| --- | --- | --- |
| `Tool.py` | Sinh ID, tạo payload, gửi sự kiện và CLI cũ. | Có, sau khi kiểm tra mã nguồn. |
| `ToolDesktop.py` | Giao diện, cấu hình lượt chạy, ngôn ngữ và lưu trạng thái. | Có. |
| `StartDesktop.bat` | Mở giao diện bằng Python trên Windows. | Có. |
| `requirements.txt` | Danh sách thư viện cần cài. | Có. |
| `config.example.json` | Cấu hình mẫu không chứa khóa thật. | Có. |
| `config.local.json` | Khóa và metadata project trên máy. | **Không**; đã được ignore. |
| `android_retention_keys.txt` | ID user và trạng thái cho returning. | **Không**; đã được ignore. |
| `live-events*.json` | Export sự kiện, có thể chứa ID và lịch sử người dùng. | **Không**; đã được ignore theo mẫu tên này. |
| `__pycache__/`, `.venv/` | Cache Python và môi trường ảo. | Không; đã được ignore. |

Mỗi dòng trạng thái gồm `user_id,session_num,last_active,manufacturer,device,os_version,lifetime_session_length`. Tên file có chữ “keys” nhưng **không phải nơi lưu Game Key/Secret Key**. UUID không nhất thiết là ID phần cứng thật; dữ liệu nhập từ export vẫn cần giữ riêng.

Export mang tên khác có thể chưa được `.gitignore` chặn. Kiểm tra `git status` và nội dung thay đổi trước mỗi commit. `.gitignore` không loại file đã được theo dõi hoặc bí mật trong lịch sử commit. Không ép thêm file riêng tư bằng `git add -f`. Nếu khóa đã lộ, cần thay khóa và xử lý các bản đã chia sẻ.

### 8. Lưu ý và giới hạn

- **Chỉ số tổng hợp:** không bảo đảm tăng DAU, retention hoặc thời lượng trên dashboard đúng kỳ vọng. Returning giữ ID và tăng số phiên; retention còn phụ thuộc ngày quay lại và cách dịch vụ xử lý dữ liệu.
- **Không thu hồi sự kiện từ xa:** chạy thử không gửi dữ liệu; dừng lượt gửi thật không thu hồi sự kiện server đã nhận.
- **Lưu trạng thái:** GUI ghi sau mỗi phiên hoàn tất bằng thay file nguyên tử. Không chạy nhiều GUI/CLI cùng lúc vì dùng chung file; cơ chế này không giải quyết xung đột giữa nhiều tiến trình.
- **Đổi project:** trạng thái chưa chia theo Game Key. Dừng ứng dụng và sao lưu/di chuyển file trạng thái ra nơi riêng trước khi dùng project khác; giữ bản đúng project để khôi phục khi cần.
- **Lỗi mạng:** mỗi request có timeout cấu hình 15 giây; đây không phải cam kết toàn bộ thao tác dừng xong trong 15 giây. Không có retry tự động. Trong GUI, lỗi init/start hoặc kết thúc phiên dừng user đó; lỗi sự kiện giữa phiên được ghi log và có thể tiếp tục.
- **Lệch dữ liệu:** server nhận một phần dữ liệu hoặc lưu local thất bại có thể khiến hai bên lệch nhau. Kiểm tra log, sao lưu file và đối chiếu export mới trước khi chạy lại.
- **Ngôn ngữ:** log cũ, log kỹ thuật, phản hồi dịch vụ và thông báo hệ điều hành giữ nguyên ngôn ngữ gốc. CLI cũ chủ yếu dùng tiếng Anh.
- **Quyền riêng tư:** khóa trong cấu hình riêng vẫn là văn bản trên máy; không gửi kèm file này, export hoặc ảnh chụp lộ khóa khi chia sẻ dự án/báo lỗi.

### 9. Xử lý lỗi và kiểm tra

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| Không nhận lệnh `python` | Kiểm tra cài đặt Python và PATH; dùng đúng interpreter. |
| `No module named requests` | Cài `requirements.txt` bằng interpreter dùng mở tool. |
| `Can't find a usable init.tcl` hoặc lỗi Tkinter | Thử `python -m tkinter`; nếu lỗi, Modify/Repair Python và kiểm tra thành phần Tcl/Tk and IDLE. |
| Thiếu khóa | Kiểm tra cấu hình hoặc hai ô khóa trên GUI; CLI chỉ đọc khóa từ file. |
| JSON cấu hình lỗi | Dùng object có giá trị chuỗi, không comment/dấu phẩy cuối; kiểm tra escape đường dẫn. |
| Thiếu returning hoặc vượt pool | Giảm số user, chọn đúng chế độ hoặc nhập dữ liệu phù hợp; giữ trạng thái nếu còn cần lịch sử. |
| HTTP lỗi hoặc chỉ số không như mong đợi | Kiểm tra log, khóa, metadata và project đích; đối chiếu export trước khi gửi lại. |

Chạy test:

```powershell
python -m unittest discover -v
```

Các test hiện tại không gửi request analytics thật. Test GUI có thể bị bỏ qua nếu Tcl/Tk không hoạt động; chạy test không thay thế việc kiểm tra toàn bộ tính an toàn hoặc tương thích dịch vụ.

### 10. Mục đích học tập và trách nhiệm

**Dự án phục vụ mục đích học tập, nghiên cứu và thử nghiệm. Người sử dụng tự chịu trách nhiệm về cách sử dụng, quyền truy cập project, dữ liệu gửi đi và mọi hậu quả phát sinh.** Không dùng dữ liệu giả lập để trình bày sai lượng người chơi thật hoặc gây hiểu nhầm cho người khác. Chỉ thử nghiệm trong phạm vi được phép và kiểm tra yêu cầu của dịch vụ liên quan trước khi gửi dữ liệu.

---

## English

### 1. Overview and purpose

Android Session Tool is a Python desktop application that creates simulated user IDs, models Android play sessions, and sends events to **GameAnalytics**. It helps you learn how analytics records new users, returning users, session counts, gameplay events, and activity duration.

Informally, this can be described as “boosting users / playtime”: generating synthetic data that increases the users, sessions, and duration submitted to a project. This is **simulated data**, not evidence of real players or real growth. Successful submission does not guarantee corresponding increases in every dashboard metric.

The tool **does not create Android virtual machines, run APKs, or control physical phones**. Each new user is a random UUID with simulated device metadata; the program sends HTTP requests using GameAnalytics event structures. Imported JSON IDs are preserved and may originate from real data or earlier simulations.

Use a separate test project that you own or are authorized to send data to. Synthetic events in production can distort reports and decisions based on analytics.

### 2. Features

- **Create new users:** generate UUIDs and select manufacturer, device model, and Android version from simulated profiles in the code.
- **Returning saved users:** reuse IDs and state for users with previous sessions.
- **Returning from JSON:** import an event export, group by `user_id`, and keep the highest session count, last activity timestamp, and lifetime duration across imported and saved state. This mode selects only IDs present in the JSON.
- **Mixed new / returning:** select existing users according to the configured percentage and create the remaining users.
- **Run configuration:** users, sessions per user, concurrent users, session duration, event intervals, and pauses between sessions.
- **Event simulation:** initialize, start sessions, send gameplay/design events, and end sessions with device/build metadata, session numbers, and duration fields.
- **Dry run:** display logs over the simulated duration without sending analytics requests or saving user state.
- **Progress and stopping:** logs, progress, and coordinated stopping; the GUI attempts to close active sessions before finishing.
- **Vietnamese / English:** switch interface labels, status messages, and application validation messages.
- **Private configuration:** separate project credentials and build metadata from shareable source code.

The current pool limit is **150 users**, not 150 running virtual machines. The GUI rejects additions that would exceed the limit; it does not delete existing users to make space.

### 3. Requirements and installation

- Python **3.10 or later**, with `pip` and Tkinter.
- Windows for the `.bat` launcher. Commands below use PowerShell.
- Internet access and valid credentials for live submissions.
- Write access to the project directory to save state after live sessions.

Download or clone the project, open PowerShell in the directory containing `Tool.py`, and run:

```powershell
python --version
python -m pip install -r requirements.txt
python -m tkinter
```

`requirements.txt` currently installs `requests>=2.31,<3`. Tkinter comes with a suitable Python installation; do not use `pip install tkinter`. The last command opens a Tkinter test window; close it before starting the tool.

To isolate dependencies from your shared Python installation, optionally use a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe ToolDesktop.py
```

Calling the interpreter directly requires no activation. Other `python ...` commands in this document must use the interpreter where you installed dependencies.

### 4. Credentials and project configuration

No credentials are needed to open the GUI or use dry run. For live submissions, create private configuration **if it does not already exist**:

```powershell
Copy-Item config.example.json config.local.json
```

Do not overwrite an existing configuration. Edit `config.local.json` and enter information for a project you are authorized to test:

| Field | Meaning |
| --- | --- |
| `game_key`, `secret_key` | GameAnalytics credentials for the destination project. Never share real values. |
| `live_events_file` | Export used to import users; relative paths resolve from the directory containing `Tool.py`. Defaults to `live-events.json`. |
| `sdk_version`, `engine_version` | SDK and engine versions submitted with events. |
| `build` | Game build label. |
| `platform` | Platform, defaulting to `android`. |
| `android_bundle_id` | Application package/bundle ID. |
| `android_app_version`, `android_app_build` | Application version and build number. |
| `android_app_signature` | Application signature metadata; not a private signing key file. |
| `android_channel_id`, `connection_type` | Simulated installation channel and connection type metadata. |

All values must be **JSON strings**, including the build number. `0.0.0` and `com.example.game` are placeholders; replace them with appropriate metadata before live submissions. JSON must not contain comments or trailing commas. For Windows paths, use `/` or escape `\` as `\\`.

Restart after editing the file. The GUI lets you override Game Key/Secret Key for the current application session without saving those changes to the file. When switching projects, use separate user state as explained below.

### 5. Launch options

#### Option A — Windows `.bat` launcher

After installing dependencies, double-click `StartDesktop.bat`, or run:

```powershell
.\StartDesktop.bat
```

The launcher changes to the project directory and runs `python ToolDesktop.py`. On failure, it pauses the console so you can read the error. It does not install Python or dependencies and uses `python` from the current environment. If dependencies exist only in `.venv`, use the direct interpreter command above or launch the `.bat` from an activated environment.

#### Option B — inspect the source and run Python directly

If you prefer not to execute the `.bat`, inspect `StartDesktop.bat`, `ToolDesktop.py`, `Tool.py`, and `requirements.txt`, then run:

```powershell
python ToolDesktop.py
```

This opens **the same GUI** as the launcher. Direct execution gives you control over the interpreter and lets you review the source first; it does not by itself establish that unreviewed code is safe.

#### Option C — legacy command-line mode

```powershell
python Tool.py
```

**This command sends live data immediately when `config.local.json` contains both credentials; it has no dry-run checkbox.** It does not read settings entered in the GUI. Defaults select a target of 1–3 users according to local time, one session per user lasting about 6–10 minutes, event intervals of about 30–75 seconds, and a target returning ratio of 60%, subject to the available pool.

The CLI saves the pool at the end of the run and handles errors differently from the GUI. Use the GUI for configurable session counts, dry run, and coordinated stopping.

### 6. Using the GUI

1. Select **Tiếng Việt** or **English** at the top. Each launch defaults to Vietnamese; switching preserves entered values. The selector is disabled during a run.
2. Select a user mode. For returning from JSON, use **Browse… / Chọn file…** to select an export containing a list of events.
3. Enter users, sessions per user, and concurrent users. **Planned sessions = users × sessions per user.** Each user runs its sessions sequentially.
4. Set minimum/maximum duration in **minutes**; event intervals and pauses are in **seconds**. Duration and event intervals must be positive, with minimum ≤ maximum.
5. Leave **Dry run / Chạy thử** enabled for the first check. Example: 1 user, 1 session, duration 0.01–0.02 minutes, events every 0.1–0.2 seconds. Dry run still waits for the configured duration.
6. Review logs and the destination project, disable dry run if you intend to submit live data, then press **Start / Bắt đầu**.
7. Press **Stop / Dừng** to interrupt waits, close current sessions, and skip later sessions. Closing the window during a run also requests a stop and waits for session handling.

Mixed mode uses `round(users × percentage / 100)` with Python's rounding rules. Insufficient returning users cause an error; missing returning users are not silently replaced with new IDs.

### 7. Files and sensitive data

| File | Purpose | Commit to Git? |
| --- | --- | --- |
| `Tool.py` | ID generation, payloads, submissions, and legacy CLI. | Yes, after reviewing the source. |
| `ToolDesktop.py` | GUI, run configuration, language selection, and state persistence. | Yes. |
| `StartDesktop.bat` | Launch the GUI with Python on Windows. | Yes. |
| `requirements.txt` | Required dependencies. | Yes. |
| `config.example.json` | Example without real credentials. | Yes. |
| `config.local.json` | Local credentials and project metadata. | **No**; ignored. |
| `android_retention_keys.txt` | User IDs and state for returning sessions. | **No**; ignored. |
| `live-events*.json` | Event exports that may contain user IDs and activity history. | **No**; ignored under this filename pattern. |
| `__pycache__/`, `.venv/` | Python cache and virtual environment. | No; ignored. |

Each state row contains `user_id,session_num,last_active,manufacturer,device,os_version,lifetime_session_length`. Despite “keys” in the filename, this file **does not store Game Key/Secret Key**. A UUID is not necessarily a hardware ID; imported export data must still be kept private.

Exports with other filenames may not be covered by `.gitignore`. Review `git status` and pending changes before committing. `.gitignore` does not remove tracked files or secrets from history. Do not force private files into Git with `git add -f`. If credentials have been exposed, rotate them and address previously shared copies.

### 8. Notes and limitations

- **Synthetic metrics:** no guarantee of specific changes to DAU, retention, or dashboard duration. Returning sessions preserve IDs and increment session numbers; retention also depends on return dates and service processing.
- **No remote retraction:** dry run submits no events; stopping a live run does not retract events already received by the server.
- **State persistence:** the GUI saves after each completed session using atomic replacement. Do not run multiple GUI/CLI instances simultaneously; they share state, and atomic replacement does not resolve conflicts across processes.
- **Switching projects:** state is not partitioned by Game Key. Stop the app and back up/move state to a separate location before using another project; keep the matching state to restore when needed.
- **Network failures:** each request has a configured 15-second timeout, not a guarantee that the entire stop operation finishes within 15 seconds. No automatic retry. In the GUI, initialization/start or session-end failures stop that user; intermediate event failures are logged and may allow the session to continue.
- **State mismatch:** partial server acceptance or local save failures can leave state inconsistent. Review logs, back up files, and compare a fresh export before running again.
- **Language:** old logs, technical logs, service responses, and OS messages keep their original language. The legacy CLI mainly uses English.
- **Privacy:** credentials remain plaintext in local configuration. Do not include this file, exports, or screenshots exposing credentials when sharing the project or reporting issues.

### 9. Troubleshooting and tests

| Symptom | Check |
| --- | --- |
| `python` is not recognized | Check Python installation and PATH; select the intended interpreter. |
| `No module named requests` | Install `requirements.txt` with the interpreter used to launch the tool. |
| `Can't find a usable init.tcl` or Tkinter errors | Try `python -m tkinter`; if it fails, Modify/Repair Python and check the Tcl/Tk and IDLE component. |
| Missing credentials | Check configuration or GUI credential fields; the CLI reads credentials only from the file. |
| Invalid configuration JSON | Use an object with string values, no comments/trailing commas, and properly escaped paths. |
| Insufficient returning users or pool limit exceeded | Reduce counts, select the appropriate mode, or import suitable data; preserve state if its history is needed. |
| HTTP failures or unexpected metrics | Check logs, credentials, metadata, and the destination project; compare exports before resubmitting. |

Run tests:

```powershell
python -m unittest discover -v
```

Current tests do not submit real analytics requests. GUI tests may be skipped when Tcl/Tk is unavailable; passing tests do not replace a full security review or service compatibility check.

### 10. Educational use and responsibility

**This project is intended for education, research, and experimentation. Users are responsible for their use of the tool, authorization to access the project, submitted data, and any resulting consequences.** Do not present synthetic activity as real players or use it to mislead others. Test only within authorized scope and check the relevant service requirements before submitting data.
