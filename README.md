# Bot-telegram-Tracuuphatnguoi

Bot Telegram để kiểm tra phạt nguội dựa trên biển số xe.

## Tính năng

- Đăng ký biển số xe để theo dõi vi phạm
- Kiểm tra vi phạm giao thông qua API bên ngoài
- Xem danh sách biển số đã đăng ký
- Kiểm tra vi phạm định kỳ hàng tuần
- Menu tương tác với các tùy chọn đăng ký, kiểm tra và xem biển số

## Cài đặt

1. Clone repository:
    ```bash
    git clone https://github.com/lowji194/Bot-telegram-Tracuuphatnguoi.git
    cd Bot-telegram-Tracuuphatnguoi
    ```

2. Cài đặt các thư viện phụ thuộc:
    ```bash
    pip install -r requirements.txt
    ```

3. Thiết lập token của bot Telegram trong script:
    ```python
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    ```

## Sử dụng

1. Chạy bot:
    ```bash
    python bot.py
    ```

2. Tương tác với bot trên Telegram:
    - `/start` - Hiển thị menu
    - `/dangky` - Đăng ký biển số cần theo dõi
    - `/kiemtra` - Kiểm tra các biển số đã đăng ký
    - `/danhsach` - Xem danh sách biển số đã đăng ký
    - `/huongdan` - Hiển thị hướng dẫn sử dụng
    - `/lienhe` - Hiển thị thông tin liên hệ

## Kiểm tra định kỳ

Bot sẽ thực hiện kiểm tra vi phạm giao thông vào mỗi thứ Hai hàng tuần. Nếu phát hiện vi phạm, bot sẽ gửi thông báo đến người dùng đã đăng ký biển số.

## Đóng góp

Hãy gửi các vấn đề hoặc pull request. Chúng tôi hoan nghênh mọi đóng góp!

## Giấy phép

Dự án này được cấp phép dưới giấy phép MIT.
