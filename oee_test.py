from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum


class MachineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class DowntimeEvent:
    start: datetime
    end: datetime
    reason: str


@dataclass
class ProductionRecord:
    timestamp: datetime
    machine_id: str
    produced: int
    defective: int


@dataclass
class Machine:
    machine_id: str
    machine_type: str
    status: MachineStatus
    production_rate: float  # units per hour (ideal)
    oee: float = 0.0
    last_maintenance: datetime = field(default_factory=datetime.now)
    next_maintenance: datetime = field(default_factory=datetime.now)


class ManufacturingExecutionSystem:
    def __init__(self):
        self.machines = {}
        self.downtime_log: List[DowntimeEvent] = []
        self.production_log: List[ProductionRecord] = []

    def add_downtime(self, machine_id: str, start: datetime, end: datetime, reason: str):
        self.downtime_log.append(DowntimeEvent(start=start, end=end, reason=reason))

    def add_production(self, machine_id: str, timestamp: datetime, produced: int, defective: int):
        self.production_log.append(ProductionRecord(
            timestamp=timestamp,
            machine_id=machine_id,
            produced=produced,
            defective=defective
        ))

    def _get_downtime(self, machine_id: str, hours: int) -> float:
        cutoff = datetime.now() - timedelta(hours=hours)
        total_minutes = 0.0
        for event in self.downtime_log:
            if event.start >= cutoff:
                duration = (event.end - event.start).total_seconds() / 60
                total_minutes += duration
        return total_minutes

    def _get_production_count(self, machine_id: str, hours: int) -> int:
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(
            r.produced for r in self.production_log
            if r.machine_id == machine_id and r.timestamp >= cutoff
        )

    def _get_defect_count(self, machine_id: str, hours: int) -> int:
        cutoff = datetime.now() - timedelta(hours=hours)
        return sum(
            r.defective for r in self.production_log
            if r.machine_id == machine_id and r.timestamp >= cutoff
        )

    def calculate_oee(self, machine_id: str, time_period_hours: int = 24) -> dict:
        machine = self.machines.get(machine_id)
        if not machine:
            return {'error': 'Machine not found'}

        planned_time = time_period_hours * 60  # minutes
        downtime = self._get_downtime(machine_id, time_period_hours)
        operating_time = planned_time - downtime
        availability = operating_time / planned_time

        actual_production = self._get_production_count(machine_id, time_period_hours)
        ideal_production = machine.production_rate * time_period_hours
        performance = actual_production / ideal_production if ideal_production > 0 else 0

        defects = self._get_defect_count(machine_id, time_period_hours)
        quality = (actual_production - defects) / actual_production if actual_production > 0 else 0

        oee = availability * performance * quality

        return {
            'machine_id': machine_id,
            'period_hours': time_period_hours,
            'planned_time_min': planned_time,
            'downtime_min': round(downtime, 1),
            'operating_time_min': round(operating_time, 1),
            'ideal_production': ideal_production,
            'actual_production': actual_production,
            'defects': defects,
            'availability': round(availability * 100, 1),
            'performance': round(performance * 100, 1),
            'quality': round(quality * 100, 1),
            'oee': round(oee * 100, 1),
            'world_class_oee': 85.0,
            'assessment': (
                'World Class' if oee * 100 >= 85 else
                'Good' if oee * 100 >= 70 else
                'Average' if oee * 100 >= 50 else
                'Poor'
            )
        }


# ──────────────────────────────────────────
# 실제 데이터 시나리오 설정
# 가정: 8시간 교대 (1-shift), 사출성형 라인 #1
# 이상 생산속도: 120 units/hr
# ──────────────────────────────────────────

mes = ManufacturingExecutionSystem()

# 머신 등록
mes.machines['INJ-001'] = Machine(
    machine_id='INJ-001',
    machine_type='Injection Molder',
    status=MachineStatus.RUNNING,
    production_rate=120.0,
    last_maintenance=datetime.now() - timedelta(days=5),
    next_maintenance=datetime.now() + timedelta(days=25),
)

now = datetime.now()

# 다운타임 이벤트 (최근 8시간 기준)
mes.add_downtime('INJ-001',
    start=now - timedelta(hours=7, minutes=30),
    end=now - timedelta(hours=7),
    reason='금형 교체'
)
mes.add_downtime('INJ-001',
    start=now - timedelta(hours=4, minutes=15),
    end=now - timedelta(hours=3, minutes=50),
    reason='재료 공급 불량'
)
mes.add_downtime('INJ-001',
    start=now - timedelta(hours=1, minutes=10),
    end=now - timedelta(hours=0, minutes=55),
    reason='설비 경보'
)

# 생산 실적 (시간대별)
production_data = [
    # (hours_ago, produced, defective)
    (7.8, 42,  2),   # 금형 교체 직후 안정화 중
    (7.0, 98,  3),
    (6.0, 105, 2),
    (5.0, 112, 1),
    (4.5, 60,  1),   # 재료 불량 직전 감속
    (3.5, 95,  4),   # 재료 불량 직후 재가동
    (2.5, 118, 1),
    (1.5, 72,  2),   # 설비 경보 전후
    (0.5, 110, 0),
]

for hours_ago, produced, defective in production_data:
    mes.add_production(
        'INJ-001',
        timestamp=now - timedelta(hours=hours_ago),
        produced=produced,
        defective=defective
    )

# ──────────────────────────────────────────
# OEE 계산 및 출력
# ──────────────────────────────────────────

result = mes.calculate_oee('INJ-001', time_period_hours=8)

print("=" * 50)
print(f"  OEE 분석 리포트 — {result['machine_id']}")
print("=" * 50)
print(f"  분석 기간       : {result['period_hours']}시간")
print(f"  계획 가동 시간  : {result['planned_time_min']} 분")
print(f"  비가동 시간     : {result['downtime_min']} 분")
print(f"  실 가동 시간    : {result['operating_time_min']} 분")
print()
print(f"  이상 생산량     : {result['ideal_production']:.0f} 개")
print(f"  실제 생산량     : {result['actual_production']} 개")
print(f"  불량품          : {result['defects']} 개")
print()
print(f"  가동률 (A)      : {result['availability']} %")
print(f"  성능률 (P)      : {result['performance']} %")
print(f"  품질률 (Q)      : {result['quality']} %")
print("-" * 50)
print(f"  OEE             : {result['oee']} %")
print(f"  세계 수준 기준  : {result['world_class_oee']} %")
print(f"  평가            : {result['assessment']}")
print("=" * 50)
