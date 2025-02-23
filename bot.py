import asyncio
import requests
import json
import os
import datetime
import threading
import re
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# API_PHAT_NGUOI = os.getenv("API_PHAT_NGUOI", "https://api.checkphatnguoi.vn/phatnguoi")
API_PHAT_NGUOI = os.getenv("API_PHAT_NGUOI_2", "https://api.zm.io.vn/v1/csgt/tracuu")

DATA_DIR = "/app/data"
DATA_FILE = os.path.join(DATA_DIR, "registered_plates.json")

registered_plates = {}
pending_registrations = set()

# Lưu dữ liệu vào file JSON
def save_data():
    """Lưu dữ liệu ra File"""
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_plates, f, ensure_ascii=False, indent=4)


# Tải dữ liệu từ file JSON
def load_data():
    """Đọc dữ liệu từ File"""
    global registered_plates
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            registered_plates = json.load(f)


# Tải dữ liệu khi bot khởi động
load_data()

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

async def check_violation(plate_number):
    """Request API kiểm tra dữ liệu biển số sử dụng method GET"""
    try:
        # Tạo URL với tham số query string
        url = f"{API_PHAT_NGUOI}?licensePlate={plate_number}"
        
        # Thực hiện request GET
        response = requests.get(url)
        data = response.json()
        print("Response data:", data)  # Debug log
        
        # Kiểm tra message trước
        if data.get("message") == "Không tìm thấy vi phạm":
            return f"✅ Biển số {plate_number} chưa phát hiện lỗi phạt nguội."

        # Kiểm tra cấu trúc dữ liệu và đảm bảo có vi phạm
        if (
            "data" in data 
            and isinstance(data["data"], dict)
            and "json" in data["data"] 
            and isinstance(data["data"]["json"], list) 
            and len(data["data"]["json"]) > 0
        ):
            violations = data["data"]["json"]
            results = []
            for item in violations:
                # Sử dụng dict.get() để tránh KeyError
                result = (
                    f"🚗 Biển số: {item.get('bienkiemsoat', 'Không có thông tin')}\n"
                    f"🔹 Loại xe: {item.get('loaiphuongtien', 'Không có thông tin')}\n"
                    f"🎨 Màu biển: {item.get('maubien', 'Không có thông tin')}\n"
                    f"⏰ Thời gian vi phạm: {item.get('thoigianvipham', 'Không có thông tin')}\n"
                    f"📍 Địa điểm: {item.get('diadiemvipham', 'Không có thông tin')}\n"
                    f"⚠️ Hành vi vi phạm: {item.get('hanhvivipham', 'Không có thông tin')}\n"
                    f"{'🟥' if item.get('trangthai') == 'Chưa xử phạt' else '🟩'} Trạng thái: {item.get('trangthai', 'Không có thông tin')}\n"
                    f"👮 Đơn vị phát hiện: {item.get('donviphathienvipham', 'Không có thông tin')}\n"
                    f"🏢 Nơi giải quyết:\n{chr(10).join(f'🏢 {x}' for x in item.get('noigiaiquyetvuviec', []))}\n"
                    "——————————————"
                )
                results.append(result)

            return "\n\n".join(results)
        
        # Nếu không có vi phạm hoặc dữ liệu không đúng cấu trúc
        return f"✅ Biển số {plate_number} chưa phát hiện lỗi phạt nguội."

    except requests.exceptions.RequestException as e:
        return f"⚠️ Lỗi kết nối API: {str(e)}"
    except Exception as e:
        return f"⚠️ Đã xảy ra lỗi: {str(e)}"


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🚗 Đăng ký biển số", callback_data="dangky")],
        [InlineKeyboardButton("🔍 Kiểm tra phạt nguội", callback_data="kiemtra")],
        [InlineKeyboardButton("📋 Danh sách biển số", callback_data="danhsach")],
        [InlineKeyboardButton("📖 Hướng dẫn", callback_data="huongdan"), InlineKeyboardButton("📞 Liên hệ", callback_data="lienhe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.set_my_commands([
        BotCommand("start", "Hiển thị menu"),
        BotCommand("dangky", "Đăng ký biển số"),
        BotCommand("kiemtra", "Kiểm tra phạt nguội"),
        BotCommand("danhsach", "Xem biển số đã đăng ký"),
        BotCommand("huongdan", "Hướng dẫn sử dụng"),
        BotCommand("lienhe", "Thông tin liên hệ"),
    ])
    
    await update.message.reply_text("🚗 Chào mừng bạn đến với Bot kiểm tra phạt nguội!", reply_markup=reply_markup)


