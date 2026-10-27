# Android Session Tool

Ứng dụng desktop cho `Tool.py`, dùng Python 3.10+ và Tkinter (có trong bộ cài Python Windows thông thường).

## Chạy

```powershell
python -m pip install -r requirements.txt
python ToolDesktop.py
```

Hoặc nhấp đúp `StartDesktop.bat` sau khi cài thư viện.

Nếu cửa sổ không mở và báo `Can't find a usable init.tcl`, chạy `python -m tkinter` để kiểm tra riêng Tkinter. Nếu lệnh đó cũng lỗi, dùng bộ cài Python để **Modify / Repair**, bảo đảm đã chọn **tcl/tk and IDLE**. Đây là thành phần của Python, không cài bằng pip.

## Cấu hình riêng và Git

Khóa và thông tin build/project được đọc từ `config.local.json` cạnh `Tool.py`. File này chỉ lưu trên máy, đã được `.gitignore` loại khỏi Git. Nếu máy đã có file này, giữ nguyên để tiếp tục dùng cấu hình hiện tại.

Trên máy mới, tạo cấu hình từ bản mẫu:

```powershell
Copy-Item config.example.json config.local.json
```

Điền `game_key`, `secret_key` và thông tin build thực tế của project vào `config.local.json`; các phiên bản `0.0.0` và bundle `com.example.game` chỉ là giá trị mẫu. Mọi giá trị trong file phải là chuỗi. `live_events_file` có thể là đường dẫn tương đối với thư mục ứng dụng, mặc định `live-events.json`; giao diện vẫn cho phép chọn JSON khác. Khởi động lại ứng dụng sau khi sửa cấu hình.

Không có cấu hình riêng vẫn mở được giao diện và chạy thử. Gửi thật yêu cầu đủ hai khóa; có thể nhập khóa trên giao diện cho phiên sử dụng hiện tại. CLI yêu cầu khóa trong `config.local.json`.

Chỉ đưa `config.example.json` chứa giá trị mẫu lên Git. Không chia sẻ `config.local.json`, `android_retention_keys.txt`, các bản export `live-events*.json` hoặc cache Python. `.gitignore` không loại file đã được Git theo dõi; nếu khóa từng bị công khai, cần thay khóa trên dịch vụ và xử lý lịch sử Git.

## Sử dụng

- **Tạo user mới:** sinh UUID mới cho từng user.
- **Chạy lại user đã lưu:** chọn user có phiên trước đó trong `android_retention_keys.txt`.
- **Returning từ JSON:** chọn file export GameAnalytics dạng danh sách sự kiện. Gộp theo `user_id`, lấy `session_num`, `client_ts`, `lifetime_session_length` lớn nhất giữa JSON và trạng thái đã lưu. Chỉ chọn user có trong JSON.
- **Kết hợp:** lấy returning từ trạng thái đã lưu và JSON (nếu chọn file), còn lại tạo mới. Số returning = làm tròn(số user × tỷ lệ / 100). Báo lỗi nếu thiếu returning hoặc vượt pool 150; không xóa user cũ để tạo chỗ.
- **Số user × phiên/user** là tổng phiên dự kiến. **User đồng thời** giới hạn số user đang chạy; mỗi user thực hiện lần lượt các phiên của mình.
- Thời lượng mỗi phiên tính bằng **phút**. Khoảng gửi sự kiện và nghỉ giữa phiên tính bằng **giây**. Có thể dùng số thập phân để thử nhanh.
- Mặc định **chạy thử**: vẫn chờ theo thời lượng đã chọn, ghi log nhưng không gửi request và không lưu user. Ví dụ thử nhanh: 0.01–0.02 phút, sự kiện mỗi 0.1–0.2 giây.
- Bỏ chọn chạy thử để gửi thật tới project có Game Key/Secret Key đang hiển thị. Thông tin build/project lấy từ cấu hình riêng; thiết bị/gameplay kế thừa `Tool.py`. Chỉ dùng project bạn có quyền gửi dữ liệu kiểm thử.
- **Dừng** ngắt thời gian chờ, gửi kết thúc phiên hiện tại và không mở thêm phiên. Request đang chạy chờ timeout tối đa 15 giây mỗi request. Đóng cửa sổ trong lúc chạy cũng chờ đóng phiên và lưu trạng thái.

Trạng thái gửi thật được ghi sau mỗi phiên hoàn tất bằng thay file nguyên tử. Chạy thử không sửa file này. Không chạy nhiều bản app hoặc CLI cùng lúc vì chúng dùng chung file trạng thái. Đổi project phải dùng file trạng thái riêng (di chuyển file hiện tại ra nơi khác trước khi chạy), vì file chưa chia theo Game Key.

Nếu init/start hoặc session_end lỗi, user đó dừng; không có retry tự động. Nếu server đã nhận một phần dữ liệu hoặc lưu file thất bại, trạng thái local có thể lệch với server; nhập lại JSON mới từ GameAnalytics trước khi chạy lại. Returning giữ ID và tăng số phiên, không đảm bảo tỷ lệ retention trên dashboard vì retention còn phụ thuộc ngày quay lại.

`python Tool.py` vẫn chạy chế độ dòng lệnh cũ, đọc khóa từ cấu hình riêng. UI cho phép thay khóa trong phiên sử dụng nhưng không ghi thay đổi đó vào file cấu hình.

## Kiểm tra

```powershell
python -m unittest discover -v
```

Các test không gửi dữ liệu lên GameAnalytics.
