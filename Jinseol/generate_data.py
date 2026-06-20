import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

SEED = 20250507
rng = np.random.default_rng(SEED)

Path("data").mkdir(exist_ok=True)

# ============================================================
# 1. orders.csv
# ============================================================
PRODUCTS  = ["황칠황", "뿌리토", "리퀴드케어"]
CUSTOMERS = ["한국건강㈜", "웰니스코리아", "자연드림㈜", "건강한세상", "초록마을㈜"]

N_ORDERS   = 30
BASE_DATE  = datetime(2025, 1, 6)

orders = pd.DataFrame({
    "order_id"    : [f"ORD-{i:03d}" for i in range(1, N_ORDERS + 1)],
    "product_name": rng.choice(PRODUCTS, size=N_ORDERS),
    "order_qty"   : rng.integers(100, 501, size=N_ORDERS),   # 100~500
    "order_date"  : [
        (BASE_DATE + timedelta(days=int(d))).strftime("%Y-%m-%d")
        for d in rng.integers(0, 90, size=N_ORDERS)
    ],
    "customer"    : rng.choice(CUSTOMERS, size=N_ORDERS),
})

orders.to_csv("data/orders.csv", index=False, encoding="utf-8-sig")
print("=== orders.csv ===")
print(orders.head(3).to_string(index=False))
print(f"shape: {orders.shape}\n")

# ============================================================
# 2. work_orders.csv  (1~2개 작업지시 / 수주)
# ============================================================
EQUIPMENTS  = ["수동충진기", "자동충진기"]
WO_STATUSES = ["대기", "진행", "완료"]

wo_rows    = []
wo_counter = 1

for _, row in orders.iterrows():
    n_wo       = int(rng.integers(1, 3))          # 1 or 2
    order_date = datetime.strptime(row["order_date"], "%Y-%m-%d")
    total_qty  = int(row["order_qty"])
    equipment  = str(rng.choice(EQUIPMENTS))      # 수주 단위로 설비 배정

    for j in range(n_wo):
        scheduled_date = order_date + timedelta(days=int(rng.integers(1, 8)))
        status         = str(rng.choice(WO_STATUSES))

        if n_wo == 1:
            planned_qty = total_qty
        elif j == 0:
            planned_qty = int(total_qty * float(rng.uniform(0.4, 0.6)))
        else:
            planned_qty = total_qty - wo_rows[-1]["planned_qty"]

        wo_rows.append({
            "wo_id"         : f"WO-{wo_counter:03d}",
            "order_id"      : row["order_id"],
            "product_name"  : row["product_name"],
            "planned_qty"   : planned_qty,
            "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
            "equipment"     : equipment,
            "status"        : status,
        })
        wo_counter += 1

work_orders = pd.DataFrame(wo_rows)
work_orders.to_csv("data/work_orders.csv", index=False, encoding="utf-8-sig")
print("=== work_orders.csv ===")
print(work_orders.head(3).to_string(index=False))
print(f"shape: {work_orders.shape}\n")

# ============================================================
# 3. lots.csv  (2~4 LOT / 작업지시)
# ============================================================
OPERATORS    = ["작업자A", "작업자B", "작업자C", "작업자D"]
LOT_STATUSES = ["진행중", "완료", "보류"]

lot_rows    = []
lot_counter = 1

for _, row in work_orders.iterrows():
    n_lots         = int(rng.integers(2, 5))      # 2~4
    scheduled_date = datetime.strptime(row["scheduled_date"], "%Y-%m-%d")

    for _ in range(n_lots):
        lot_date = scheduled_date + timedelta(days=int(rng.integers(0, 3)))
        lot_rows.append({
            "lot_id"    : f"LOT-{lot_counter:04d}",
            "wo_id"     : row["wo_id"],
            "lot_date"  : lot_date.strftime("%Y-%m-%d"),
            "operator"  : str(rng.choice(OPERATORS)),
            "equipment" : row["equipment"],
            "lot_status": str(rng.choice(LOT_STATUSES)),
        })
        lot_counter += 1

lots = pd.DataFrame(lot_rows)
lots.to_csv("data/lots.csv", index=False, encoding="utf-8-sig")
print("=== lots.csv ===")
print(lots.head(3).to_string(index=False))
print(f"shape: {lots.shape}\n")

# ============================================================
# 4. production_records.csv  (n=5 단위 실적 / LOT, SPC 서브그룹)
# ============================================================
DEFECT_CODES = ["정상", "과충진", "미달충진", "캡핑불량", "라벨불량"]
# 85% 정상, 나머지 4개 결함코드에 15% 균등 배분
DEFECT_PROBS = [0.85, 0.0375, 0.0375, 0.0375, 0.0375]

N_PER_LOT   = 5
SPEC_UPPER  = 515.0   # 500 + 15
SPEC_LOWER  = 485.0   # 500 - 15

rec_rows    = []
rec_counter = 1

for _, lot in lots.iterrows():
    lot_date     = datetime.strptime(lot["lot_date"], "%Y-%m-%d")
    current_time = lot_date.replace(hour=8, minute=0, second=0)

    for _ in range(N_PER_LOT):
        fill_vol    = float(rng.normal(500.0, 8.0))   # N(500, 8²)
        defect_code = str(rng.choice(DEFECT_CODES, p=DEFECT_PROBS))

        # 규격 이탈 시 물리적 정합성 보장: 결함코드 강제 설정
        if fill_vol > SPEC_UPPER:
            defect_code = "과충진"
        elif fill_vol < SPEC_LOWER:
            defect_code = "미달충진"

        # LOT 내 순차 타임스탬프 (1~3분 간격)
        current_time += timedelta(seconds=int(rng.integers(60, 181)))

        rec_rows.append({
            "record_id"     : f"REC-{rec_counter:05d}",
            "lot_id"        : lot["lot_id"],
            "fill_volume_ml": round(fill_vol, 2),
            "defect_code"   : defect_code,
            "work_time_sec" : int(rng.integers(30, 91)),   # 30~90 sec
            "timestamp"     : current_time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        rec_counter += 1

production = pd.DataFrame(rec_rows)
production.to_csv("data/production_records.csv", index=False, encoding="utf-8-sig")
print("=== production_records.csv ===")
print(production.head(3).to_string(index=False))
print(f"shape: {production.shape}\n")