async def handle_menu(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "dangky":
        await dangky(update, context)
    elif query.data == "kiemtra":
        await kiemtra(update, context)
    elif query.data == "danhsach":
        await danhsach(update, context)
    elif query.data == "huongdan":
        await huongdan(update, context)
    elif query.data == "lienhe":
        await lienhe(update, context)
        

async def huongdan(update: Update, context: CallbackContext) -> None:
    guide_text = (
        "📌 Hướng dẫn sử dụng bot kiểm tra phạt nguội:\n"
        "🔍 Mỗi người đăng ký đc tối đa 4 biển số.\n\n"
        "/dangky - Đăng ký biển số cần theo dõi.\n"
        "/kiemtra - Kiểm tra các biển số đã đăng ký.\n"
        "/danhsach - Xem danh sách biển số đã đăng ký.\n"
        "/lienhe - Xem thông tin liên hệ.\n"
    )

    if update.message:
        await update.message.reply_text(guide_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(guide_text)


async def lienhe(update: Update, context: CallbackContext) -> None:
    contact_text = (
        "📞 Thông tin liên hệ:\n"
        "🌐 Website: https://nguyenanh98.com\n"
        "🔥 Bot kiểm tra phạt nguội 🔥\n"
    )

    if update.message:
        await update.message.reply_text(contact_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(contact_text)


async def dangky(update: Update, context: CallbackContext) -> None:
    """Đăng ký biển số"""
    chat_id = update.effective_chat.id
    if chat_id in pending_registrations:
        await update.effective_message.reply_text("⚠️ Bạn đang trong quá trình nhập biển số. Hãy gửi biển số của bạn.")
        return
    pending_registrations.add(chat_id)
    await update.effective_message.reply_text("🚗 Nhập biển số xe đăng ký (VD: 51F-123.45 hoặc 51F12345):")


async def handle_dangky(update: Update, context: CallbackContext) -> None:
    """Tiến trình đăng ký biển số"""
    chat_id = update.message.chat_id
    if chat_id not in pending_registrations:
        return

    # Lấy danh sách biển số của người dùng
    user_plates = [plate for plate, cid in registered_plates.items() if cid == chat_id]

    # Kiểm tra nếu đã đăng ký tối đa 4 biển số
    if len(user_plates) >= 4:
        await update.message.reply_text("⚠️ Bạn đã đăng ký tối đa 4 biển số. Hãy xóa bớt để thêm mới.")
        return

    # Xử lý nhập liệu: Xóa khoảng trắng và ký tự đặc biệt
    plate_number = re.sub(r'\s+|[^a-zA-Z0-9]', '', update.message.text.strip().upper())

    if not plate_number:
        await update.message.reply_text("⚠️ Vui lòng nhập biển số xe!")
        return

    # Kiểm tra định dạng biển số xe
    pattern = re.compile(r'^\d{2}[A-Z]{1,2}\d{5,6}$')
    if not pattern.match(plate_number):
        await update.message.reply_text("⚠️ Biển số xe không đúng định dạng! Vui lòng nhập lại.")
        return

    # Đăng ký biển số nếu hợp lệ
    registered_plates[plate_number] = chat_id
    pending_registrations.remove(chat_id)
    await update.message.reply_text(f"✅ Đăng ký theo dõi biển số {plate_number} thành công.")
    save_data()


async def kiemtra(update: Update, context: CallbackContext) -> None:
    """Kiểm tra phạt nguội"""
    chat_id = update.effective_chat.id
    plates = [plate for plate, cid in registered_plates.items() if cid == chat_id]
    
    if not plates:
        await update.effective_message.reply_text("❌ Bạn chưa đăng ký biển số nào.")
        return
    
    keyboard = [[InlineKeyboardButton(f"🔍 Kiểm tra {plate}", callback_data=f"check_{plate}")] for plate in plates]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text("📋 Chọn biển số để kiểm tra phạt nguội:", reply_markup=reply_markup)


async def danhsach(update: Update, context: CallbackContext) -> None:
    """Danh sách biển số đã đăng ký"""
    chat_id = update.effective_chat.id
    plates = [plate for plate, cid in registered_plates.items() if cid == chat_id]
    max_plates = 4  # Số lượng biển số tối đa

    if not plates:
        await update.effective_message.reply_text("❌ Bạn chưa đăng ký biển số nào.")
        return

    # Hiển thị số biển đã đăng ký trên tổng số tối đa
    text = f"📋 Các biển số bạn đã đăng ký ({len(plates)}/{max_plates}):"

    # Tạo danh sách nút xóa cho từng biển số
    keyboard = [[InlineKeyboardButton(f"❌ Xóa - [{plate}]", callback_data=f"remove_{plate}")] for plate in plates]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(text, reply_markup=reply_markup)


async def handle_xoabienso(update: Update, context: CallbackContext) -> None:
    """Tiến trình xóa biển số"""
    query = update.callback_query
    await query.answer()

    plate_number = query.data.replace("remove_", "")
    chat_id = query.message.chat_id
    await query.message.edit_text(f"🗑️ Đang xóa biển số... {plate_number}")

    if plate_number in registered_plates and registered_plates[plate_number] == chat_id:
        del registered_plates[plate_number]
        save_data()
        await asyncio.sleep(2)  # Tạo độ trễ để người dùng thấy tin nhắn tạm thời
        await query.message.edit_text(f"✅ Đã xóa biển số {plate_number}.")
    else:
        await asyncio.sleep(2)  # Đợi 2 giây trước khi cập nhật lỗi
        await query.message.edit_text("❌ Biển số không tồn tại hoặc bạn không có quyền xóa.")


async def handle_kiemtra_bienso(update: Update, context: CallbackContext) -> None:
    """Xử lý khi người dùng nhấn vào nút kiểm tra biển số."""
    query = update.callback_query
    await query.answer()
    plate_number = query.data.replace("check_", "")
    
    await query.message.edit_text(f"🔍 Đang kiểm tra biển số... `{plate_number}`")
    
    result = await check_violation(plate_number)
    await query.message.reply_text(result)


async def scheduled_violation_check(app):
    """Kiểm tra phạt nguội vào Thứ Hai, chạy song song với bot"""
    print("🚀 Lịch kiểm tra đã chạy")
    has_run_today = False  

    while True:
        now = datetime.datetime.now()
        if now.weekday() == 0:  # Nếu là Thứ Hai
            if not has_run_today:  
                print("📅 Hôm nay là Thứ Hai - Kiểm tra phạt nguội...")

                for plate, chat_id in registered_plates.items():
                    result = await check_violation(plate)
                    
                    if "——————————————" in result:
                        try:
                            await app.bot.send_message(chat_id, f"🚨 Cảnh báo phạt nguội:\n{result}")
                        except Exception as e:
                            print(f"❌ Không thể gửi tin nhắn: {e}")

                    await asyncio.sleep(10)  # Thêm delay 10 giây giữa mỗi lần kiểm tra biển số

                has_run_today = True  

        else:
            has_run_today = False  

        await asyncio.sleep(21600)  # Chờ 6 tiếng
        
def start_scheduled_task(app):
    """Chạy scheduled_violation_check trong một luồng riêng"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduled_violation_check(app))

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dangky", dangky))
    app.add_handler(CommandHandler("kiemtra", kiemtra))
    app.add_handler(CommandHandler("danhsach", danhsach))
    app.add_handler(CommandHandler("huongdan", huongdan))
    app.add_handler(CommandHandler("lienhe", lienhe))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dangky))
    app.add_handler(CallbackQueryHandler(handle_kiemtra_bienso, pattern=r"^check_"))
    app.add_handler(CallbackQueryHandler(handle_xoabienso, pattern=r"^remove_"))
    app.add_handler(CallbackQueryHandler(handle_menu, pattern=r"^(dangky|kiemtra|danhsach|huongdan|lienhe)$"))

    # Tạo luồng riêng để chạy scheduled_violation_check
    thread = threading.Thread(target=start_scheduled_task, args=(app,), daemon=True)
    thread.start()
    
    print("✅ Bot đã sẵn sàng...")
    app.run_polling()

if __name__ == "__main__":
    main()
