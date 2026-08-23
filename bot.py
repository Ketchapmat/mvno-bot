import os
import requests
import json
from datetime import datetime

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# =========================================================
# 🎯 [다중 조건 설정] 원하는 그룹을 자유롭게 추가/수정 가능
# =========================================================
CONDITIONS = [
    {
        "name": "🔥 0원 대란 요금제",
        "max_price": 0,
        "min_data": 10,        # 10GB 이상
        "min_duration": 4      # 4개월 이상
    },
    {
        "name": "📱 메인 500원 이하 (20GB+)",
        "max_price": 500,     # 월 500원 이하
        "min_data": 20,       # 20GB 이상
        "min_duration": 6      # 6개월 이상
    },
    {
        "name": "📱 메인 500원 초과 (20GB+)",
        "min_price": 501,
        "max_price": 1000,     # 월 1,000원 이하
        "min_data": 20,        # 20GB 이상
        "min_duration": 6      # 6개월 이상
    },
    {
        "name": "🚗 갓성비 찾아보기 (30GB+)",
        "max_price": 1100,     # 월 1,100원 이하
        "min_data": 30,        # 30GB 이상
        "min_duration": 3      # 3개월 이상
    }
]
# =========================================================

def send_telegram_message(text):
    """텔레그램 메시지 발송 함수"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ 오류: 토큰 또는 Chat ID 누락")
        return False
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json().get('ok', False)
    except Exception as e:
        print(f"❌ 텔레그램 발송 오류: {e}")
        return False

def check_mvno_plans():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now_str}] 다중 조건 알뜰폰 요금제 탐색 시작...")

    results_by_group = {cond["name"]: [] for cond in CONDITIONS}
    
    try:
        api_url = "https://api.moyoplan.com/plans?page=1&amount=50"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(api_url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            plans = res.json().get('data', {}).get('plans', [])
            
            for p in plans:
                p_name = p.get('name', '')
                p_carrier = p.get('carrier', {}).get('name', '통신사')
                p_price = p.get('regularPrice', 99999)
                p_duration = p.get('discountMonth', 0)
                p_data_gb = p.get('data', 0) / 1000
                plan_id = p.get('id', '')
                detail_url = f"https://www.moyoplan.com/plans/{plan_id}" if plan_id else "https://www.moyoplan.com"

                # 설정된 각 조건 그룹별로 매칭 검사
                for cond in CONDITIONS:
                    if (p_price <= cond["max_price"] and 
                        p_data_gb >= cond["min_data"] and 
                        p_duration >= cond["min_duration"]):
                        
                        results_by_group[cond["name"]].append({
                            "carrier": p_carrier,
                            "name": p_name,
                            "price": p_price,
                            "duration": p_duration,
                            "data": f"{int(p_data_gb)}GB",
                            "url": detail_url
                        })
    except Exception as e:
        print(f"API 조회 오류: {e}")

    # 메시지 조합
    total_found = sum(len(items) for items in results_by_group.values())
    
    if total_found > 0:
        msg = f"🔔 <b>[맞춤 알뜰폰 특가 요금제 발견]</b>\n"
        msg += f"📅 확인 시각: {now_str}\n\n"
        
        for cond_name, items in results_by_group.items():
            if items:
                msg += f"━━━━━━━━━━━━━━\n"
                msg += f"<b>{cond_name}</b> ({len(items)}건)\n"
                msg += f"━━━━━━━━━━━━━━\n"
                for idx, item in enumerate(items[:3], 1): # 각 그룹별 최대 3개 표시
                    msg += f"<b>{idx}. [{item['carrier']}] {item['name']}</b>\n"
                    msg += f"• 요금: <b>{item['price']:,}원</b> ({item['duration']}개월 할인)\n"
                    msg += f"• 데이터: <b>{item['data']}</b>\n"
                    msg += f"👉 <a href='{item['url']}'>상세보기</a>\n\n"
        send_telegram_message(msg)
    else:
        # 조건 일치 요금제가 없을 때 발송
        msg = f"🤖 <b>[알뜰폰 특가 알리미 - 탐색 완료]</b>\n\n"
        msg += f"📅 확인 시각: {now_str}\n\n"
        msg += f"현재 설정된 <b>{len(CONDITIONS)}개 조건 그룹</b>에 일치하는 특가 요금제가 없습니다.\n새로운 요금제가 등록되면 즉시 알려드립니다!"
        send_telegram_message(msg)

if __name__ == "__main__":
    check_mvno_plans()
