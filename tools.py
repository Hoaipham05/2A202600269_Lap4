from langchain_core.tools import tool
import re

# ================= DATA (GIỮ NGUYÊN) =================

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:10", "arrival": "09:25", "price": 2250000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "16:30", "arrival": "18:45", "price": 4600000, "class": "business"},
        {"airline": "VietJet Air", "departure": "09:40", "arrival": "11:55", "price": 1590000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "13:20", "arrival": "15:35", "price": 1980000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Phú Quốc": [
        {"name": "9Station Hostel", "price_per_night": 200000, "rating": 4.5},
        {"name": "Lahana Resort", "price_per_night": 800000, "rating": 4.0},
        {"name": "Sol by Meliá", "price_per_night": 1500000, "rating": 4.2},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000, "area": "An Thượng", "rating": 4.7},
    ]
}

# ================= HELPER =================

def format_vnd(x: int) -> str:
    return f"{x:,}".replace(",", ".") + "đ"


# ================= TOOLS =================

@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm chuyến bay giữa hai thành phố.
    Trả về DANH SÁCH chuyến bay, đánh dấu chuyến rẻ nhất.
    Nếu không có sẽ thử tra ngược chiều.
    """
    flights = FLIGHTS_DB.get((origin, destination))
    reversed_flag = False

    if not flights:
        flights = FLIGHTS_DB.get((destination, origin))
        if flights:
            reversed_flag = True
        else:
            return f"Không tìm thấy chuyến bay từ {origin} đến {destination}."

    # tìm giá rẻ nhất
    min_price = min(f["price"] for f in flights)

    note = " (đảo chiều)" if reversed_flag else ""
    result = [f"Danh sách chuyến bay {origin} → {destination}{note}:\n"]

    for f in flights:
        tag = " (RẺ NHẤT)" if f["price"] == min_price else ""

        result.append(
            f"- {f['airline']} | {f['departure']} - {f['arrival']} | "
            f"{f['class']} | {format_vnd(f['price'])}{tag}"
        )

    return "\n".join(result)


@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Tìm khách sạn theo thành phố.
    - Lọc theo giá
    - Trả về danh sách + gợi ý khách sạn rẻ nhất
    """
    hotels = HOTELS_DB.get(city)

    if not hotels:
        return f"Không có dữ liệu khách sạn tại {city}."

    # lọc theo budget
    filtered = [h for h in hotels if h["price_per_night"] <= max_price_per_night]

    if not filtered:
        return f"Không tìm thấy khách sạn tại {city} dưới {format_vnd(max_price_per_night)}."

    # sort theo giá tăng
    filtered.sort(key=lambda x: x["price_per_night"])

    result = [f"Khách sạn tại {city}:\n"]

    for h in filtered:
        result.append(
            f"- {h['name']} | Rating {h['rating']} | "
            f"{format_vnd(h['price_per_night'])}/đêm"
        )

    # gợi ý khách sạn rẻ nhất
    best = filtered[0]
    result.append(
        f"\nGợi ý: chọn {best['name']} ({format_vnd(best['price_per_night'])}/đêm) để tiết kiệm."
    )

    return "\n".join(result)


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách.
    Format input: 've:1000000,hotel:1600000'
    """
    try:
        total = 0
        detail = []

        items = expenses.split(",")

        for i in items:
            if ":" not in i:
                return "Sai format. Dùng: ten:sotien,ten:sotien"

            name, val = i.split(":", 1)

            # xử lý input bẩn (có dấu . đ space)
            val = re.sub(r"[^\d]", "", val)

            if val == "":
                return f"Lỗi giá trị: {name}"

            val = int(val)

            total += val
            detail.append((name.strip(), val))

        remain = total_budget - total

        # format output
        result = ["Bảng chi phí:"]

        for name, val in detail:
            result.append(f"- {name}: {format_vnd(val)}")

        result.append("---")
        result.append(f"Tổng chi: {format_vnd(total)}")
        result.append(f"Ngân sách: {format_vnd(total_budget)}")

        if remain >= 0:
            result.append(f"Còn lại: {format_vnd(remain)}")
        else:
            result.append(f"Vượt ngân sách {format_vnd(abs(remain))}!")

        return "\n".join(result)

    except Exception:
        return "Lỗi format chi phí."