from __future__ import annotations

from .models import HRTorrentState, HRStatus


def should_protect_source_file(state: HRTorrentState) -> bool:
    # 只有 HR ACTIVE / UNKNOWN 的种子保护源文件
    return state.hr_status in {HRStatus.ACTIVE, HRStatus.UNKNOWN}

