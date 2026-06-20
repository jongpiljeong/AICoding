"""
mes_core.py — ㈜진설초해 황칠 충진라인 MES Lite 핵심 모듈
영업관리(수주)·생산관리(작업지시·LOT·실적) 기능 제공
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# 파일별 날짜 컬럼 목록
_DATE_COLS: dict[str, list[str]] = {
    "orders"            : ["order_date"],
    "work_orders"       : ["scheduled_date"],
    "lots"              : ["lot_date"],
    "production_records": ["timestamp"],
}

_STATUS_ORDER = {"대기": 0, "진행": 1, "완료": 2}


# ============================================================
# 1. load_data
# ============================================================
def load_data() -> dict[str, pd.DataFrame]:
    """
    data/ 폴더의 CSV 4종을 읽어 DataFrame dict로 반환한다.

    Returns
    -------
    dict
        키: 'orders' | 'work_orders' | 'lots' | 'production_records'
        값: 해당 pd.DataFrame (날짜 컬럼은 datetime64 변환 완료)

    Raises
    ------
    FileNotFoundError
        data/ 폴더 또는 CSV 파일이 없을 때
    """
    tables: dict[str, pd.DataFrame] = {}

    for name, date_cols in _DATE_COLS.items():
        path = DATA_DIR / f"{name}.csv"
        df = pd.read_csv(path, encoding="utf-8-sig")
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        tables[name] = df

    return tables

# 사용 예시:
# data = load_data()
# df_orders = data["orders"]
# df_wo     = data["work_orders"]


# ============================================================
# 2. get_order_summary
# ============================================================
def get_order_summary(
    df_orders: pd.DataFrame,
    df_work_orders: pd.DataFrame,
) -> pd.DataFrame:
    """
    수주별 생산진행 현황을 집계하여 반환한다.

    생산완료율(%) = (완료 상태 WO의 planned_qty 합 / order_qty) × 100
    완료 WO가 없는 수주는 완료_wo_수=0, 생산완료율=0.0 으로 채운다.

    Parameters
    ----------
    df_orders : pd.DataFrame
        orders.csv 기반 DataFrame
    df_work_orders : pd.DataFrame
        work_orders.csv 기반 DataFrame

    Returns
    -------
    pd.DataFrame
        컬럼: order_id, product_name, order_qty,
              완료_wo_수, 생산완료율(%)
    """
    completed = df_work_orders[df_work_orders["status"] == "완료"]

    # 완료 WO 건수
    cnt = (
        completed.groupby("order_id")
        .size()
        .rename("완료_wo_수")
    )

    # 완료 WO의 planned_qty 합 → 완료율 계산용
    qty = (
        completed.groupby("order_id")["planned_qty"]
        .sum()
        .rename("_완료_qty")
    )

    summary = df_orders[["order_id", "product_name", "order_qty"]].copy()
    summary = summary.merge(cnt, on="order_id", how="left")
    summary = summary.merge(qty, on="order_id", how="left")

    summary["완료_wo_수"]   = summary["완료_wo_수"].fillna(0).astype(int)
    summary["_완료_qty"]    = summary["_완료_qty"].fillna(0)
    summary["생산완료율(%)"] = (
        (summary["_완료_qty"] / summary["order_qty"] * 100)
        .clip(upper=100)
        .round(1)
    )

    return summary.drop(columns=["_완료_qty"]).reset_index(drop=True)

# 사용 예시:
# data    = load_data()
# summary = get_order_summary(data["orders"], data["work_orders"])
# print(summary.head())


# ============================================================
# 3. issue_work_order
# ============================================================
def issue_work_order(df_work_orders: pd.DataFrame, wo_id: str) -> str:
    """
    지정한 작업지시의 상태를 '대기' → '진행'으로 변경하고 CSV에 저장한다.

    Parameters
    ----------
    df_work_orders : pd.DataFrame
        work_orders.csv 기반 DataFrame (in-place 변경됨)
    wo_id : str
        발행할 작업지시 ID (예: "WO-005")

    Returns
    -------
    str
        성공: "작업지시 {wo_id} 발행 완료"
        실패: 오류 사유가 담긴 메시지 문자열
    """
    mask = df_work_orders["wo_id"] == wo_id

    if not mask.any():
        return f"오류: 작업지시 {wo_id} 를 찾을 수 없습니다."

    current = df_work_orders.loc[mask, "status"].iloc[0]

    if current != "대기":
        return f"오류: {wo_id} 는 현재 '{current}' 상태이므로 발행할 수 없습니다."

    df_work_orders.loc[mask, "status"] = "진행"
    df_work_orders.to_csv(DATA_DIR / "work_orders.csv", index=False, encoding="utf-8-sig")

    return f"작업지시 {wo_id} 발행 완료"

# 사용 예시:
# data = load_data()
# msg  = issue_work_order(data["work_orders"], "WO-002")
# print(msg)  # → "작업지시 WO-002 발행 완료"  또는 오류 메시지


# ============================================================
# 4. get_production_status
# ============================================================
def get_production_status(df_work_orders: pd.DataFrame) -> pd.DataFrame:
    """
    작업지시 현황을 상태(대기·진행·완료)별로 집계하여 반환한다.

    Parameters
    ----------
    df_work_orders : pd.DataFrame
        work_orders.csv 기반 DataFrame

    Returns
    -------
    pd.DataFrame
        컬럼: status, 작업지시_건수, planned_qty_합계
        행 순서: 대기 → 진행 → 완료
    """
    agg = (
        df_work_orders.groupby("status", as_index=False)
        .agg(
            작업지시_건수  =("wo_id",       "count"),
            planned_qty_합계=("planned_qty", "sum"),
        )
    )

    # 업무 흐름 순서(대기→진행→완료)로 정렬, 미출현 상태는 자연 정렬
    agg["_sort"] = agg["status"].map(_STATUS_ORDER).fillna(99)
    agg = agg.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    return agg

# 사용 예시:
# data   = load_data()
# status = get_production_status(data["work_orders"])
# print(status)


# ============================================================
# 5. execute_lot_production
# ============================================================
def execute_lot_production(
    df_lots: pd.DataFrame,
    df_production_records: pd.DataFrame,
    lot_id: str,
) -> dict:
    """
    지정 LOT의 생산실적을 집계하여 반환한다.

    Parameters
    ----------
    df_lots : pd.DataFrame
        lots.csv 기반 DataFrame
    df_production_records : pd.DataFrame
        production_records.csv 기반 DataFrame
    lot_id : str
        집계할 LOT ID (예: "LOT-0003")

    Returns
    -------
    dict
        {lot_id, operator, equipment, total_records,
         avg_fill_ml, defect_count, defect_rate_pct, work_time_total_sec}

    Raises
    ------
    ValueError
        lot_id가 df_lots에 존재하지 않을 때
    """
    if not (df_lots["lot_id"] == lot_id).any():
        raise ValueError(f"LOT '{lot_id}' 를 찾을 수 없습니다.")

    lot = df_lots.loc[df_lots["lot_id"] == lot_id].iloc[0]
    recs = df_production_records[df_production_records["lot_id"] == lot_id]

    total = len(recs)
    defect_count = int((recs["defect_code"] != "정상").sum()) if total else 0

    return {
        "lot_id"              : lot_id,
        "operator"            : lot["operator"],
        "equipment"           : lot["equipment"],
        "total_records"       : total,
        "avg_fill_ml"         : round(float(recs["fill_volume_ml"].mean()), 2) if total else None,
        "defect_count"        : defect_count,
        "defect_rate_pct"     : round(defect_count / total * 100, 1) if total else 0.0,
        "work_time_total_sec" : int(recs["work_time_sec"].sum()) if total else 0,
    }

# 사용 예시:
# data   = load_data()
# result = execute_lot_production(data["lots"], data["production_records"], "LOT-0001")
# print(result)


# ============================================================
# 6. get_lot_traceability
# ============================================================
def get_lot_traceability(
    lot_id: str,
    df_orders: pd.DataFrame,
    df_work_orders: pd.DataFrame,
    df_lots: pd.DataFrame,
    df_production_records: pd.DataFrame,
) -> dict:
    """
    LOT ID를 기점으로 수주 → 작업지시 → LOT → 단위실적까지
    전체 이력 연결 정보를 반환한다 (Forward/Backward traceability).

    Parameters
    ----------
    lot_id : str
        추적 기준 LOT ID
    df_orders, df_work_orders, df_lots, df_production_records : pd.DataFrame
        각 테이블 기반 DataFrame

    Returns
    -------
    dict
        {
          "order"         : {order_id, product_name, customer},
          "work_order"    : {wo_id, equipment, planned_qty},
          "lot"           : {lot_id, lot_date, operator},
          "records_count" : int,
          "defect_summary": {"불량코드": 건수, ...},
          "avg_fill_ml"   : float | None
        }

    Raises
    ------
    ValueError
        lot_id가 df_lots에 존재하지 않을 때
    """
    if not (df_lots["lot_id"] == lot_id).any():
        raise ValueError(f"LOT '{lot_id}' 를 찾을 수 없습니다.")

    # LOT → WO → Order 체인 조인
    lot = df_lots.loc[df_lots["lot_id"] == lot_id].iloc[0]

    wo = df_work_orders.loc[df_work_orders["wo_id"] == lot["wo_id"]].iloc[0]

    order = df_orders.loc[df_orders["order_id"] == wo["order_id"]].iloc[0]

    recs = df_production_records[df_production_records["lot_id"] == lot_id]

    # 불량코드별 건수 (빈도 내림차순)
    defect_summary: dict[str, int] = (
        recs["defect_code"].value_counts().to_dict()
        if not recs.empty else {}
    )

    return {
        "order": {
            "order_id"    : order["order_id"],
            "product_name": order["product_name"],
            "customer"    : order["customer"],
        },
        "work_order": {
            "wo_id"      : wo["wo_id"],
            "equipment"  : wo["equipment"],
            "planned_qty": int(wo["planned_qty"]),
        },
        "lot": {
            "lot_id"  : lot_id,
            "lot_date": pd.Timestamp(lot["lot_date"]).strftime("%Y-%m-%d"),
            "operator": lot["operator"],
        },
        "records_count": len(recs),
        "defect_summary": defect_summary,
        "avg_fill_ml"   : round(float(recs["fill_volume_ml"].mean()), 2) if not recs.empty else None,
    }

# 사용 예시:
# data  = load_data()
# trace = get_lot_traceability(
#     "LOT-0005",
#     data["orders"], data["work_orders"], data["lots"], data["production_records"]
# )
# import pprint; pprint.pprint(trace)


# ============================================================
# 7. get_defect_by_process
# ============================================================
def get_defect_by_process(
    df_lots: pd.DataFrame,
    df_production_records: pd.DataFrame,
) -> pd.DataFrame:
    """
    설비(equipment)별 불량코드 발생 건수를 피벗 테이블로 반환한다.
    수동충진기 vs 자동충진기 품질 비교에 활용한다.

    Parameters
    ----------
    df_lots : pd.DataFrame
        lots.csv 기반 DataFrame (equipment 컬럼 포함)
    df_production_records : pd.DataFrame
        production_records.csv 기반 DataFrame

    Returns
    -------
    pd.DataFrame
        index  : equipment
        columns: 불량코드 (정상 우선, 이후 가나다 순) + 합계
        값     : 발생 건수 (0-fill)
    """
    merged = df_production_records.merge(
        df_lots[["lot_id", "equipment"]],
        on="lot_id",
        how="left",
    )

    pivot = (
        merged.groupby(["equipment", "defect_code"])
        .size()
        .unstack(fill_value=0)
    )

    # "정상"을 맨 앞으로, 나머지 결함코드는 가나다 순
    ordered_cols = ["정상"] + sorted(c for c in pivot.columns if c != "정상")
    pivot = pivot[[c for c in ordered_cols if c in pivot.columns]]
    pivot["합계"] = pivot.sum(axis=1)

    return pivot.reset_index()

# 사용 예시:
# data  = load_data()
# pivot = get_defect_by_process(data["lots"], data["production_records"])
# print(pivot.to_string(index=False))


# ============================================================
# 동작 확인용 간이 실행 블록
# ============================================================
if __name__ == "__main__":
    import pprint
    data = load_data()

    SEP = "─" * 60

    # ── Phase 1 ──────────────────────────────────────────────
    print(SEP)
    print("[1] 수주 요약")
    print(SEP)
    print(get_order_summary(data["orders"], data["work_orders"]).to_string(index=False))

    print(f"\n{SEP}")
    print("[2] 생산 현황 (상태별 집계)")
    print(SEP)
    print(get_production_status(data["work_orders"]).to_string(index=False))

    print(f"\n{SEP}")
    print("[3] 작업지시 발행 테스트")
    print(SEP)
    waiting = data["work_orders"][data["work_orders"]["status"] == "대기"]
    if not waiting.empty:
        target = waiting.iloc[0]["wo_id"]
        print(f"  대상 WO : {target}")
        print(" ", issue_work_order(data["work_orders"], target))
        print(" ", issue_work_order(data["work_orders"], target))   # 중복 발행 → 오류
    else:
        print("  대기 상태 작업지시 없음")

    print(f"\n{SEP}")
    print("[4] 발행 후 생산 현황")
    print(SEP)
    print(get_production_status(data["work_orders"]).to_string(index=False))

    # ── Phase 2 ──────────────────────────────────────────────
    sample_lot = data["lots"]["lot_id"].iloc[0]

    print(f"\n{SEP}")
    print(f"[5] LOT 실적 집계  (대상: {sample_lot})")
    print(SEP)
    pprint.pprint(execute_lot_production(
        data["lots"], data["production_records"], sample_lot
    ))

    print(f"\n{SEP}")
    print(f"[6] LOT 추적성 조회  (대상: {sample_lot})")
    print(SEP)
    pprint.pprint(get_lot_traceability(
        sample_lot,
        data["orders"], data["work_orders"],
        data["lots"],   data["production_records"],
    ))

    print(f"\n{SEP}")
    print("[7] 설비별 불량코드 피벗")
    print(SEP)
    print(get_defect_by_process(data["lots"], data["production_records"]).to_string(index=False))

    # ValueError 분기 확인
    print(f"\n{SEP}")
    print("[8] 존재하지 않는 LOT 조회 → ValueError")
    print(SEP)
    try:
        get_lot_traceability(
            "LOT-9999",
            data["orders"], data["work_orders"],
            data["lots"],   data["production_records"],
        )
    except ValueError as e:
        print(f"  ValueError: {e}")
