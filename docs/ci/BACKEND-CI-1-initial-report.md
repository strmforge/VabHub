============ dev_check_backend: start ============
当前目录: /mnt/f/VabHub项目/VabHub

=== 后端: 测试 (lint/mypy/pytest) ===
============ dev_check_backend: start ============
[info] CWD: /mnt/f/VabHub项目/VabHub/backend
[info] Python: Python 3.11.9
[step] ruff check (app + alembic + scripts + tools) ...
warning: The top-level linter settings are deprecated in favour of their counterparts in the `lint` section. Please update the following options in `ruff.toml`:
  - 'per-file-ignores' -> 'lint.per-file-ignores'
F401 `app.api.ocr` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\api\__init__.py:68:5
   |
66 |     category,  # 分类配置管理
67 |     system_update,  # 系统更新管理
68 |     ocr,  # OCR功能
   |     ^^^
69 |     subscription_refresh,  # 订阅刷新监控
70 |     graphql,  # GraphQL API
   |
help: Use an explicit re-export: `ocr as ocr`

F401 `app.api.tvwall_smart_open` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\api\__init__.py:80:5
   |
78 |     decision,  # 下载决策调试
79 |     intel,  # Local Intel 系统
80 |     tvwall_smart_open,  # 电视墙智能打开 (TVWALL-LOCAL-LIB-PLAY-1)
   |     ^^^^^^^^^^^^^^^^^
81 |     global_rules,  # 全局规则设置 (SETTINGS-RULES-1)API（Phase 6）
82 |     local_intel_admin,
   |
help: Use an explicit re-export: `tvwall_smart_open as tvwall_smart_open`

F401 [*] `typing.Dict` imported but unused
 --> app\api\admin_library_settings.py:8:20
  |
7 | from fastapi import APIRouter, Depends
8 | from typing import Dict, Any
  |                    ^^^^
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\api\admin_library_settings.py:8:26
  |
7 | from fastapi import APIRouter, Depends
8 | from typing import Dict, Any
  |                          ^^^
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\api\admin_tts_settings.py:8:26
   |
 7 | from fastapi import APIRouter, Depends
 8 | from typing import Dict, Any, List, Optional, Tuple
   |                          ^^^
 9 | from collections import defaultdict
10 | from datetime import datetime, timedelta
   |
help: Remove unused import: `typing.Any`

F401 [*] `datetime.timedelta` imported but unused
  --> app\api\admin_tts_settings.py:10:32
   |
 8 | from typing import Dict, Any, List, Optional, Tuple
 9 | from collections import defaultdict
10 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
11 | from loguru import logger
12 | from sqlalchemy import func, select
   |
help: Remove unused import: `datetime.timedelta`

E712 Avoid equality comparisons to `True`; use `AudiobookFile.is_tts_generated:` for truth checks
   --> app\api\admin_tts_settings.py:184:24
    |
182 |                     func.max(AudiobookFile.created_at).label("last_used_at")
183 |                 )
184 |                 .where(AudiobookFile.is_tts_generated == True)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
185 |                 .group_by(AudiobookFile.ebook_id)
186 |             )
    |
help: Replace with `AudiobookFile.is_tts_generated`

E712 Avoid equality comparisons to `True`; use `AudiobookFile.is_tts_generated:` for truth checks
   --> app\api\admin_tts_settings.py:259:13
    |
257 |         # 查询 is_tts_generated=True 的总数
258 |         total_query = select(func.count(AudiobookFile.id)).where(
259 |             AudiobookFile.is_tts_generated == True
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
260 |         )
261 |         total_result = await db.execute(total_query)
    |
help: Replace with `AudiobookFile.is_tts_generated`

E712 Avoid equality comparisons to `True`; use `AudiobookFile.is_tts_generated:` for truth checks
   --> app\api\admin_tts_settings.py:269:13
    |
267 |             func.count(AudiobookFile.id).label("count")
268 |         ).where(
269 |             AudiobookFile.is_tts_generated == True
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
270 |         ).group_by(AudiobookFile.tts_provider)
    |
help: Replace with `AudiobookFile.is_tts_generated`

F401 [*] `typing.Optional` imported but unused
  --> app\api\ai_cleanup_advisor.py:8:20
   |
 6 | """
 7 |
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 |
10 | from fastapi import APIRouter, Depends, HTTPException, status
   |
help: Remove unused import: `typing.Optional`

F401 [*] `typing.Optional` imported but unused
  --> app\api\ai_log_doctor.py:8:20
   |
 6 | """
 7 |
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 |
10 | from fastapi import APIRouter, Depends, HTTPException, status
   |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\api\ai_orchestrator.py:11:36
   |
 9 | from fastapi import APIRouter, Depends, HTTPException, status
10 | from pydantic import BaseModel, Field
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
12 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `typing.Optional` imported but unused
  --> app\api\ai_reading_assistant.py:8:20
   |
 6 | """
 7 |
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 |
10 | from fastapi import APIRouter, Depends, HTTPException, status
   |
help: Remove unused import: `typing.Optional`

F401 [*] `typing.List` imported but unused
  --> app\api\ai_subs_workflow.py:8:31
   |
 6 | """
 7 |
 8 | from typing import Any, Dict, List, Optional
   |                               ^^^^
 9 |
10 | from fastapi import APIRouter, Depends, HTTPException, status
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\api\ai_subs_workflow.py:8:37
   |
 6 | """
 7 |
 8 | from typing import Any, Dict, List, Optional
   |                                     ^^^^^^^^
 9 |
10 | from fastapi import APIRouter, Depends, HTTPException, status
   |
help: Remove unused import

F401 [*] `pydantic.Field` imported but unused
  --> app\api\ai_subs_workflow.py:12:33
   |
10 | from fastapi import APIRouter, Depends, HTTPException, status
11 | from loguru import logger
12 | from pydantic import BaseModel, Field
   |                                 ^^^^^
13 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `pydantic.Field`

F401 [*] `app.schemas.ai_subs_workflow.SubsWorkflowDraft` imported but unused
  --> app\api\ai_subs_workflow.py:19:5
   |
17 | from app.services.ai_subs_workflow import AISubsWorkflowService
18 | from app.schemas.ai_subs_workflow import (
19 |     SubsWorkflowDraft,
   |     ^^^^^^^^^^^^^^^^^
20 |     SubsWorkflowPreviewRequest,
21 |     SubsWorkflowPreviewResponse,
   |
help: Remove unused import

F401 [*] `app.schemas.ai_subs_workflow.SubsTargetMediaType` imported but unused
  --> app\api\ai_subs_workflow.py:24:5
   |
22 |     SubsWorkflowApplyRequest,
23 |     SubsWorkflowApplyResponse,
24 |     SubsTargetMediaType,
   |     ^^^^^^^^^^^^^^^^^^^
25 | )
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
 --> app\api\audiobook.py:6:20
  |
5 | from fastapi import APIRouter, Depends, Query, HTTPException, status
6 | from typing import List, Optional
  |                    ^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select, func, or_, and_
  |
help: Remove unused import: `typing.List`

F401 [*] `sqlalchemy.and_` imported but unused
 --> app\api\audiobook.py:8:43
  |
6 | from typing import List, Optional
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select, func, or_, and_
  |                                           ^^^^
9 | from loguru import logger
  |
help: Remove unused import: `sqlalchemy.and_`

F401 [*] `app.core.schemas.NotFoundResponse` imported but unused
  --> app\api\audiobook.py:15:5
   |
13 |     BaseResponse,
14 |     PaginatedResponse,
15 |     NotFoundResponse,
   |     ^^^^^^^^^^^^^^^^
16 |     success_response,
17 |     error_response
   |
help: Remove unused import: `app.core.schemas.NotFoundResponse`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\api\audiobook.py:46:44
   |
44 |     try:
45 |         # 构建查询
46 |         stmt = select(AudiobookFile).where(AudiobookFile.is_deleted == False)
   |                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
47 |         
48 |         # 关键词搜索（需要 join EBook）
   |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\api\audiobook.py:73:65
   |
72 |         # 总数查询（需要与主查询保持相同的条件）
73 |         count_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
   |                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74 |         has_join = False
   |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:144:13
    |
142 |         stmt = select(AudiobookFile).where(
143 |             AudiobookFile.id == audiobook_id,
144 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
145 |         )
146 |         result = await db.execute(stmt)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:208:65
    |
206 |     try:
207 |         # 总数
208 |         total_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
    |                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
209 |         total_result = await db.execute(total_stmt)
210 |         audiobooks_total = total_result.scalar() or 0
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:214:13
    |
212 |         # 涉及的作品数（去重）
213 |         works_stmt = select(func.count(func.distinct(AudiobookFile.ebook_id))).where(
214 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
215 |         )
216 |         works_result = await db.execute(works_stmt)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:221:13
    |
219 |         # 总大小
220 |         size_stmt = select(func.sum(AudiobookFile.file_size_mb)).where(
221 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
222 |         )
223 |         size_result = await db.execute(size_stmt)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:228:13
    |
226 |         # 总时长
227 |         duration_stmt = select(func.sum(AudiobookFile.duration_seconds)).where(
228 |             AudiobookFile.is_deleted == False,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
229 |             AudiobookFile.duration_seconds.isnot(None)
230 |         )
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook.py:285:13
    |
283 |         stmt = select(AudiobookFile).where(
284 |             AudiobookFile.ebook_id == ebook_id,
285 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
286 |         ).order_by(AudiobookFile.created_at.desc())
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\api\audiobook_center.py:80:20
   |
78 |         audiobook_ebook_stmt = (
79 |             select(AudiobookFile.ebook_id)
80 |             .where(AudiobookFile.is_deleted == False)
   |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
81 |             .distinct()
82 |         )
   |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\audiobook_center.py:168:17
    |
166 |             .where(
167 |                 AudiobookFile.ebook_id.in_(ebook_ids),
168 |                 AudiobookFile.is_deleted == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
169 |             )
170 |             .group_by(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\api\audiobooks.py:62:13
   |
60 |         stmt = select(AudiobookFile).where(
61 |             AudiobookFile.id == file_id,
62 |             AudiobookFile.is_deleted == False
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
63 |         )
64 |         result = await db.execute(stmt)
   |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `datetime.timedelta` imported but unused
  --> app\api\auth.py:9:32
   |
 7 | from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from typing import Optional
11 | from pydantic import BaseModel, EmailStr
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `app.models.backup.BackupRecord` imported but unused
  --> app\api\backup.py:15:31
   |
13 | from app.core.schemas import BaseResponse, success_response, error_response
14 | from app.modules.backup.service import BackupService, BackupConfig
15 | from app.models.backup import BackupRecord
   |                               ^^^^^^^^^^^^
16 | from app.core.config import settings
   |
help: Remove unused import: `app.models.backup.BackupRecord`

F401 [*] `typing.List` imported but unused
 --> app\api\bangumi.py:7:20
  |
6 | from fastapi import APIRouter, HTTPException, Query, status
7 | from typing import List, Optional
  |                    ^^^^
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\api\bangumi.py:7:26
  |
6 | from fastapi import APIRouter, HTTPException, Query, status
7 | from typing import List, Optional
  |                          ^^^^^^^^
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\api\category.py:7:31
  |
6 | from pathlib import Path
7 | from typing import Any, Dict, Optional
  |                               ^^^^^^^^
8 |
9 | from fastapi import APIRouter, Depends, HTTPException, status
  |
help: Remove unused import: `typing.Optional`

F401 [*] `fastapi.Depends` imported but unused
  --> app\api\category.py:9:32
   |
 7 | from typing import Any, Dict, Optional
 8 |
 9 | from fastapi import APIRouter, Depends, HTTPException, status
   |                                ^^^^^^^
10 | from fastapi.responses import FileResponse
11 | from loguru import logger
   |
help: Remove unused import: `fastapi.Depends`

F401 [*] `fastapi.responses.FileResponse` imported but unused
  --> app\api\category.py:10:31
   |
 9 | from fastapi import APIRouter, Depends, HTTPException, status
10 | from fastapi.responses import FileResponse
   |                               ^^^^^^^^^^^^
11 | from loguru import logger
12 | from pydantic import BaseModel
   |
help: Remove unused import: `fastapi.responses.FileResponse`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\api\category.py:13:36
   |
11 | from loguru import logger
12 | from pydantic import BaseModel
13 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
14 |
15 | from app.constants.media_types import is_tv_like
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `app.core.database.get_db` imported but unused
  --> app\api\category.py:16:31
   |
15 | from app.constants.media_types import is_tv_like
16 | from app.core.database import get_db
   |                               ^^^^^^
17 | from app.core.schemas import BaseResponse, error_response, success_response
   |
help: Remove unused import: `app.core.database.get_db`

F401 [*] `typing.List` imported but unused
 --> app\api\charts.py:7:20
  |
6 | from fastapi import APIRouter, Depends, HTTPException, Query, status
7 | from typing import List, Optional
  |                    ^^^^
8 | from pydantic import BaseModel, Field
9 | from datetime import datetime
  |
help: Remove unused import: `typing.List`

F401 [*] `app.models.cloud_storage.CloudStorage` imported but unused
  --> app\api\cloud_storage.py:14:38
   |
12 | from app.core.database import get_db
13 | from app.modules.cloud_storage.service import CloudStorageService
14 | from app.models.cloud_storage import CloudStorage
   |                                      ^^^^^^^^^^^^
15 | from app.core.schemas import (
16 |     BaseResponse,
   |
help: Remove unused import: `app.models.cloud_storage.CloudStorage`

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\cloud_storage_chain.py:7:32
  |
5 | """
6 |
7 | from fastapi import APIRouter, Depends, HTTPException, status
  |                                ^^^^^^^
8 | from typing import List, Optional, Dict, Any
9 | from pydantic import BaseModel
  |
help: Remove unused import: `fastapi.Depends`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\api\config_admin.py:10:36
   |
 8 | from typing import Dict, Any
 9 | from fastapi import APIRouter, Depends, HTTPException, status
10 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
11 |
12 | from app.core.deps import get_db, get_current_user
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `app.core.deps.get_db` imported but unused
  --> app\api\config_admin.py:12:27
   |
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 |
12 | from app.core.deps import get_db, get_current_user
   |                           ^^^^^^
13 | from app.models.user import User
14 | from app.schemas.response import BaseResponse, success_response
   |
help: Remove unused import: `app.core.deps.get_db`

F401 [*] `app.core.config_schema.ConfigValidationResult` imported but unused
  --> app\api\config_admin.py:19:5
   |
17 |     validate_config,
18 |     get_effective_config,
19 |     ConfigValidationResult
   |     ^^^^^^^^^^^^^^^^^^^^^^
20 | )
   |
help: Remove unused import: `app.core.config_schema.ConfigValidationResult`

F401 [*] `fastapi.responses.JSONResponse` imported but unused
  --> app\api\cookiecloud.py:9:31
   |
 7 | import inspect
 8 | from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
 9 | from fastapi.responses import JSONResponse
   |                               ^^^^^^^^^^^^
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 | from typing import Dict, Any, Optional, List
   |
help: Remove unused import: `fastapi.responses.JSONResponse`

F401 [*] `datetime.timedelta` imported but unused
  --> app\api\cookiecloud.py:12:32
   |
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 | from typing import Dict, Any, Optional, List
12 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
13 | import asyncio
14 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `asyncio` imported but unused
  --> app\api\cookiecloud.py:13:8
   |
11 | from typing import Dict, Any, Optional, List
12 | from datetime import datetime, timedelta
13 | import asyncio
   |        ^^^^^^^
14 | from loguru import logger
15 | from pydantic import ValidationError
   |
help: Remove unused import: `asyncio`

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
   --> app\api\cookiecloud.py:399:21
    |
397 |             cookiecloud_sites_result = await db.execute(
398 |                 select(func.count(Site.id)).where(
399 |                     Site.is_active == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^
400 |                     Site.cookie_source == CookieSource.COOKIECLOUD
401 |                 )
    |
help: Replace with `Site.is_active`

F401 [*] `app.core.cache_decorator.cache_key_builder` imported but unused
  --> app\api\dashboard.py:20:38
   |
18 | )
19 | from app.core.cache import get_cache
20 | from app.core.cache_decorator import cache_key_builder
   |                                      ^^^^^^^^^^^^^^^^^
21 |
22 | router = APIRouter()
   |
help: Remove unused import: `app.core.cache_decorator.cache_key_builder`

F401 [*] `typing.List` imported but unused
 --> app\api\directory.py:4:20
  |
2 | 目录配置API端点
3 | """
4 | from typing import List, Optional
  |                    ^^^^
5 | from fastapi import APIRouter, Depends, HTTPException, status
6 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.List`

F821 Undefined name `douban_id`
   --> app\api\douban.py:164:49
    |
162 |         # 使用 douban_id（与 subject_id 相同）
163 |         if normalized_media_type == MEDIA_TYPE_TV:
164 |             detail = await client.get_tv_detail(douban_id)
    |                                                 ^^^^^^^^^
165 |             rating = await client.get_tv_rating(douban_id)
166 |         else:
    |

F821 Undefined name `douban_id`
   --> app\api\douban.py:165:49
    |
163 |         if normalized_media_type == MEDIA_TYPE_TV:
164 |             detail = await client.get_tv_detail(douban_id)
165 |             rating = await client.get_tv_rating(douban_id)
    |                                                 ^^^^^^^^^
166 |         else:
167 |             detail = await client.get_movie_detail(douban_id)
    |

F821 Undefined name `douban_id`
   --> app\api\douban.py:167:52
    |
165 |             rating = await client.get_tv_rating(douban_id)
166 |         else:
167 |             detail = await client.get_movie_detail(douban_id)
    |                                                    ^^^^^^^^^
168 |             rating = await client.get_movie_rating(douban_id)
    |

F821 Undefined name `douban_id`
   --> app\api\douban.py:168:52
    |
166 |         else:
167 |             detail = await client.get_movie_detail(douban_id)
168 |             rating = await client.get_movie_rating(douban_id)
    |                                                    ^^^^^^^^^
169 |         
170 |         # 转换响应格式
    |

F821 Undefined name `douban_id`
   --> app\api\douban.py:172:40
    |
170 |         # 转换响应格式
171 |         detail_response = {
172 |             "id": str(detail.get("id", douban_id)),
    |                                        ^^^^^^^^^
173 |             "title": detail.get("title", ""),
174 |             "original_title": detail.get("original_title"),
    |

F401 [*] `uuid` imported but unused
  --> app\api\download.py:10:8
   |
 8 | from pydantic import BaseModel
 9 | from datetime import datetime
10 | import uuid
   |        ^^^^
11 | from loguru import logger
   |
help: Remove unused import: `uuid`

F401 [*] `sqlalchemy.func` imported but unused
   --> app\api\download.py:111:48
    |
109 |                 from app.core.intel_local.models import HRStatus
110 |                 from app.core.database import AsyncSessionLocal
111 |                 from sqlalchemy import select, func
    |                                                ^^^^
112 |                 from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
113 |                 from datetime import datetime, timedelta
    |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `datetime.timedelta` imported but unused
   --> app\api\download.py:113:48
    |
111 |                 from sqlalchemy import select, func
112 |                 from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
113 |                 from datetime import datetime, timedelta
    |                                                ^^^^^^^^^
114 |                 
115 |                 # 收集所有任务的 site_id 和 torrent_id
    |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.List` imported but unused
  --> app\api\downloader.py:8:20
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import List, Optional, Dict, Any
   |                    ^^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
  --> app\api\downloader.py:8:36
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import List, Optional, Dict, Any
   |                                    ^^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\api\downloader.py:8:42
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import List, Optional, Dict, Any
   |                                          ^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `app.modules.media_renamer.duplicate_detector.DuplicateFile` imported but unused
  --> app\api\duplicate_detection.py:12:77
   |
11 | from app.core.database import get_db
12 | from app.modules.media_renamer.duplicate_detector import DuplicateDetector, DuplicateFile
   |                                                                             ^^^^^^^^^^^^^
13 | from app.core.schemas import (
14 |     BaseResponse,
   |
help: Remove unused import: `app.modules.media_renamer.duplicate_detector.DuplicateFile`

F401 [*] `fastapi.HTTPException` imported but unused
 --> app\api\ebook.py:5:48
  |
3 | """
4 |
5 | from fastapi import APIRouter, Depends, Query, HTTPException, status
  |                                                ^^^^^^^^^^^^^
6 | from typing import List, Optional
7 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `fastapi.status` imported but unused
 --> app\api\ebook.py:5:63
  |
3 | """
4 |
5 | from fastapi import APIRouter, Depends, Query, HTTPException, status
  |                                                               ^^^^^^
6 | from typing import List, Optional
7 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `app.core.schemas.PaginatedResponse` imported but unused
  --> app\api\ebook.py:16:5
   |
14 | from app.core.schemas import (
15 |     BaseResponse,
16 |     PaginatedResponse,
   |     ^^^^^^^^^^^^^^^^^
17 |     NotFoundResponse,
18 |     success_response,
   |
help: Remove unused import: `app.core.schemas.PaginatedResponse`

E712 Avoid equality comparisons to `False`; use `not EBookFile.is_deleted:` for false checks
   --> app\api\ebook.py:137:17
    |
135 |             files_stmt = select(EBookFile).where(
136 |                 EBookFile.ebook_id == ebook.id,
137 |                 EBookFile.is_deleted == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
138 |             ).order_by(EBookFile.created_at.desc())
139 |             files_result = await db.execute(files_stmt)
    |
help: Replace with `not EBookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not EBookFile.is_deleted:` for false checks
   --> app\api\ebook.py:241:61
    |
240 |         # 统计文件数量（未删除的）
241 |         files_stmt = select(func.count(EBookFile.id)).where(EBookFile.is_deleted == False)
    |                                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
242 |         files_result = await db.execute(files_stmt)
243 |         total_files = files_result.scalar() or 0
    |
help: Replace with `not EBookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not EBookFile.is_deleted:` for false checks
   --> app\api\ebook.py:256:68
    |
255 |         # 统计总大小（MB）
256 |         size_stmt = select(func.sum(EBookFile.file_size_mb)).where(EBookFile.is_deleted == False)
    |                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
257 |         size_result = await db.execute(size_stmt)
258 |         total_size_mb = size_result.scalar() or 0.0
    |
help: Replace with `not EBookFile.is_deleted`

F401 [*] `fastapi.HTTPException` imported but unused
 --> app\api\ext_indexer.py:8:32
  |
7 | from typing import Optional
8 | from fastapi import APIRouter, HTTPException
  |                                ^^^^^^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `fastapi.HTTPException`

F401 `external_indexer_engine.core` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\api\ext_indexer.py:70:20
   |
68 |         has_engine = False
69 |         try:
70 |             import external_indexer_engine.core
   |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
71 |             has_engine = True
72 |         except ImportError:
   |
help: Remove unused import: `external_indexer_engine.core`

F401 [*] `typing.Optional` imported but unused
 --> app\api\external_indexer_debug.py:7:20
  |
5 | """
6 |
7 | from typing import Optional
  |                    ^^^^^^^^
8 | from fastapi import APIRouter, Query, HTTPException
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.core.ext_indexer.site_importer.get_site_config` imported but unused
  --> app\api\external_indexer_debug.py:17:5
   |
15 | from app.core.ext_indexer.site_importer import (
16 |     load_all_site_configs,
17 |     get_site_config,
   |     ^^^^^^^^^^^^^^^
18 | )
19 | from app.core.ext_indexer.models import ExternalTorrentResult
   |
help: Remove unused import: `app.core.ext_indexer.site_importer.get_site_config`

F401 [*] `fastapi.responses.StreamingResponse` imported but unused
 --> app\api\file_browser.py:7:45
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Query
7 | from fastapi.responses import FileResponse, StreamingResponse
  |                                             ^^^^^^^^^^^^^^^^^
8 | from typing import List, Optional
9 | from pydantic import BaseModel, Field
  |
help: Remove unused import: `fastapi.responses.StreamingResponse`

F401 [*] `os` imported but unused
  --> app\api\file_browser.py:13:8
   |
11 | from pathlib import Path
12 | import mimetypes
13 | import os
   |        ^^
14 |
15 | from app.core.database import get_db
   |
help: Remove unused import: `os`

F401 [*] `app.modules.media_renamer.organizer.MediaOrganizer` imported but unused
  --> app\api\file_browser.py:19:49
   |
17 | from app.modules.file_browser.service import FileBrowserService
18 | from app.modules.media_renamer.identifier import MediaIdentifier
19 | from app.modules.media_renamer.organizer import MediaOrganizer
   |                                                 ^^^^^^^^^^^^^^
20 | from app.modules.file_operation.transfer_service import TransferService
21 | from app.core.config import settings
   |
help: Remove unused import: `app.modules.media_renamer.organizer.MediaOrganizer`

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\file_cleaner.py:5:32
  |
3 | """
4 |
5 | from fastapi import APIRouter, Depends, HTTPException, status, Query
  |                                ^^^^^^^
6 | from typing import Optional
7 | from pydantic import BaseModel
  |
help: Remove unused import: `fastapi.Depends`

F401 [*] `app.modules.file_cleaner.service.CleanupResult` imported but unused
  --> app\api\file_cleaner.py:11:66
   |
10 | from app.core.schemas import BaseResponse, success_response, error_response
11 | from app.modules.file_cleaner.service import FileCleanerService, CleanupResult
   |                                                                  ^^^^^^^^^^^^^
12 |
13 | router = APIRouter(prefix="/file-cleaner", tags=["文件清理"])
   |
help: Remove unused import: `app.modules.file_cleaner.service.CleanupResult`

F401 [*] `fastapi.responses.JSONResponse` imported but unused
 --> app\api\filter_rule_groups.py:7:31
  |
5 | from typing import Dict, List, Optional
6 | from fastapi import APIRouter, Query, HTTPException
7 | from fastapi.responses import JSONResponse
  |                               ^^^^^^^^^^^^
8 | from pydantic import BaseModel
  |
help: Remove unused import: `fastapi.responses.JSONResponse`

F841 Local variable `service` is assigned to but never used
   --> app\api\filter_rule_groups.py:306:5
    |
304 |     db: DbSessionDep
305 | ):
306 |     service = FilterRuleGroupService(db)
    |     ^^^^^^^
307 |     """
308 |     验证规则组配置
    |
help: Remove assignment to unused variable `service`

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\gateway.py:6:32
  |
4 | """
5 |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Body
  |                                ^^^^^^^
7 | from pydantic import BaseModel
8 | from typing import Optional
  |
help: Remove unused import

F401 [*] `fastapi.Body` imported but unused
 --> app\api\gateway.py:6:64
  |
4 | """
5 |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Body
  |                                                                ^^^^
7 | from pydantic import BaseModel
8 | from typing import Optional
  |
help: Remove unused import

F401 [*] `app.core.database.get_db` imported but unused
  --> app\api\gateway.py:11:31
   |
 9 | from loguru import logger
10 |
11 | from app.core.database import get_db
   |                               ^^^^^^
12 | from app.core.schemas import (
13 |     BaseResponse,
   |
help: Remove unused import: `app.core.database.get_db`

F401 [*] `typing.Any` imported but unused
  --> app\api\global_rules.py:9:26
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select
 9 | from typing import Dict, Any
   |                          ^^^
10 | from datetime import datetime
11 | from loguru import logger
   |
help: Remove unused import: `typing.Any`

F541 [*] f-string without any placeholders
   --> app\api\global_rules.py:438:21
    |
436 |                 updated_by=settings.updated_by
437 |             ),
438 |             message=f"重置全局规则设置成功"
    |                     ^^^^^^^^^^^^^^^^^^^^^^^
439 |         )
    |
help: Remove extraneous `f` prefix

F401 [*] `app.schemas.global_search.GlobalSearchResponse` imported but unused
  --> app\api\global_search.py:11:39
   |
 9 | from app.core.deps import get_db, get_current_user
10 | from app.models.user import User
11 | from app.schemas.global_search import GlobalSearchResponse
   |                                       ^^^^^^^^^^^^^^^^^^^^
12 | from app.schemas.response import BaseResponse, success_response
13 | from app.services.global_search_service import search_all
   |
help: Remove unused import: `app.schemas.global_search.GlobalSearchResponse`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
 --> app\api\graphql\schema.py:9:36
  |
7 | from typing import List, Optional, AsyncIterator
8 | from datetime import datetime
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |                                    ^^^^^^^^^^^^
  |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `fastapi.HTTPException` imported but unused
 --> app\api\health.py:6:32
  |
4 | """
5 |
6 | from fastapi import APIRouter, HTTPException, status
  |                                ^^^^^^^^^^^^^
7 | from fastapi.responses import JSONResponse
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `fastapi.status` imported but unused
 --> app\api\health.py:6:47
  |
4 | """
5 |
6 | from fastapi import APIRouter, HTTPException, status
  |                                               ^^^^^^
7 | from fastapi.responses import JSONResponse
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `app.core.schemas.BaseResponse` imported but unused
  --> app\api\health.py:21:5
   |
20 | from app.core.schemas import (
21 |     BaseResponse,
   |     ^^^^^^^^^^^^
22 |     NotFoundResponse,
23 |     success_response,
   |
help: Remove unused import

F401 [*] `app.core.schemas.NotFoundResponse` imported but unused
  --> app\api\health.py:22:5
   |
20 | from app.core.schemas import (
21 |     BaseResponse,
22 |     NotFoundResponse,
   |     ^^^^^^^^^^^^^^^^
23 |     success_response,
24 |     error_response
   |
help: Remove unused import

F401 [*] `app.core.schemas.success_response` imported but unused
  --> app\api\health.py:23:5
   |
21 |     BaseResponse,
22 |     NotFoundResponse,
23 |     success_response,
   |     ^^^^^^^^^^^^^^^^
24 |     error_response
25 | )
   |
help: Remove unused import

F401 [*] `app.core.schemas.error_response` imported but unused
  --> app\api\health.py:24:5
   |
22 |     NotFoundResponse,
23 |     success_response,
24 |     error_response
   |     ^^^^^^^^^^^^^^
25 | )
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
 --> app\api\hnr.py:6:20
  |
4 | """
5 | from fastapi import APIRouter, Depends, HTTPException, Query, status
6 | from typing import List, Optional
  |                    ^^^^
7 | from pydantic import BaseModel, Field
8 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `app.schemas.home_dashboard.HomeDashboardResponse` imported but unused
  --> app\api\home.py:11:40
   |
 9 | from app.core.deps import get_db, get_current_user
10 | from app.models.user import User
11 | from app.schemas.home_dashboard import HomeDashboardResponse
   |                                        ^^^^^^^^^^^^^^^^^^^^^
12 | from app.schemas.response import BaseResponse, success_response
13 | from app.services.home_dashboard_service import get_home_dashboard
   |
help: Remove unused import: `app.schemas.home_dashboard.HomeDashboardResponse`

F401 [*] `typing.Any` imported but unused
  --> app\api\inbox_dev.py:8:32
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status
 8 | from typing import List, Dict, Any
   |                                ^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import: `typing.Any`

F401 [*] `sqlalchemy.select` imported but unused
  --> app\api\inbox_dev.py:14:24
   |
13 | from sqlalchemy.ext.asyncio import AsyncSession
14 | from sqlalchemy import select, desc
   |                        ^^^^^^
15 |
16 | from app.core.database import get_db
   |
help: Remove unused import

F401 [*] `sqlalchemy.desc` imported but unused
  --> app\api\inbox_dev.py:14:32
   |
13 | from sqlalchemy.ext.asyncio import AsyncSession
14 | from sqlalchemy import select, desc
   |                                ^^^^
15 |
16 | from app.core.database import get_db
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
  --> app\api\intel.py:8:20
   |
 6 | from fastapi import APIRouter, HTTPException, Depends
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import List, Optional
   |                    ^^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `app.core.intel_local.repo.SqlAlchemySiteGuardRepository` imported but unused
  --> app\api\intel.py:15:68
   |
13 | from app.core.intel_local.factory import build_local_intel_engine
14 | from app.core.intel_local.models import HRStatus
15 | from app.core.intel_local.repo import SqlAlchemyHRCasesRepository, SqlAlchemySiteGuardRepository
   |                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.models.intel_local import HRCase, SiteGuardEvent
   |
help: Remove unused import: `app.core.intel_local.repo.SqlAlchemySiteGuardRepository`

F401 [*] `app.models.intel_local.HRCase` imported but unused
  --> app\api\intel.py:16:36
   |
14 | from app.core.intel_local.models import HRStatus
15 | from app.core.intel_local.repo import SqlAlchemyHRCasesRepository, SqlAlchemySiteGuardRepository
16 | from app.models.intel_local import HRCase, SiteGuardEvent
   |                                    ^^^^^^
17 |
18 | router = APIRouter(prefix="/intel", tags=["Local Intel"])
   |
help: Remove unused import

F401 [*] `app.models.intel_local.SiteGuardEvent` imported but unused
  --> app\api\intel.py:16:44
   |
14 | from app.core.intel_local.models import HRStatus
15 | from app.core.intel_local.repo import SqlAlchemyHRCasesRepository, SqlAlchemySiteGuardRepository
16 | from app.models.intel_local import HRCase, SiteGuardEvent
   |                                            ^^^^^^^^^^^^^^
17 |
18 | router = APIRouter(prefix="/intel", tags=["Local Intel"])
   |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
   --> app\api\intel.py:127:40
    |
125 |     """
126 |     try:
127 |         from sqlalchemy import select, or_, desc
    |                                        ^^^
128 |         from app.models.intel_local import InboxEvent as InboxEventModel, SiteGuardEvent as SiteGuardEventModel
129 |         from datetime import datetime
    |
help: Remove unused import: `sqlalchemy.or_`

F541 [*] f-string without any placeholders
   --> app\api\intel.py:193:23
    |
191 |             # 构建标题和消息
192 |             title = f"{event.site}: 站点风控"
193 |             message = f"站点被限流/封禁"
    |                       ^^^^^^^^^^^^^^^^^^
194 |             if event.cause:
195 |                 message = f"{message}，原因: {event.cause}"
    |
help: Remove extraneous `f` prefix

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
   --> app\api\intel.py:240:54
    |
239 |         # 查询数据库中的站点
240 |         result = await db.execute(select(Site).where(Site.is_active == True))
    |                                                      ^^^^^^^^^^^^^^^^^^^^^^
241 |         sites = result.scalars().all()
    |
help: Replace with `Site.is_active`

F401 [*] `datetime.datetime` imported but unused
  --> app\api\library.py:11:22
   |
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, func, desc, or_
11 | from datetime import datetime
   |                      ^^^^^^^^
12 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\library.py:143:29
    |
141 |                         .where(
142 |                             AudiobookFile.ebook_id.in_(ebook_ids),
143 |                             AudiobookFile.is_deleted == False
    |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
144 |                         )
145 |                         .distinct()
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\library.py:261:24
    |
259 |                 select(AudiobookFile, EBook)
260 |                 .join(EBook, AudiobookFile.ebook_id == EBook.id)
261 |                 .where(AudiobookFile.is_deleted == False)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
262 |                 .order_by(desc(AudiobookFile.created_at))
263 |                 .limit(fetch_limit)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\library.py:389:63
    |
387 |     if include_audiobook:
388 |         try:
389 |             stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
    |                                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
390 |             result = await db.execute(stmt)
391 |             total += result.scalar() or 0
    |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `typing.List` imported but unused
  --> app\api\log_center.py:8:30
   |
 6 | from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
 7 | from fastapi.responses import StreamingResponse
 8 | from typing import Optional, List
   |                              ^^^^
 9 | from datetime import datetime, timedelta
10 | from pydantic import BaseModel
   |
help: Remove unused import: `typing.List`

F401 [*] `app.modules.log_center.service.LogLevel` imported but unused
  --> app\api\log_center.py:13:60
   |
11 | from loguru import logger
12 |
13 | from app.modules.log_center.service import get_log_center, LogLevel, LogSource
   |                                                            ^^^^^^^^
14 | from app.core.schemas import (
15 |     BaseResponse,
   |
help: Remove unused import

F401 [*] `app.modules.log_center.service.LogSource` imported but unused
  --> app\api\log_center.py:13:70
   |
11 | from loguru import logger
12 |
13 | from app.modules.log_center.service import get_log_center, LogLevel, LogSource
   |                                                                      ^^^^^^^^^
14 | from app.core.schemas import (
15 |     BaseResponse,
   |
help: Remove unused import

E741 Ambiguous variable name: `l`
  --> app\api\log_center.py:67:51
   |
65 |     filters = {}
66 |     if level:
67 |         filters["level"] = [l.strip().upper() for l in level.split(",")]
   |                                                   ^
68 |     if source:
69 |         filters["source"] = [s.strip().lower() for s in source.split(",")]
   |

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\logs.py:5:32
  |
3 | """
4 |
5 | from fastapi import APIRouter, Depends, HTTPException, status, Query
  |                                ^^^^^^^
6 | from fastapi.responses import FileResponse
7 | from typing import Optional, List
  |
help: Remove unused import: `fastapi.Depends`

F401 [*] `pathlib.Path` imported but unused
  --> app\api\logs.py:10:21
   |
 8 | from pydantic import BaseModel
 9 | from datetime import datetime
10 | from pathlib import Path
   |                     ^^^^
11 | from loguru import logger
   |
help: Remove unused import: `pathlib.Path`

F401 [*] `app.core.config.settings` imported but unused
  --> app\api\logs.py:15:29
   |
13 | from app.core.schemas import BaseResponse, success_response, error_response
14 | from app.modules.log.service import LogService
15 | from app.core.config import settings
   |                             ^^^^^^^^
16 |
17 | router = APIRouter(prefix="/logs", tags=["日志"])
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `app.schemas.manga_download_job.MangaDownloadJobList` imported but unused
  --> app\api\manga_local.py:26:66
   |
24 | )
25 | from app.schemas.manga_import import MangaImportOptions
26 | from app.schemas.manga_download_job import MangaDownloadJobRead, MangaDownloadJobList, MangaDownloadJobSummary
   |                                                                  ^^^^^^^^^^^^^^^^^^^^
27 | from app.services.manga_import_service import (
28 |     import_series_from_remote,
   |
help: Remove unused import: `app.schemas.manga_download_job.MangaDownloadJobList`

F401 [*] `app.services.manga_import_service.download_chapter` imported but unused
  --> app\api\manga_local.py:29:5
   |
27 | from app.services.manga_import_service import (
28 |     import_series_from_remote,
29 |     download_chapter,
   |     ^^^^^^^^^^^^^^^^
30 |     bulk_download_pending_chapters,
31 | )
   |
help: Remove unused import

F401 [*] `app.services.manga_import_service.bulk_download_pending_chapters` imported but unused
  --> app\api\manga_local.py:30:5
   |
28 |     import_series_from_remote,
29 |     download_chapter,
30 |     bulk_download_pending_chapters,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
31 | )
32 | from app.services.manga_download_job_service import MangaDownloadJobService
   |
help: Remove unused import

F401 [*] `app.services.manga_import_service.download_chapter` imported but unused
   --> app\api\manga_local.py:500:55
    |
498 |     """
499 |     try:
500 |         from app.services.manga_import_service import download_chapter
    |                                                       ^^^^^^^^^^^^^^^^
501 |         
502 |         # 获取章节信息
    |
help: Remove unused import: `app.services.manga_import_service.download_chapter`

F401 [*] `sqlalchemy.orm.joinedload` imported but unused
   --> app\api\manga_local.py:703:36
    |
701 |     """
702 |     try:
703 |         from sqlalchemy.orm import joinedload
    |                                    ^^^^^^^^^^
704 |         
705 |         # 计算偏移量
    |
help: Remove unused import: `sqlalchemy.orm.joinedload`

F401 [*] `typing.Optional` imported but unused
 --> app\api\manga_progress.py:4:20
  |
2 | 漫画阅读进度 API
3 | """
4 | from typing import Optional
  |                    ^^^^^^^^
5 | from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam, Query
6 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.schemas.manga_reading_progress.MangaReadingProgressRead` imported but unused
  --> app\api\manga_progress.py:14:5
   |
12 | from app.models.user import User
13 | from app.schemas.manga_reading_progress import (
14 |     MangaReadingProgressRead,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^
15 |     MangaReadingProgressUpdate,
16 |     MangaReadingHistoryItem,
   |
help: Remove unused import

F401 [*] `app.schemas.manga_reading_progress.MangaReadingHistoryItem` imported but unused
  --> app\api\manga_progress.py:16:5
   |
14 |     MangaReadingProgressRead,
15 |     MangaReadingProgressUpdate,
16 |     MangaReadingHistoryItem,
   |     ^^^^^^^^^^^^^^^^^^^^^^^
17 | )
18 | from app.services.manga_progress_service import (
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
 --> app\api\manga_remote.py:4:30
  |
2 | 远程漫画浏览 API（只读，普通用户可访问）
3 | """
4 | from typing import Optional, List
  |                              ^^^^
5 | from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
6 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.List`

F401 [*] `app.core.schemas.error_response` imported but unused
  --> app\api\manga_source_admin.py:11:62
   |
10 | from app.core.database import get_db
11 | from app.core.schemas import BaseResponse, success_response, error_response, PaginatedResponse
   |                                                              ^^^^^^^^^^^^^^
12 | from app.core.dependencies import get_current_user, get_current_admin_user
13 | from app.models.manga_source import MangaSource
   |
help: Remove unused import: `app.core.schemas.error_response`

F401 [*] `app.core.dependencies.get_current_user` imported but unused
  --> app\api\manga_source_admin.py:12:35
   |
10 | from app.core.database import get_db
11 | from app.core.schemas import BaseResponse, success_response, error_response, PaginatedResponse
12 | from app.core.dependencies import get_current_user, get_current_admin_user
   |                                   ^^^^^^^^^^^^^^^^
13 | from app.models.manga_source import MangaSource
14 | from app.models.user import User
   |
help: Remove unused import: `app.core.dependencies.get_current_user`

F401 [*] `sqlalchemy.select` imported but unused
 --> app\api\manga_sync.py:6:24
  |
4 | from fastapi import APIRouter, Depends, HTTPException, status, Path as PathParam, Body
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, func
  |                        ^^^^^^
7 | from loguru import logger
  |
help: Remove unused import: `sqlalchemy.select`

F401 [*] `sqlalchemy.func` imported but unused
   --> app\api\manga_sync.py:122:40
    |
120 |     """
121 |     try:
122 |         from sqlalchemy import select, func, and_
    |                                        ^^^^
123 |         from app.models.user_favorite_media import UserFavoriteMedia
124 |         from app.models.manga_series_local import MangaSeriesLocal
    |
help: Remove unused import: `sqlalchemy.func`

F541 [*] f-string without any placeholders
   --> app\api\manga_sync.py:193:21
    |
191 |         return success_response(
192 |             data=sync_result,
193 |             message=f"批量同步完成"
    |                     ^^^^^^^^^^^^^^^
194 |         )
195 |     except Exception as e:
    |
help: Remove extraneous `f` prefix

F401 [*] `sqlalchemy.update` imported but unused
  --> app\api\media.py:11:32
   |
 9 | from loguru import logger
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 | from sqlalchemy import select, update, delete
   |                                ^^^^^^
12 |
13 | from app.core.config import settings
   |
help: Remove unused import: `sqlalchemy.update`

E722 Do not use bare `except`
   --> app\api\media_identification.py:333:13
    |
331 |             try:
332 |                 start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
333 |             except:
    |             ^^^^^^
334 |                 pass
335 |         if end_date:
    |

E722 Do not use bare `except`
   --> app\api\media_identification.py:338:13
    |
336 |             try:
337 |                 end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
338 |             except:
    |             ^^^^^^
339 |                 pass
    |

F401 [*] `fastapi.File` imported but unused
 --> app\api\media_renamer.py:6:86
  |
4 | """
5 |
6 | from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query, File, UploadFile
  |                                                                                      ^^^^
7 | from typing import List, Optional
8 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `fastapi.UploadFile` imported but unused
 --> app\api\media_renamer.py:6:92
  |
4 | """
5 |
6 | from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query, File, UploadFile
  |                                                                                            ^^^^^^^^^^
7 | from typing import List, Optional
8 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `app.modules.media_renamer.renamer.MediaRenamer` imported but unused
  --> app\api\media_renamer.py:13:47
   |
11 | from app.core.database import get_db
12 | from app.modules.media_renamer.identifier import MediaIdentifier
13 | from app.modules.media_renamer.renamer import MediaRenamer
   |                                               ^^^^^^^^^^^^
14 | from app.modules.media_renamer.organizer import MediaOrganizer
15 | from app.core.schemas import (
   |
help: Remove unused import: `app.modules.media_renamer.renamer.MediaRenamer`

F401 [*] `typing.List` imported but unused
 --> app\api\media_server.py:6:20
  |
5 | from fastapi import APIRouter, Depends, HTTPException, Query, status
6 | from typing import List, Optional
  |                    ^^^^
7 | from pydantic import BaseModel
8 | from datetime import datetime
  |
help: Remove unused import: `typing.List`

F401 [*] `datetime.datetime` imported but unused
 --> app\api\media_server.py:8:22
  |
6 | from typing import List, Optional
7 | from pydantic import BaseModel
8 | from datetime import datetime
  |                      ^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.List` imported but unused
 --> app\api\multimodal.py:7:30
  |
6 | from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
7 | from typing import Optional, List, Dict, Any
  |                              ^^^^
8 | from pydantic import BaseModel, Field
9 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `fastapi.Body` imported but unused
 --> app\api\multimodal_auto_optimization.py:5:63
  |
3 | """
4 |
5 | from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
  |                                                               ^^^^
6 | from typing import Optional, Dict, Any
7 | from loguru import logger
  |
help: Remove unused import: `fastapi.Body`

F401 [*] `datetime.timedelta` imported but unused
 --> app\api\multimodal_history.py:7:32
  |
5 | from fastapi import APIRouter, Depends, HTTPException, Query, status
6 | from typing import Optional
7 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.Optional` imported but unused
 --> app\api\multimodal_optimization.py:7:20
  |
6 | from fastapi import APIRouter, Depends, HTTPException, Query, status
7 | from typing import Optional, List
  |                    ^^^^^^^^
8 | from pydantic import BaseModel, Field
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
   --> app\api\music.py:363:44
    |
361 |     """
362 |     try:
363 |         from sqlalchemy.ext.asyncio import AsyncSession
    |                                            ^^^^^^^^^^^^
364 |         from sqlalchemy import select
365 |         from app.models.music import MusicTrack
    |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

E722 Do not use bare `except`
   --> app\api\music.py:387:13
    |
385 |             try:
386 |                 genre = json.loads(genre)
387 |             except:
    |             ^^^^^^
388 |                 genre = [genre] if genre else []
    |

F401 [*] `sqlalchemy.delete` imported but unused
  --> app\api\music_chart_admin.py:10:38
   |
 8 | from fastapi import APIRouter, Depends, HTTPException, Query
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, func, delete
   |                                      ^^^^^^
11 | from sqlalchemy.orm import selectinload
12 | from datetime import datetime
   |
help: Remove unused import: `sqlalchemy.delete`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\api\music_chart_admin.py:11:28
   |
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, func, delete
11 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
12 | from datetime import datetime
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F401 [*] `datetime.datetime` imported but unused
  --> app\api\music_chart_admin.py:12:22
   |
10 | from sqlalchemy import select, func, delete
11 | from sqlalchemy.orm import selectinload
12 | from datetime import datetime
   |                      ^^^^^^^^
13 |
14 | from app.core.database import get_async_session
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `datetime.datetime` imported but unused
  --> app\api\music_subscription.py:11:22
   |
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, func, and_
11 | from datetime import datetime
   |                      ^^^^^^^^
12 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.schemas.music.SubscriptionRunResult` imported but unused
  --> app\api\music_subscription.py:25:5
   |
23 |     UserMusicSubscriptionRead,
24 |     UserMusicSubscriptionListResponse,
25 |     SubscriptionRunResult,
   |     ^^^^^^^^^^^^^^^^^^^^^
26 |     MusicSubscriptionRunResponse,
27 |     MusicSubscriptionBatchRunResponse,
   |
help: Remove unused import: `app.schemas.music.SubscriptionRunResult`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\api\my_shelf.py:9:44
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status, Query
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, desc, func, and_, or_
   |                                            ^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.and_`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\my_shelf.py:282:17
    |
280 |             .where(
281 |                 AudiobookFile.ebook_id.in_(ebook_ids),
282 |                 AudiobookFile.is_deleted == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
283 |             )
284 |             .group_by(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
    |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `typing.List` imported but unused
  --> app\api\notifications.py:8:20
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status, Query
 8 | from typing import List, Optional
   |                    ^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, func
   |
help: Remove unused import: `typing.List`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications.py:105:17
    |
103 |             .where(
104 |                 UserNotification.user_id == current_user.id,
105 |                 UserNotification.is_read == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
106 |             )
107 |         )
    |
help: Replace with `not UserNotification.is_read`

F401 [*] `typing.List` imported but unused
 --> app\api\notifications_user.py:7:20
  |
5 | """
6 |
7 | from typing import List
  |                    ^^^^
8 | from fastapi import APIRouter, Depends, Query, HTTPException
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.List`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
  --> app\api\notifications_user.py:57:13
   |
55 |         .where(
56 |             UserNotification.user_id == current_user.id,
57 |             UserNotification.is_read == False
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
58 |         )
59 |     )
   |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:119:13
    |
117 |         .where(
118 |             UserNotification.user_id == current_user.id,
119 |             UserNotification.is_read == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
120 |         )
121 |     )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:153:21
    |
151 |                 .where(
152 |                     UserNotification.user_id == current_user.id,
153 |                     UserNotification.is_read == False,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
154 |                     UserNotification.type.in_([t.value for t in category_types])
155 |                 )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:180:13
    |
178 |         .where(
179 |             UserNotification.user_id == current_user.id,
180 |             UserNotification.is_read == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
181 |         )
182 |     )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:198:13
    |
196 |         .where(
197 |             UserNotification.user_id == current_user.id,
198 |             UserNotification.is_read == False,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
199 |             UserNotification.type == "TTS_JOB_FAILED"
200 |         )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:209:13
    |
207 |         .where(
208 |             UserNotification.user_id == current_user.id,
209 |             UserNotification.is_read == False,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
210 |             UserNotification.type.in_(["TTS_JOB_COMPLETED", "AUDIOBOOK_READY"])
211 |         )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:220:13
    |
218 |         .where(
219 |             UserNotification.user_id == current_user.id,
220 |             UserNotification.is_read == False,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
221 |             UserNotification.type == "warning"
222 |         )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:231:13
    |
229 |         .where(
230 |             UserNotification.user_id == current_user.id,
231 |             UserNotification.is_read == False,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
232 |             UserNotification.type.in_(["MANGA_NEW_CHAPTER", "NOVEL_NEW_CHAPTER", "AUDIOBOOK_NEW_TRACK", "SYSTEM_MESSAGE"])
233 |         )
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:261:64
    |
260 |     # 构建查询条件
261 |     conditions = [UserNotification.user_id == current_user.id, UserNotification.is_read == False]
    |                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
262 |     
263 |     if request.ids is not None:
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\api\notifications_user.py:351:13
    |
349 |         .where(
350 |             UserNotification.user_id == current_user.id,
351 |             UserNotification.is_read == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
352 |         )
353 |     )
    |
help: Replace with `not UserNotification.is_read`

F401 [*] `fastapi.Depends` imported but unused
  --> app\api\notify_preferences.py:10:32
   |
 8 | from datetime import datetime, timedelta
 9 | from typing import Optional
10 | from fastapi import APIRouter, Depends, HTTPException
   |                                ^^^^^^^
11 |
12 | from app.core.deps import DbSessionDep, CurrentUserDep
   |
help: Remove unused import: `fastapi.Depends`

F401 [*] `app.models.user.User` imported but unused
  --> app\api\notify_preferences.py:13:29
   |
12 | from app.core.deps import DbSessionDep, CurrentUserDep
13 | from app.models.user import User
   |                             ^^^^
14 | from app.schemas.notify_preferences import (
15 |     UserNotifyPreferenceCreate,
   |
help: Remove unused import: `app.models.user.User`

F401 [*] `app.schemas.notify_preferences.UserNotifyPreferenceCreate` imported but unused
  --> app\api\notify_preferences.py:15:5
   |
13 | from app.models.user import User
14 | from app.schemas.notify_preferences import (
15 |     UserNotifyPreferenceCreate,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^
16 |     UserNotifyPreferenceUpdate,
17 |     UserNotifyPreferenceRead,
   |
help: Remove unused import: `app.schemas.notify_preferences.UserNotifyPreferenceCreate`

F401 [*] `app.schemas.notify_actions.NotificationAction` imported but unused
  --> app\api\notify_test.py:19:5
   |
17 | from app.models.enums.notification_type import NotificationType
18 | from app.schemas.notify_actions import (
19 |     NotificationAction,
   |     ^^^^^^^^^^^^^^^^^^
20 |     NotificationActionType,
21 |     action_open_manga,
   |
help: Remove unused import

F401 [*] `app.schemas.notify_actions.NotificationActionType` imported but unused
  --> app\api\notify_test.py:20:5
   |
18 | from app.schemas.notify_actions import (
19 |     NotificationAction,
20 |     NotificationActionType,
   |     ^^^^^^^^^^^^^^^^^^^^^^
21 |     action_open_manga,
22 |     action_mark_read,
   |
help: Remove unused import

F401 [*] `app.modules.user_notify_channels.base.ChannelCapabilities` imported but unused
  --> app\api\notify_test.py:27:5
   |
25 | from app.modules.user_notify_channels.base import (
26 |     get_capabilities_for_channel_type,
27 |     ChannelCapabilities,
   |     ^^^^^^^^^^^^^^^^^^^
28 | )
29 | from app.services.notify_user_service import notify_user
   |
help: Remove unused import: `app.modules.user_notify_channels.base.ChannelCapabilities`

F821 Undefined name `require_admin`
   --> app\api\notify_test.py:190:34
    |
188 | async def preview_notification(
189 |     event_type: str = "MANGA_UPDATED",
190 |     current_user: User = Depends(require_admin),
    |                                  ^^^^^^^^^^^^^
191 | ):
192 |     """
    |

F541 [*] f-string without any placeholders
   --> app\api\notify_test.py:276:22
    |
274 |     if len(sample["actions"]) > 1:
275 |         other_actions = [a.label for a in sample["actions"][1:]]
276 |         bark_body += f"\n\n其他操作（请在 Web 端进行）：\n• " + "\n• ".join(other_actions)
    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
277 |     
278 |     if len(bark_body) > 1024:
    |
help: Remove extraneous `f` prefix

F821 Undefined name `DbSessionDep`
   --> app\api\notify_test.py:311:9
    |
309 | @router.get("/my_channels")
310 | async def get_my_channels(
311 |     db: DbSessionDep,
    |         ^^^^^^^^^^^^
312 |     current_user: CurrentUserDep,
313 | ):
    |

F821 Undefined name `CurrentUserDep`
   --> app\api\notify_test.py:312:19
    |
310 | async def get_my_channels(
311 |     db: DbSessionDep,
312 |     current_user: CurrentUserDep,
    |                   ^^^^^^^^^^^^^^
313 | ):
314 |     """获取当前用户已配置的通知渠道"""
    |

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\novel_center.py:133:17
    |
131 |             .where(
132 |                 AudiobookFile.ebook_id.in_(ebook_ids),
133 |                 AudiobookFile.is_deleted == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
134 |             )
135 |             .group_by(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
    |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `app.core.schemas.success_response` imported but unused
  --> app\api\novel_demo.py:19:30
   |
18 | from app.core.database import get_db
19 | from app.core.schemas import success_response, error_response
   |                              ^^^^^^^^^^^^^^^^
20 | from app.core.config import settings
21 | from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
   |
help: Remove unused import: `app.core.schemas.success_response`

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\api\novel_inbox.py:9:44
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, func, and_, or_, desc
   |                                            ^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `app.api.auth.oauth2_scheme` imported but unused
  --> app\api\novel_inbox.py:14:26
   |
12 | from app.core.database import get_db
13 | from app.core.config import settings
14 | from app.api.auth import oauth2_scheme
   |                          ^^^^^^^^^^^^^
15 | from app.core.security import decode_access_token
16 | from app.core.dependencies import get_current_admin_user
   |
help: Remove unused import: `app.api.auth.oauth2_scheme`

F401 [*] `app.core.security.decode_access_token` imported but unused
  --> app\api\novel_inbox.py:15:31
   |
13 | from app.core.config import settings
14 | from app.api.auth import oauth2_scheme
15 | from app.core.security import decode_access_token
   |                               ^^^^^^^^^^^^^^^^^^^
16 | from app.core.dependencies import get_current_admin_user
17 | from app.models.user import User
   |
help: Remove unused import: `app.core.security.decode_access_token`

F401 [*] `typing.List` imported but unused
  --> app\api\ocr.py:8:30
   |
 6 | from fastapi import APIRouter, Depends, Query, HTTPException
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, List
   |                              ^^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `typing.List` imported but unused
 --> app\api\player_wall.py:6:20
  |
4 | 提供作品聚合列表，用于海报墙展示
5 | """
6 | from typing import List, Optional
  |                    ^^^^
7 | from fastapi import APIRouter, Depends, HTTPException, status, Query
8 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.List`

F401 [*] `app.models.media.MediaFile` imported but unused
  --> app\api\player_wall.py:16:37
   |
14 | from app.core.security import decode_access_token
15 | from app.models.user import User
16 | from app.models.media import Media, MediaFile
   |                                     ^^^^^^^^^
17 | from app.models.strm import STRMFile
18 | from app.core.schemas import BaseResponse, SuccessResponse, PaginatedResponse
   |
help: Remove unused import: `app.models.media.MediaFile`

F401 [*] `app.models.strm.STRMFile` imported but unused
  --> app\api\player_wall.py:17:29
   |
15 | from app.models.user import User
16 | from app.models.media import Media, MediaFile
17 | from app.models.strm import STRMFile
   |                             ^^^^^^^^
18 | from app.core.schemas import BaseResponse, SuccessResponse, PaginatedResponse
19 | from app.services.player_wall_aggregation_service import PlayerWallAggregationService
   |
help: Remove unused import: `app.models.strm.STRMFile`

F401 [*] `fastapi.Depends` imported but unused
  --> app\api\plugin_admin.py:8:32
   |
 6 | """
 7 |
 8 | from fastapi import APIRouter, Depends, HTTPException
   |                                ^^^^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from loguru import logger
   |
help: Remove unused import: `fastapi.Depends`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\api\plugin_admin.py:9:36
   |
 8 | from fastapi import APIRouter, Depends, HTTPException
 9 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `app.models.user.User` imported but unused
  --> app\api\plugin_admin.py:13:29
   |
12 | from app.core.deps import DbSessionDep, CurrentAdminUserDep
13 | from app.models.user import User
   |                             ^^^^
14 | from app.models.plugin import PluginStatus
15 | from app.schemas.plugin import (
   |
help: Remove unused import: `app.models.user.User`

F401 [*] `typing.Any` imported but unused
  --> app\api\plugin_api.py:9:20
   |
 7 | """
 8 |
 9 | from typing import Any, Callable, Awaitable, Optional
   |                    ^^^
10 | from fastapi import APIRouter, HTTPException, Request
11 | from fastapi.responses import JSONResponse
   |
help: Remove unused import

F401 [*] `typing.Callable` imported but unused
  --> app\api\plugin_api.py:9:25
   |
 7 | """
 8 |
 9 | from typing import Any, Callable, Awaitable, Optional
   |                         ^^^^^^^^
10 | from fastapi import APIRouter, HTTPException, Request
11 | from fastapi.responses import JSONResponse
   |
help: Remove unused import

F401 [*] `typing.Awaitable` imported but unused
  --> app\api\plugin_api.py:9:35
   |
 7 | """
 8 |
 9 | from typing import Any, Callable, Awaitable, Optional
   |                                   ^^^^^^^^^
10 | from fastapi import APIRouter, HTTPException, Request
11 | from fastapi.responses import JSONResponse
   |
help: Remove unused import

F401 [*] `app.core.config.settings` imported but unused
  --> app\api\plugin_hub.py:12:29
   |
10 | from loguru import logger
11 |
12 | from app.core.config import settings, PluginHubSourceConfig
   |                             ^^^^^^^^
13 | from app.core.deps import DbSessionDep, CurrentAdminUserDep
14 | from app.schemas.plugin_hub import (
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `app.schemas.plugin_hub.PluginHubIndexResponse` imported but unused
  --> app\api\plugin_hub.py:16:5
   |
14 | from app.schemas.plugin_hub import (
15 |     RemotePluginWithLocalStatus,
16 |     PluginHubIndexResponse,
   |     ^^^^^^^^^^^^^^^^^^^^^^
17 |     PluginHubSourcePublic,
18 |     PluginHubSourceUpdateRequest,
   |
help: Remove unused import: `app.schemas.plugin_hub.PluginHubIndexResponse`

F401 [*] `app.services.plugin_hub_service.get_plugin_hub_index` imported but unused
  --> app\api\plugin_hub.py:21:5
   |
19 | )
20 | from app.services.plugin_hub_service import (
21 |     get_plugin_hub_index,
   |     ^^^^^^^^^^^^^^^^^^^^
22 |     get_remote_plugin_detail,
23 |     get_plugin_readme,
   |
help: Remove unused import

F401 [*] `app.services.plugin_hub_service.normalize_hub_url` imported but unused
  --> app\api\plugin_hub.py:29:5
   |
27 |     hub_source_to_public,
28 |     public_to_hub_source,
29 |     normalize_hub_url,
   |     ^^^^^^^^^^^^^^^^^
30 |     generate_hub_id_from_url,
31 | )
   |
help: Remove unused import

F401 [*] `app.services.plugin_hub_service.generate_hub_id_from_url` imported but unused
  --> app\api\plugin_hub.py:30:5
   |
28 |     public_to_hub_source,
29 |     normalize_hub_url,
30 |     generate_hub_id_from_url,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^
31 | )
32 | from app.services.plugin_install_service import (
   |
help: Remove unused import

F811 [*] Redefinition of unused `settings` from line 12
  --> app\api\plugin_hub.py:57:33
   |
55 |     返回社区插件相关配置，供前端使用
56 |     """
57 |     from app.core.config import settings
   |                                 ^^^^^^^^ `settings` redefined here
58 |     
59 |     return {
   |
  ::: app\api\plugin_hub.py:12:29
   |
10 | from loguru import logger
11 |
12 | from app.core.config import settings, PluginHubSourceConfig
   |                             -------- previous definition of `settings` here
13 | from app.core.deps import DbSessionDep, CurrentAdminUserDep
14 | from app.schemas.plugin_hub import (
   |
help: Remove definition: `settings`

F541 [*] f-string without any placeholders
   --> app\api\plugin_hub.py:287:13
    |
285 |             "mkdir -p plugins",
286 |             "",
287 |             f"# 3. 克隆插件仓库",
    |             ^^^^^^^^^^^^^^^^^^^^
288 |             f"git clone {plugin.repo} plugins/{plugin.id}",
289 |             "",
    |
help: Remove extraneous `f` prefix

F811 [*] Redefinition of unused `settings` from line 12
   --> app\api\plugin_hub.py:346:33
    |
344 |         HTTPException: 如果社区插件被禁止一键安装
345 |     """
346 |     from app.core.config import settings
    |                                 ^^^^^^^^ `settings` redefined here
347 |     
348 |     # 如果允许社区插件安装，直接返回
    |
   ::: app\api\plugin_hub.py:12:29
    |
 10 | from loguru import logger
 11 |
 12 | from app.core.config import settings, PluginHubSourceConfig
    |                             -------- previous definition of `settings` here
 13 | from app.core.deps import DbSessionDep, CurrentAdminUserDep
 14 | from app.schemas.plugin_hub import (
    |
help: Remove definition: `settings`

F811 [*] Redefinition of unused `json` from line 6
  --> app\api\plugins.py:6:8
   |
 4 | """
 5 |
 6 | import json
   |        ---- previous definition of `json` here
 7 | from pathlib import Path
 8 | from typing import Any, Dict, List, Optional
 9 |
10 | import json
   |        ^^^^ `json` redefined here
11 | from urllib.parse import urlparse
   |
help: Remove definition: `json`

F401 [*] `fastapi.Depends` imported but unused
  --> app\api\plugins.py:14:38
   |
13 | import httpx
14 | from fastapi import APIRouter, Body, Depends, HTTPException, status
   |                                      ^^^^^^^
15 | from loguru import logger
16 | from pydantic import BaseModel
   |
help: Remove unused import: `fastapi.Depends`

F401 [*] `app.core.database.get_db` imported but unused
  --> app\api\plugins.py:18:31
   |
16 | from pydantic import BaseModel
17 |
18 | from app.core.database import get_db
   |                               ^^^^^^
19 | from app.core.plugins.hot_reload import HotReloadManager
20 | from app.core.schemas import BaseResponse, error_response, success_response
   |
help: Remove unused import: `app.core.database.get_db`

F821 Undefined name `PluginMetadata`
   --> app\api\plugins.py:441:70
    |
439 |                 {
440 |                     "id": plugin_name,
441 |                     "name": manager.plugin_metadata.get(plugin_name, PluginMetadata(
    |                                                                      ^^^^^^^^^^^^^^
442 |                         id=plugin_name,
443 |                         name=plugin_name,
    |

F821 Undefined name `PluginMetadata`
   --> app\api\plugins.py:447:73
    |
445 |                         description=f"插件 {plugin_name}"
446 |                     )).name,
447 |                     "version": manager.plugin_metadata.get(plugin_name, PluginMetadata(
    |                                                                         ^^^^^^^^^^^^^^
448 |                         id=plugin_name,
449 |                         name=plugin_name,
    |

F821 Undefined name `PluginMetadata`
   --> app\api\plugins.py:453:77
    |
451 |                         description=""
452 |                     )).version,
453 |                     "description": manager.plugin_metadata.get(plugin_name, PluginMetadata(
    |                                                                             ^^^^^^^^^^^^^^
454 |                         id=plugin_name,
455 |                         name=plugin_name,
    |

F821 Undefined name `settings`
   --> app\api\plugins.py:501:16
    |
499 |     """
500 |     try:
501 |         if not settings.PLUGIN_REMOTE_INSTALL_ENABLED:
    |                ^^^^^^^^
502 |             raise HTTPException(
503 |                 status_code=status.HTTP_403_FORBIDDEN,
    |

F821 Undefined name `settings`
   --> app\api\plugins.py:553:50
    |
551 |             )
552 |
553 |         if not _is_host_allowed(parsed.hostname, settings.PLUGIN_REMOTE_ALLOWED_HOSTS):
    |                                                  ^^^^^^^^
554 |             raise HTTPException(
555 |                 status_code=status.HTTP_403_FORBIDDEN,
    |

F821 Undefined name `settings`
   --> app\api\plugins.py:570:35
    |
568 |                 response.raise_for_status()
569 |                 content = response.content
570 |                 if len(content) > settings.PLUGIN_INSTALL_MAX_BYTES:
    |                                   ^^^^^^^^
571 |                     raise HTTPException(
572 |                         status_code=status.HTTP_400_BAD_REQUEST,
    |

F821 Undefined name `settings`
   --> app\api\plugins.py:575:58
    |
573 |                         detail=error_response(
574 |                             error_code="FILE_TOO_LARGE",
575 |                             error_message=f"插件文件过大，超过限制 {settings.PLUGIN_INSTALL_MAX_BYTES} 字节",
    |                                                                     ^^^^^^^^
576 |                         ).model_dump(),
577 |                     )
    |

F401 [*] `app.modules.media_renamer.quality_comparator.QualityInfo` imported but unused
  --> app\api\quality_comparison.py:12:77
   |
11 | from app.core.database import get_db
12 | from app.modules.media_renamer.quality_comparator import QualityComparator, QualityInfo
   |                                                                             ^^^^^^^^^^^
13 | from app.core.schemas import (
14 |     BaseResponse,
   |
help: Remove unused import: `app.modules.media_renamer.quality_comparator.QualityInfo`

F401 [*] `app.schemas.reading_hub.ReadingOngoingItem` imported but unused
  --> app\api\reading_hub.py:15:5
   |
13 | from app.models.enums.reading_media_type import ReadingMediaType
14 | from app.schemas.reading_hub import (
15 |     ReadingOngoingItem,
   |     ^^^^^^^^^^^^^^^^^^
16 |     ReadingHistoryItem,
17 |     ReadingStats,
   |
help: Remove unused import

F401 [*] `app.schemas.reading_hub.ReadingHistoryItem` imported but unused
  --> app\api\reading_hub.py:16:5
   |
14 | from app.schemas.reading_hub import (
15 |     ReadingOngoingItem,
16 |     ReadingHistoryItem,
   |     ^^^^^^^^^^^^^^^^^^
17 |     ReadingStats,
18 | )
   |
help: Remove unused import

F401 [*] `app.schemas.reading_hub.ReadingStats` imported but unused
  --> app\api\reading_hub.py:17:5
   |
15 |     ReadingOngoingItem,
16 |     ReadingHistoryItem,
17 |     ReadingStats,
   |     ^^^^^^^^^^^^
18 | )
19 | from app.services.reading_hub_service import (
   |
help: Remove unused import

F401 [*] `app.schemas.reading_hub.ReadingActivityItem` imported but unused
  --> app\api\reading_hub.py:25:37
   |
23 |     get_recent_activity,
24 | )
25 | from app.schemas.reading_hub import ReadingActivityItem
   |                                     ^^^^^^^^^^^^^^^^^^^
26 |
27 | router = APIRouter(prefix="/api/reading", tags=["阅读中心"])
   |
help: Remove unused import: `app.schemas.reading_hub.ReadingActivityItem`

F401 [*] `app.core.schemas.PaginatedResponse` imported but unused
  --> app\api\recommendation.py:16:5
   |
14 | from app.core.schemas import (
15 |     BaseResponse,
16 |     PaginatedResponse,
   |     ^^^^^^^^^^^^^^^^^
17 |     NotFoundResponse,
18 |     success_response,
   |
help: Remove unused import

F401 [*] `app.core.schemas.NotFoundResponse` imported but unused
  --> app\api\recommendation.py:17:5
   |
15 |     BaseResponse,
16 |     PaginatedResponse,
17 |     NotFoundResponse,
   |     ^^^^^^^^^^^^^^^^
18 |     success_response,
19 |     error_response
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\api\remote_video_115.py:4:20
  |
2 | 115 远程视频播放 API
3 | """
4 | from typing import Optional
  |                    ^^^^^^^^
5 | from fastapi import APIRouter, Depends, HTTPException, status, Path
6 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.core.schemas.error_response` imported but unused
  --> app\api\remote_video_115.py:18:62
   |
16 | )
17 | from app.modules.remote_playback.remote_115_service import Remote115PlaybackService
18 | from app.core.schemas import BaseResponse, success_response, error_response
   |                                                              ^^^^^^^^^^^^^^
19 |
20 | router = APIRouter()
   |
help: Remove unused import: `app.core.schemas.error_response`

F401 [*] `typing.List` imported but unused
 --> app\api\rsshub.py:7:20
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
7 | from typing import List, Optional
  |                    ^^^^
8 | from pydantic import BaseModel
9 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `typing.Optional` imported but unused
  --> app\api\ruleset.py:8:20
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, Dict, Any
   |                    ^^^^^^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

E722 Do not use bare `except`
  --> app\api\ruleset.py:55:13
   |
53 |             try:
54 |                 rules = json.loads(ruleset_json) if isinstance(ruleset_json, str) else ruleset_json
55 |             except:
   |             ^^^^^^
56 |                 rules = {}
57 |         else:
   |

F401 [*] `typing.List` imported but unused
 --> app\api\scheduler.py:7:20
  |
6 | from fastapi import APIRouter, Depends, HTTPException, Query, status
7 | from typing import List, Dict, Optional
  |                    ^^^^
8 | from pydantic import BaseModel
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
 --> app\api\scheduler.py:7:26
  |
6 | from fastapi import APIRouter, Depends, HTTPException, Query, status
7 | from typing import List, Dict, Optional
  |                          ^^^^
8 | from pydantic import BaseModel
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
  --> app\api\scraper.py:8:30
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, Dict, Any
   |                              ^^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\api\scraper.py:8:36
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, Dict, Any
   |                                    ^^^
 9 | from pydantic import BaseModel
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\api\scraping_switches.py:6:26
  |
4 | """
5 | from fastapi import APIRouter, Depends, HTTPException, status
6 | from typing import Dict, Optional, Any
  |                          ^^^^^^^^
7 | from pydantic import BaseModel
8 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.core.schemas.PaginatedResponse` imported but unused
  --> app\api\search.py:17:5
   |
15 | from app.core.schemas import (
16 |     BaseResponse,
17 |     PaginatedResponse,
   |     ^^^^^^^^^^^^^^^^^
18 |     NotFoundResponse,
19 |     success_response,
   |
help: Remove unused import: `app.core.schemas.PaginatedResponse`

F821 Undefined name `asyncio`
   --> app\api\search.py:388:28
    |
386 |                 search_tasks = []
387 |                 for indexer in selected_indexers:
388 |                     task = asyncio.create_task(
    |                            ^^^^^^^
389 |                         indexer_manager._search_with_timeout(
390 |                             indexer,
    |

F821 Undefined name `asyncio`
   --> app\api\search.py:467:23
    |
465 | …         progress = min(100, int((i + len(batch)) / len(results) * 100)) if results else 100
466 | …         yield f"data: {json.dumps({'type': 'results', 'data': batch, 'index': i, 'total': len(results), 'progress': progress})}\n\n"
467 | …         await asyncio.sleep(0.05)  # 减少延迟，提升响应速度
    |                 ^^^^^^^
468 | …     
469 | …     # 发送完成事件
    |

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\secrets.py:6:32
  |
4 | """
5 |
6 | from fastapi import APIRouter, Depends, HTTPException, status
  |                                ^^^^^^^
7 | from pydantic import BaseModel
8 | from loguru import logger
  |
help: Remove unused import: `fastapi.Depends`

E722 Do not use bare `except`
  --> app\api\secrets.py:73:9
   |
71 |                 douban_api_key = await settings_service.get_setting("DOUBAN_API_KEY", category="advanced_media")
72 |                 douban_api_key_configured = bool(douban_api_key)
73 |         except:
   |         ^^^^^^
74 |             douban_api_key_configured = False
   |

F401 [*] `typing.List` imported but unused
 --> app\api\seeding.py:6:20
  |
5 | from fastapi import APIRouter, Depends, HTTPException, Query, status
6 | from typing import List, Optional
  |                    ^^^^
7 | from pydantic import BaseModel, Field
8 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `pydantic.Field` imported but unused
 --> app\api\seeding.py:7:33
  |
5 | from fastapi import APIRouter, Depends, HTTPException, Query, status
6 | from typing import List, Optional
7 | from pydantic import BaseModel, Field
  |                                 ^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `pydantic.Field`

F401 [*] `fastapi.Depends` imported but unused
  --> app\api\self_check.py:8:32
   |
 6 | """
 7 |
 8 | from fastapi import APIRouter, Depends, HTTPException
   |                                ^^^^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from loguru import logger
   |
help: Remove unused import: `fastapi.Depends`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\api\self_check.py:9:36
   |
 8 | from fastapi import APIRouter, Depends, HTTPException
 9 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `app.modules.safety.models.GlobalSafetySettings` imported but unused
   --> app\api\settings.py:351:47
    |
349 |     try:
350 |         from app.modules.safety.settings import SafetySettingsService
351 |         from app.modules.safety.models import GlobalSafetySettings
    |                                               ^^^^^^^^^^^^^^^^^^^^
352 |         
353 |         safety_service = SafetySettingsService(db)
    |
help: Remove unused import: `app.modules.safety.models.GlobalSafetySettings`

F401 [*] `typing.Optional` imported but unused
 --> app\api\site_ai_adapter.py:7:20
  |
5 | """
6 |
7 | from typing import Optional
  |                    ^^^^^^^^
8 | from fastapi import APIRouter, HTTPException, Depends, status
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.Optional`

F401 [*] `pydantic.HttpUrl` imported but unused
 --> app\api\site_domain.py:8:33
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Query
7 | from typing import List, Optional
8 | from pydantic import BaseModel, HttpUrl
  |                                 ^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `pydantic.HttpUrl`

F841 Local variable `updated_config` is assigned to but never used
  --> app\api\site_domain.py:70:9
   |
68 |     try:
69 |         service = SiteDomainService(db)
70 |         updated_config = await service.update_domain_config(
   |         ^^^^^^^^^^^^^^
71 |             site_id=site_id,
72 |             active_domains=config.active_domains,
   |
help: Remove assignment to unused variable `updated_config`

F841 Local variable `config` is assigned to but never used
   --> app\api\site_domain.py:109:9
    |
107 |     try:
108 |         service = SiteDomainService(db)
109 |         config = await service.add_domain(
    |         ^^^^^^
110 |             site_id=site_id,
111 |             domain=request.domain,
    |
help: Remove assignment to unused variable `config`

F841 Local variable `config` is assigned to but never used
   --> app\api\site_domain.py:138:9
    |
136 |     try:
137 |         service = SiteDomainService(db)
138 |         config = await service.remove_domain(site_id=site_id, domain=domain)
    |         ^^^^^^
139 |         config_info = await service.get_domain_info(site_id)
140 |         return success_response(data=config_info, message="移除成功")
    |
help: Remove assignment to unused variable `config`

F841 Local variable `config` is assigned to but never used
   --> app\api\site_domain.py:164:9
    |
162 |     try:
163 |         service = SiteDomainService(db)
164 |         config = await service.switch_domain(
    |         ^^^^^^
165 |             site_id=site_id,
166 |             domain=domain,
    |
help: Remove assignment to unused variable `config`

F841 Local variable `config` is assigned to but never used
   --> app\api\site_domain.py:270:9
    |
268 |         service = SiteDomainService(db)
269 |         # 使用 switch_domain 方法，它实际上就是设置活动域名
270 |         config = await service.switch_domain(
    |         ^^^^^^
271 |             site_id=site_id,
272 |             domain=domain,
    |
help: Remove assignment to unused variable `config`

F401 [*] `pydantic.BaseModel` imported but unused
 --> app\api\site_manager.py:8:22
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
7 | from typing import List, Optional
8 | from pydantic import BaseModel
  |                      ^^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `pydantic.BaseModel`

F401 [*] `app.schemas.site_manager.SiteBrief` imported but unused
  --> app\api\site_manager.py:20:5
   |
18 | from app.modules.site_manager.service import SiteManagerService
19 | from app.schemas.site_manager import (
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
   |     ^^^^^^^^^
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
   |
help: Remove unused import

F401 [*] `app.schemas.site_manager.SiteDetail` imported but unused
  --> app\api\site_manager.py:20:16
   |
18 | from app.modules.site_manager.service import SiteManagerService
19 | from app.schemas.site_manager import (
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
   |                ^^^^^^^^^^
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
   |
help: Remove unused import

F401 [*] `app.schemas.site_manager.SiteHealthResult` imported but unused
  --> app\api\site_manager.py:21:21
   |
19 | from app.schemas.site_manager import (
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
   |                     ^^^^^^^^^^^^^^^^
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
23 | )
   |
help: Remove unused import

F401 [*] `app.schemas.site_manager.SiteExportItem` imported but unused
  --> app\api\site_manager.py:21:55
   |
19 | from app.schemas.site_manager import (
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
   |                                                       ^^^^^^^^^^^^^^
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
23 | )
   |
help: Remove unused import

F401 [*] `app.schemas.site_manager.ImportResult` imported but unused
  --> app\api\site_manager.py:22:5
   |
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
   |     ^^^^^^^^^^^^
23 | )
   |
help: Remove unused import

F401 [*] `app.schemas.site_manager.BatchHealthCheckResult` imported but unused
  --> app\api\site_manager.py:22:19
   |
20 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
21 |     SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
22 |     ImportResult, BatchHealthCheckResult, HealthStatus, CheckType
   |                   ^^^^^^^^^^^^^^^^^^^^^^
23 | )
   |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `SiteCategory.enabled:` for truth checks
   --> app\api\site_manager.py:389:44
    |
387 |         from app.models.site import SiteCategory
388 |         
389 |         query = select(SiteCategory).where(SiteCategory.enabled == True).order_by(SiteCategory.sort_order)
    |                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
390 |         result = await db.execute(query)
391 |         categories = result.scalars().all()
    |
help: Replace with `SiteCategory.enabled`

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
   --> app\api\site_manager.py:430:59
    |
429 |         # 启用站点数
430 |         enabled_query = select(func.count(Site.id)).where(Site.is_active == True)
    |                                                           ^^^^^^^^^^^^^^^^^^^^^^
431 |         enabled_result = await db.execute(enabled_query)
432 |         enabled_sites = enabled_result.scalar()
    |
help: Replace with `Site.is_active`

F401 [*] `typing.Dict` imported but unused
 --> app\api\site_profile.py:7:30
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Query
7 | from typing import Optional, Dict, Any
  |                              ^^^^
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\api\site_profile.py:7:36
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status, Query
7 | from typing import Optional, Dict, Any
  |                                    ^^^
8 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\api\smart_health.py:7:31
  |
5 | """
6 | from fastapi import APIRouter, Depends
7 | from typing import Dict, Any, Optional, List
  |                               ^^^^^^^^
8 | from datetime import datetime, timedelta
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.timedelta` imported but unused
 --> app\api\smart_health.py:8:32
  |
6 | from fastapi import APIRouter, Depends
7 | from typing import Dict, Any, Optional, List
8 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `datetime.timedelta`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\smart_health.py:150:21
    |
148 |                 .where(
149 |                     AudiobookFile.ebook_id.in_(ebook_ids),
150 |                     AudiobookFile.is_deleted == False
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
151 |                 )
152 |                 .distinct()
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\smart_health.py:605:69
    |
604 |         # Audiobook（文件级，统计 AudiobookFile）
605 |         audiobook_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
    |                                                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
606 |         audiobook_result = await db.execute(audiobook_stmt)
607 |         library_status["counts"]["audiobook"] = audiobook_result.scalar() or 0
    |
help: Replace with `not AudiobookFile.is_deleted`

F401 `sqlalchemy.ext.asyncio.AsyncSession` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> app\api\smart_health.py:678:48
    |
676 |         try:
677 |             # 尝试导入数据库相关模块，检查数据库是否可用
678 |             from sqlalchemy.ext.asyncio import AsyncSession
    |                                                ^^^^^^^^^^^^
679 |             from app.core.database import get_db
680 |             # 简单检查：如果能导入说明数据库配置正常
    |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 `app.core.database.get_db` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> app\api\smart_health.py:679:43
    |
677 |             # 尝试导入数据库相关模块，检查数据库是否可用
678 |             from sqlalchemy.ext.asyncio import AsyncSession
679 |             from app.core.database import get_db
    |                                           ^^^^^^
680 |             # 简单检查：如果能导入说明数据库配置正常
681 |             local_intel_status["db_ready"] = True
    |
help: Remove unused import: `app.core.database.get_db`

F401 [*] `app.models.tts_voice_preset.TTSVoicePreset` imported but unused
   --> app\api\smart_health.py:829:49
    |
827 |     try:
828 |         from app.models.tts_work_profile import TTSWorkProfile
829 |         from app.models.tts_voice_preset import TTSVoicePreset
    |                                                 ^^^^^^^^^^^^^^
830 |         
831 |         # 简化统计：只计算最基础的异常情况
    |
help: Remove unused import: `app.models.tts_voice_preset.TTSVoicePreset`

E712 Avoid equality comparisons to `True`; use `AudiobookFile.is_tts_generated:` for truth checks
   --> app\api\smart_health.py:859:17
    |
857 |             .where(
858 |                 TTSWorkProfile.preset_id.isnot(None),
859 |                 AudiobookFile.is_tts_generated == True
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
860 |             )
861 |             .group_by(TTSWorkProfile.preset_id)
    |
help: Replace with `AudiobookFile.is_tts_generated`

F401 [*] `typing.List` imported but unused
  --> app\api\storage.py:8:30
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, Query
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, List
   |                              ^^^^
 9 | from pydantic import BaseModel
10 | from pathlib import Path
   |
help: Remove unused import: `typing.List`

F401 [*] `fastapi.responses.JSONResponse` imported but unused
  --> app\api\storage.py:20:31
   |
18 | from app.modules.cloud_storage.service import CloudStorageService
19 | from fastapi import status
20 | from fastapi.responses import JSONResponse
   |                               ^^^^^^^^^^^^
21 |
22 | router = APIRouter()
   |
help: Remove unused import: `fastapi.responses.JSONResponse`

F401 [*] `datetime.datetime` imported but unused
  --> app\api\storage_monitor.py:9:22
   |
 7 | from typing import Optional, List
 8 | from pydantic import BaseModel, Field
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 |
11 | from app.core.database import get_db
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.modules.strm.config.STRMConfig` imported but unused
   --> app\api\strm.py:776:45
    |
774 |     try:
775 |         from app.core.schemas import success_response
776 |         from app.modules.strm.config import STRMConfig
    |                                             ^^^^^^^^^^
777 |         from app.modules.strm.file_operation_mode import STRMSyncConfig
778 |         from app.modules.strm.sync_manager import STRMSyncManager
    |
help: Remove unused import: `app.modules.strm.config.STRMConfig`

F401 [*] `app.modules.strm.config.STRMConfig` imported but unused
   --> app\api\strm.py:858:45
    |
856 |     try:
857 |         from app.core.schemas import success_response
858 |         from app.modules.strm.config import STRMConfig
    |                                             ^^^^^^^^^^
859 |         from app.modules.strm.file_operation_mode import STRMSyncConfig
860 |         from app.modules.strm.sync_manager import STRMSyncManager
    |
help: Remove unused import: `app.modules.strm.config.STRMConfig`

F401 [*] `app.modules.strm.config.STRMConfig` imported but unused
   --> app\api\strm.py:943:45
    |
941 |     try:
942 |         from app.core.schemas import success_response
943 |         from app.modules.strm.config import STRMConfig
    |                                             ^^^^^^^^^^
944 |         from app.modules.strm.file_operation_mode import STRMSyncConfig
945 |         from app.modules.strm.sync_manager import STRMSyncManager
    |
help: Remove unused import: `app.modules.strm.config.STRMConfig`

E722 Do not use bare `except`
   --> app\api\subscription.py:504:13
    |
502 |             try:
503 |                 await service.delete_subscription(temp_subscription.id)
504 |             except:
    |             ^^^^^^
505 |                 pass
506 |             raise e
    |

F401 [*] `fastapi.Query` imported but unused
 --> app\api\subscription_defaults.py:6:32
  |
5 | from typing import Dict, List, Optional
6 | from fastapi import APIRouter, Query, HTTPException
  |                                ^^^^^
7 | from fastapi.responses import JSONResponse
8 | from pydantic import BaseModel
  |
help: Remove unused import: `fastapi.Query`

F401 [*] `fastapi.responses.JSONResponse` imported but unused
 --> app\api\subscription_defaults.py:7:31
  |
5 | from typing import Dict, List, Optional
6 | from fastapi import APIRouter, Query, HTTPException
7 | from fastapi.responses import JSONResponse
  |                               ^^^^^^^^^^^^
8 | from pydantic import BaseModel
  |
help: Remove unused import: `fastapi.responses.JSONResponse`

F401 [*] `app.modules.subscription.defaults.DefaultSubscriptionConfig` imported but unused
  --> app\api\subscription_defaults.py:13:5
   |
11 | from app.core.schemas import BaseResponse
12 | from app.modules.subscription.defaults import (
13 |     DefaultSubscriptionConfig,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^
14 |     DefaultSubscriptionConfigService
15 | )
   |
help: Remove unused import: `app.modules.subscription.defaults.DefaultSubscriptionConfig`

F401 [*] `typing.List` imported but unused
  --> app\api\subscription_refresh.py:8:30
   |
 6 | from fastapi import APIRouter, Depends, Query, HTTPException
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, List
   |                              ^^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `typing.List` imported but unused
 --> app\api\subtitle.py:7:20
  |
6 | from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
7 | from typing import List, Optional
  |                    ^^^^
8 | from pydantic import BaseModel
9 | from datetime import datetime
  |
help: Remove unused import: `typing.List`

E402 Module level import not at top of file
  --> app\api\system_health.py:86:1
   |
84 | # ============== 磁盘监控配置 (OPS-2D) ==============
85 |
86 | from app.schemas.disk_monitor import DiskPathConfig, DiskMonitorConfig
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
87 | from app.services.health_checks import check_disks_multi
   |

E402 Module level import not at top of file
  --> app\api\system_health.py:87:1
   |
86 | from app.schemas.disk_monitor import DiskPathConfig, DiskMonitorConfig
87 | from app.services.health_checks import check_disks_multi
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
88 |
89 | # 简单的内存存储，生产环境应该使用数据库或配置文件
   |

E722 Do not use bare `except`
   --> app\api\system_settings.py:207:17
    |
205 |                 try:
206 |                     env_data.SECURITY_IMAGE_DOMAINS = json.loads(security_domains)
207 |                 except:
    |                 ^^^^^^
208 |                     env_data.SECURITY_IMAGE_DOMAINS = [security_domains]
209 |             else:
    |

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\system_update.py:6:55
  |
4 | """
5 |
6 | from fastapi import APIRouter, HTTPException, status, Depends, Body
  |                                                       ^^^^^^^
7 | from typing import Optional, Dict, Any, List
8 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `fastapi.Body` imported but unused
 --> app\api\system_update.py:6:64
  |
4 | """
5 |
6 | from fastapi import APIRouter, HTTPException, status, Depends, Body
  |                                                                ^^^^
7 | from typing import Optional, Dict, Any, List
8 | from pydantic import BaseModel
  |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
 --> app\api\system_update.py:7:30
  |
6 | from fastapi import APIRouter, HTTPException, status, Depends, Body
7 | from typing import Optional, Dict, Any, List
  |                              ^^^^
8 | from pydantic import BaseModel
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\api\system_update.py:7:36
  |
6 | from fastapi import APIRouter, HTTPException, status, Depends, Body
7 | from typing import Optional, Dict, Any, List
  |                                    ^^^
8 | from pydantic import BaseModel
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `app.core.database.get_db` imported but unused
  --> app\api\system_update.py:11:31
   |
 9 | from loguru import logger
10 |
11 | from app.core.database import get_db
   |                               ^^^^^^
12 | from app.modules.system.update_manager import UpdateManager, UpdateMode
13 | from app.core.schemas import (
   |
help: Remove unused import: `app.core.database.get_db`

F821 Undefined name `DeploymentType`
   --> app\api\system_update.py:242:39
    |
241 |         # 执行重启（根据部署方式）
242 |         if manager.deployment_type == DeploymentType.DOCKER:
    |                                       ^^^^^^^^^^^^^^
243 |             # Docker: 重启容器
244 |             container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
    |

F821 Undefined name `os`
   --> app\api\system_update.py:244:30
    |
242 |         if manager.deployment_type == DeploymentType.DOCKER:
243 |             # Docker: 重启容器
244 |             container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
    |                              ^^
245 |             result = await asyncio.create_subprocess_exec(
246 |                 "docker", "restart", container_name,
    |

F821 Undefined name `asyncio`
   --> app\api\system_update.py:245:28
    |
243 |             # Docker: 重启容器
244 |             container_name = os.getenv("CONTAINER_NAME", "vabhub-backend")
245 |             result = await asyncio.create_subprocess_exec(
    |                            ^^^^^^^
246 |                 "docker", "restart", container_name,
247 |                 stdout=asyncio.subprocess.PIPE,
    |

F821 Undefined name `asyncio`
   --> app\api\system_update.py:247:24
    |
245 |             result = await asyncio.create_subprocess_exec(
246 |                 "docker", "restart", container_name,
247 |                 stdout=asyncio.subprocess.PIPE,
    |                        ^^^^^^^
248 |                 stderr=asyncio.subprocess.PIPE
249 |             )
    |

F821 Undefined name `asyncio`
   --> app\api\system_update.py:248:24
    |
246 |                 "docker", "restart", container_name,
247 |                 stdout=asyncio.subprocess.PIPE,
248 |                 stderr=asyncio.subprocess.PIPE
    |                        ^^^^^^^
249 |             )
250 |             await result.wait()
    |

F401 [*] `fastapi.status` imported but unused
 --> app\api\task_center.py:6:63
  |
4 | """
5 | import logging
6 | from fastapi import APIRouter, Depends, Query, HTTPException, status
  |                                                               ^^^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `fastapi.status`

F401 [*] `app.schemas.task_center.TaskCenterListResponse` imported but unused
  --> app\api\task_center.py:11:37
   |
 9 | from app.core.deps import get_db, get_current_user
10 | from app.models.user import User
11 | from app.schemas.task_center import TaskCenterListResponse
   |                                     ^^^^^^^^^^^^^^^^^^^^^^
12 | from app.schemas.response import BaseResponse, success_response
13 | from app.services.task_center_service import list_tasks
   |
help: Remove unused import: `app.schemas.task_center.TaskCenterListResponse`

F811 Redefinition of unused `status` from line 6
  --> app\api\task_center.py:24:5
   |
22 |     media_type: str | None = Query(None, description="媒体类型过滤"),
23 |     kind: str | None = Query(None, description="任务类型过滤"),
24 |     status: str | None = Query(None, description="状态过滤"),
   |     ^^^^^^ `status` redefined here
25 |     page: int = Query(1, ge=1, description="页码"),
26 |     page_size: int = Query(50, ge=1, le=100, description="每页数量"),
   |
  ::: app\api\task_center.py:6:63
   |
 4 | """
 5 | import logging
 6 | from fastapi import APIRouter, Depends, Query, HTTPException, status
   |                                                               ------ previous definition of `status` here
 7 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove definition: `status`

F401 [*] `typing.List` imported but unused
  --> app\api\tasks.py:8:30
   |
 6 | from fastapi import APIRouter, Depends, HTTPException, Query, status
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from typing import Optional, List
   |                              ^^^^
 9 | from pydantic import BaseModel
10 | from datetime import datetime
   |
help: Remove unused import: `typing.List`

F841 Local variable `service` is assigned to but never used
   --> app\api\transfer_history.py:202:9
    |
200 |     """
201 |     try:
202 |         service = TransferHistoryService(db)
    |         ^^^^^^^
203 |         
204 |         # 查询历史记录
    |
help: Remove assignment to unused variable `service`

F841 Local variable `service` is assigned to but never used
   --> app\api\transfer_history.py:252:9
    |
250 |     """
251 |     try:
252 |         service = TransferHistoryService(db)
    |         ^^^^^^^
253 |         
254 |         # 1. 读取原始 TransferHistory 记录
    |
help: Remove assignment to unused variable `service`

F401 [*] `app.models.ebook.EBook` imported but unused
  --> app\api\tts_jobs.py:16:30
   |
14 | from app.core.deps import DbSessionDep
15 | from app.models.tts_job import TTSJob
16 | from app.models.ebook import EBook
   |                              ^^^^^
17 | from app.schemas.tts import TTSJobResponse, RunBatchJobsRequest, TTSBatchJobsResponse
18 | from app.modules.tts.job_service import (
   |
help: Remove unused import: `app.models.ebook.EBook`

F401 [*] `os` imported but unused
 --> app\api\tts_playground.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import uuid
9 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `typing.Optional` imported but unused
  --> app\api\tts_playground.py:11:20
   |
 9 | from pathlib import Path
10 | from datetime import datetime
11 | from typing import Optional
   |                    ^^^^^^^^
12 | from fastapi import APIRouter, Depends, HTTPException, status
13 | from fastapi.responses import StreamingResponse, FileResponse
   |
help: Remove unused import: `typing.Optional`

F401 [*] `fastapi.responses.StreamingResponse` imported but unused
  --> app\api\tts_playground.py:13:31
   |
11 | from typing import Optional
12 | from fastapi import APIRouter, Depends, HTTPException, status
13 | from fastapi.responses import StreamingResponse, FileResponse
   |                               ^^^^^^^^^^^^^^^^^
14 | from sqlalchemy.ext.asyncio import AsyncSession
15 | from sqlalchemy import select
   |
help: Remove unused import: `fastapi.responses.StreamingResponse`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\api\tts_user_flow.py:10:28
   |
 8 | from fastapi import APIRouter, HTTPException, status, Query
 9 | from sqlalchemy import select, desc, func
10 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
11 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

E712 Avoid equality comparisons to `True`; use `AudiobookFile.is_tts_generated:` for truth checks
   --> app\api\tts_user_flow.py:136:16
    |
134 |         select(func.count(AudiobookFile.id))
135 |         .where(AudiobookFile.ebook_id == ebook_id)
136 |         .where(AudiobookFile.is_tts_generated == True)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
137 |     )
138 |     has_tts_audiobook = (audiobook_result.scalar() or 0) > 0
    |
help: Replace with `AudiobookFile.is_tts_generated`

F401 [*] `typing.Optional` imported but unused
 --> app\api\tts_voice_presets.py:8:26
  |
7 | from fastapi import APIRouter, Depends, HTTPException, Path as PathParam
8 | from typing import List, Optional
  |                          ^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

E712 Avoid equality comparisons to `True`; use `TTSVoicePreset.is_default:` for truth checks
   --> app\api\tts_voice_presets.py:117:24
    |
115 |                 select(TTSVoicePreset)
116 |                 .where(TTSVoicePreset.id != preset.id)
117 |                 .where(TTSVoicePreset.is_default == True)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
118 |             )
119 |             for other in other_defaults_result.scalars().all():
    |
help: Replace with `TTSVoicePreset.is_default`

E712 Avoid equality comparisons to `True`; use `TTSVoicePreset.is_default:` for truth checks
   --> app\api\tts_voice_presets.py:138:24
    |
136 |             other_defaults_result = await db.execute(
137 |                 select(TTSVoicePreset)
138 |                 .where(TTSVoicePreset.is_default == True)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
139 |             )
140 |             for other in other_defaults_result.scalars().all():
    |
help: Replace with `TTSVoicePreset.is_default`

F401 [*] `app.schemas.tts.TTSWorkBatchPreviewItem` imported but unused
  --> app\api\tts_work_batch.py:18:5
   |
16 |     TTSWorkBatchFilter,
17 |     TTSWorkBatchPreviewResponse,
18 |     TTSWorkBatchPreviewItem,
   |     ^^^^^^^^^^^^^^^^^^^^^^^
19 |     ApplyTTSWorkPresetRequest,
20 |     ApplyTTSWorkPresetResult
   |
help: Remove unused import: `app.schemas.tts.TTSWorkBatchPreviewItem`

F401 [*] `app.services.media_library_jump.MediaLibraryJump` imported but unused
  --> app\api\tvwall_smart_open.py:15:71
   |
13 | from app.core.config import Settings, get_settings
14 | from app.core.network_context import resolve_network_context, NetworkContext
15 | from app.services.media_library_jump import build_media_library_jump, MediaLibraryJump
   |                                                                       ^^^^^^^^^^^^^^^^
16 | from app.core.database import get_db
17 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `app.services.media_library_jump.MediaLibraryJump`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
   --> app\api\upload.py:298:36
    |
296 |     try:
297 |         from sqlalchemy import select
298 |         from sqlalchemy.orm import selectinload
    |                                    ^^^^^^^^^^^^
299 |         
300 |         result = await db.execute(
    |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\api\user_audiobooks.py:9:32
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, func
   |                                ^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\api\user_audiobooks.py:94:13
   |
92 |         files_stmt = select(AudiobookFile).where(
93 |             AudiobookFile.ebook_id == ebook_id,
94 |             AudiobookFile.is_deleted == False
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
95 |         ).order_by(AudiobookFile.id)  # 按 ID 排序，后续可以改为按 track_number
   |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\user_audiobooks.py:200:13
    |
198 |             AudiobookFile.id == req.audiobook_file_id,
199 |             AudiobookFile.ebook_id == ebook_id,
200 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
201 |         )
202 |         file_result = await db.execute(file_stmt)
    |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `app.core.version.APP_NAME` imported but unused
  --> app\api\version.py:10:48
   |
 8 | from typing import Optional
 9 |
10 | from app.core.version import get_version_info, APP_NAME, APP_VERSION
   |                                                ^^^^^^^^
11 | from app.core.config import settings
   |
help: Remove unused import

F401 [*] `app.core.version.APP_VERSION` imported but unused
  --> app\api\version.py:10:58
   |
 8 | from typing import Optional
 9 |
10 | from app.core.version import get_version_info, APP_NAME, APP_VERSION
   |                                                          ^^^^^^^^^^^
11 | from app.core.config import settings
   |
help: Remove unused import

F401 [*] `sqlalchemy.delete` imported but unused
 --> app\api\video_progress.py:8:32
  |
6 | from fastapi import APIRouter, Depends, HTTPException, Query
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select, delete, func
  |                                ^^^^^^
9 | from typing import List, Optional
  |
help: Remove unused import: `sqlalchemy.delete`

F401 [*] `typing.List` imported but unused
  --> app\api\video_progress.py:9:20
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, delete, func
 9 | from typing import List, Optional
   |                    ^^^^
10 |
11 | from app.core.database import get_db
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\api\video_progress.py:9:26
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, delete, func
 9 | from typing import List, Optional
   |                          ^^^^^^^^
10 |
11 | from app.core.database import get_db
   |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `UserVideoProgress.is_finished:` for truth checks
   --> app\api\video_progress.py:184:32
    |
183 |         if only_finished:
184 |             stmt = stmt.filter(UserVideoProgress.is_finished == True)
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
185 |         
186 |         # 获取总数
    |
help: Replace with `UserVideoProgress.is_finished`

F401 [*] `fastapi.Depends` imported but unused
 --> app\api\websocket.py:6:64
  |
4 | """
5 |
6 | from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
  |                                                                ^^^^^^^
7 | from typing import List, Dict, Any
8 | import json
  |
help: Remove unused import: `fastapi.Depends`

E402 Module level import not at top of file
  --> app\api\websocket.py:21:1
   |
19 | logger = getattr(loguru_logger, "bind", lambda **_: loguru_logger)(module="websocket")
20 |
21 | from app.core.database import get_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from app.modules.dashboard.service import DashboardService
23 | from app.modules.download.service import DownloadService
   |

F401 [*] `app.core.database.get_db` imported but unused
  --> app\api\websocket.py:21:31
   |
19 | logger = getattr(loguru_logger, "bind", lambda **_: loguru_logger)(module="websocket")
20 |
21 | from app.core.database import get_db
   |                               ^^^^^^
22 | from app.modules.dashboard.service import DashboardService
23 | from app.modules.download.service import DownloadService
   |
help: Remove unused import: `app.core.database.get_db`

E402 Module level import not at top of file
  --> app\api\websocket.py:22:1
   |
21 | from app.core.database import get_db
22 | from app.modules.dashboard.service import DashboardService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 | from app.modules.download.service import DownloadService
   |

E402 Module level import not at top of file
  --> app\api\websocket.py:23:1
   |
21 | from app.core.database import get_db
22 | from app.modules.dashboard.service import DashboardService
23 | from app.modules.download.service import DownloadService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
24 |
25 | router = APIRouter()
   |

F401 [*] `app.modules.download.service.DownloadService` imported but unused
  --> app\api\websocket.py:23:42
   |
21 | from app.core.database import get_db
22 | from app.modules.dashboard.service import DashboardService
23 | from app.modules.download.service import DownloadService
   |                                          ^^^^^^^^^^^^^^^
24 |
25 | router = APIRouter()
   |
help: Remove unused import: `app.modules.download.service.DownloadService`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\api\work.py:10:37
   |
 8 | from typing import List
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, or_, and_
   |                                     ^^^^
11 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.and_`

E712 Avoid equality comparisons to `False`; use `not EBookFile.is_deleted:` for false checks
  --> app\api\work.py:76:13
   |
74 |         ebook_files_stmt = select(EBookFile).where(
75 |             EBookFile.ebook_id == ebook_id,
76 |             EBookFile.is_deleted == False
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
77 |         ).order_by(EBookFile.created_at.desc())
78 |         ebook_files_result = await db.execute(ebook_files_stmt)
   |
help: Replace with `not EBookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
   --> app\api\work.py:113:13
    |
111 |         audiobook_stmt = select(AudiobookFile).where(
112 |             AudiobookFile.ebook_id == ebook_id,
113 |             AudiobookFile.is_deleted == False
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
114 |         ).order_by(AudiobookFile.created_at.desc())
115 |         audiobook_result = await db.execute(audiobook_stmt)
    |
help: Replace with `not AudiobookFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not ComicFile.is_deleted:` for false checks
   --> app\api\work.py:156:21
    |
154 |                 include_comic_file_stmt = select(ComicFile).where(
155 |                     ComicFile.comic_id.in_(include_comic_ids_list),
156 |                     ComicFile.is_deleted == False
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
157 |                 ).order_by(ComicFile.created_at.desc())
158 |                 include_comic_file_result = await db.execute(include_comic_file_stmt)
    |
help: Replace with `not ComicFile.is_deleted`

E712 Avoid equality comparisons to `False`; use `not ComicFile.is_deleted:` for false checks
   --> app\api\work.py:197:25
    |
195 |                     comic_file_stmt = select(ComicFile).where(
196 |                         ComicFile.comic_id.in_(filtered_comic_ids),
197 |                         ComicFile.is_deleted == False
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
198 |                     ).order_by(ComicFile.created_at.desc())
199 |                     comic_file_result = await db.execute(comic_file_stmt)
    |
help: Replace with `not ComicFile.is_deleted`

F401 [*] `typing.List` imported but unused
  --> app\api\work_links.py:8:20
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status, Query
 8 | from typing import List, Optional
   |                    ^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\api\work_links.py:8:26
   |
 7 | from fastapi import APIRouter, Depends, HTTPException, status, Query
 8 | from typing import List, Optional
   |                          ^^^^^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_
   |
help: Remove unused import

F401 [*] `app.schemas.work_link.WorkLinkUpdate` imported but unused
  --> app\api\work_links.py:23:5
   |
21 | from app.schemas.work_link import (
22 |     WorkLinkCreate,
23 |     WorkLinkUpdate,
   |     ^^^^^^^^^^^^^^
24 |     WorkLinkResponse
25 | )
   |
help: Remove unused import: `app.schemas.work_link.WorkLinkUpdate`

F541 [*] f-string without any placeholders
   --> app\api\work_links.py:266:35
    |
264 |                 detail=error_response(
265 |                     error_code="NOT_FOUND",
266 |                     error_message=f"未找到对应的关联记录"
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^
267 |                 ).model_dump()
268 |             )
    |
help: Remove extraneous `f` prefix

F401 `app.chain.storage.StorageChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:11:51
   |
10 | if TYPE_CHECKING:
11 |     from app.chain.storage import StorageChain as StorageChainType
   |                                                   ^^^^^^^^^^^^^^^^
12 |     from app.chain.subscribe import SubscribeChain as SubscribeChainType
13 |     from app.chain.download import DownloadChain as DownloadChainType
   |
help: Add unused import `StorageChainType` to __all__

F401 `app.chain.subscribe.SubscribeChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:12:55
   |
10 | if TYPE_CHECKING:
11 |     from app.chain.storage import StorageChain as StorageChainType
12 |     from app.chain.subscribe import SubscribeChain as SubscribeChainType
   |                                                       ^^^^^^^^^^^^^^^^^^
13 |     from app.chain.download import DownloadChain as DownloadChainType
14 |     from app.chain.search import SearchChain as SearchChainType
   |
help: Add unused import `SubscribeChainType` to __all__

F401 `app.chain.download.DownloadChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:13:53
   |
11 |     from app.chain.storage import StorageChain as StorageChainType
12 |     from app.chain.subscribe import SubscribeChain as SubscribeChainType
13 |     from app.chain.download import DownloadChain as DownloadChainType
   |                                                     ^^^^^^^^^^^^^^^^^
14 |     from app.chain.search import SearchChain as SearchChainType
15 |     from app.chain.workflow import WorkflowChain as WorkflowChainType
   |
help: Add unused import `DownloadChainType` to __all__

F401 `app.chain.search.SearchChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:14:49
   |
12 |     from app.chain.subscribe import SubscribeChain as SubscribeChainType
13 |     from app.chain.download import DownloadChain as DownloadChainType
14 |     from app.chain.search import SearchChain as SearchChainType
   |                                                 ^^^^^^^^^^^^^^^
15 |     from app.chain.workflow import WorkflowChain as WorkflowChainType
16 |     from app.chain.site import SiteChain as SiteChainType
   |
help: Add unused import `SearchChainType` to __all__

F401 `app.chain.workflow.WorkflowChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:15:53
   |
13 |     from app.chain.download import DownloadChain as DownloadChainType
14 |     from app.chain.search import SearchChain as SearchChainType
15 |     from app.chain.workflow import WorkflowChain as WorkflowChainType
   |                                                     ^^^^^^^^^^^^^^^^^
16 |     from app.chain.site import SiteChain as SiteChainType
17 |     from app.chain.music import MusicChain as MusicChainType
   |
help: Add unused import `WorkflowChainType` to __all__

F401 `app.chain.site.SiteChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:16:45
   |
14 |     from app.chain.search import SearchChain as SearchChainType
15 |     from app.chain.workflow import WorkflowChain as WorkflowChainType
16 |     from app.chain.site import SiteChain as SiteChainType
   |                                             ^^^^^^^^^^^^^
17 |     from app.chain.music import MusicChain as MusicChainType
18 |     from app.chain.dashboard import DashboardChain as DashboardChainType
   |
help: Add unused import `SiteChainType` to __all__

F401 `app.chain.music.MusicChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:17:47
   |
15 |     from app.chain.workflow import WorkflowChain as WorkflowChainType
16 |     from app.chain.site import SiteChain as SiteChainType
17 |     from app.chain.music import MusicChain as MusicChainType
   |                                               ^^^^^^^^^^^^^^
18 |     from app.chain.dashboard import DashboardChain as DashboardChainType
19 |     from app.chain.manager import (
   |
help: Add unused import `MusicChainType` to __all__

F401 `app.chain.dashboard.DashboardChain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:18:55
   |
16 |     from app.chain.site import SiteChain as SiteChainType
17 |     from app.chain.music import MusicChain as MusicChainType
18 |     from app.chain.dashboard import DashboardChain as DashboardChainType
   |                                                       ^^^^^^^^^^^^^^^^^^
19 |     from app.chain.manager import (
20 |         ChainManager as ChainManagerType,
   |
help: Add unused import `DashboardChainType` to __all__

F401 `app.chain.manager.ChainManager` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:20:25
   |
18 |     from app.chain.dashboard import DashboardChain as DashboardChainType
19 |     from app.chain.manager import (
20 |         ChainManager as ChainManagerType,
   |                         ^^^^^^^^^^^^^^^^
21 |         get_chain_manager as GetChainManagerType,
22 |         get_storage_chain as GetStorageChainType,
   |
help: Add unused import `ChainManagerType` to __all__

F401 `app.chain.manager.get_chain_manager` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:21:30
   |
19 |     from app.chain.manager import (
20 |         ChainManager as ChainManagerType,
21 |         get_chain_manager as GetChainManagerType,
   |                              ^^^^^^^^^^^^^^^^^^^
22 |         get_storage_chain as GetStorageChainType,
23 |         get_subscribe_chain as GetSubscribeChainType,
   |
help: Add unused import `GetChainManagerType` to __all__

F401 `app.chain.manager.get_storage_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:22:30
   |
20 |         ChainManager as ChainManagerType,
21 |         get_chain_manager as GetChainManagerType,
22 |         get_storage_chain as GetStorageChainType,
   |                              ^^^^^^^^^^^^^^^^^^^
23 |         get_subscribe_chain as GetSubscribeChainType,
24 |         get_download_chain as GetDownloadChainType,
   |
help: Add unused import `GetStorageChainType` to __all__

F401 `app.chain.manager.get_subscribe_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:23:32
   |
21 |         get_chain_manager as GetChainManagerType,
22 |         get_storage_chain as GetStorageChainType,
23 |         get_subscribe_chain as GetSubscribeChainType,
   |                                ^^^^^^^^^^^^^^^^^^^^^
24 |         get_download_chain as GetDownloadChainType,
25 |         get_search_chain as GetSearchChainType,
   |
help: Add unused import `GetSubscribeChainType` to __all__

F401 `app.chain.manager.get_download_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:24:31
   |
22 |         get_storage_chain as GetStorageChainType,
23 |         get_subscribe_chain as GetSubscribeChainType,
24 |         get_download_chain as GetDownloadChainType,
   |                               ^^^^^^^^^^^^^^^^^^^^
25 |         get_search_chain as GetSearchChainType,
26 |         get_workflow_chain as GetWorkflowChainType,
   |
help: Add unused import `GetDownloadChainType` to __all__

F401 `app.chain.manager.get_search_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:25:29
   |
23 |         get_subscribe_chain as GetSubscribeChainType,
24 |         get_download_chain as GetDownloadChainType,
25 |         get_search_chain as GetSearchChainType,
   |                             ^^^^^^^^^^^^^^^^^^
26 |         get_workflow_chain as GetWorkflowChainType,
27 |         get_site_chain as GetSiteChainType,
   |
help: Add unused import `GetSearchChainType` to __all__

F401 `app.chain.manager.get_workflow_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:26:31
   |
24 |         get_download_chain as GetDownloadChainType,
25 |         get_search_chain as GetSearchChainType,
26 |         get_workflow_chain as GetWorkflowChainType,
   |                               ^^^^^^^^^^^^^^^^^^^^
27 |         get_site_chain as GetSiteChainType,
28 |         get_music_chain as GetMusicChainType,
   |
help: Add unused import `GetWorkflowChainType` to __all__

F401 `app.chain.manager.get_site_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:27:27
   |
25 |         get_search_chain as GetSearchChainType,
26 |         get_workflow_chain as GetWorkflowChainType,
27 |         get_site_chain as GetSiteChainType,
   |                           ^^^^^^^^^^^^^^^^
28 |         get_music_chain as GetMusicChainType,
29 |         get_dashboard_chain as GetDashboardChainType,
   |
help: Add unused import `GetSiteChainType` to __all__

F401 `app.chain.manager.get_music_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:28:28
   |
26 |         get_workflow_chain as GetWorkflowChainType,
27 |         get_site_chain as GetSiteChainType,
28 |         get_music_chain as GetMusicChainType,
   |                            ^^^^^^^^^^^^^^^^^
29 |         get_dashboard_chain as GetDashboardChainType,
30 |     )
   |
help: Add unused import `GetMusicChainType` to __all__

F401 `app.chain.manager.get_dashboard_chain` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\chain\__init__.py:29:32
   |
27 |         get_site_chain as GetSiteChainType,
28 |         get_music_chain as GetMusicChainType,
29 |         get_dashboard_chain as GetDashboardChainType,
   |                                ^^^^^^^^^^^^^^^^^^^^^
30 |     )
31 | else:
   |
help: Add unused import `GetDashboardChainType` to __all__

F401 [*] `typing.Optional` imported but unused
 --> app\chain\dashboard.py:6:20
  |
4 | """
5 |
6 | from typing import Optional, Dict, Any
  |                    ^^^^^^^^
7 | from app.chain.base import ChainBase
8 | from app.core.database import AsyncSessionLocal
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.chain.base.ChainBase` imported but unused
  --> app\chain\manager.py:9:28
   |
 7 | from loguru import logger
 8 |
 9 | from app.chain.base import ChainBase
   |                            ^^^^^^^^^
10 | from app.chain.storage import StorageChain
11 | from app.chain.subscribe import SubscribeChain
   |
help: Remove unused import: `app.chain.base.ChainBase`

F401 [*] `json` imported but unused
  --> app\core\ai_orchestrator\service.py:10:8
   |
 8 | """
 9 |
10 | import json
   |        ^^^^
11 | import re
12 | from typing import Any, Optional
   |
help: Remove unused import: `json`

F401 [*] `re` imported but unused
  --> app\core\ai_orchestrator\service.py:11:8
   |
10 | import json
11 | import re
   |        ^^
12 | from typing import Any, Optional
13 | from enum import Enum
   |
help: Remove unused import: `re`

F401 [*] `.llm_client.LLMResponse` imported but unused
  --> app\core\ai_orchestrator\service.py:17:75
   |
15 | from loguru import logger
16 |
17 | from .llm_client import LLMClient, ChatMessage, MessageRole, LLMToolCall, LLMResponse
   |                                                                           ^^^^^^^^^^^
18 | from .tools.base import AITool, OrchestratorContext
19 | from .tools.registry import get_tool_registry
   |
help: Remove unused import: `.llm_client.LLMResponse`

F401 [*] `.tools.base.AITool` imported but unused
  --> app\core\ai_orchestrator\service.py:18:25
   |
17 | from .llm_client import LLMClient, ChatMessage, MessageRole, LLMToolCall, LLMResponse
18 | from .tools.base import AITool, OrchestratorContext
   |                         ^^^^^^
19 | from .tools.registry import get_tool_registry
   |
help: Remove unused import: `.tools.base.AITool`

F811 [*] Redefinition of unused `re` from line 11
   --> app\core\ai_orchestrator\service.py:388:16
    |
387 |         # 尝试提取 JSON 建议
388 |         import re
    |                ^^ `re` redefined here
389 |         json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
390 |         if json_match:
    |
   ::: app\core\ai_orchestrator\service.py:11:8
    |
 10 | import json
 11 | import re
    |        -- previous definition of `re` here
 12 | from typing import Any, Optional
 13 | from enum import Enum
    |
help: Remove definition: `re`

F821 Undefined name `SystemDiagnosisReport`
   --> app\core\ai_orchestrator\service.py:579:81
    |
577 | """
578 |     
579 |     def parse_diagnosis_report(self, llm_suggested_changes: Optional[dict]) -> "SystemDiagnosisReport":
    |                                                                                 ^^^^^^^^^^^^^^^^^^^^^
580 |         """
581 |         从 LLM 建议中解析诊断报告
    |

F821 Undefined name `CleanupPlanDraft`
   --> app\core\ai_orchestrator\service.py:737:78
    |
735 | """
736 |     
737 |     def parse_cleanup_draft(self, llm_suggested_changes: Optional[dict]) -> "CleanupPlanDraft":
    |                                                                              ^^^^^^^^^^^^^^^^
738 |         """
739 |         从 LLM 建议中解析清理计划草案
    |

F821 Undefined name `ReadingPlanDraft`
   --> app\core\ai_orchestrator\service.py:892:77
    |
890 | """
891 |     
892 |     def parse_reading_plan(self, llm_suggested_changes: Optional[dict]) -> "ReadingPlanDraft":
    |                                                                             ^^^^^^^^^^^^^^^^
893 |         """
894 |         从 LLM 建议中解析阅读计划草案
    |

F401 [*] `app.models.user_audiobook_progress.UserAudiobookProgress` imported but unused
   --> app\core\ai_orchestrator\tools\library_books.py:127:60
    |
125 |             from app.models.ebook import EBook
126 |             from app.models.user_novel_reading_progress import UserNovelReadingProgress
127 |             from app.models.user_audiobook_progress import UserAudiobookProgress
    |                                                            ^^^^^^^^^^^^^^^^^^^^^
128 |             from app.models.manga_series_local import MangaSeriesLocal
129 |             from app.models.manga_reading_progress import MangaReadingProgress
    |
help: Remove unused import: `app.models.user_audiobook_progress.UserAudiobookProgress`

E712 Avoid equality comparisons to `True`; use `UserNovelReadingProgress.is_finished:` for truth checks
   --> app\core\ai_orchestrator\tools\library_books.py:139:24
    |
137 |                 select(func.count()).select_from(UserNovelReadingProgress)
138 |                 .where(UserNovelReadingProgress.user_id == context.user_id)
139 |                 .where(UserNovelReadingProgress.is_finished == True)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
140 |             )
141 |             read_novel_count = read_novels.scalar() or 0
    |
help: Replace with `UserNovelReadingProgress.is_finished`

E712 Avoid equality comparisons to `False`; use `not UserNovelReadingProgress.is_finished:` for false checks
   --> app\core\ai_orchestrator\tools\library_books.py:146:24
    |
144 |                 select(func.count()).select_from(UserNovelReadingProgress)
145 |                 .where(UserNovelReadingProgress.user_id == context.user_id)
146 |                 .where(UserNovelReadingProgress.is_finished == False)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
147 |             )
148 |             reading_novel_count = reading_novels.scalar() or 0
    |
help: Replace with `not UserNovelReadingProgress.is_finished`

E712 Avoid equality comparisons to `True`; use `MangaReadingProgress.is_finished:` for truth checks
   --> app\core\ai_orchestrator\tools\library_books.py:165:24
    |
163 |                 select(func.count()).select_from(MangaReadingProgress)
164 |                 .where(MangaReadingProgress.user_id == context.user_id)
165 |                 .where(MangaReadingProgress.is_finished == True)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
166 |             )
167 |             read_manga_count = read_manga.scalar() or 0
    |
help: Replace with `MangaReadingProgress.is_finished`

E712 Avoid equality comparisons to `False`; use `not MangaReadingProgress.is_finished:` for false checks
   --> app\core\ai_orchestrator\tools\library_books.py:172:24
    |
170 |                 select(func.count()).select_from(MangaReadingProgress)
171 |                 .where(MangaReadingProgress.user_id == context.user_id)
172 |                 .where(MangaReadingProgress.is_finished == False)
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
173 |             )
174 |             reading_manga_count = reading_manga.scalar() or 0
    |
help: Replace with `not MangaReadingProgress.is_finished`

E712 Avoid equality comparisons to `True`; use `UserNovelReadingProgress.is_finished:` for truth checks
   --> app\core\ai_orchestrator\tools\library_books.py:223:28
    |
221 |                     .where(EBook.series == series_name)
222 |                     .where(UserNovelReadingProgress.user_id == context.user_id)
223 |                     .where(UserNovelReadingProgress.is_finished == True)
    |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
224 |                 )
225 |                 read_result = await context.db.execute(read_query)
    |
help: Replace with `UserNovelReadingProgress.is_finished`

F401 [*] `datetime.datetime` imported but unused
  --> app\core\ai_orchestrator\tools\runner_status.py:9:22
   |
 8 | from typing import Optional
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 | from pydantic import BaseModel, Field
11 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

E712 Avoid equality comparisons to `True`; use `Subscription.is_active:` for truth checks
   --> app\core\ai_orchestrator\tools\site_overview.py:150:21
    |
148 |             if hasattr(Subscription, "is_active"):
149 |                 active_query = select(func.count()).select_from(Subscription).where(
150 |                     Subscription.is_active == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
151 |                 )
152 |                 result = await context.db.execute(active_query)
    |
help: Replace with `Subscription.is_active`

F401 [*] `typing.Optional` imported but unused
  --> app\core\ai_orchestrator\tools\storage_snapshot.py:8:20
   |
 6 | """
 7 |
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 | from pydantic import BaseModel, Field
10 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

E712 Avoid equality comparisons to `True`; use `TorrentIndex.is_hr:` for truth checks
   --> app\core\ai_orchestrator\tools\torrent_insight.py:146:50
    |
144 |                 hr_count = 0
145 |                 if hasattr(TorrentIndex, "is_hr"):
146 |                     hr_query = count_query.where(TorrentIndex.is_hr == True)
    |                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
147 |                     result = await context.db.execute(hr_query)
148 |                     hr_count = result.scalar() or 0
    |
help: Replace with `TorrentIndex.is_hr`

F401 [*] `typing.Dict` imported but unused
 --> app\core\api_key_manager.py:6:30
  |
4 | 使用CloudKeyManager进行加密存储
5 | """
6 | from typing import Optional, Dict
  |                              ^^^^
7 | from loguru import logger
8 | from app.core.cloud_key_manager import get_key_manager
  |
help: Remove unused import: `typing.Dict`

F841 [*] Local variable `e` is assigned to but never used
  --> app\core\auth.py:33:25
   |
32 |         return user
33 |     except Exception as e:
   |                         ^
34 |         raise HTTPException(
35 |             status_code=status.HTTP_401_UNAUTHORIZED,
   |
help: Remove assignment to unused variable `e`

F401 [*] `httpx` imported but unused
 --> app\core\bangumi_client.py:6:8
  |
4 | """
5 |
6 | import httpx
  |        ^^^^^
7 | from typing import List, Optional, Dict, Any
8 | from datetime import datetime
  |
help: Remove unused import: `httpx`

F841 Local variable `weekday_cn` is assigned to but never used
   --> app\core\bangumi_client.py:172:17
    |
170 |                 weekday_info = weekday_data.get("weekday", {})
171 |                 weekday_id = weekday_info.get("id", 0)
172 |                 weekday_cn = weekday_info.get("cn", "")
    |                 ^^^^^^^^^^
173 |                 items = weekday_data.get("items", [])
174 |                 for item in items:
    |
help: Remove assignment to unused variable `weekday_cn`

F401 [*] `typing.Union` imported but unused
 --> app\core\cache.py:6:35
  |
4 | """
5 |
6 | from typing import Optional, Any, Union
  |                                   ^^^^^
7 | from datetime import datetime, timedelta
8 | import json
  |
help: Remove unused import: `typing.Union`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\core\cache.py:12:36
   |
10 | from functools import wraps
11 | from loguru import logger
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
13 | from sqlalchemy import select, delete, and_
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\core\cache.py:13:40
   |
11 | from loguru import logger
12 | from sqlalchemy.ext.asyncio import AsyncSession
13 | from sqlalchemy import select, delete, and_
   |                                        ^^^^
14 |
15 | try:
   |
help: Remove unused import: `sqlalchemy.and_`

F541 [*] f-string without any placeholders
   --> app\core\cache.py:368:30
    |
366 |             error_str = str(e).lower()
367 |             if "no such table" in error_str or "does not exist" in error_str:
368 |                 logger.debug(f"缓存表不存在，将在数据库初始化时创建")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
369 |             else:
370 |                 logger.debug(f"数据库删除缓存失败（已降级）: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\core\cache.py:405:30
    |
403 |             error_str = str(e).lower()
404 |             if "no such table" in error_str or "does not exist" in error_str:
405 |                 logger.debug(f"缓存表不存在，将在数据库初始化时创建")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
406 |             else:
407 |                 logger.debug(f"数据库检查缓存失败（已降级）: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\core\cache.py:424:30
    |
422 |             error_str = str(e).lower()
423 |             if "no such table" in error_str or "does not exist" in error_str:
424 |                 logger.debug(f"缓存表不存在，将在数据库初始化时创建")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
425 |             else:
426 |                 logger.debug(f"数据库清空缓存失败（已降级）: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\core\cache.py:447:30
    |
445 |             error_str = str(e).lower()
446 |             if "no such table" in error_str or "does not exist" in error_str:
447 |                 logger.debug(f"缓存表不存在，将在数据库初始化时创建")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
448 |             else:
449 |                 logger.debug(f"清理过期缓存失败（已降级）: {e}")
    |
help: Remove extraneous `f` prefix

F821 Undefined name `asyncio`
  --> app\core\cache_decorator.py:87:33
   |
85 |             return async_wrapper
86 |         
87 |         return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
   |                                 ^^^^^^^
88 |     
89 |     return decorator
   |

F401 [*] `typing.Optional` imported but unused
 --> app\core\cache_optimizer.py:6:32
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                                ^^^^^^^^
7 | from datetime import datetime, timedelta
8 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
 --> app\core\cache_optimizer.py:7:22
  |
6 | from typing import Dict, List, Optional, Any
7 | from datetime import datetime, timedelta
  |                      ^^^^^^^^
8 | from loguru import logger
9 | from app.core.cache import get_cache
  |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
 --> app\core\cache_optimizer.py:7:32
  |
6 | from typing import Dict, List, Optional, Any
7 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
8 | from loguru import logger
9 | from app.core.cache import get_cache
  |
help: Remove unused import

F401 [*] `loguru.logger` imported but unused
 --> app\core\cache_optimizer.py:8:20
  |
6 | from typing import Dict, List, Optional, Any
7 | from datetime import datetime, timedelta
8 | from loguru import logger
  |                    ^^^^^^
9 | from app.core.cache import get_cache
  |
help: Remove unused import: `loguru.logger`

F401 [*] `secrets` imported but unused
  --> app\core\cloud_key_manager.py:9:8
   |
 7 | import json
 8 | import base64
 9 | import secrets
   |        ^^^^^^^
10 | from typing import Dict, Optional, Any
11 | from pathlib import Path
   |
help: Remove unused import: `secrets`

F401 [*] `cryptography.hazmat.primitives.hashes` imported but unused
  --> app\core\cloud_key_manager.py:14:44
   |
12 | from datetime import datetime
13 | from cryptography.fernet import Fernet
14 | from cryptography.hazmat.primitives import hashes
   |                                            ^^^^^^
15 | from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
16 | from loguru import logger
   |
help: Remove unused import: `cryptography.hazmat.primitives.hashes`

F401 [*] `cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC` imported but unused
  --> app\core\cloud_key_manager.py:15:55
   |
13 | from cryptography.fernet import Fernet
14 | from cryptography.hazmat.primitives import hashes
15 | from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
   |                                                       ^^^^^^^^^^
16 | from loguru import logger
   |
help: Remove unused import: `cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC`

F811 Redefinition of unused `CloudStorageUsage` from line 8
  --> app\core\cloud_storage\providers\base.py:33:7
   |
32 | @dataclass
33 | class CloudStorageUsage:
   |       ^^^^^^^^^^^^^^^^^ `CloudStorageUsage` redefined here
34 |     """云存储使用情况"""
35 |     total: int  # 总容量（字节）
   |
  ::: app\core\cloud_storage\providers\base.py:8:44
   |
 6 | from typing import List, Optional, Dict, Any, Tuple, Callable
 7 | from dataclasses import dataclass
 8 | from app.core.cloud_storage.schemas import CloudStorageUsage
   |                                            ----------------- previous definition of `CloudStorageUsage` here
 9 | from datetime import datetime
   |
help: Remove definition: `CloudStorageUsage`

F821 Undefined name `OSS2_AVAILABLE`
   --> app\core\cloud_storage\providers\cloud_115.py:766:16
    |
764 |             上传是否成功
765 |         """
766 |         if not OSS2_AVAILABLE:
    |                ^^^^^^^^^^^^^^
767 |             logger.error("oss2库未安装，无法使用115网盘上传功能")
768 |             return False
    |

F821 Undefined name `hashlib`
   --> app\core\cloud_storage\providers\cloud_115.py:837:32
    |
835 |                     f.seek(start)
836 |                     chunk = f.read(end - start + 1)
837 |                     sign_val = hashlib.sha1(chunk).hexdigest().upper()
    |                                ^^^^^^^
838 |                 
839 |                 # 重新初始化请求
    |

F821 Undefined name `target_path`
   --> app\core\cloud_storage\providers\cloud_115.py:889:60
    |
888 |                 # 使用智能延迟获取文件信息
889 |                 file_info = await self._delay_get_item(str(target_path))
    |                                                            ^^^^^^^^^^^
890 |                 if file_info:
891 |                     logger.debug(f"【115】秒传后获取文件信息成功: {file_info.name}")
    |

F541 [*] f-string without any placeholders
   --> app\core\cloud_storage\providers\cloud_115.py:911:26
    |
909 |             security_token = token_data.get("SecurityToken")
910 |             
911 |             logger.debug(f"上传 Step 4 获取上传凭证成功")
    |                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
912 |             
913 |             # Step 5: 断点续传检测
    |
help: Remove extraneous `f` prefix

F821 Undefined name `oss2`
   --> app\core\cloud_storage\providers\cloud_115.py:936:28
    |
934 |                 try:
935 |                     # 创建OSS认证
936 |                     auth = oss2.StsAuth(
    |                            ^^^^
937 |                         access_key_id=access_key_id,
938 |                         access_key_secret=access_key_secret,
    |

F821 Undefined name `oss2`
   --> app\core\cloud_storage\providers\cloud_115.py:941:30
    |
939 |                         security_token=security_token
940 |                     )
941 |                     bucket = oss2.Bucket(auth, endpoint, bucket_name)
    |                              ^^^^
942 |                     
943 |                     # 确定分片大小（默认10MB）
    |

F821 Undefined name `determine_part_size`
   --> app\core\cloud_storage\providers\cloud_115.py:944:33
    |
943 |                     # 确定分片大小（默认10MB）
944 |                     part_size = determine_part_size(file_size, preferred_size=10 * 1024 * 1024)
    |                                 ^^^^^^^^^^^^^^^^^^^
945 |                     logger.info(f"开始上传: {local_path} -> {remote_path}，分片大小: {part_size / 1024 / 1024:.2f}MB")
    |

F821 Undefined name `SizedFileAdapter`
   --> app\core\cloud_storage\providers\cloud_115.py:971:38
    |
969 | …                         upload_id,
970 | …                         part_number,
971 | …                         data=SizedFileAdapter(fileobj, num_to_upload)
    |                                ^^^^^^^^^^^^^^^^
972 | …                     )
973 | …                     parts.append(PartInfo(part_number, result.etag))
    |

F821 Undefined name `PartInfo`
   --> app\core\cloud_storage\providers\cloud_115.py:973:42
    |
971 | …                         data=SizedFileAdapter(fileobj, num_to_upload)
972 | …                     )
973 | …                     parts.append(PartInfo(part_number, result.etag))
    |                                    ^^^^^^^^
974 | …                     
975 | …                     logger.debug(f"{target_name} 分片 {part_number} 上传完成")
    |

F821 Undefined name `oss2`
   --> app\core\cloud_storage\providers\cloud_115.py:990:32
    |
988 |                     # 编码回调
989 |                     def encode_callback(cb: str) -> str:
990 |                         return oss2.utils.b64encode_as_string(cb)
    |                                ^^^^
991 |                     
992 |                     # 完成分片上传
    |

F821 Undefined name `oss2`
    --> app\core\cloud_storage\providers\cloud_115.py:1013:24
     |
1011 |                         return False
1012 |                         
1013 |                 except oss2.exceptions.OssError as e:
     |                        ^^^^
1014 |                     if e.code == "FileAlreadyExists":
1015 |                         logger.warning(f"{target_name} 已存在")
     |

F821 Undefined name `target_path`
    --> app\core\cloud_storage\providers\cloud_115.py:1030:60
     |
1028 |             if success:
1029 |                 # 使用智能延迟获取文件信息
1030 |                 file_info = await self._delay_get_item(str(target_path))
     |                                                            ^^^^^^^^^^^
1031 |                 if file_info:
1032 |                     logger.debug(f"上传后获取文件信息成功: {file_info.name}")
     |

F821 Undefined name `target_path`
    --> app\core\cloud_storage\providers\cloud_115.py:1034:52
     |
1032 |                     logger.debug(f"上传后获取文件信息成功: {file_info.name}")
1033 |                 else:
1034 |                     logger.warning(f"上传后无法获取文件信息: {target_path}")
     |                                                               ^^^^^^^^^^^
1035 |             
1036 |             return success
     |

F821 Undefined name `hashlib`
    --> app\core\cloud_storage\providers\cloud_115.py:1384:16
     |
1382 |             SHA1哈希值（十六进制字符串）
1383 |         """
1384 |         sha1 = hashlib.sha1()
     |                ^^^^^^^
1385 |         with open(filepath, 'rb') as f:
1386 |             if size:
     |

F401 [*] `datetime.timedelta` imported but unused
  --> app\core\cloud_storage\providers\cloud_115_api.py:11:32
   |
 9 | import httpx
10 | from typing import Dict, List, Optional, Any
11 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
12 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `pathlib.Path` imported but unused
  --> app\core\cloud_storage\providers\cloud_115_oss.py:13:21
   |
11 | from typing import Dict, Optional, Any, Callable
12 | from loguru import logger
13 | from pathlib import Path
   |                     ^^^^
14 |
15 | # 导入速度限制器
   |
help: Remove unused import: `pathlib.Path`

F841 Local variable `file_size` is assigned to but never used
   --> app\core\cloud_storage\providers\cloud_115_oss.py:100:9
    |
 98 |             上传结果
 99 |         """
100 |         file_size = os.path.getsize(file_path)
    |         ^^^^^^^^^
101 |         
102 |         # 使用分片上传（推荐，支持大文件）
    |
help: Remove assignment to unused variable `file_size`

F401 [*] `asyncio` imported but unused
  --> app\core\cloud_storage\providers\cloud_115_upload.py:9:8
   |
 7 | import os
 8 | import hashlib
 9 | import asyncio
   |        ^^^^^^^
10 | from typing import Dict, Optional, Any, Callable
11 | from pathlib import Path
   |
help: Remove unused import: `asyncio`

F821 Undefined name `speed_limit`
   --> app\core\cloud_storage\providers\cloud_115_upload.py:242:37
    |
240 |                         init_result=init_result,
241 |                         progress_callback=progress_callback,
242 |                         speed_limit=speed_limit,
    |                                     ^^^^^^^^^^^
243 |                         pick_code=pick_code
244 |                     )
    |

E722 Do not use bare `except`
   --> app\core\cloud_storage\providers\rclone.py:178:21
    |
176 |                         # RClone返回的时间格式: "2024-01-01T00:00:00Z"
177 |                         modified_at = datetime.fromisoformat(item["ModTime"].replace('Z', '+00:00'))
178 |                     except:
    |                     ^^^^^^
179 |                         pass
    |

E722 Do not use bare `except`
   --> app\core\cloud_storage\providers\rclone.py:227:17
    |
225 |                 try:
226 |                     modified_at = datetime.fromisoformat(item["ModTime"].replace('Z', '+00:00'))
227 |                 except:
    |                 ^^^^^^
228 |                     pass
    |

E722 Do not use bare `except`
   --> app\core\cloud_storage\providers\rclone.py:330:21
    |
328 |                             progress = float(percent_str)
329 |                             progress_callback(progress)
330 |                     except:
    |                     ^^^^^^
331 |                         pass
    |

E722 Do not use bare `except`
   --> app\core\cloud_storage\providers\rclone.py:373:21
    |
371 |                             progress = float(percent_str)
372 |                             progress_callback(progress)
373 |                     except:
    |                     ^^^^^^
374 |                         pass
    |

F821 Undefined name `CloudFileInfo`
   --> app\core\cloud_storage\schemas.py:149:47
    |
147 | # 模型转换工具函数
148 |
149 | def cloud_file_info_to_file_item(cloud_file: 'CloudFileInfo', storage: str = "cloud") -> FileItem:
    |                                               ^^^^^^^^^^^^^
150 |     """
151 |     将CloudFileInfo转换为FileItem
    |

F821 Undefined name `CloudFileInfo`
   --> app\core\cloud_storage\schemas.py:188:59
    |
188 | def file_item_to_cloud_file_info(file_item: FileItem) -> 'CloudFileInfo':
    |                                                           ^^^^^^^^^^^^^
189 |     """
190 |     将FileItem转换为CloudFileInfo
    |

E722 Do not use bare `except`
   --> app\core\config.py:371:9
    |
369 |         try:
370 |             SECURITY_IMAGE_DOMAINS = json.loads(os.getenv("SECURITY_IMAGE_DOMAINS"))
371 |         except:
    |         ^^^^^^
372 |             SECURITY_IMAGE_DOMAINS = []
    |

F841 [*] Local variable `e` is assigned to but never used
   --> app\core\config.py:572:69
    |
570 |                 if isinstance(raw_list, list) and raw_list:
571 |                     return [PluginHubSourceConfig(**item) for item in raw_list]
572 |             except (json.JSONDecodeError, TypeError, ValueError) as e:
    |                                                                     ^
573 |                 # 解析失败，使用默认值
574 |                 pass
    |
help: Remove assignment to unused variable `e`

F401 [*] `pydantic.Field` imported but unused
 --> app\core\config_schema.py:8:33
  |
6 | """
7 | from typing import Optional, List, Any, Dict
8 | from pydantic import BaseModel, Field
  |                                 ^^^^^
9 | from enum import Enum
  |
help: Remove unused import: `pydantic.Field`

F401 [*] `app.models.user.User` imported but unused
  --> app\core\database.py:70:33
   |
68 |     """初始化数据库"""
69 |     # 导入所有模型以确保它们被注册到Base.metadata
70 |     from app.models.user import User
   |                                 ^^^^
71 |     from app.models.media import Media, MediaFile
72 |     from app.models.subscription import Subscription
   |
help: Remove unused import: `app.models.user.User`

F401 [*] `app.models.media.Media` imported but unused
  --> app\core\database.py:71:34
   |
69 |     # 导入所有模型以确保它们被注册到Base.metadata
70 |     from app.models.user import User
71 |     from app.models.media import Media, MediaFile
   |                                  ^^^^^
72 |     from app.models.subscription import Subscription
73 |     from app.models.download import DownloadTask
   |
help: Remove unused import

F401 [*] `app.models.media.MediaFile` imported but unused
  --> app\core\database.py:71:41
   |
69 |     # 导入所有模型以确保它们被注册到Base.metadata
70 |     from app.models.user import User
71 |     from app.models.media import Media, MediaFile
   |                                         ^^^^^^^^^
72 |     from app.models.subscription import Subscription
73 |     from app.models.download import DownloadTask
   |
help: Remove unused import

F401 [*] `app.models.subscription.Subscription` imported but unused
  --> app\core\database.py:72:41
   |
70 |     from app.models.user import User
71 |     from app.models.media import Media, MediaFile
72 |     from app.models.subscription import Subscription
   |                                         ^^^^^^^^^^^^
73 |     from app.models.download import DownloadTask
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
   |
help: Remove unused import: `app.models.subscription.Subscription`

F401 [*] `app.models.download.DownloadTask` imported but unused
  --> app\core\database.py:73:37
   |
71 |     from app.models.media import Media, MediaFile
72 |     from app.models.subscription import Subscription
73 |     from app.models.download import DownloadTask
   |                                     ^^^^^^^^^^^^
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
75 |     from app.models.workflow import Workflow, WorkflowExecution
   |
help: Remove unused import: `app.models.download.DownloadTask`

F401 [*] `app.models.upload.UploadTask` imported but unused
  --> app\core\database.py:74:35
   |
72 |     from app.models.subscription import Subscription
73 |     from app.models.download import DownloadTask
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
   |                                   ^^^^^^^^^^
75 |     from app.models.workflow import Workflow, WorkflowExecution
76 |     from app.models.site import Site
   |
help: Remove unused import

F401 [*] `app.models.upload.UploadProgress` imported but unused
  --> app\core\database.py:74:47
   |
72 |     from app.models.subscription import Subscription
73 |     from app.models.download import DownloadTask
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
   |                                               ^^^^^^^^^^^^^^
75 |     from app.models.workflow import Workflow, WorkflowExecution
76 |     from app.models.site import Site
   |
help: Remove unused import

F401 [*] `app.models.workflow.Workflow` imported but unused
  --> app\core\database.py:75:37
   |
73 |     from app.models.download import DownloadTask
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
75 |     from app.models.workflow import Workflow, WorkflowExecution
   |                                     ^^^^^^^^
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
   |
help: Remove unused import

F401 [*] `app.models.workflow.WorkflowExecution` imported but unused
  --> app\core\database.py:75:47
   |
73 |     from app.models.download import DownloadTask
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
75 |     from app.models.workflow import Workflow, WorkflowExecution
   |                                               ^^^^^^^^^^^^^^^^^
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
   |
help: Remove unused import

F401 [*] `app.models.site.Site` imported but unused
  --> app\core\database.py:76:33
   |
74 |     from app.models.upload import UploadTask, UploadProgress  # 上传任务
75 |     from app.models.workflow import Workflow, WorkflowExecution
76 |     from app.models.site import Site
   |                                 ^^^^
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |
help: Remove unused import: `app.models.site.Site`

F401 [*] `app.models.notification.Notification` imported but unused
  --> app\core\database.py:77:41
   |
75 |     from app.models.workflow import Workflow, WorkflowExecution
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
   |                                         ^^^^^^^^^^^^
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
   |
help: Remove unused import: `app.models.notification.Notification`

F401 [*] `app.models.music.MusicSubscription` imported but unused
  --> app\core\database.py:78:34
   |
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |                                  ^^^^^^^^^^^^^^^^^
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |
help: Remove unused import

F401 [*] `app.models.music.MusicTrack` imported but unused
  --> app\core\database.py:78:53
   |
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |                                                     ^^^^^^^^^^
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |
help: Remove unused import

F401 [*] `app.models.music.MusicPlaylist` imported but unused
  --> app\core\database.py:78:65
   |
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |                                                                 ^^^^^^^^^^^^^
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |
help: Remove unused import

F401 [*] `app.models.music.MusicLibrary` imported but unused
  --> app\core\database.py:78:80
   |
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |                                                                                ^^^^^^^^^^^^
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |
help: Remove unused import

F401 [*] `app.models.music.MusicChartRecord` imported but unused
  --> app\core\database.py:78:94
   |
76 |     from app.models.site import Site
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
   |                                                                                              ^^^^^^^^^^^^^^^^
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |
help: Remove unused import

F401 [*] `app.models.cache.CacheEntry` imported but unused
  --> app\core\database.py:79:34
   |
77 |     from app.models.notification import Notification
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
   |                                  ^^^^^^^^^^
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
   |
help: Remove unused import: `app.models.cache.CacheEntry`

F401 [*] `app.models.identification_history.IdentificationHistory` imported but unused
  --> app\core\database.py:80:51
   |
78 |     from app.models.music import MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary, MusicChartRecord
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
   |                                                   ^^^^^^^^^^^^^^^^^^^^^
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
   |
help: Remove unused import: `app.models.identification_history.IdentificationHistory`

F401 [*] `app.models.cloud_storage.CloudStorage` imported but unused
  --> app\core\database.py:81:42
   |
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
   |                                          ^^^^^^^^^^^^
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
   |
help: Remove unused import

F401 [*] `app.models.cloud_storage.CloudStorageAuth` imported but unused
  --> app\core\database.py:81:56
   |
79 |     from app.models.cache import CacheEntry  # L3数据库缓存
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
   |                                                        ^^^^^^^^^^^^^^^^
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
   |
help: Remove unused import

F401 [*] `app.models.rss_subscription.RSSSubscription` imported but unused
  --> app\core\database.py:82:45
   |
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
   |                                             ^^^^^^^^^^^^^^^
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
84 |     from app.models.multimodal_metrics import (
   |
help: Remove unused import

F401 [*] `app.models.rss_subscription.RSSItem` imported but unused
  --> app\core\database.py:82:62
   |
80 |     from app.models.identification_history import IdentificationHistory  # 媒体识别历史记录
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
   |                                                              ^^^^^^^
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
84 |     from app.models.multimodal_metrics import (
   |
help: Remove unused import

F401 [*] `app.models.subtitle.Subtitle` imported but unused
  --> app\core\database.py:83:37
   |
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
   |                                     ^^^^^^^^
84 |     from app.models.multimodal_metrics import (
85 |         MultimodalPerformanceMetric,
   |
help: Remove unused import

F401 [*] `app.models.subtitle.SubtitleDownloadHistory` imported but unused
  --> app\core\database.py:83:47
   |
81 |     from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
82 |     from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
   |                                               ^^^^^^^^^^^^^^^^^^^^^^^
84 |     from app.models.multimodal_metrics import (
85 |         MultimodalPerformanceMetric,
   |
help: Remove unused import

F401 [*] `app.models.multimodal_metrics.MultimodalPerformanceMetric` imported but unused
  --> app\core\database.py:85:9
   |
83 |     from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
84 |     from app.models.multimodal_metrics import (
85 |         MultimodalPerformanceMetric,
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
86 |         MultimodalPerformanceAlert,
87 |         MultimodalOptimizationHistory
   |
help: Remove unused import

F401 [*] `app.models.multimodal_metrics.MultimodalPerformanceAlert` imported but unused
  --> app\core\database.py:86:9
   |
84 |     from app.models.multimodal_metrics import (
85 |         MultimodalPerformanceMetric,
86 |         MultimodalPerformanceAlert,
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
87 |         MultimodalOptimizationHistory
88 |     )  # 多模态分析性能指标
   |
help: Remove unused import

F401 [*] `app.models.multimodal_metrics.MultimodalOptimizationHistory` imported but unused
  --> app\core\database.py:87:9
   |
85 |         MultimodalPerformanceMetric,
86 |         MultimodalPerformanceAlert,
87 |         MultimodalOptimizationHistory
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
88 |     )  # 多模态分析性能指标
89 |     from app.models.media_server import (
   |
help: Remove unused import

F401 [*] `app.models.media_server.MediaServer` imported but unused
  --> app\core\database.py:90:9
   |
88 |     )  # 多模态分析性能指标
89 |     from app.models.media_server import (
90 |         MediaServer,
   |         ^^^^^^^^^^^
91 |         MediaServerSyncHistory,
92 |         MediaServerItem,
   |
help: Remove unused import

F401 [*] `app.models.media_server.MediaServerSyncHistory` imported but unused
  --> app\core\database.py:91:9
   |
89 |     from app.models.media_server import (
90 |         MediaServer,
91 |         MediaServerSyncHistory,
   |         ^^^^^^^^^^^^^^^^^^^^^^
92 |         MediaServerItem,
93 |         MediaServerPlaybackSession
   |
help: Remove unused import

F401 [*] `app.models.media_server.MediaServerItem` imported but unused
  --> app\core\database.py:92:9
   |
90 |         MediaServer,
91 |         MediaServerSyncHistory,
92 |         MediaServerItem,
   |         ^^^^^^^^^^^^^^^
93 |         MediaServerPlaybackSession
94 |     )  # 媒体服务器
   |
help: Remove unused import

F401 [*] `app.models.media_server.MediaServerPlaybackSession` imported but unused
  --> app\core\database.py:93:9
   |
91 |         MediaServerSyncHistory,
92 |         MediaServerItem,
93 |         MediaServerPlaybackSession
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^
94 |     )  # 媒体服务器
95 |     from app.models.scheduler_task import (
   |
help: Remove unused import

F401 [*] `app.models.scheduler_task.SchedulerTask` imported but unused
  --> app\core\database.py:96:9
   |
94 |     )  # 媒体服务器
95 |     from app.models.scheduler_task import (
96 |         SchedulerTask,
   |         ^^^^^^^^^^^^^
97 |         SchedulerTaskExecution
98 |     )
   |
help: Remove unused import

F401 [*] `app.models.scheduler_task.SchedulerTaskExecution` imported but unused
  --> app\core\database.py:97:9
   |
95 |     from app.models.scheduler_task import (
96 |         SchedulerTask,
97 |         SchedulerTaskExecution
   |         ^^^^^^^^^^^^^^^^^^^^^^
98 |     )
99 |     from app.models.storage_monitor import (
   |
help: Remove unused import

F401 [*] `app.models.storage_monitor.StorageDirectory` imported but unused
   --> app\core\database.py:100:9
    |
 98 |     )
 99 |     from app.models.storage_monitor import (
100 |         StorageDirectory,
    |         ^^^^^^^^^^^^^^^^
101 |         StorageUsageHistory,
102 |         StorageAlert
    |
help: Remove unused import

F401 [*] `app.models.storage_monitor.StorageUsageHistory` imported but unused
   --> app\core\database.py:101:9
    |
 99 |     from app.models.storage_monitor import (
100 |         StorageDirectory,
101 |         StorageUsageHistory,
    |         ^^^^^^^^^^^^^^^^^^^
102 |         StorageAlert
103 |     )  # 存储监控
    |
help: Remove unused import

F401 [*] `app.models.storage_monitor.StorageAlert` imported but unused
   --> app\core\database.py:102:9
    |
100 |         StorageDirectory,
101 |         StorageUsageHistory,
102 |         StorageAlert
    |         ^^^^^^^^^^^^
103 |     )  # 存储监控
104 |     from app.models.strm import (
    |
help: Remove unused import

F401 [*] `app.models.strm.STRMWorkflowTask` imported but unused
   --> app\core\database.py:105:9
    |
103 |     )  # 存储监控
104 |     from app.models.strm import (
105 |         STRMWorkflowTask,
    |         ^^^^^^^^^^^^^^^^
106 |         STRMFile,
107 |         STRMFileTree,
    |
help: Remove unused import

F401 [*] `app.models.strm.STRMFile` imported but unused
   --> app\core\database.py:106:9
    |
104 |     from app.models.strm import (
105 |         STRMWorkflowTask,
106 |         STRMFile,
    |         ^^^^^^^^
107 |         STRMFileTree,
108 |         STRMLifeEvent,
    |
help: Remove unused import

F401 [*] `app.models.strm.STRMFileTree` imported but unused
   --> app\core\database.py:107:9
    |
105 |         STRMWorkflowTask,
106 |         STRMFile,
107 |         STRMFileTree,
    |         ^^^^^^^^^^^^
108 |         STRMLifeEvent,
109 |         STRMConfig
    |
help: Remove unused import

F401 [*] `app.models.strm.STRMLifeEvent` imported but unused
   --> app\core\database.py:108:9
    |
106 |         STRMFile,
107 |         STRMFileTree,
108 |         STRMLifeEvent,
    |         ^^^^^^^^^^^^^
109 |         STRMConfig
110 |     )  # STRM文件生成系统
    |
help: Remove unused import

F401 [*] `app.models.strm.STRMConfig` imported but unused
   --> app\core\database.py:109:9
    |
107 |         STRMFileTree,
108 |         STRMLifeEvent,
109 |         STRMConfig
    |         ^^^^^^^^^^
110 |     )  # STRM文件生成系统
111 |     from app.models.directory import Directory  # 目录配置
    |
help: Remove unused import

F401 [*] `app.models.directory.Directory` imported but unused
   --> app\core\database.py:111:38
    |
109 |         STRMConfig
110 |     )  # STRM文件生成系统
111 |     from app.models.directory import Directory  # 目录配置
    |                                      ^^^^^^^^^
112 |     from app.models.backup import BackupRecord  # 备份记录
113 |     from app.models.transfer_history import TransferHistory  # 转移历史记录
    |
help: Remove unused import: `app.models.directory.Directory`

F401 [*] `app.models.backup.BackupRecord` imported but unused
   --> app\core\database.py:112:35
    |
110 |     )  # STRM文件生成系统
111 |     from app.models.directory import Directory  # 目录配置
112 |     from app.models.backup import BackupRecord  # 备份记录
    |                                   ^^^^^^^^^^^^
113 |     from app.models.transfer_history import TransferHistory  # 转移历史记录
114 |     from app.models.work_link import WorkLink  # 作品关联（Work Link）
    |
help: Remove unused import: `app.models.backup.BackupRecord`

F401 [*] `app.models.transfer_history.TransferHistory` imported but unused
   --> app\core\database.py:113:45
    |
111 |     from app.models.directory import Directory  # 目录配置
112 |     from app.models.backup import BackupRecord  # 备份记录
113 |     from app.models.transfer_history import TransferHistory  # 转移历史记录
    |                                             ^^^^^^^^^^^^^^^
114 |     from app.models.work_link import WorkLink  # 作品关联（Work Link）
115 |     from app.models.global_rules import GlobalRuleSettings  # 全局规则设置（SETTINGS-RULES-1）
    |
help: Remove unused import: `app.models.transfer_history.TransferHistory`

F401 [*] `app.models.work_link.WorkLink` imported but unused
   --> app\core\database.py:114:38
    |
112 |     from app.models.backup import BackupRecord  # 备份记录
113 |     from app.models.transfer_history import TransferHistory  # 转移历史记录
114 |     from app.models.work_link import WorkLink  # 作品关联（Work Link）
    |                                      ^^^^^^^^
115 |     from app.models.global_rules import GlobalRuleSettings  # 全局规则设置（SETTINGS-RULES-1）
    |
help: Remove unused import: `app.models.work_link.WorkLink`

F401 [*] `app.models.global_rules.GlobalRuleSettings` imported but unused
   --> app\core\database.py:115:41
    |
113 |     from app.models.transfer_history import TransferHistory  # 转移历史记录
114 |     from app.models.work_link import WorkLink  # 作品关联（Work Link）
115 |     from app.models.global_rules import GlobalRuleSettings  # 全局规则设置（SETTINGS-RULES-1）
    |                                         ^^^^^^^^^^^^^^^^^^
116 |     
117 |     async with engine.begin() as conn:
    |
help: Remove unused import: `app.models.global_rules.GlobalRuleSettings`

E402 Module level import not at top of file
  --> app\core\database_indexes.py:16:1
   |
15 | # 延迟导入以避免循环导入
16 | from sqlalchemy import text
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `typing.Type` imported but unused
 --> app\core\dependencies.py:6:26
  |
4 | """
5 |
6 | from typing import Dict, Type, TypeVar, Optional, Any
  |                          ^^^^
7 | from functools import lru_cache
8 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.Type`

F401 [*] `json` imported but unused
 --> app\core\downloaders\transmission.py:8:8
  |
6 | from loguru import logger
7 | import base64
8 | import json
  |        ^^^^
  |
help: Remove unused import: `json`

F401 [*] `loguru.logger` imported but unused
  --> app\core\ext_indexer\auth_bridge.py:10:20
   |
 8 | from datetime import datetime
 9 | from typing import Optional
10 | from loguru import logger
   |                    ^^^^^^
11 |
12 | from app.core.ext_indexer.interfaces import ExternalAuthBridge
   |
help: Remove unused import: `loguru.logger`

F401 [*] `app.core.ext_indexer.interfaces.ExternalAuthBridge` imported but unused
  --> app\core\ext_indexer\auth_bridge.py:12:45
   |
10 | from loguru import logger
11 |
12 | from app.core.ext_indexer.interfaces import ExternalAuthBridge
   |                                             ^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.core.ext_indexer.interfaces.ExternalAuthBridge`

F401 [*] `datetime.datetime` imported but unused
  --> app\core\ext_indexer\interfaces.py:8:22
   |
 7 | from typing import Protocol, Optional, List, Dict, Any
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 |
10 | from app.core.ext_indexer.models import (
   |
help: Remove unused import: `datetime.datetime`

F821 Undefined name `ExternalAuthState`
   --> app\core\ext_indexer\interfaces.py:204:11
    |
202 |         self,
203 |         site_id: str,
204 |     ) -> "ExternalAuthState":
    |           ^^^^^^^^^^^^^^^^^
205 |         """
206 |         获取站点授权状态
    |

F401 [*] `dataclasses.dataclass` imported but unused
 --> app\core\ext_indexer\models.py:7:25
  |
5 | """
6 |
7 | from dataclasses import dataclass, field
  |                         ^^^^^^^^^
8 | from typing import Optional, Dict, Any, List
9 | from datetime import datetime
  |
help: Remove unused import

F401 [*] `dataclasses.field` imported but unused
 --> app\core\ext_indexer\models.py:7:36
  |
5 | """
6 |
7 | from dataclasses import dataclass, field
  |                                    ^^^^^
8 | from typing import Optional, Dict, Any, List
9 | from datetime import datetime
  |
help: Remove unused import

F401 [*] `app.core.ext_indexer.interfaces.ExternalIndexerRuntime` imported but unused
  --> app\core\ext_indexer\runtime.py:11:45
   |
 9 | from loguru import logger
10 |
11 | from app.core.ext_indexer.interfaces import ExternalIndexerRuntime
   |                                             ^^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.core.ext_indexer.interfaces.ExternalIndexerRuntime`

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
  --> app\core\ext_indexer\search_provider.py:79:48
   |
77 |                     async with AsyncSessionLocal() as db:
78 |                         result = await db.execute(
79 |                             select(Site).where(Site.is_active == True)
   |                                                ^^^^^^^^^^^^^^^^^^^^^^
80 |                         )
81 |                         all_sites = result.scalars().all()
   |
help: Replace with `Site.is_active`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\core\health.py:8:36
   |
 6 | from typing import Dict, Any, Optional
 7 | from datetime import datetime
 8 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
 9 | from sqlalchemy import text, select, func
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `sqlalchemy.select` imported but unused
  --> app\core\health.py:9:30
   |
 7 | from datetime import datetime
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import text, select, func
   |                              ^^^^^^
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
  --> app\core\health.py:9:38
   |
 7 | from datetime import datetime
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import text, select, func
   |                                      ^^^^
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `asyncio` imported but unused
  --> app\core\intel\service.py:14:8
   |
12 | from typing import Any, Dict, Optional
13 |
14 | import asyncio
   |        ^^^^^^^
15 | import json
16 | from pathlib import Path
   |
help: Remove unused import: `asyncio`

F401 [*] `.site_profiles.get_site_profile` imported but unused
  --> app\core\intel_local\factory.py:18:51
   |
16 | from .hr_watcher import HRWatcher
17 | from .inbox_watcher import InboxWatcher
18 | from .site_profiles import get_all_site_profiles, get_site_profile
   |                                                   ^^^^^^^^^^^^^^^^
19 | from .http_clients import SiteHttpClientRegistry, get_http_client_registry, set_http_client_registry
20 | from .http_clients_impl import HttpxSiteHttpClient
   |
help: Remove unused import: `.site_profiles.get_site_profile`

F401 [*] `.http_clients.SiteHttpClientRegistry` imported but unused
  --> app\core\intel_local\factory.py:19:27
   |
17 | from .inbox_watcher import InboxWatcher
18 | from .site_profiles import get_all_site_profiles, get_site_profile
19 | from .http_clients import SiteHttpClientRegistry, get_http_client_registry, set_http_client_registry
   |                           ^^^^^^^^^^^^^^^^^^^^^^
20 | from .http_clients_impl import HttpxSiteHttpClient
   |
help: Remove unused import

F401 [*] `.http_clients.set_http_client_registry` imported but unused
  --> app\core\intel_local\factory.py:19:77
   |
17 | from .inbox_watcher import InboxWatcher
18 | from .site_profiles import get_all_site_profiles, get_site_profile
19 | from .http_clients import SiteHttpClientRegistry, get_http_client_registry, set_http_client_registry
   |                                                                             ^^^^^^^^^^^^^^^^^^^^^^^^
20 | from .http_clients_impl import HttpxSiteHttpClient
   |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
  --> app\core\intel_local\factory.py:72:36
   |
70 |         async with AsyncSessionLocal() as db:
71 |             result = await db.execute(
72 |                 select(Site).where(Site.is_active == True, Site.cookie.isnot(None))
   |                                    ^^^^^^^^^^^^^^^^^^^^^^
73 |             )
74 |             sites = result.scalars().all()
   |
help: Replace with `Site.is_active`

F401 [*] `app.core.site_ai_adapter.load_parsed_config` imported but unused
  --> app\core\intel_local\factory.py:96:58
   |
94 |             if not matched_profile:
95 |                 try:
96 |                     from app.core.site_ai_adapter import load_parsed_config
   |                                                          ^^^^^^^^^^^^^^^^^^
97 |                     from app.core.site_ai_adapter.intel_bridge import ai_config_to_intel_profile
98 |                     from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback
   |
help: Remove unused import: `app.core.site_ai_adapter.load_parsed_config`

F401 [*] `app.core.site_ai_adapter.intel_bridge.ai_config_to_intel_profile` imported but unused
  --> app\core\intel_local\factory.py:97:71
   |
95 |                 try:
96 |                     from app.core.site_ai_adapter import load_parsed_config
97 |                     from app.core.site_ai_adapter.intel_bridge import ai_config_to_intel_profile
   |                                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^
98 |                     from app.core.intel_local.site_profiles import get_site_profile_with_ai_fallback
   |
help: Remove unused import: `app.core.site_ai_adapter.intel_bridge.ai_config_to_intel_profile`

F401 [*] `.models.HRTorrentState` imported but unused
 --> app\core\intel_local\hr_policy.py:7:21
  |
6 | from .actions import LocalIntelAction, LocalIntelActionType
7 | from .models import HRTorrentState, HRStatus
  |                     ^^^^^^^^^^^^^^
8 | from .repo import HRCasesRepository
  |
help: Remove unused import: `.models.HRTorrentState`

F401 [*] `typing.Dict` imported but unused
 --> app\core\intel_local\hr_state.py:5:20
  |
3 | import asyncio
4 | from datetime import datetime
5 | from typing import Dict, Iterable, Optional
  |                    ^^^^
6 |
7 | from .models import HRStatus, HRTorrentState, TorrentLife
  |
help: Remove unused import: `typing.Dict`

F401 [*] `.hr_cache.remove_from_cache` imported but unused
  --> app\core\intel_local\hr_state.py:8:53
   |
 7 | from .models import HRStatus, HRTorrentState, TorrentLife
 8 | from .hr_cache import get_from_cache, set_to_cache, remove_from_cache, iter_site_states as cache_iter_site_states
   |                                                     ^^^^^^^^^^^^^^^^^
 9 |
10 | def _get_hr_repository():
   |
help: Remove unused import: `.hr_cache.remove_from_cache`

F401 [*] `.http_clients.SiteHttpClient` imported but unused
  --> app\core\intel_local\http_clients_impl.py:12:27
   |
10 | from loguru import logger
11 |
12 | from .http_clients import SiteHttpClient
   |                           ^^^^^^^^^^^^^^
13 | from .site_profiles import IntelSiteProfile
   |
help: Remove unused import: `.http_clients.SiteHttpClient`

F401 [*] `datetime.timedelta` imported but unused
  --> app\core\intel_local\indexer.py:8:32
   |
 6 | from __future__ import annotations
 7 |
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from typing import List, Optional
10 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.Optional` imported but unused
  --> app\core\intel_local\indexer.py:9:26
   |
 8 | from datetime import datetime, timedelta
 9 | from typing import List, Optional
   |                          ^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `.site_profiles.IntelSiteProfile` imported but unused
  --> app\core\intel_local\indexer.py:12:28
   |
10 | from loguru import logger
11 |
12 | from .site_profiles import IntelSiteProfile, get_site_profile
   |                            ^^^^^^^^^^^^^^^^
13 | from .http_clients import get_http_client_registry
14 | from .scheduler_hooks import before_pt_scan
   |
help: Remove unused import: `.site_profiles.IntelSiteProfile`

F401 [*] `.parsers.torrent_list_parser.ParsedTorrentRow` imported but unused
  --> app\core\intel_local\indexer.py:18:5
   |
16 |     parse_torrent_list_page_generic,
17 |     parse_torrent_list_page_hdsky,
18 |     ParsedTorrentRow,
   |     ^^^^^^^^^^^^^^^^
19 | )
20 | from .repo import (
   |
help: Remove unused import: `.parsers.torrent_list_parser.ParsedTorrentRow`

F541 [*] f-string without any placeholders
   --> app\core\intel_local\indexer.py:164:38
    |
162 |                     # 如果连续失败，停止扫描
163 |                     if len(errors) >= 3:
164 |                         logger.error(f"LocalIntel Indexer: 连续失败3次，停止扫描")
    |                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
165 |                         break
166 |                     page += 1
    |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\hr_html_parser.py:114:25
    |
112 |                             date_str = date_match.group(1).replace("/", "-")
113 |                             deadline = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
114 |                         except:
    |                         ^^^^^^
115 |                             try:
116 |                                 deadline = datetime.strptime(date_str, "%Y-%m-%d")
    |

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\hr_html_parser.py:117:29
    |
115 | …                     try:
116 | …                         deadline = datetime.strptime(date_str, "%Y-%m-%d")
117 | …                     except:
    |                       ^^^^^^
118 | …                         pass
    |

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\inbox_html_parser.py:107:25
    |
105 |                             date_str = date_match.group(1).replace("/", "-")
106 |                             created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
107 |                         except:
    |                         ^^^^^^
108 |                             try:
109 |                                 created_at = datetime.strptime(date_str, "%Y-%m-%d")
    |

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\inbox_html_parser.py:110:29
    |
108 |                             try:
109 |                                 created_at = datetime.strptime(date_str, "%Y-%m-%d")
110 |                             except:
    |                             ^^^^^^
111 |                                 pass
112 |                         break
    |

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\inbox_html_parser.py:201:25
    |
199 |                             subject = "（无主题）"  # TTG 可能有无主题消息
200 |                             body = "\n".join(lines[1:]) if len(lines) > 1 else first_line
201 |                         except:
    |                         ^^^^^^
202 |                             subject = first_line
203 |                             body = "\n".join(lines[1:]) if len(lines) > 1 else None
    |

F401 [*] `typing.Optional` imported but unused
  --> app\core\intel_local\parsers\torrent_list_parser.py:10:26
   |
 8 | from dataclasses import dataclass
 9 | from datetime import datetime
10 | from typing import List, Optional
   |                          ^^^^^^^^
11 | import re
12 | from bs4 import BeautifulSoup
   |
help: Remove unused import: `typing.Optional`

E722 Do not use bare `except`
   --> app\core\intel_local\parsers\torrent_list_parser.py:164:25
    |
162 |                             date_str = date_match.group(1).replace("/", "-")
163 |                             published_at = datetime.strptime(date_str, "%Y-%m-%d")
164 |                         except:
    |                         ^^^^^^
165 |                             pass
    |

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\core\intel_local\repo\sqlalchemy.py:13:38
   |
11 | from typing import Callable, Iterable, Optional, List
12 |
13 | from sqlalchemy import select, and_, or_, func, case
   |                                      ^^^
14 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
  --> app\core\intel_local\repo\sqlalchemy.py:13:43
   |
11 | from typing import Callable, Iterable, Optional, List
12 |
13 | from sqlalchemy import select, and_, or_, func, case
   |                                           ^^^^
14 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `sqlalchemy.case` imported but unused
  --> app\core\intel_local\repo\sqlalchemy.py:13:49
   |
11 | from typing import Callable, Iterable, Optional, List
12 |
13 | from sqlalchemy import select, and_, or_, func, case
   |                                                 ^^^^
14 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `typing.Iterable` imported but unused
 --> app\core\intel_local\repo\torrent_index_repo.py:9:20
  |
7 | from dataclasses import dataclass
8 | from datetime import datetime
9 | from typing import Iterable, Optional, Protocol, List
  |                    ^^^^^^^^
  |
help: Remove unused import: `typing.Iterable`

F401 [*] `os` imported but unused
 --> app\core\legacy_adapter.py:7:8
  |
6 | import sys
7 | import os
  |        ^^
8 | from pathlib import Path
9 | from typing import Dict, List, Optional, Any, Callable
  |
help: Remove unused import: `os`

F401 [*] `typing.List` imported but unused
  --> app\core\legacy_adapter.py:9:26
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Callable
   |                          ^^^^
10 | import importlib.util
11 | import logging
   |
help: Remove unused import

F401 [*] `typing.Callable` imported but unused
  --> app\core\legacy_adapter.py:9:47
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Callable
   |                                               ^^^^^^^^
10 | import importlib.util
11 | import logging
   |
help: Remove unused import

F401 [*] `logging` imported but unused
  --> app\core\legacy_adapter.py:11:8
   |
 9 | from typing import Dict, List, Optional, Any, Callable
10 | import importlib.util
11 | import logging
   |        ^^^^^^^
12 | from loguru import logger
   |
help: Remove unused import: `logging`

F401 [*] `os` imported but unused
 --> app\core\legacy_adapter_improved.py:6:8
  |
5 | import sys
6 | import os
  |        ^^
7 | from pathlib import Path
8 | from typing import Dict, List, Optional, Any
  |
help: Remove unused import: `os`

F401 [*] `typing.List` imported but unused
  --> app\core\legacy_adapter_improved.py:8:26
   |
 6 | import os
 7 | from pathlib import Path
 8 | from typing import Dict, List, Optional, Any
   |                          ^^^^
 9 | import importlib.util
10 | import importlib
   |
help: Remove unused import: `typing.List`

F841 [*] Local variable `e` is assigned to but never used
   --> app\core\legacy_adapter_improved.py:177:29
    |
175 |             logger.info(f"创建实例: {function_name}")
176 |             return instance
177 |         except TypeError as e:
    |                             ^
178 |             # 如果无参构造失败，尝试使用默认参数
179 |             try:
    |
help: Remove assignment to unused variable `e`

F401 [*] `sys` imported but unused
 --> app\core\legacy_validator.py:6:8
  |
4 | """
5 |
6 | import sys
  |        ^^^
7 | import os
8 | from pathlib import Path
  |
help: Remove unused import: `sys`

F401 [*] `os` imported but unused
 --> app\core\legacy_validator.py:7:8
  |
6 | import sys
7 | import os
  |        ^^
8 | from pathlib import Path
9 | from typing import Dict, List, Optional, Any, Tuple
  |
help: Remove unused import: `os`

F401 [*] `pathlib.Path` imported but unused
  --> app\core\legacy_validator.py:8:21
   |
 6 | import sys
 7 | import os
 8 | from pathlib import Path
   |                     ^^^^
 9 | from typing import Dict, List, Optional, Any, Tuple
10 | import importlib.util
   |
help: Remove unused import: `pathlib.Path`

F401 [*] `typing.List` imported but unused
  --> app\core\legacy_validator.py:9:26
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Tuple
   |                          ^^^^
10 | import importlib.util
11 | import traceback
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\core\legacy_validator.py:9:32
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Tuple
   |                                ^^^^^^^^
10 | import importlib.util
11 | import traceback
   |
help: Remove unused import

F401 [*] `typing.Tuple` imported but unused
  --> app\core\legacy_validator.py:9:47
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Tuple
   |                                               ^^^^^
10 | import importlib.util
11 | import traceback
   |
help: Remove unused import

F401 [*] `importlib.util` imported but unused
  --> app\core\legacy_validator.py:10:8
   |
 8 | from pathlib import Path
 9 | from typing import Dict, List, Optional, Any, Tuple
10 | import importlib.util
   |        ^^^^^^^^^^^^^^
11 | import traceback
12 | from loguru import logger
   |
help: Remove unused import: `importlib.util`

F541 [*] f-string without any placeholders
   --> app\core\legacy_validator.py:189:27
    |
188 |                 if version_result["errors"]:
189 |                     print(f"      错误:")
    |                           ^^^^^^^^^^^^^^
190 |                     for error in version_result["errors"]:
191 |                         print(f"        - {error}")
    |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
  --> app\core\legacy_wrapper.py:63:28
   |
61 |             if hasattr(engine, "get_recommendations"):
62 |                 try:
63 |                     import asyncio
   |                            ^^^^^^^
64 |                     import inspect
65 |                     method = getattr(engine, "get_recommendations")
   |
help: Remove unused import: `asyncio`

F401 [*] `concurrent.futures` imported but unused
  --> app\core\log_handler.py:59:24
   |
57 |             except RuntimeError:
58 |                 # 如果没有运行中的事件循环，使用线程池
59 |                 import concurrent.futures
   |                        ^^^^^^^^^^^^^^^^^^
60 |                 import threading
   |
help: Remove unused import: `concurrent.futures`

F401 [*] `logging` imported but unused
 --> app\core\logging.py:5:8
  |
3 | """
4 |
5 | import logging
  |        ^^^^^^^
6 | import sys
7 | from pathlib import Path
  |
help: Remove unused import: `logging`

F401 [*] `app.models.plugin.PluginType` imported but unused
   --> app\core\migrations\steps.py:173:35
    |
172 |     from sqlalchemy import text
173 |     from app.models.plugin import PluginType
    |                                   ^^^^^^^^^^
174 |     
175 |     # 添加远程插件相关字段
    |
help: Remove unused import: `app.models.plugin.PluginType`

F401 [*] `json` imported but unused
 --> app\core\music_clients\netease.py:6:8
  |
4 | """
5 | import aiohttp
6 | import json
  |        ^^^^
7 | from typing import Dict, List, Optional, Any
8 | from loguru import logger
  |
help: Remove unused import: `json`

F401 [*] `typing.List` imported but unused
  --> app\core\network_context.py:9:20
   |
 8 | from enum import Enum
 9 | from typing import List
   |                    ^^^^
10 | from fastapi import Request
11 | import ipaddress
   |
help: Remove unused import: `typing.List`

F401 [*] `typing.Tuple` imported but unused
  --> app\core\ocr.py:10:30
   |
 8 | import base64
 9 | import asyncio
10 | from typing import Optional, Tuple, Dict, Any
   |                              ^^^^^
11 | from loguru import logger
12 | import httpx
   |
help: Remove unused import: `typing.Tuple`

F401 [*] `io.BytesIO` imported but unused
   --> app\core\ocr.py:365:28
    |
363 |             import cv2
364 |             import numpy as np
365 |             from io import BytesIO
    |                            ^^^^^^^
366 |             
367 |             # 解码Base64
    |
help: Remove unused import: `io.BytesIO`

F401 [*] `numpy` imported but unused
   --> app\core\ocr.py:401:29
    |
399 |         try:
400 |             import cv2
401 |             import numpy as np
    |                             ^^
402 |             
403 |             # 转换为灰度图
    |
help: Remove unused import: `numpy`

F401 [*] `typing.List` imported but unused
  --> app\core\performance.py:8:26
   |
 6 | import time
 7 | import asyncio
 8 | from typing import Dict, List, Optional, Callable, Any
   |                          ^^^^
 9 | from functools import wraps
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\core\performance.py:8:32
   |
 6 | import time
 7 | import asyncio
 8 | from typing import Dict, List, Optional, Callable, Any
   |                                ^^^^^^^^
 9 | from functools import wraps
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\core\performance.py:11:32
   |
 9 | from functools import wraps
10 | from loguru import logger
11 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
12 | from collections import defaultdict
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `asyncio` imported but unused
 --> app\core\plugins\file_watcher.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import time
8 | from pathlib import Path
  |
help: Remove unused import: `asyncio`

F401 [*] `typing.Set` imported but unused
  --> app\core\plugins\hot_reload.py:12:41
   |
10 | from datetime import datetime
11 | from pathlib import Path
12 | from typing import Any, Dict, Optional, Set
   |                                         ^^^
13 |
14 | from fastapi import APIRouter
   |
help: Remove unused import: `typing.Set`

F401 [*] `watchdog.events.FileCreatedEvent` imported but unused
  --> app\core\plugins\hot_reload.py:17:5
   |
15 | from loguru import logger
16 | from watchdog.events import (
17 |     FileCreatedEvent,
   |     ^^^^^^^^^^^^^^^^
18 |     FileDeletedEvent,
19 |     FileModifiedEvent,
   |
help: Remove unused import

F401 [*] `watchdog.events.FileDeletedEvent` imported but unused
  --> app\core\plugins\hot_reload.py:18:5
   |
16 | from watchdog.events import (
17 |     FileCreatedEvent,
18 |     FileDeletedEvent,
   |     ^^^^^^^^^^^^^^^^
19 |     FileModifiedEvent,
20 |     FileSystemEventHandler,
   |
help: Remove unused import

F401 [*] `watchdog.events.FileModifiedEvent` imported but unused
  --> app\core\plugins\hot_reload.py:19:5
   |
17 |     FileCreatedEvent,
18 |     FileDeletedEvent,
19 |     FileModifiedEvent,
   |     ^^^^^^^^^^^^^^^^^
20 |     FileSystemEventHandler,
21 | )
   |
help: Remove unused import

F401 [*] `os` imported but unused
 --> app\core\rsshub\client.py:5:8
  |
3 | """
4 |
5 | import os
  |        ^^
6 | import httpx
7 | from typing import Optional
  |
help: Remove unused import: `os`

F841 [*] Local variable `e` is assigned to but never used
  --> app\core\rsshub\client.py:52:42
   |
50 |                 response.raise_for_status()
51 |                 return response.text
52 |         except httpx.TimeoutException as e:
   |                                          ^
53 |             logger.error(f"RSSHub请求超时: {url}, 超时时间: {self.timeout}秒")
54 |             raise
   |
help: Remove assignment to unused variable `e`

F401 [*] `typing.Any` imported but unused
 --> app\core\scheduler.py:7:46
  |
6 | import asyncio
7 | from typing import Dict, Optional, Callable, Any, List
  |                                              ^^^
8 | from datetime import datetime, timedelta
9 | from loguru import logger
  |
help: Remove unused import: `typing.Any`

F401 [*] `datetime.timedelta` imported but unused
  --> app\core\scheduler.py:8:32
   |
 6 | import asyncio
 7 | from typing import Dict, Optional, Callable, Any, List
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from loguru import logger
10 | from apscheduler.schedulers.asyncio import AsyncIOScheduler
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `datetime.timedelta` imported but unused
   --> app\core\scheduler.py:451:44
    |
449 |             from app.modules.settings.service import SettingsService
450 |             from sqlalchemy import select
451 |             from datetime import datetime, timedelta
    |                                            ^^^^^^^^^
452 |             
453 |             async with AsyncSessionLocal() as session:
    |
help: Remove unused import: `datetime.timedelta`

F541 [*] f-string without any placeholders
   --> app\core\site_ai_adapter\service.py:167:30
    |
166 |             if not result:
167 |                 logger.error(f"AI 适配分析失败: 返回 None")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
168 |                 return None
    |
help: Remove extraneous `f` prefix

F401 [*] `fastapi.WebSocketDisconnect` imported but unused
 --> app\core\websocket.py:4:32
  |
2 | WebSocket管理
3 | """
4 | from fastapi import WebSocket, WebSocketDisconnect
  |                                ^^^^^^^^^^^^^^^^^^^
5 | from typing import Dict, List
6 | from loguru import logger
  |
help: Remove unused import: `fastapi.WebSocketDisconnect`

F401 [*] `asyncio` imported but unused
 --> app\core\websocket.py:8:8
  |
6 | from loguru import logger
7 | import json
8 | import asyncio
  |        ^^^^^^^
  |
help: Remove unused import: `asyncio`

F401 [*] `app.core.database.AsyncSession` imported but unused
  --> app\graphql\schema.py:10:31
   |
 8 | from strawberry.types import Info
 9 |
10 | from app.core.database import AsyncSession
   |                               ^^^^^^^^^^^^
11 | from app.core.plugins.hot_reload import get_hot_reload_manager
12 | from app.graphql.types import (
   |
help: Remove unused import: `app.core.database.AsyncSession`

F401 [*] `datetime.datetime` imported but unused
  --> app\middleware\performance.py:12:22
   |
10 | from loguru import logger
11 | from collections import defaultdict
12 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
13 | import json
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\middleware\performance.py:12:32
   |
10 | from loguru import logger
11 | from collections import defaultdict
12 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
13 | import json
   |
help: Remove unused import

F401 [*] `json` imported but unused
  --> app\middleware\performance.py:13:8
   |
11 | from collections import defaultdict
12 | from datetime import datetime, timedelta
13 | import json
   |        ^^^^
14 |
15 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `json`

F401 [*] `app.core.database.AsyncSessionLocal` imported but unused
  --> app\middleware\performance.py:15:31
   |
13 | import json
14 |
15 | from app.core.database import AsyncSessionLocal
   |                               ^^^^^^^^^^^^^^^^^
16 | from sqlalchemy import text
   |
help: Remove unused import: `app.core.database.AsyncSessionLocal`

F401 [*] `sqlalchemy.text` imported but unused
  --> app\middleware\performance.py:16:24
   |
15 | from app.core.database import AsyncSessionLocal
16 | from sqlalchemy import text
   |                        ^^^^
   |
help: Remove unused import: `sqlalchemy.text`

F401 `app.models.rsshub.RSSHubSource` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\models\__init__.py:25:31
   |
23 | from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
24 | from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
25 | from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
   |                               ^^^^^^^^^^^^
26 | from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
27 | from app.models.multimodal_metrics import (
   |
help: Add unused import `RSSHubSource` to __all__

F401 `app.models.rsshub.RSSHubComposite` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\models\__init__.py:25:45
   |
23 | from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
24 | from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
25 | from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
   |                                             ^^^^^^^^^^^^^^^
26 | from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
27 | from app.models.multimodal_metrics import (
   |
help: Add unused import `RSSHubComposite` to __all__

F401 `app.models.rsshub.UserRSSHubSubscription` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\models\__init__.py:25:62
   |
23 | from app.models.cloud_storage import CloudStorage, CloudStorageAuth  # 云存储
24 | from app.models.rss_subscription import RSSSubscription, RSSItem  # RSS订阅
25 | from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
   |                                                              ^^^^^^^^^^^^^^^^^^^^^^
26 | from app.models.subtitle import Subtitle, SubtitleDownloadHistory  # 字幕
27 | from app.models.multimodal_metrics import (
   |
help: Add unused import `UserRSSHubSubscription` to __all__

F811 [*] Redefinition of unused `AISiteAdapter` from line 15
  --> app\models\__init__.py:66:40
   |
64 |     TorrentIndex,
65 | )  # Local Intel
66 | from app.models.ai_site_adapter import AISiteAdapter  # 站点 AI 适配配置
   |                                        ^^^^^^^^^^^^^ `AISiteAdapter` redefined here
67 | from app.models.inbox import InboxRunLog  # 统一收件箱运行日志
68 | from app.models.ebook import EBook, EBookFile  # 电子书
   |
  ::: app\models\__init__.py:15:40
   |
13 | from app.models.site_icon import SiteIcon
14 | from app.models.site_domain import SiteDomainConfig
15 | from app.models.ai_site_adapter import AISiteAdapter
   |                                        ------------- previous definition of `AISiteAdapter` here
16 | from app.models.notification import Notification
17 | from app.models.music import Music, MusicFile, MusicSubscription, MusicTrack, MusicPlaylist, MusicLibrary  # VabHub特色功能（包含统一收         …
   |
help: Remove definition: `AISiteAdapter`

F401 `app.models.inbox.InboxRunLog` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\models\__init__.py:67:30
   |
65 | )  # Local Intel
66 | from app.models.ai_site_adapter import AISiteAdapter  # 站点 AI 适配配置
67 | from app.models.inbox import InboxRunLog  # 统一收件箱运行日志
   |                              ^^^^^^^^^^^
68 | from app.models.ebook import EBook, EBookFile  # 电子书
69 | from app.models.audiobook import AudiobookFile  # 有声书
   |
help: Add unused import `InboxRunLog` to __all__

F401 [*] `sqlalchemy.Text` imported but unused
 --> app\models\audiobook.py:5:68
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Index
  |                                                                    ^^^^
6 | from datetime import datetime
7 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `sqlalchemy.Index` imported but unused
 --> app\models\audiobook.py:5:93
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Index
  |                                                                                             ^^^^^
6 | from datetime import datetime
7 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `datetime.datetime` imported but unused
 --> app\models\backup.py:8:22
  |
6 | from sqlalchemy.sql import func
7 | from app.core.database import Base
8 | from datetime import datetime
  |                      ^^^^^^^^
9 | from typing import Dict, Any, Optional
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.Optional` imported but unused
 --> app\models\backup.py:9:31
  |
7 | from app.core.database import Base
8 | from datetime import datetime
9 | from typing import Dict, Any, Optional
  |                               ^^^^^^^^
  |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.timedelta` imported but unused
  --> app\models\cache.py:8:32
   |
 6 | from sqlalchemy import Column, String, Text, DateTime, Integer, Index
 7 | from sqlalchemy.sql import func
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 |
10 | from app.core.database import Base
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `sqlalchemy.Text` imported but unused
 --> app\models\directory.py:4:58
  |
2 | 目录配置数据模型
3 | """
4 | from sqlalchemy import Column, Integer, String, Boolean, Text, Index
  |                                                          ^^^^
5 | from sqlalchemy.ext.declarative import declarative_base
6 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.Text`

F401 [*] `sqlalchemy.ext.declarative.declarative_base` imported but unused
 --> app\models\directory.py:5:40
  |
3 | """
4 | from sqlalchemy import Column, Integer, String, Boolean, Text, Index
5 | from sqlalchemy.ext.declarative import declarative_base
  |                                        ^^^^^^^^^^^^^^^^
6 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.ext.declarative.declarative_base`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\download.py:5:78
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
  |                                                                              ^^^^^^^
6 | from datetime import datetime
7 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `sqlalchemy.Text` imported but unused
 --> app\models\global_rules.py:6:59
  |
4 | """
5 |
6 | from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
  |                                                           ^^^^
7 | from datetime import datetime
8 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\global_rules.py:6:65
  |
4 | """
5 |
6 | from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
  |                                                                 ^^^^^^^
7 | from datetime import datetime
8 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `sqlalchemy.JSON` imported but unused
 --> app\models\hnr.py:4:93
  |
2 | HNR检测相关模型
3 | """
4 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
  |                                                                                             ^^^^
5 | from datetime import datetime
6 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.JSON`

F401 [*] `sqlalchemy.Float` imported but unused
 --> app\models\intel_local.py:6:65
  |
4 | """
5 |
6 | from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Index
  |                                                                 ^^^^^
7 | from datetime import datetime
8 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.Float`

F401 [*] `app.modules.hr_case.models.HrCase` imported but unused
  --> app\models\intel_local.py:13:50
   |
11 | # HRCase 模型已迁移至 app/modules/hr_case/models.py
12 | # 为了向后兼容，提供别名导入
13 | from app.modules.hr_case.models import HrCase as HRCase
   |                                                  ^^^^^^
   |
help: Remove unused import: `app.modules.hr_case.models.HrCase`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\manga_download_job.py:5:5
  |
3 | """
4 | from sqlalchemy import (
5 |     Boolean,
  |     ^^^^^^^
6 |     Column,
7 |     DateTime,
  |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `datetime.datetime` imported but unused
 --> app\models\manga_source.py:4:22
  |
2 | 漫画源模型
3 | """
4 | from datetime import datetime
  |                      ^^^^^^^^
5 | from sqlalchemy import (
6 |     Boolean,
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.Text` imported but unused
 --> app\models\music_chart_item.py:7:59
  |
5 | """
6 |
7 | from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
  |                                                           ^^^^
8 | from datetime import datetime
9 | import hashlib
  |
help: Remove unused import: `sqlalchemy.Text`

F401 [*] `datetime.datetime` imported but unused
 --> app\models\novel_inbox_import_log.py:8:22
  |
6 | from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum, Text
7 | from sqlalchemy.orm import relationship
8 | from datetime import datetime
  |                      ^^^^^^^^
9 | import enum
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.List` imported but unused
  --> app\models\plugin.py:14:30
   |
12 | from enum import Enum
13 | from datetime import datetime
14 | from typing import Optional, List
   |                              ^^^^
15 |
16 | from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, JSON, Boolean
   |
help: Remove unused import: `typing.List`

F401 [*] `typing.Optional` imported but unused
  --> app\models\plugin_config.py:9:20
   |
 8 | from datetime import datetime
 9 | from typing import Optional
   |                    ^^^^^^^^
10 |
11 | from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
   |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.Index` imported but unused
  --> app\models\plugin_config.py:11:65
   |
 9 | from typing import Optional
10 |
11 | from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
   |                                                                 ^^^^^
12 | from sqlalchemy.sql import func
   |
help: Remove unused import: `sqlalchemy.Index`

F401 [*] `sqlalchemy.and_` imported but unused
 --> app\models\rsshub.py:5:93
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Table, and_
  |                                                                                             ^^^^
6 | from sqlalchemy.orm import relationship, foreign
7 | from sqlalchemy.sql import func
  |
help: Remove unused import: `sqlalchemy.and_`

F401 [*] `sqlalchemy.orm.foreign` imported but unused
 --> app\models\rsshub.py:6:42
  |
5 | from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Table, and_
6 | from sqlalchemy.orm import relationship, foreign
  |                                          ^^^^^^^
7 | from sqlalchemy.sql import func
8 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.orm.foreign`

F401 [*] `datetime.datetime` imported but unused
  --> app\models\rsshub.py:8:22
   |
 6 | from sqlalchemy.orm import relationship, foreign
 7 | from sqlalchemy.sql import func
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 |
10 | from app.core.database import Base
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.JSON` imported but unused
 --> app\models\search_history.py:4:59
  |
2 | 搜索历史模型
3 | """
4 | from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
  |                                                           ^^^^
5 | from datetime import datetime
6 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.JSON`

F401 [*] `sqlalchemy.JSON` imported but unused
 --> app\models\storage_monitor.py:5:68
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Index, Text
  |                                                                    ^^^^
6 | from datetime import datetime
7 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.JSON`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\strm.py:5:80
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Float, BigInteger, Text, JSON, Boolean, ForeignKey, Index
  |                                                                                ^^^^^^^
6 | from sqlalchemy.orm import relationship
7 | from sqlalchemy.sql import func
  |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `sqlalchemy.sql.func` imported but unused
 --> app\models\strm.py:7:28
  |
5 | from sqlalchemy import Column, Integer, String, Float, BigInteger, Text, JSON, Boolean, ForeignKey, Index
6 | from sqlalchemy.orm import relationship
7 | from sqlalchemy.sql import func
  |                            ^^^^
8 | from datetime import datetime
9 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.sql.func`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\subscription_refresh.py:6:49
  |
4 | """
5 |
6 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
  |                                                 ^^^^^^^
7 | from datetime import datetime
8 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `datetime.datetime` imported but unused
 --> app\models\system_health.py:6:22
  |
4 | """
5 |
6 | from datetime import datetime
  |                      ^^^^^^^^
7 | from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
8 | from app.core.database import Base
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.sql.func` imported but unused
 --> app\models\transfer_history.py:7:28
  |
6 | from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Index
7 | from sqlalchemy.sql import func
  |                            ^^^^
8 | from datetime import datetime
9 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.sql.func`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\tts_job.py:7:49
  |
5 | """
6 |
7 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
  |                                                 ^^^^^^^
8 | from datetime import datetime
9 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `sqlalchemy.Index` imported but unused
 --> app\models\tts_job.py:7:92
  |
5 | """
6 |
7 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
  |                                                                                            ^^^^^
8 | from datetime import datetime
9 | from app.core.database import Base
  |
help: Remove unused import

F401 [*] `sqlalchemy.orm.declarative_base` imported but unused
 --> app\models\tts_storage_cleanup_log.py:7:28
  |
5 | """
6 | from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Text
7 | from sqlalchemy.orm import declarative_base
  |                            ^^^^^^^^^^^^^^^^
8 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.orm.declarative_base`

F401 [*] `datetime.datetime` imported but unused
  --> app\models\tts_storage_cleanup_log.py:8:22
   |
 6 | from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Text
 7 | from sqlalchemy.orm import declarative_base
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 |
10 | from app.core.database import Base
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.models.tts_voice_preset.TTSVoicePreset` imported but unused
  --> app\models\tts_work_profile.py:15:45
   |
14 | if TYPE_CHECKING:
15 |     from app.models.tts_voice_preset import TTSVoicePreset
   |                                             ^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.models.tts_voice_preset.TTSVoicePreset`

F401 [*] `typing.Optional` imported but unused
 --> app\models\upload.py:7:20
  |
5 | from datetime import datetime
6 | from enum import Enum
7 | from typing import Optional, Dict, Any
  |                    ^^^^^^^^
8 | from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, Index, ForeignKey
9 | from sqlalchemy.orm import relationship
  |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.Boolean` imported but unused
  --> app\models\upload.py:8:62
   |
 6 | from enum import Enum
 7 | from typing import Optional, Dict, Any
 8 | from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, Index, ForeignKey
   |                                                              ^^^^^^^
 9 | from sqlalchemy.orm import relationship
10 | from sqlalchemy.dialects.postgresql import UUID
   |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `sqlalchemy.dialects.postgresql.UUID` imported but unused
  --> app\models\upload.py:10:44
   |
 8 | from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, Index, ForeignKey
 9 | from sqlalchemy.orm import relationship
10 | from sqlalchemy.dialects.postgresql import UUID
   |                                            ^^^^
11 | from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
12 | import uuid
   |
help: Remove unused import: `sqlalchemy.dialects.postgresql.UUID`

F401 [*] `sqlalchemy.dialects.sqlite.JSON` imported but unused
  --> app\models\upload.py:11:48
   |
 9 | from sqlalchemy.orm import relationship
10 | from sqlalchemy.dialects.postgresql import UUID
11 | from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
   |                                                ^^^^^^^^^^
12 | import uuid
   |
help: Remove unused import: `sqlalchemy.dialects.sqlite.JSON`

F401 [*] `sqlalchemy.Enum` imported but unused
 --> app\models\user.py:6:68
  |
4 | """
5 |
6 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
  |                                                                    ^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy.orm import relationship
  |
help: Remove unused import: `sqlalchemy.Enum`

F401 [*] `sqlalchemy.BigInteger` imported but unused
 --> app\models\user_audiobook_progress.py:6:41
  |
4 | 记录用户对每本作品的播放进度
5 | """
6 | from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint
  |                                         ^^^^^^^^^^
7 | from sqlalchemy.orm import relationship
  |
help: Remove unused import: `sqlalchemy.BigInteger`

F401 [*] `sqlalchemy.String` imported but unused
 --> app\models\user_favorite_media.py:5:51
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, DateTime, String, Enum, ForeignKey, UniqueConstraint, Index, func
  |                                                   ^^^^^^
6 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.String`

F401 [*] `datetime.datetime` imported but unused
 --> app\models\user_favorite_media.py:6:22
  |
5 | from sqlalchemy import Column, Integer, DateTime, String, Enum, ForeignKey, UniqueConstraint, Index, func
6 | from datetime import datetime
  |                      ^^^^^^^^
7 |
8 | from app.core.database import Base
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.Boolean` imported but unused
 --> app\models\user_manga_follow.py:4:41
  |
2 | from datetime import datetime
3 |
4 | from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String, UniqueConstraint, Index
  |                                         ^^^^^^^
5 |
6 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.Boolean`

F401 [*] `sqlalchemy.orm.relationship` imported but unused
  --> app\models\user_notification.py:8:28
   |
 7 | from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, JSON
 8 | from sqlalchemy.orm import relationship
   |                            ^^^^^^^^^^^^
 9 |
10 | from app.core.database import Base
   |
help: Remove unused import: `sqlalchemy.orm.relationship`

F401 [*] `app.models.enums.notification_type.NotificationType` imported but unused
  --> app\models\user_notification.py:11:48
   |
10 | from app.core.database import Base
11 | from app.models.enums.notification_type import NotificationType
   |                                                ^^^^^^^^^^^^^^^^
12 | from app.models.enums.reading_media_type import ReadingMediaType
   |
help: Remove unused import: `app.models.enums.notification_type.NotificationType`

F401 [*] `app.models.enums.reading_media_type.ReadingMediaType` imported but unused
  --> app\models\user_notification.py:12:49
   |
10 | from app.core.database import Base
11 | from app.models.enums.notification_type import NotificationType
12 | from app.models.enums.reading_media_type import ReadingMediaType
   |                                                 ^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.models.enums.reading_media_type.ReadingMediaType`

F401 [*] `sqlalchemy.orm.relationship` imported but unused
  --> app\models\user_notify_channel.py:12:28
   |
10 | from datetime import datetime
11 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
12 | from sqlalchemy.orm import relationship
   |                            ^^^^^^^^^^^^
13 |
14 | from app.core.database import Base
   |
help: Remove unused import: `sqlalchemy.orm.relationship`

F401 [*] `datetime.datetime` imported but unused
  --> app\models\user_notify_preference.py:11:22
   |
 9 | """
10 |
11 | from datetime import datetime
   |                      ^^^^^^^^
12 | from sqlalchemy import (
13 |     Column, Integer, Boolean, DateTime, ForeignKey, Index,
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.orm.relationship` imported but unused
  --> app\models\user_telegram_binding.py:8:28
   |
 6 | from datetime import datetime
 7 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey
 8 | from sqlalchemy.orm import relationship
   |                            ^^^^^^^^^^^^
 9 |
10 | from app.core.database import Base
   |
help: Remove unused import: `sqlalchemy.orm.relationship`

F401 [*] `sqlalchemy.BigInteger` imported but unused
 --> app\models\user_video_progress.py:6:41
  |
4 | 记录用户对每个视频作品的播放进度
5 | """
6 | from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, Float, String
  |                                         ^^^^^^^^^^
7 | from sqlalchemy.orm import relationship
  |
help: Remove unused import: `sqlalchemy.BigInteger`

F401 [*] `datetime.datetime` imported but unused
 --> app\models\work_link.py:8:22
  |
7 | from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
8 | from datetime import datetime
  |                      ^^^^^^^^
9 | from app.core.database import Base
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.JSON` imported but unused
 --> app\models\workflow.py:5:74
  |
3 | """
4 |
5 | from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
  |                                                                          ^^^^
6 | from datetime import datetime
7 | from app.core.database import Base
  |
help: Remove unused import: `sqlalchemy.JSON`

F401 [*] `urllib.parse.urljoin` imported but unused
 --> app\modules\alert_channels\bark.py:7:26
  |
6 | import httpx
7 | from urllib.parse import urljoin
  |                          ^^^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `urllib.parse.urljoin`

F401 [*] `os` imported but unused
 --> app\modules\audiobook\importer.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import shutil
9 | import re
  |
help: Remove unused import: `os`

F401 [*] `typing.Mapping` imported but unused
  --> app\modules\audiobook\importer.py:11:41
   |
 9 | import re
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any, Mapping
   |                                         ^^^^^^^
12 | from datetime import datetime
13 | from loguru import logger
   |
help: Remove unused import: `typing.Mapping`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\audiobook\importer.py:12:22
   |
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any, Mapping
12 | from datetime import datetime
   |                      ^^^^^^^^
13 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `asyncio` imported but unused
 --> app\modules\backup\service.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import gzip
8 | import json
  |
help: Remove unused import: `asyncio`

F401 [*] `sqlalchemy.inspect` imported but unused
  --> app\modules\backup\service.py:15:32
   |
13 | from dataclasses import dataclass
14 | from sqlalchemy.ext.asyncio import AsyncSession
15 | from sqlalchemy import select, inspect, text, delete
   |                                ^^^^^^^
16 | from sqlalchemy.orm import class_mapper
17 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.text` imported but unused
  --> app\modules\backup\service.py:15:41
   |
13 | from dataclasses import dataclass
14 | from sqlalchemy.ext.asyncio import AsyncSession
15 | from sqlalchemy import select, inspect, text, delete
   |                                         ^^^^
16 | from sqlalchemy.orm import class_mapper
17 | from loguru import logger
   |
help: Remove unused import

E722 Do not use bare `except`
   --> app\modules\backup\service.py:447:29
    |
445 | …                     try:
446 | …                         item_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
447 | …                     except:
    |                       ^^^^^^
448 | …                         pass
    |

F401 [*] `asyncio` imported but unused
 --> app\modules\backup\tasks.py:5:8
  |
3 | """
4 |
5 | import asyncio
  |        ^^^^^^^
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from loguru import logger
  |
help: Remove unused import: `asyncio`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
 --> app\modules\backup\tasks.py:6:36
  |
5 | import asyncio
6 | from sqlalchemy.ext.asyncio import AsyncSession
  |                                    ^^^^^^^^^^^^
7 | from loguru import logger
  |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 `app.modules.bots.commands.basic` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:10:5
   |
 8 | # 导入所有命令模块以注册处理器
 9 | from app.modules.bots.commands import (
10 |     basic,
   |     ^^^^^
11 |     menu,
12 |     search,
   |
help: Add unused import `basic` to __all__

F401 `app.modules.bots.commands.menu` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:11:5
   |
 9 | from app.modules.bots.commands import (
10 |     basic,
11 |     menu,
   |     ^^^^
12 |     search,
13 |     subscriptions,
   |
help: Add unused import `menu` to __all__

F401 `app.modules.bots.commands.search` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:12:5
   |
10 |     basic,
11 |     menu,
12 |     search,
   |     ^^^^^^
13 |     subscriptions,
14 |     downloads,
   |
help: Add unused import `search` to __all__

F401 `app.modules.bots.commands.subscriptions` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:13:5
   |
11 |     menu,
12 |     search,
13 |     subscriptions,
   |     ^^^^^^^^^^^^^
14 |     downloads,
15 |     reading,
   |
help: Add unused import `subscriptions` to __all__

F401 `app.modules.bots.commands.downloads` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:14:5
   |
12 |     search,
13 |     subscriptions,
14 |     downloads,
   |     ^^^^^^^^^
15 |     reading,
16 |     shelf,  # 书架/收藏视角命令
   |
help: Add unused import `downloads` to __all__

F401 `app.modules.bots.commands.reading` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:15:5
   |
13 |     subscriptions,
14 |     downloads,
15 |     reading,
   |     ^^^^^^^
16 |     shelf,  # 书架/收藏视角命令
17 |     admin,
   |
help: Add unused import `reading` to __all__

F401 `app.modules.bots.commands.shelf` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:16:5
   |
14 |     downloads,
15 |     reading,
16 |     shelf,  # 书架/收藏视角命令
   |     ^^^^^
17 |     admin,
18 |     notif,
   |
help: Add unused import `shelf` to __all__

F401 `app.modules.bots.commands.admin` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:17:5
   |
15 |     reading,
16 |     shelf,  # 书架/收藏视角命令
17 |     admin,
   |     ^^^^^
18 |     notif,
19 |     notify,  # 通知偏好命令
   |
help: Add unused import `admin` to __all__

F401 `app.modules.bots.commands.notif` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:18:5
   |
16 |     shelf,  # 书架/收藏视角命令
17 |     admin,
18 |     notif,
   |     ^^^^^
19 |     notify,  # 通知偏好命令
20 |     music,  # 音乐中心命令
   |
help: Add unused import `notif` to __all__

F401 `app.modules.bots.commands.notify` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:19:5
   |
17 |     admin,
18 |     notif,
19 |     notify,  # 通知偏好命令
   |     ^^^^^^
20 |     music,  # 音乐中心命令
21 | )
   |
help: Add unused import `notify` to __all__

F401 `app.modules.bots.commands.music` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> app\modules\bots\commands\__init__.py:20:5
   |
18 |     notif,
19 |     notify,  # 通知偏好命令
20 |     music,  # 音乐中心命令
   |     ^^^^^
21 | )
   |
help: Add unused import `music` to __all__

F401 [*] `app.modules.bots.telegram_keyboard.inline_keyboard` imported but unused
  --> app\modules\bots\commands\admin.py:14:48
   |
12 | from app.modules.bots.telegram_router import router
13 | from app.modules.bots.telegram_context import TelegramUpdateContext
14 | from app.modules.bots.telegram_keyboard import inline_keyboard, inline_button
   |                                                ^^^^^^^^^^^^^^^
   |
help: Remove unused import

F401 [*] `app.modules.bots.telegram_keyboard.inline_button` imported but unused
  --> app\modules\bots\commands\admin.py:14:65
   |
12 | from app.modules.bots.telegram_router import router
13 | from app.modules.bots.telegram_context import TelegramUpdateContext
14 | from app.modules.bots.telegram_keyboard import inline_keyboard, inline_button
   |                                                                 ^^^^^^^^^^^^^
   |
help: Remove unused import

F821 Undefined name `_cmd_health`
  --> app\modules\bots\commands\admin.py:31:15
   |
29 |         await _show_admin_help(ctx)
30 |     elif args == "health":
31 |         await _cmd_health(ctx)
   |               ^^^^^^^^^^^
32 |     elif args == "alerts":
33 |         await _cmd_alerts(ctx)
   |

F821 Undefined name `_cmd_alerts`
  --> app\modules\bots\commands\admin.py:33:15
   |
31 |         await _cmd_health(ctx)
32 |     elif args == "alerts":
33 |         await _cmd_alerts(ctx)
   |               ^^^^^^^^^^^
34 |     elif args == "disks":
35 |         await _cmd_disks(ctx)
   |

F821 Undefined name `_cmd_disks`
  --> app\modules\bots\commands\admin.py:35:15
   |
33 |         await _cmd_alerts(ctx)
34 |     elif args == "disks":
35 |         await _cmd_disks(ctx)
   |               ^^^^^^^^^^
36 |     elif args == "ping":
37 |         await _cmd_ping(ctx)
   |

F821 Undefined name `_cmd_ping`
  --> app\modules\bots\commands\admin.py:37:15
   |
35 |         await _cmd_disks(ctx)
36 |     elif args == "ping":
37 |         await _cmd_ping(ctx)
   |               ^^^^^^^^^
38 |     elif args == "errors":
39 |         await _cmd_errors(ctx)
   |

F821 Undefined name `_cmd_errors`
  --> app\modules\bots\commands\admin.py:39:15
   |
37 |         await _cmd_ping(ctx)
38 |     elif args == "errors":
39 |         await _cmd_errors(ctx)
   |               ^^^^^^^^^^^
40 |     elif args == "safety_status":
41 |         await _cmd_safety_status(ctx)
   |

F541 [*] f-string without any placeholders
  --> app\modules\bots\commands\admin.py:66:24
   |
65 |             # 全局设置
66 |             message += f"🔧 **全局设置**:\n"
   |                        ^^^^^^^^^^^^^^^^^^^^^
67 |             message += f"• 安全模式: {global_settings.get('mode', 'SAFE')}\n"
68 |             message += f"• HR保护: {'✅ 启用' if global_settings.get('hr_protection_enabled') else '❌ 禁用'}\n"
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\bots\commands\admin.py:74:24
   |
73 |             # HR案例统计
74 |             message += f"📊 **HR案例统计**:\n"
   |                        ^^^^^^^^^^^^^^^^^^^^^^^
75 |             message += f"• 总案例数: {hr_stats.get('total', 0)}\n"
76 |             message += f"• 活跃案例: {hr_stats.get('active', 0)}\n"
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\bots\commands\admin.py:81:24
   |
80 |             # 最近的安全事件
81 |             message += f"📋 **最近安全事件**:\n"
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^
82 |             # TODO: 添加安全事件查询逻辑
83 |             message += "• 暂无最近事件\n\n"
   |
help: Remove extraneous `f` prefix

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\bots\commands\basic.py:9:22
   |
 8 | from loguru import logger
 9 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
10 | from typing import Dict, List, Tuple
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\bots\commands\basic.py:9:32
   |
 8 | from loguru import logger
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from typing import Dict, List, Tuple
   |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
  --> app\modules\bots\commands\basic.py:10:20
   |
 8 | from loguru import logger
 9 | from datetime import datetime, timedelta
10 | from typing import Dict, List, Tuple
   |                    ^^^^
11 |
12 | from app.modules.bots.telegram_router import router
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
  --> app\modules\bots\commands\basic.py:10:26
   |
 8 | from loguru import logger
 9 | from datetime import datetime, timedelta
10 | from typing import Dict, List, Tuple
   |                          ^^^^
11 |
12 | from app.modules.bots.telegram_router import router
   |
help: Remove unused import

F401 [*] `typing.Tuple` imported but unused
  --> app\modules\bots\commands\basic.py:10:32
   |
 8 | from loguru import logger
 9 | from datetime import datetime, timedelta
10 | from typing import Dict, List, Tuple
   |                                ^^^^^
11 |
12 | from app.modules.bots.telegram_router import router
   |
help: Remove unused import

F821 Undefined name `select`
   --> app\modules\bots\commands\basic.py:380:16
    |
378 |     try:
379 |         # 查询订阅并检查权限
380 |         stmt = select(Subscription).where(Subscription.id == subscription_id)
    |                ^^^^^^
381 |         result = await ctx.session.execute(stmt)
382 |         subscription = result.scalar_one_or_none()
    |

F821 Undefined name `select`
   --> app\modules\bots\commands\basic.py:464:16
    |
462 |     try:
463 |         # 查询订阅并检查权限
464 |         stmt = select(Subscription).where(Subscription.id == subscription_id)
    |                ^^^^^^
465 |         result = await ctx.session.execute(stmt)
466 |         subscription = result.scalar_one_or_none()
    |

F841 Local variable `old_status` is assigned to but never used
   --> app\modules\bots\commands\basic.py:477:9
    |
476 |         # 切换状态
477 |         old_status = subscription.status
    |         ^^^^^^^^^^
478 |         if subscription.status == "active":
479 |             subscription.status = "paused"
    |
help: Remove assignment to unused variable `old_status`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:495:16
    |
493 |         media_type_text = "电影" if subscription.media_type == "movie" else "美剧"
494 |         
495 |         text = f"✅ *订阅状态更新成功*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
496 |         text += f"#{subscription_id} {media_type_text}《{subscription.title}》\n"
497 |         text += f"状态已切换为：【{new_status_text}】"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:587:17
    |
586 |         text += "💡 *创建订阅：*\n"
587 |         text += f"/sub_create 1  # 以第 1 条结果创建订阅（安全模式）\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
588 |         text += f"/sub_create 2  # 以第 2 条结果创建订阅\n"
589 |         text += "...\n\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:588:17
    |
586 |         text += "💡 *创建订阅：*\n"
587 |         text += f"/sub_create 1  # 以第 1 条结果创建订阅（安全模式）\n"
588 |         text += f"/sub_create 2  # 以第 2 条结果创建订阅\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
589 |         text += "...\n\n"
590 |         text += "⏰ 搜索结果缓存 10 分钟，请及时选择"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:713:16
    |
711 |         year_text = f" ({item.year})" if item.year else ""
712 |         
713 |         text = f"✅ *订阅创建成功*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
714 |         text += f"订阅ID：#{new_subscription.id}\n"
715 |         text += f"目标：{media_type_text}《{item.title}》{year_text}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:718:17
    |
716 |         text += f"TMDB ID：{item.tmdb_id}\n"
717 |         text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
718 |         text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
719 |         text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:803:20
    |
802 |             # 格式化响应
803 |             text = f"✅ *订阅创建成功*\n\n"
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^
804 |             text += f"订阅ID：#{new_subscription.id}\n"
805 |             text += f"目标：{new_subscription.title}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:808:21
    |
806 |             text += f"TMDB ID：{tmdb_id}\n"
807 |             text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
808 |             text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
809 |             text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:826:16
    |
824 |         year_text = f" ({year})" if year else ""
825 |         
826 |         text = f"✅ *订阅创建成功*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
827 |         text += f"订阅ID：#{new_subscription.id}\n"
828 |         text += f"目标：{media_type_text}《{title}》{year_text}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:831:17
    |
829 |         text += f"TMDB ID：{tmdb_id}\n"
830 |         text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
831 |         text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
832 |         text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:870:16
    |
869 |         # 格式化响应
870 |         text = f"✅ *订阅创建成功*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
871 |         text += f"订阅ID：#{new_subscription.id}\n"
872 |         text += f"目标：{new_subscription.title}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:875:17
    |
873 |         text += f"TMDB ID：{tmdb_id}\n"
874 |         text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
875 |         text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
876 |         text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:901:12
    |
900 |     # 简化实现：引导用户使用Web界面
901 |     text = f"🔍 *快速下载功能*\n\n"
    |            ^^^^^^^^^^^^^^^^^^^^^^^^
902 |     text += f"搜索关键词：{query}\n\n"
903 |     text += "⚠️ *此功能正在开发中*\n\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\basic.py:942:12
    |
941 |     # 简化实现：引导用户使用Web界面
942 |     text = f"⚡ *创建下载任务*\n\n"
    |            ^^^^^^^^^^^^^^^^^^^^^^^^
943 |     text += f"选择索引：{index}\n\n"
944 |     text += "⚠️ *此功能正在开发中*\n\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\downloads.py:302:12
    |
300 |     }
301 |     
302 |     text = f"📋 *任务详情*\n\n"
    |            ^^^^^^^^^^^^^^^^^^^^
303 |     text += f"📌 *{job.title}*\n"
304 |     text += f"类型: {type_names.get(job.job_type, job.job_type)}\n"
    |
help: Remove extraneous `f` prefix

F401 [*] `app.modules.bots.telegram_keyboard.parse_callback_data` imported but unused
  --> app\modules\bots\commands\menu.py:15:5
   |
13 |     inline_keyboard,
14 |     inline_button,
15 |     parse_callback_data,
   |     ^^^^^^^^^^^^^^^^^^^
16 | )
   |
help: Remove unused import: `app.modules.bots.telegram_keyboard.parse_callback_data`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:571:16
    |
570 |         # 构建详情文本
571 |         text = f"🎵 *音乐订阅详情*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
572 |         text += f"ID: *#{sub.id}*\n"
573 |         text += f"类型: {type_name}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:579:17
    |
577 |         text += f"状态: {status_icon} {status_name}\n"
578 |         text += f"安全策略: {security}\n\n"
579 |         text += f"📊 *最近运行:*\n"
    |                 ^^^^^^^^^^^^^^^^^^^
580 |         text += f"- 最近运行: {_format_datetime(sub.last_run_at)}\n"
581 |         text += f"- 新增曲目: {sub.last_run_new_count or 0}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:584:17
    |
582 |         text += f"- 搜索数量: {sub.last_run_search_count or 0}\n"
583 |         text += f"- 下载任务: {sub.last_run_download_count or 0}\n\n"
584 |         text += f"🔧 *操作:*\n"
    |                 ^^^^^^^^^^^^^^^
585 |         text += f"- 试运行: `/music_sub_check {sub.id}`\n"
586 |         text += f"- 真实执行: `/music_sub_run {sub.id}`\n"
    |
help: Remove extraneous `f` prefix

F841 Local variable `processing_msg` is assigned to but never used
   --> app\modules\bots\commands\music.py:645:9
    |
644 |         # 发送处理中消息
645 |         processing_msg = await ctx.reply_text("🔄 正在试运行订阅...")
    |         ^^^^^^^^^^^^^^
646 |         
647 |         # 执行试运行
    |
help: Remove assignment to unused variable `processing_msg`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:655:16
    |
654 |         # 构建结果文本
655 |         text = f"✅ *试运行完成*（不会创建真实下载任务）\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
656 |         text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
657 |         text += f"当前状态: {status_icon} {status_name}\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:659:17
    |
657 |         text += f"当前状态: {status_icon} {status_name}\n"
658 |         text += f"安全策略: {security}\n\n"
659 |         text += f"📊 *本次统计:*\n"
    |                 ^^^^^^^^^^^^^^^^^^^
660 |         text += f"- 原始候选: {result.found_total}\n"
661 |         text += f"- 过滤: "
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:661:17
    |
659 |         text += f"📊 *本次统计:*\n"
660 |         text += f"- 原始候选: {result.found_total}\n"
661 |         text += f"- 过滤: "
    |                 ^^^^^^^^^^^
662 |         
663 |         if result.filtered_out:
    |
help: Remove extraneous `f` prefix

F841 Local variable `processing_msg` is assigned to but never used
   --> app\modules\bots\commands\music.py:752:9
    |
751 |         # 发送处理中消息
752 |         processing_msg = await ctx.reply_text("🔄 正在执行订阅...")
    |         ^^^^^^^^^^^^^^
753 |         
754 |         # 执行真实运行
    |
help: Remove assignment to unused variable `processing_msg`

F841 Local variable `filtered_total` is assigned to but never used
   --> app\modules\bots\commands\music.py:758:9
    |
757 |         # 构建统计信息
758 |         filtered_total = sum(result.filtered_out.values()) if result.filtered_out else 0
    |         ^^^^^^^^^^^^^^
759 |         
760 |         # 构建结果文本
    |
help: Remove assignment to unused variable `filtered_total`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:761:16
    |
760 |         # 构建结果文本
761 |         text = f"✅ *订阅执行完成*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
762 |         text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
763 |         text += f"安全策略: {security}\n\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:764:17
    |
762 |         text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
763 |         text += f"安全策略: {security}\n\n"
764 |         text += f"📊 *本次统计:*\n"
    |                 ^^^^^^^^^^^^^^^^^^^
765 |         text += f"- 原始候选: {result.found_total}\n"
766 |         text += f"- 过滤: "
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:766:17
    |
764 |         text += f"📊 *本次统计:*\n"
765 |         text += f"- 原始候选: {result.found_total}\n"
766 |         text += f"- 过滤: "
    |                 ^^^^^^^^^^^
767 |         
768 |         if result.filtered_out:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:793:21
    |
792 |         if result.created_tasks > 0:
793 |             text += f"\n\n💡 你可以在 Web 端的「下载任务」中查看详细进度。"
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
794 |         
795 |         # 更新消息
    |
help: Remove extraneous `f` prefix

F841 Local variable `old_status` is assigned to but never used
   --> app\modules\bots\commands\music.py:856:9
    |
855 |         # 切换状态
856 |         old_status = sub.status
    |         ^^^^^^^^^^
857 |         sub.status = "paused" if sub.status == "active" else "active"
    |
help: Remove assignment to unused variable `old_status`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:866:16
    |
864 |         new_status_icon = "✅" if sub.status == "active" else "⏸"
865 |         
866 |         text = f"✅ *已切换订阅状态*\n\n"
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^
867 |         text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
868 |         text += f"新状态: {new_status_icon} {new_status_name}\n\n"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:869:17
    |
867 |         text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
868 |         text += f"新状态: {new_status_icon} {new_status_name}\n\n"
869 |         text += f"📝 *说明:*\n"
    |                 ^^^^^^^^^^^^^^^
870 |         text += f"- 激活时: 系统会根据你的设置自动参与音乐订阅执行\n"
871 |         text += f"- 暂停时: 不会再自动执行，但你仍然可以用 `/music_sub_check {sub_id}` 试运行"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\music.py:870:17
    |
868 |         text += f"新状态: {new_status_icon} {new_status_name}\n\n"
869 |         text += f"📝 *说明:*\n"
870 |         text += f"- 激活时: 系统会根据你的设置自动参与音乐订阅执行\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
871 |         text += f"- 暂停时: 不会再自动执行，但你仍然可以用 `/music_sub_check {sub_id}` 试运行"
    |
help: Remove extraneous `f` prefix

F401 [*] `loguru.logger` imported but unused
  --> app\modules\bots\commands\notify.py:8:20
   |
 6 | """
 7 |
 8 | from loguru import logger
   |                    ^^^^^^
 9 |
10 | from app.modules.bots.telegram_router import router
   |
help: Remove unused import: `loguru.logger`

F401 [*] `app.modules.bots.telegram_keyboard.build_back_to_menu_button` imported but unused
  --> app\modules\bots\commands\notify.py:17:5
   |
15 |     callback_data,
16 |     parse_callback_data,
17 |     build_back_to_menu_button,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^
18 | )
19 | from app.services import notify_preference_service
   |
help: Remove unused import: `app.modules.bots.telegram_keyboard.build_back_to_menu_button`

F401 [*] `app.schemas.reading_status.ReadingStatusHelper` imported but unused
  --> app\modules\bots\commands\reading.py:26:40
   |
24 | from app.services.reading_control_service import mark_reading_finished, add_favorite_from_reading, ReadingControlError
25 | from app.schemas.reading_hub import ReadingOngoingItem, ReadingActivityItem
26 | from app.schemas.reading_status import ReadingStatusHelper
   |                                        ^^^^^^^^^^^^^^^^^^^
27 | from app.models.enums.reading_media_type import ReadingMediaType
28 | from app.core.config import settings
   |
help: Remove unused import: `app.schemas.reading_status.ReadingStatusHelper`

F841 Local variable `type_names` is assigned to but never used
  --> app\modules\bots\commands\reading.py:67:5
   |
65 |         ReadingMediaType.MANGA: "🖼"
66 |     }
67 |     type_names = {
   |     ^^^^^^^^^^
68 |         ReadingMediaType.NOVEL: "小说",
69 |         ReadingMediaType.AUDIOBOOK: "有声书",
   |
help: Remove assignment to unused variable `type_names`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\reading.py:480:9
    |
479 |     lines = [
480 |         f"👉 打开 Web 继续阅读：",
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^
481 |         web_url
482 |     ]
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\reading.py:517:9
    |
516 |     lines = [
517 |         f"已为你打开：",
    |         ^^^^^^^^^^^^^^^
518 |         f"{icon}《{item.title}》 · {item.activity_label or '继续阅读'}",
519 |         "",
    |
help: Remove extraneous `f` prefix

F841 Local variable `shelf_item` is assigned to but never used
   --> app\modules\bots\commands\reading.py:603:9
    |
601 |     # 调用 Service 层执行收藏操作
602 |     try:
603 |         shelf_item = await add_favorite_from_reading(
    |         ^^^^^^^^^^
604 |             session=ctx.session,
605 |             user_id=ctx.user_id,
    |
help: Remove assignment to unused variable `shelf_item`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\bots\commands\search.py:9:32
   |
 7 | """
 8 |
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from typing import Optional
11 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\shelf.py:306:9
    |
305 |     lines = [
306 |         f"📚 书架条目详情（只读模式）",
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
307 |         "",
308 |         f"{_get_media_type_label(item.media_type)}《{item.title}》",
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\shelf.py:362:9
    |
361 |     lines = [
362 |         f"👉 打开 Web 页面：",
    |         ^^^^^^^^^^^^^^^^^^^^^
363 |         web_url
364 |     ]
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\bots\commands\subscriptions.py:256:12
    |
254 |     status_text = "✅ 启用" if item.status == "enabled" else "⏸ 暂停"
255 |     
256 |     text = f"📋 *订阅详情*\n\n"
    |            ^^^^^^^^^^^^^^^^^^^^
257 |     text += f"📌 *{item.title}*\n"
258 |     text += f"类型: {kind_names.get(item.kind, item.kind)}\n"
    |
help: Remove extraneous `f` prefix

F811 Redefinition of unused `commands` from line 18
  --> app\modules\bots\telegram_bot_handlers.py:59:5
   |
57 |         return False
58 |     
59 |     commands = [
   |     ^^^^^^^^ `commands` redefined here
60 |         {"command": "start", "description": "绑定账号 / 打开主菜单"},
61 |         {"command": "menu", "description": "打开主菜单"},
   |
  ::: app\modules\bots\telegram_bot_handlers.py:18:30
   |
17 | # 导入所有命令模块以注册处理器
18 | from app.modules.bots import commands  # noqa: F401
   |                              -------- previous definition of `commands` here
   |
help: Remove definition: `commands`

F401 [*] `app.schemas.reading_hub.ReadingShelfItem` imported but unused
  --> app\modules\bots\telegram_bot_state.py:13:78
   |
11 | from app.services.tmdb_search_service import TmdbSearchItem
12 | from app.services.download_search_service import SafeDownloadCandidate
13 | from app.schemas.reading_hub import ReadingOngoingItem, ReadingActivityItem, ReadingShelfItem
   |                                                                              ^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.schemas.reading_hub.ReadingShelfItem`

F821 Undefined name `ReadingShelfCache`
   --> app\modules\bots\telegram_bot_state.py:486:23
    |
484 | reading_list_cache = ReadingListCache()
485 | reading_activity_cache = ReadingActivityCache()
486 | reading_shelf_cache = ReadingShelfCache()
    |                       ^^^^^^^^^^^^^^^^^
    |

F401 [*] `loguru.logger` imported but unused
  --> app\modules\bots\telegram_context.py:10:20
   |
 8 | from typing import Any, Optional
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from loguru import logger
   |                    ^^^^^^
11 |
12 | from app.models.user import User
   |
help: Remove unused import: `loguru.logger`

F401 [*] `typing.Any` imported but unused
 --> app\modules\bots\telegram_keyboard.py:9:20
  |
8 | import json
9 | from typing import Any, Optional
  |                    ^^^
  |
help: Remove unused import: `typing.Any`

F401 [*] `datetime.timedelta` imported but unused
 --> app\modules\calendar\service.py:4:32
  |
2 | 日历服务
3 | """
4 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
5 | from typing import List, Optional
  |
help: Remove unused import: `datetime.timedelta`

F401 [*] `asyncio` imported but unused
 --> app\modules\charts\service.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import logging
8 | from typing import Dict, List, Optional, Any
  |
help: Remove unused import: `asyncio`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\charts\service.py:9:22
   |
 7 | import logging
 8 | from typing import Dict, List, Optional, Any
 9 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
10 | import json
11 | import aiohttp
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\charts\service.py:9:32
   |
 7 | import logging
 8 | from typing import Dict, List, Optional, Any
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | import json
11 | import aiohttp
   |
help: Remove unused import

F401 [*] `app.core.music_clients.NeteaseClient` imported but unused
  --> app\modules\charts\service.py:16:51
   |
14 | from bs4 import BeautifulSoup
15 |
16 | from app.core.music_clients import SpotifyClient, NeteaseClient, QQMusicClient
   |                                                   ^^^^^^^^^^^^^
17 | from app.modules.settings.service import SettingsService
18 | from app.core.cache import get_cache
   |
help: Remove unused import

F401 [*] `app.core.music_clients.QQMusicClient` imported but unused
  --> app\modules\charts\service.py:16:66
   |
14 | from bs4 import BeautifulSoup
15 |
16 | from app.core.music_clients import SpotifyClient, NeteaseClient, QQMusicClient
   |                                                                  ^^^^^^^^^^^^^
17 | from app.modules.settings.service import SettingsService
18 | from app.core.cache import get_cache
   |
help: Remove unused import

F811 Redefinition of unused `logger` from line 13
  --> app\modules\charts\service.py:21:1
   |
19 | from app.modules.charts.providers.chart_row import ChartRow
20 |
21 | logger = logging.getLogger(__name__)
   | ^^^^^^ `logger` redefined here
   |
  ::: app\modules\charts\service.py:13:20
   |
11 | import aiohttp
12 | from sqlalchemy.ext.asyncio import AsyncSession
13 | from loguru import logger
   |                    ------ previous definition of `logger` here
14 | from bs4 import BeautifulSoup
   |
help: Remove definition: `logger`

F811 [*] Redefinition of unused `datetime` from line 9
   --> app\modules\charts\service.py:180:30
    |
178 |             ChartRow格式的数据列表（字典格式，便于JSON序列化）
179 |         """
180 |         from datetime import datetime
    |                              ^^^^^^^^ `datetime` redefined here
181 |         
182 |         chart_rows = []
    |
   ::: app\modules\charts\service.py:9:22
    |
  7 | import logging
  8 | from typing import Dict, List, Optional, Any
  9 | from datetime import datetime, timedelta
    |                      -------- previous definition of `datetime` here
 10 | import json
 11 | import aiohttp
    |
help: Remove definition: `datetime`

F541 [*] f-string without any placeholders
   --> app\modules\charts\service.py:352:19
    |
351 |             # 使用第三方API
352 |             url = f"https://netease-cloud-music-api-psi-six.vercel.app/playlist/detail"
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
353 |             params = {
354 |                 'id': playlist_id
    |
help: Remove extraneous `f` prefix

F841 Local variable `items_found` is assigned to but never used
   --> app\modules\charts\service.py:625:33
    |
623 | …                     items = soup.select(selector)
624 | …                     if items:
625 | …                         items_found = True
    |                           ^^^^^^^^^^^
626 | …                         for li in items:
627 | …                             # 提取标题
    |
help: Remove assignment to unused variable `items_found`

F541 [*] f-string without any placeholders
   --> app\modules\charts\service.py:679:65
    |
677 | …                     'duration': 0,  # Billboard页面通常不提供时长
678 | …                     'platform': 'billboard_china',
679 | …                     'external_url': f"https://www.billboard.com/charts/china-tme-uni-songs/",
    |                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
680 | …                     'image_url': None,  # Billboard页面通常不提供封面图URL
681 | …                     'popularity': popularity,
    |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
 --> app\modules\charts\video_charts.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import logging
8 | from typing import Dict, List, Optional, Any
  |
help: Remove unused import: `asyncio`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\charts\video_charts.py:9:22
   |
 7 | import logging
 8 | from typing import Dict, List, Optional, Any
 9 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
10 | import httpx
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\charts\video_charts.py:9:32
   |
 7 | import logging
 8 | from typing import Dict, List, Optional, Any
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | import httpx
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F811 Redefinition of unused `logger` from line 12
  --> app\modules\charts\video_charts.py:19:1
   |
17 | from app.modules.charts.providers.imdb_datasets import IMDBDatasetsProvider
18 |
19 | logger = logging.getLogger(__name__)
   | ^^^^^^ `logger` redefined here
   |
  ::: app\modules\charts\video_charts.py:12:20
   |
10 | import httpx
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from loguru import logger
   |                    ------ previous definition of `logger` here
13 |
14 | from app.modules.settings.service import SettingsService
   |
help: Remove definition: `logger`

F401 [*] `sqlalchemy.update` imported but unused
  --> app\modules\cloud_storage\service.py:8:32
   |
 6 | from typing import List, Optional, Dict, Any, Tuple
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, update, delete
   |                                ^^^^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.update`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\cloud_storage\service.py:9:32
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, update, delete
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
  --> app\modules\cloud_storage\service.py:94:48
   |
92 |         """获取所有已启用的云存储配置"""
93 |         try:
94 |             query = select(CloudStorage).where(CloudStorage.enabled == True)
   |                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
95 |             result = await self.db.execute(query)
96 |             return list(result.scalars().all())
   |
help: Replace with `CloudStorage.enabled`

E722 Do not use bare `except`
   --> app\modules\cloud_storage\service.py:244:17
    |
242 |                 try:
243 |                     await provider.close()
244 |                 except:
    |                 ^^^^^^
245 |                     pass
246 |             del self._providers[storage_id]
    |

F401 [*] `os` imported but unused
 --> app\modules\comic\importer.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import shutil
9 | import re
  |
help: Remove unused import: `os`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\comic\importer.py:12:22
   |
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any
12 | from datetime import datetime
   |                      ^^^^^^^^
13 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

E722 Do not use bare `except`
   --> app\modules\comic\importer.py:217:25
    |
215 |                         try:
216 |                             parsed_volume_index = int(parsed_volume_index)
217 |                         except:
    |                         ^^^^^^
218 |                             parsed_volume_index = None
    |

F401 [*] `re` imported but unused
 --> app\modules\comic\work_resolver.py:7:8
  |
5 | """
6 |
7 | import re
  |        ^^
8 | from typing import Optional
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `re`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\modules\cookiecloud\service.py:11:40
   |
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 | from sqlalchemy import select, update, and_
   |                                        ^^^^
12 | from sqlalchemy.orm import Session
13 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.and_`

F401 [*] `app.schemas.cookiecloud.SiteCookieSyncResult` imported but unused
  --> app\modules\cookiecloud\service.py:20:5
   |
18 | from app.schemas.cookiecloud import (
19 |     CookieCloudSyncResult, 
20 |     SiteCookieSyncResult,
   |     ^^^^^^^^^^^^^^^^^^^^
21 |     CookieCloudSiteSyncResult,
22 |     CookieSource
   |
help: Remove unused import: `app.schemas.cookiecloud.SiteCookieSyncResult`

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
   --> app\modules\cookiecloud\service.py:445:36
    |
443 |             # 2. 获取所有启用的站点
444 |             result = await self.db.execute(
445 |                 select(Site).where(Site.is_active == True)
    |                                    ^^^^^^^^^^^^^^^^^^^^^^
446 |             )
447 |             sites = result.scalars().all()
    |
help: Replace with `Site.is_active`

E712 Avoid equality comparisons to `True`; use `DashboardLayout.is_default:` for truth checks
  --> app\modules\dashboard\layout_service.py:41:25
   |
39 |                 result = await self.db.execute(
40 |                     select(DashboardLayout).where(
41 |                         DashboardLayout.is_default == True
   |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
42 |                     ).limit(1)
43 |                 )
   |
help: Replace with `DashboardLayout.is_default`

E712 Avoid equality comparisons to `True`; use `DashboardLayout.is_default:` for truth checks
   --> app\modules\dashboard\layout_service.py:149:47
    |
147 |         try:
148 |             result = await self.db.execute(
149 |                 select(DashboardLayout).where(DashboardLayout.is_default == True)
    |                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
150 |             )
151 |             layouts = result.scalars().all()
    |
help: Replace with `DashboardLayout.is_default`

F401 [*] `os` imported but unused
  --> app\modules\dashboard\service.py:10:8
   |
 8 | import psutil
 9 | import platform
10 | import os
   |        ^^
11 | import logging
   |
help: Remove unused import: `os`

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:20:1
   |
18 | logger = getattr(loguru_logger, "bind", lambda **_: loguru_logger)(module="dashboard_service")
19 |
20 | from app.models.media import Media, MediaFile
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.models.download import DownloadTask
22 | from app.models.subscription import Subscription
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:21:1
   |
20 | from app.models.media import Media, MediaFile
21 | from app.models.download import DownloadTask
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from app.models.subscription import Subscription
23 | from app.models.tts_job import TTSJob
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:22:1
   |
20 | from app.models.media import Media, MediaFile
21 | from app.models.download import DownloadTask
22 | from app.models.subscription import Subscription
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 | from app.models.tts_job import TTSJob
24 | from app.models.plugin import Plugin
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:23:1
   |
21 | from app.models.download import DownloadTask
22 | from app.models.subscription import Subscription
23 | from app.models.tts_job import TTSJob
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
24 | from app.models.plugin import Plugin
25 | from app.models.user_novel_reading_progress import UserNovelReadingProgress
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:24:1
   |
22 | from app.models.subscription import Subscription
23 | from app.models.tts_job import TTSJob
24 | from app.models.plugin import Plugin
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
25 | from app.models.user_novel_reading_progress import UserNovelReadingProgress
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:25:1
   |
23 | from app.models.tts_job import TTSJob
24 | from app.models.plugin import Plugin
25 | from app.models.user_novel_reading_progress import UserNovelReadingProgress
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
27 | from app.models.manga_reading_progress import MangaReadingProgress
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:26:1
   |
24 | from app.models.plugin import Plugin
25 | from app.models.user_novel_reading_progress import UserNovelReadingProgress
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
27 | from app.models.manga_reading_progress import MangaReadingProgress
28 | from app.services.reading_hub_service import get_reading_stats
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:27:1
   |
25 | from app.models.user_novel_reading_progress import UserNovelReadingProgress
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
27 | from app.models.manga_reading_progress import MangaReadingProgress
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
28 | from app.services.reading_hub_service import get_reading_stats
29 | from app.core.cache import get_cache
   |

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:28:1
   |
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
27 | from app.models.manga_reading_progress import MangaReadingProgress
28 | from app.services.reading_hub_service import get_reading_stats
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
29 | from app.core.cache import get_cache
   |

F401 [*] `app.services.reading_hub_service.get_reading_stats` imported but unused
  --> app\modules\dashboard\service.py:28:46
   |
26 | from app.models.user_audiobook_progress import UserAudiobookProgress
27 | from app.models.manga_reading_progress import MangaReadingProgress
28 | from app.services.reading_hub_service import get_reading_stats
   |                                              ^^^^^^^^^^^^^^^^^
29 | from app.core.cache import get_cache
   |
help: Remove unused import: `app.services.reading_hub_service.get_reading_stats`

E402 Module level import not at top of file
  --> app\modules\dashboard\service.py:29:1
   |
27 | from app.models.manga_reading_progress import MangaReadingProgress
28 | from app.services.reading_hub_service import get_reading_stats
29 | from app.core.cache import get_cache
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\dashboard\service.py:107:29
    |
105 |                 "network_recv": network.bytes_recv
106 |             }
107 |         except Exception as e:
    |                             ^
108 |             # 如果psutil不可用，返回默认值
109 |             return {
    |
help: Remove assignment to unused variable `e`

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\dashboard\service.py:180:29
    |
178 |                 "by_quality": by_quality
179 |             }
180 |         except Exception as e:
    |                             ^
181 |             return {
182 |                 "total_movies": 0,
    |
help: Remove assignment to unused variable `e`

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\dashboard\service.py:253:29
    |
251 |                 "downloaded_gb": round(downloaded_gb, 2)
252 |             }
253 |         except Exception as e:
    |                             ^
254 |             return {
255 |                 "active": 0,
    |
help: Remove assignment to unused variable `e`

F401 [*] `app.models.music.MusicLibrary` imported but unused
   --> app\modules\dashboard\service.py:406:69
    |
405 |         try:
406 |             from app.models.music import MusicTrack, MusicPlaylist, MusicLibrary
    |                                                                     ^^^^^^^^^^^^
407 |             
408 |             # 统计曲目数量
    |
help: Remove unused import: `app.models.music.MusicLibrary`

E712 Avoid equality comparisons to `True`; use `Plugin.is_quarantined:` for truth checks
   --> app\modules\dashboard\service.py:599:68
    |
598 |             # 统计被隔离的插件数
599 |             quarantined_stmt = select(func.count(Plugin.id)).where(Plugin.is_quarantined == True)
    |                                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
600 |             quarantined_result = await self.db.execute(quarantined_stmt)
601 |             quarantined_plugins = quarantined_result.scalar() or 0
    |
help: Replace with `Plugin.is_quarantined`

F811 Redefinition of unused `get_reading_stats` from line 28
   --> app\modules\dashboard\service.py:621:15
    |
619 |             }
620 |     
621 |     async def get_reading_stats(self) -> Dict:
    |               ^^^^^^^^^^^^^^^^^ `get_reading_stats` redefined here
622 |         """获取阅读统计（系统级）"""
623 |         try:
    |
   ::: app\modules\dashboard\service.py:28:46
    |
 26 | from app.models.user_audiobook_progress import UserAudiobookProgress
 27 | from app.models.manga_reading_progress import MangaReadingProgress
 28 | from app.services.reading_hub_service import get_reading_stats
    |                                              ----------------- previous definition of `get_reading_stats` here
 29 | from app.core.cache import get_cache
    |
help: Remove definition: `get_reading_stats`

E712 Avoid equality comparisons to `False`; use `not UserNovelReadingProgress.is_finished:` for false checks
   --> app\modules\dashboard\service.py:641:17
    |
639 |             # 统计活跃小说数（未读完）
640 |             novels_stmt = select(func.count(UserNovelReadingProgress.id)).where(
641 |                 UserNovelReadingProgress.is_finished == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
642 |             )
643 |             novels_result = await self.db.execute(novels_stmt)
    |
help: Replace with `not UserNovelReadingProgress.is_finished`

E712 Avoid equality comparisons to `False`; use `not UserAudiobookProgress.is_finished:` for false checks
   --> app\modules\dashboard\service.py:648:17
    |
646 |             # 统计活跃有声书数（未听完）
647 |             audiobooks_stmt = select(func.count(UserAudiobookProgress.id)).where(
648 |                 UserAudiobookProgress.is_finished == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
649 |             )
650 |             audiobooks_result = await self.db.execute(audiobooks_stmt)
    |
help: Replace with `not UserAudiobookProgress.is_finished`

F541 [*] f-string without any placeholders
   --> app\modules\dashboard\service.py:734:30
    |
732 |                 events.append({
733 |                     "type": "tts_completed",
734 |                     "title": f"TTS任务完成",
    |                              ^^^^^^^^^^^^^^
735 |                     "time": row.finished_at.isoformat() if row.finished_at else None,
736 |                     "message": f"电子书ID: {row.ebook_id}",
    |
help: Remove extraneous `f` prefix

F401 [*] `time` imported but unused
  --> app\modules\douban\client.py:8:8
   |
 6 | import hashlib
 7 | import hmac
 8 | import time
   |        ^^^^
 9 | import random
10 | from typing import Optional, Dict, List, Tuple
   |
help: Remove unused import: `time`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\douban\client.py:14:22
   |
12 | import httpx
13 | from loguru import logger
14 | from datetime import datetime
   |                      ^^^^^^^^
15 |
16 | from app.core.cache import get_cache
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\douban\client.py:17:29
   |
16 | from app.core.cache import get_cache
17 | from app.core.config import settings
   |                             ^^^^^^^^
18 |
19 | # 豆瓣API配置
   |
help: Remove unused import: `app.core.config.settings`

F811 [*] Redefinition of unused `datetime` from line 14
  --> app\modules\douban\client.py:65:30
   |
64 |         # 生成时间戳（使用日期格式）
65 |         from datetime import datetime
   |                              ^^^^^^^^ `datetime` redefined here
66 |         ts = request_params.pop('_ts', datetime.now().strftime('%Y%m%d'))
67 |         request_params.update({
   |
  ::: app\modules\douban\client.py:14:22
   |
12 | import httpx
13 | from loguru import logger
14 | from datetime import datetime
   |                      -------- previous definition of `datetime` here
15 |
16 | from app.core.cache import get_cache
   |
help: Remove definition: `datetime`

F401 [*] `app.modules.settings.service.SettingsService` imported but unused
   --> app\modules\download\service.py:390:50
    |
388 |             return downloads
389 |             
390 |         from app.modules.settings.service import SettingsService
    |                                                  ^^^^^^^^^^^^^^^
391 |         from app.core.config import settings
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
    |
help: Remove unused import: `app.modules.settings.service.SettingsService`

F401 [*] `app.core.downloaders.DownloaderClient` imported but unused
   --> app\modules\download\service.py:392:42
    |
390 |         from app.modules.settings.service import SettingsService
391 |         from app.core.config import settings
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
    |                                          ^^^^^^^^^^^^^^^^
393 |         import asyncio
394 |         from datetime import datetime, timedelta
    |
help: Remove unused import

F401 [*] `app.core.downloaders.DownloaderType` imported but unused
   --> app\modules\download\service.py:392:60
    |
390 |         from app.modules.settings.service import SettingsService
391 |         from app.core.config import settings
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
    |                                                            ^^^^^^^^^^^^^^
393 |         import asyncio
394 |         from datetime import datetime, timedelta
    |
help: Remove unused import

F401 [*] `asyncio` imported but unused
   --> app\modules\download\service.py:393:16
    |
391 |         from app.core.config import settings
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
393 |         import asyncio
    |                ^^^^^^^
394 |         from datetime import datetime, timedelta
    |
help: Remove unused import: `asyncio`

F401 [*] `datetime.datetime` imported but unused
   --> app\modules\download\service.py:394:30
    |
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
393 |         import asyncio
394 |         from datetime import datetime, timedelta
    |                              ^^^^^^^^
395 |         
396 |         settings_service = self._get_settings_service()
    |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
   --> app\modules\download\service.py:394:40
    |
392 |         from app.core.downloaders import DownloaderClient, DownloaderType
393 |         import asyncio
394 |         from datetime import datetime, timedelta
    |                                        ^^^^^^^^^
395 |         
396 |         settings_service = self._get_settings_service()
    |
help: Remove unused import

F841 Local variable `cache_key` is assigned to but never used
   --> app\modules\download\service.py:428:13
    |
426 |             # 检查是否有缓存的标签信息（简单的内存缓存）
427 |             # 在实际生产环境中，建议使用 Redis 等外部缓存
428 |             cache_key = "download_labels_cache"
    |             ^^^^^^^^^
429 |             cache_timeout = 30  # 30秒缓存
    |
help: Remove assignment to unused variable `cache_key`

F841 Local variable `cache_timeout` is assigned to but never used
   --> app\modules\download\service.py:429:13
    |
427 |             # 在实际生产环境中，建议使用 Redis 等外部缓存
428 |             cache_key = "download_labels_cache"
429 |             cache_timeout = 30  # 30秒缓存
    |             ^^^^^^^^^^^^^
430 |             
431 |             # 这里简化处理：只获取当前下载任务的标签，不进行实时查询
    |
help: Remove assignment to unused variable `cache_timeout`

E722 Do not use bare `except`
   --> app\modules\download\service.py:766:25
    |
764 |                         try:
765 |                             await self.cache.delete(cache_key)
766 |                         except:
    |                         ^^^^^^
767 |                             pass  # 忽略删除失败
    |

F541 [*] f-string without any placeholders
   --> app\modules\download\service.py:782:37
    |
781 |             # 清除缓存
782 |             await self.cache.delete(f"downloads:list:*")
    |                                     ^^^^^^^^^^^^^^^^^^^
783 |             
784 |             return True
    |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\modules\download\service.py:845:25
    |
843 |                         try:
844 |                             await self.cache.delete(cache_key)
845 |                         except:
    |                         ^^^^^^
846 |                             pass  # 忽略删除失败
    |

F541 [*] f-string without any placeholders
   --> app\modules\download\service.py:861:37
    |
860 |             # 清除缓存
861 |             await self.cache.delete(f"downloads:list:*")
    |                                     ^^^^^^^^^^^^^^^^^^^
862 |             
863 |             return True
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\download\service.py:917:33
    |
916 |         # 清除缓存
917 |         await self.cache.delete(f"downloads:list:*")
    |                                 ^^^^^^^^^^^^^^^^^^^
918 |         
919 |         return True
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
    --> app\modules\download\service.py:1277:45
     |
1276 |                     # 清除缓存
1277 |                     await self.cache.delete(f"downloads:list:*")
     |                                             ^^^^^^^^^^^^^^^^^^^
1278 |                 else:
1279 |                     all_success = False
     |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
    --> app\modules\download\service.py:1343:45
     |
1342 |                     # 清除缓存
1343 |                     await self.cache.delete(f"downloads:list:*")
     |                                             ^^^^^^^^^^^^^^^^^^^
1344 |                 else:
1345 |                     all_success = False
     |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
    --> app\modules\download\service.py:1406:45
     |
1405 |                     # 清除缓存
1406 |                     await self.cache.delete(f"downloads:list:*")
     |                                             ^^^^^^^^^^^^^^^^^^^
1407 |                 else:
1408 |                     all_success = False
     |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\modules\download\status_updater.py:129:17
    |
127 |                 try:
128 |                     await client.close()
129 |                 except:
    |                 ^^^^^^
130 |                     pass
    |

E722 Do not use bare `except`
   --> app\modules\download\status_updater.py:426:17
    |
424 |                 try:
425 |                     await client.close()
426 |                 except:
    |                 ^^^^^^
427 |                     pass
428 |                 return False
    |

F401 [*] `app.core.config.settings` imported but unused
   --> app\modules\download\status_updater.py:442:41
    |
440 |             from app.models.directory import Directory
441 |             from app.schemas.directory import DirectoryConfig
442 |             from app.core.config import settings
    |                                         ^^^^^^^^
443 |             
444 |             # 获取下载器监控目录配置
    |
help: Remove unused import: `app.core.config.settings`

E712 Avoid equality comparisons to `True`; use `Directory.enabled:` for truth checks
   --> app\modules\download\status_updater.py:448:21
    |
446 |                 select(Directory).where(
447 |                     Directory.monitor_type == "downloader",
448 |                     Directory.enabled == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^
449 |                     Directory.storage == "local"
450 |                 ).order_by(Directory.priority)
    |
help: Replace with `Directory.enabled`

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:455:30
    |
454 |             if not directories:
455 |                 logger.debug(f"没有配置下载器监控目录，跳过文件整理")
    |                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
456 |                 return
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:464:32
    |
463 |             if not downloader_config:
464 |                 logger.warning(f"无法获取下载器配置，跳过文件整理")
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
465 |                 return
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:475:40
    |
473 |                     torrent_info = await client.get_torrent_info(task.downloader_hash)
474 |                     if not torrent_info:
475 |                         logger.warning(f"无法获取任务信息，跳过文件整理")
    |                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
476 |                         await client.close()
477 |                         return
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:482:40
    |
480 |                     file_path = torrent_info.get("content_path") or torrent_info.get("downloadDir")
481 |                     if not file_path:
482 |                         logger.warning(f"任务没有文件路径，跳过文件整理")
    |                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
483 |                         await client.close()
484 |                         return
    |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\modules\download\status_updater.py:563:17
    |
561 |                 try:
562 |                     await client.close()
563 |                 except:
    |                 ^^^^^^
564 |                     pass
565 |         except Exception as e:
    |

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:585:32
    |
584 |             if not downloader_config:
585 |                 logger.warning(f"无法获取下载器配置，跳过电子书入库")
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
586 |                 return
    |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\modules\download\status_updater.py:634:17
    |
632 |                 try:
633 |                     await client.close()
634 |                 except:
    |                 ^^^^^^
635 |                     pass
636 |         except Exception as e:
    |

F541 [*] f-string without any placeholders
   --> app\modules\download\status_updater.py:656:32
    |
655 |             if not downloader_config:
656 |                 logger.warning(f"无法获取下载器配置，跳过高声书入库")
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
657 |                 return
    |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
   --> app\modules\download\status_updater.py:712:17
    |
710 |                 try:
711 |                     await client.close()
712 |                 except:
    |                 ^^^^^^
713 |                     pass
    |

F401 [*] `os` imported but unused
 --> app\modules\ebook\importer.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import shutil
9 | import re
  |
help: Remove unused import: `os`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\ebook\importer.py:12:22
   |
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any, List
12 | from datetime import datetime
   |                      ^^^^^^^^
13 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.select` imported but unused
  --> app\modules\ebook\importer.py:16:24
   |
15 | from sqlalchemy.ext.asyncio import AsyncSession
16 | from sqlalchemy import select
   |                        ^^^^^^
17 |
18 | from app.core.config import settings
   |
help: Remove unused import: `sqlalchemy.select`

F401 [*] `.EBookMetadataProvider` imported but unused
  --> app\modules\ebook\metadata_providers\dummy.py:12:36
   |
11 | from app.models.ebook import EBook
12 | from . import EBookMetadataUpdate, EBookMetadataProvider
   |                                    ^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `.EBookMetadataProvider`

F401 [*] `typing.List` imported but unused
  --> app\modules\ebook\metadata_providers\openlibrary.py:8:41
   |
 7 | import re
 8 | from typing import Optional, Dict, Any, List
   |                                         ^^^^
 9 | from urllib.parse import quote
10 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `urllib.parse.quote` imported but unused
  --> app\modules\ebook\metadata_providers\openlibrary.py:9:26
   |
 7 | import re
 8 | from typing import Optional, Dict, Any, List
 9 | from urllib.parse import quote
   |                          ^^^^^
10 | from loguru import logger
11 | import httpx
   |
help: Remove unused import: `urllib.parse.quote`

F401 [*] `.EBookMetadataProvider` imported but unused
  --> app\modules\ebook\metadata_providers\openlibrary.py:15:36
   |
13 | from app.core.config import settings
14 | from app.models.ebook import EBook
15 | from . import EBookMetadataUpdate, EBookMetadataProvider
   |                                    ^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `.EBookMetadataProvider`

F841 Local variable `author_name` is assigned to but never used
   --> app\modules\ebook\metadata_providers\openlibrary.py:218:25
    |
216 |                         # 简化处理：从 key 中提取名称（实际应该再请求一次获取完整信息）
217 |                         # 例如 "/authors/OL123456A" -> "OL123456A"
218 |                         author_name = author_key.split("/")[-1]
    |                         ^^^^^^^^^^^
219 |                         # 如果有 name 字段，直接使用
220 |                         if "name" in author_ref:
    |
help: Remove assignment to unused variable `author_name`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\modules\ebook\work_resolver.py:10:32
   |
 8 | from typing import Optional, Union
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_, or_
   |                                ^^^^
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\modules\ebook\work_resolver.py:10:38
   |
 8 | from typing import Optional, Union
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_, or_
   |                                      ^^^
11 | from loguru import logger
   |
help: Remove unused import

F841 Local variable `conditions` is assigned to but never used
   --> app\modules\ebook\work_resolver.py:218:9
    |
216 |         # 策略 2: 使用规范化后的 (title, author, series, volume_index) 组合匹配
217 |         # 构建查询条件
218 |         conditions = []
    |         ^^^^^^^^^^
219 |         
220 |         # title 必须匹配（使用规范化后的值）
    |
help: Remove assignment to unused variable `conditions`

F401 `typing.List` imported but unused
 --> app\modules\fanart\__init__.py:8:48
  |
6 | """
7 | import re
8 | from typing import Optional, Dict, Any, Union, List
  |                                                ^^^^
9 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F541 [*] f-string without any placeholders
  --> app\modules\fanart\__init__.py:68:29
   |
66 |                 result = await self._request_fanart(media_type, tvdb_id)
67 |             else:
68 |                 logger.info(f"电视剧类型缺少TVDB ID，无法获取Fanart图片")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
69 |                 return None
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\fanart\__init__.py:72:28
   |
71 |         if not result or result.get('status') == 'error':
72 |             logger.warning(f"没有获取到Fanart图片数据")
   |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
73 |             return None
   |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> app\modules\file_browser\service.py:6:8
  |
4 | """
5 |
6 | import os
  |        ^^
7 | import stat
8 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `stat` imported but unused
 --> app\modules\file_browser\service.py:7:8
  |
6 | import os
7 | import stat
  |        ^^^^
8 | from pathlib import Path
9 | from typing import List, Optional, Dict, Any
  |
help: Remove unused import: `stat`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\file_browser\service.py:10:22
   |
 8 | from pathlib import Path
 9 | from typing import List, Optional, Dict, Any
10 | from datetime import datetime
   |                      ^^^^^^^^
11 | from loguru import logger
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.cloud_storage.providers.base.CloudFileInfo` imported but unused
  --> app\modules\file_browser\service.py:15:51
   |
14 | from app.modules.cloud_storage.service import CloudStorageService
15 | from app.core.cloud_storage.providers.base import CloudFileInfo
   |                                                   ^^^^^^^^^^^^^
   |
help: Remove unused import: `app.core.cloud_storage.providers.base.CloudFileInfo`

F841 Local variable `relative_path` is assigned to but never used
   --> app\modules\file_browser\service.py:114:17
    |
112 |                     relative_path = str(path)
113 |             else:
114 |                 relative_path = path.name
    |                 ^^^^^^^^^^^^^
115 |             
116 |             item = {
    |
help: Remove assignment to unused variable `relative_path`

F401 [*] `os` imported but unused
 --> app\modules\file_cleaner\service.py:6:8
  |
4 | """
5 |
6 | import os
  |        ^^
7 | import fnmatch
8 | from pathlib import Path
  |
help: Remove unused import: `os`

F841 Local variable `hr_repo` is assigned to but never used
  --> app\modules\file_cleaner\service.py:87:17
   |
86 |                 safety_engine = get_safety_policy_engine()
87 |                 hr_repo = get_hr_repository()
   |                 ^^^^^^^
88 |                 
89 |                 # 创建安全上下文
   |
help: Remove assignment to unused variable `hr_repo`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\file_operation\directory_monitor.py:7:26
  |
5 | import asyncio
6 | from pathlib import Path
7 | from typing import List, Dict, Any, Optional
  |                          ^^^^
8 | from loguru import logger
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\file_operation\directory_monitor.py:7:32
  |
5 | import asyncio
6 | from pathlib import Path
7 | from typing import List, Dict, Any, Optional
  |                                ^^^
8 | from loguru import logger
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\file_operation\directory_monitor.py:7:37
  |
5 | import asyncio
6 | from pathlib import Path
7 | from typing import List, Dict, Any, Optional
  |                                     ^^^^^^^^
8 | from loguru import logger
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `Directory.enabled:` for truth checks
   --> app\modules\file_operation\directory_monitor.py:184:21
    |
182 |                 select(Directory).where(
183 |                     Directory.monitor_type == "directory",
184 |                     Directory.enabled == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^
185 |                     Directory.storage == "local"
186 |                 ).order_by(Directory.priority)
    |
help: Replace with `Directory.enabled`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\file_operation\downloader_monitor.py:8:22
   |
 6 | from pathlib import Path
 7 | from typing import List, Dict, Any, Optional
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 | from loguru import logger
10 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `datetime.datetime`

E712 Avoid equality comparisons to `True`; use `Directory.enabled:` for truth checks
   --> app\modules\file_operation\downloader_monitor.py:227:21
    |
225 |                 select(Directory).where(
226 |                     Directory.monitor_type == "downloader",
227 |                     Directory.enabled == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^
228 |                     Directory.storage == "local"
229 |                 ).order_by(Directory.priority)
    |
help: Replace with `Directory.enabled`

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\file_operation\transfer_handler.py:8:41
  |
7 | from pathlib import Path
8 | from typing import Optional, Dict, Any, Tuple
  |                                         ^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `typing.Tuple`

F401 [*] `app.modules.strm.file_operation_mode.get_available_modes` imported but unused
  --> app\modules\file_operation\transfer_handler.py:12:90
   |
11 | from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
12 | from app.modules.strm.file_operation_mode import FileOperationMode, FileOperationConfig, get_available_modes, validate_operation_mode
   |                                                                                          ^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.modules.strm.file_operation_mode.get_available_modes`

F541 [*] f-string without any placeholders
   --> app\modules\file_operation\transfer_handler.py:378:38
    |
376 |                         return {
377 |                             "success": False,
378 |                             "error": f"复制文件失败"
    |                                      ^^^^^^^^^^^^^^^
379 |                         }
380 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\file_operation\transfer_handler.py:399:38
    |
397 |                         return {
398 |                             "success": False,
399 |                             "error": f"移动文件失败"
    |                                      ^^^^^^^^^^^^^^^
400 |                         }
401 |                 else:
    |
help: Remove extraneous `f` prefix

F401 [*] `typing.List` imported but unused
 --> app\modules\file_operation\transfer_service.py:6:41
  |
4 | """
5 | from pathlib import Path
6 | from typing import Dict, Any, Optional, List
  |                                         ^^^^
7 | from loguru import logger
8 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.List`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\file_operation\transfer_service.py:10:29
   |
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 |
10 | from app.core.config import settings
   |                             ^^^^^^^^
11 | from app.modules.file_operation.transfer_handler import TransferHandler
12 | from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `app.modules.file_operation.overwrite_handler.OverwriteHandler` imported but unused
  --> app\modules\file_operation\transfer_service.py:12:58
   |
10 | from app.core.config import settings
11 | from app.modules.file_operation.transfer_handler import TransferHandler
12 | from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
   |                                                          ^^^^^^^^^^^^^^^^
13 | from app.modules.strm.file_operation_mode import FileOperationMode, FileOperationConfig
14 | from app.schemas.directory import DirectoryConfig
   |
help: Remove unused import

F401 [*] `app.modules.file_operation.overwrite_handler.OverwriteMode` imported but unused
  --> app\modules\file_operation\transfer_service.py:12:76
   |
10 | from app.core.config import settings
11 | from app.modules.file_operation.transfer_handler import TransferHandler
12 | from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode
   |                                                                            ^^^^^^^^^^^^^
13 | from app.modules.strm.file_operation_mode import FileOperationMode, FileOperationConfig
14 | from app.schemas.directory import DirectoryConfig
   |
help: Remove unused import

F541 [*] f-string without any placeholders
   --> app\modules\file_operation\transfer_service.py:162:42
    |
160 |                         # 如果 Local Intel 未启用或 MOVE 检查未启用，跳过 HR 检查
161 |                         if not (settings.INTEL_ENABLED and intel_enabled and intel_move_check_enabled):
162 |                             logger.debug(f"LocalIntel: 已禁用或 MOVE 检查未启用，跳过 HR 保护检查")
    |                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
163 |                         else:
164 |                             # 尝试从 app.state 获取 LocalIntelEngine
    |
help: Remove extraneous `f` prefix

F401 [*] `fastapi.Request` imported but unused
   --> app\modules\file_operation\transfer_service.py:165:49
    |
163 |                         else:
164 |                             # 尝试从 app.state 获取 LocalIntelEngine
165 |                             from fastapi import Request
    |                                                 ^^^^^^^
166 |                             # 注意：这里需要从请求上下文获取 engine，或者使用全局单例
167 |                             # 为了简化，我们使用 scheduler_hooks（它内部会调用 engine）
    |
help: Remove unused import: `fastapi.Request`

E722 Do not use bare `except`
   --> app\modules\file_operation\transfer_service.py:177:29
    |
175 | …                         is_safe = await engine.is_move_safe(site_id, torrent_id)
176 | …                         keep_source = not is_safe  # is_safe=True 表示可以删除，keep_source 相反
177 | …                     except:
    |                       ^^^^^^
178 | …                         pass  # 回退到 scheduler_hooks
    |

F401 [*] `typing.Dict` imported but unused
 --> app\modules\filter_rule_group\service.py:5:20
  |
3 | """
4 |
5 | from typing import Dict, List, Optional
  |                    ^^^^
6 | from datetime import datetime
  |
help: Remove unused import: `typing.Dict`

E712 Avoid equality comparisons to `True`; use `FilterRuleGroup.enabled:` for truth checks
  --> app\modules\filter_rule_group\service.py:52:37
   |
50 |             # 启用状态过滤
51 |             if enabled_only:
52 |                 query = query.where(FilterRuleGroup.enabled == True)
   |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
53 |             
54 |             # 按优先级排序
   |
help: Replace with `FilterRuleGroup.enabled`

E712 Avoid equality comparisons to `True`; use `FilterRuleGroup.enabled:` for truth checks
   --> app\modules\filter_rule_group\service.py:267:21
    |
265 |                 and_(
266 |                     FilterRuleGroup.id.in_(valid_ids),
267 |                     FilterRuleGroup.enabled == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
268 |                     or_(
269 |                         FilterRuleGroup.user_id == user_id,
    |
help: Replace with `FilterRuleGroup.enabled`

E712 Avoid equality comparisons to `True`; use `FilterRuleGroup.enabled:` for truth checks
   --> app\modules\filter_rule_group\service.py:322:21
    |
320 |                 and_(
321 |                     FilterRuleGroup.id.in_(group_ids),
322 |                     FilterRuleGroup.enabled == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
323 |                 )
324 |             )
    |
help: Replace with `FilterRuleGroup.enabled`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\global_rules\filter.py:6:37
  |
4 | """
5 |
6 | from typing import List, Dict, Any, Optional
  |                                     ^^^^^^^^
7 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F841 Local variable `codec` is assigned to but never used
   --> app\modules\global_rules\filter.py:241:5
    |
239 |         return True
240 |     
241 |     codec = torrent.get('codec', '').lower()
    |     ^^^^^
242 |     
243 |     if policy == CodecPolicy.PREFER_H265.value:
    |
help: Remove assignment to unused variable `codec`

F401 [*] `typing.Any` imported but unused
 --> app\modules\hnr\service.py:6:42
  |
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, func, and_
6 | from typing import List, Optional, Dict, Any
  |                                          ^^^
7 | from datetime import datetime, timedelta
8 | from loguru import logger
  |
help: Remove unused import: `typing.Any`

F401 [*] `app.models.hnr.HNRSignature` imported but unused
  --> app\modules\hnr\service.py:11:51
   |
 9 | import json
10 |
11 | from app.models.hnr import HNRDetection, HNRTask, HNRSignature
   |                                                   ^^^^^^^^^^^^
12 | from app.models.download import DownloadTask
13 | from app.modules.hnr.detector import HNRDetector, HNRVerdict
   |
help: Remove unused import: `app.models.hnr.HNRSignature`

F401 [*] `app.models.download.DownloadTask` imported but unused
  --> app\modules\hnr\service.py:12:33
   |
11 | from app.models.hnr import HNRDetection, HNRTask, HNRSignature
12 | from app.models.download import DownloadTask
   |                                 ^^^^^^^^^^^^
13 | from app.modules.hnr.detector import HNRDetector, HNRVerdict
14 | from app.core.config import settings
   |
help: Remove unused import: `app.models.download.DownloadTask`

F401 [*] `app.modules.hnr.detector.HNRVerdict` imported but unused
  --> app\modules\hnr\service.py:13:51
   |
11 | from app.models.hnr import HNRDetection, HNRTask, HNRSignature
12 | from app.models.download import DownloadTask
13 | from app.modules.hnr.detector import HNRDetector, HNRVerdict
   |                                                   ^^^^^^^^^^
14 | from app.core.config import settings
   |
help: Remove unused import: `app.modules.hnr.detector.HNRVerdict`

E741 Ambiguous variable name: `l`
  --> app\modules\hnr\utils\text.py:58:27
   |
56 |     """
57 |     t = normalize(text)
58 |     return any(l in t for l in left) and any(r in t for r in right)
   |                           ^
   |

F401 [*] `sqlalchemy.Boolean` imported but unused
  --> app\modules\hr_case\models.py:14:47
   |
12 | from pydantic import BaseModel, Field
13 | from sqlalchemy import (
14 |     Column, Integer, String, DateTime, Float, Boolean, Text, JSON,
   |                                               ^^^^^^^
15 |     Index, ForeignKey
16 | )
   |
help: Remove unused import

F401 [*] `sqlalchemy.ForeignKey` imported but unused
  --> app\modules\hr_case\models.py:15:12
   |
13 | from sqlalchemy import (
14 |     Column, Integer, String, DateTime, Float, Boolean, Text, JSON,
15 |     Index, ForeignKey
   |            ^^^^^^^^^^
16 | )
17 | from sqlalchemy.orm import relationship
   |
help: Remove unused import

F401 [*] `sqlalchemy.orm.relationship` imported but unused
  --> app\modules\hr_case\models.py:17:28
   |
15 |     Index, ForeignKey
16 | )
17 | from sqlalchemy.orm import relationship
   |                            ^^^^^^^^^^^^
18 | from sqlalchemy.ext.declarative import declarative_base
   |
help: Remove unused import: `sqlalchemy.orm.relationship`

F401 [*] `sqlalchemy.ext.declarative.declarative_base` imported but unused
  --> app\modules\hr_case\models.py:18:40
   |
16 | )
17 | from sqlalchemy.orm import relationship
18 | from sqlalchemy.ext.declarative import declarative_base
   |                                        ^^^^^^^^^^^^^^^^
19 |
20 | from app.core.database import Base
   |
help: Remove unused import: `sqlalchemy.ext.declarative.declarative_base`

F401 [*] `logging` imported but unused
  --> app\modules\hr_case\repository.py:11:8
   |
 9 | from typing import Dict, Iterable, List, Optional
10 | from dataclasses import dataclass
11 | import logging
   |        ^^^^^^^
12 |
13 | from sqlalchemy import select, update, delete, and_
   |
help: Remove unused import: `logging`

F401 [*] `sqlalchemy.update` imported but unused
  --> app\modules\hr_case\repository.py:13:32
   |
11 | import logging
12 |
13 | from sqlalchemy import select, update, delete, and_
   |                                ^^^^^^
14 | from sqlalchemy.ext.asyncio import AsyncSession
15 | from sqlalchemy.orm import selectinload
   |
help: Remove unused import: `sqlalchemy.update`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\modules\hr_case\repository.py:14:36
   |
13 | from sqlalchemy import select, update, delete, and_
14 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
15 | from sqlalchemy.orm import selectinload
16 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\modules\hr_case\repository.py:15:28
   |
13 | from sqlalchemy import select, update, delete, and_
14 | from sqlalchemy.ext.asyncio import AsyncSession
15 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
16 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F841 Local variable `cache_key` is assigned to but never used
   --> app\modules\hr_case\repository.py:198:13
    |
197 |             # 2. DB成功后再更新内存缓存
198 |             cache_key = (site_key, str(hr_state.torrent_id))
    |             ^^^^^^^^^
199 |             set_to_cache(site_key, str(hr_state.torrent_id), hr_state)
    |
help: Remove assignment to unused variable `cache_key`

F841 Local variable `cache_key` is assigned to but never used
   --> app\modules\hr_case\repository.py:255:13
    |
254 |             # 同步更新内存缓存
255 |             cache_key = (site_key, torrent_id)
    |             ^^^^^^^^^
256 |             cache_state = get_from_cache(site_key, torrent_id)
257 |             if cache_state:
    |
help: Remove assignment to unused variable `cache_key`

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\modules\inbox\hint_resolver.py:12:32
   |
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, or_
   |                                ^^^
13 |
14 | from app.models.download import DownloadTask
   |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `pathlib.Path` imported but unused
  --> app\modules\inbox\media_detection\base.py:8:21
   |
 7 | from typing import Protocol, Optional, Literal, NamedTuple
 8 | from pathlib import Path
   |                     ^^^^
 9 |
10 | from app.modules.inbox.models import InboxItem
   |
help: Remove unused import: `pathlib.Path`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\inbox\media_detection\extension_detector.py:7:21
  |
5 | """
6 |
7 | from pathlib import Path
  |                     ^^^^
8 | from typing import Optional
9 | from loguru import logger
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `loguru.logger` imported but unused
  --> app\modules\inbox\media_detection\extension_detector.py:9:20
   |
 7 | from pathlib import Path
 8 | from typing import Optional
 9 | from loguru import logger
   |                    ^^^^^^
10 |
11 | from app.modules.inbox.models import InboxItem
   |
help: Remove unused import: `loguru.logger`

F401 [*] `.base.MediaTypeDetector` imported but unused
  --> app\modules\inbox\media_detection\extension_detector.py:12:19
   |
11 | from app.modules.inbox.models import InboxItem
12 | from .base import MediaTypeDetector, MediaTypeGuess, MediaTypeLiteral
   |                   ^^^^^^^^^^^^^^^^^
   |
help: Remove unused import

F401 [*] `.base.MediaTypeLiteral` imported but unused
  --> app\modules\inbox\media_detection\extension_detector.py:12:54
   |
11 | from app.modules.inbox.models import InboxItem
12 | from .base import MediaTypeDetector, MediaTypeGuess, MediaTypeLiteral
   |                                                      ^^^^^^^^^^^^^^^^
   |
help: Remove unused import

F541 [*] f-string without any placeholders
  --> app\modules\inbox\media_detection\extension_detector.py:91:24
   |
89 |                 media_type="novel_txt",
90 |                 score=0.5,  # 较低分数，需要 novel_txt_detector 进一步确认
91 |                 reason=f"extension=txt => novel_txt (0.5, needs content check)"
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
92 |             )
   |
help: Remove extraneous `f` prefix

F401 [*] `pathlib.Path` imported but unused
  --> app\modules\inbox\media_detection\novel_txt_detector.py:8:21
   |
 7 | import re
 8 | from pathlib import Path
   |                     ^^^^
 9 | from typing import Optional
10 | from loguru import logger
   |
help: Remove unused import: `pathlib.Path`

F401 [*] `.base.MediaTypeDetector` imported but unused
  --> app\modules\inbox\media_detection\novel_txt_detector.py:13:19
   |
12 | from app.modules.inbox.models import InboxItem
13 | from .base import MediaTypeDetector, MediaTypeGuess
   |                   ^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `.base.MediaTypeDetector`

F401 [*] `loguru.logger` imported but unused
  --> app\modules\inbox\media_detection\pt_category_detector.py:8:20
   |
 7 | from typing import Optional, Dict
 8 | from loguru import logger
   |                    ^^^^^^
 9 |
10 | from app.modules.inbox.models import InboxItem
   |
help: Remove unused import: `loguru.logger`

F401 [*] `.base.MediaTypeDetector` imported but unused
  --> app\modules\inbox\media_detection\pt_category_detector.py:11:19
   |
10 | from app.modules.inbox.models import InboxItem
11 | from .base import MediaTypeDetector, MediaTypeGuess, MediaTypeLiteral
   |                   ^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `.base.MediaTypeDetector`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\inbox\media_detection\service.py:7:26
  |
5 | """
6 |
7 | from typing import List, Optional
  |                          ^^^^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F541 [*] f-string without any placeholders
   --> app\modules\inbox\router.py:324:25
    |
322 |             await self.db.commit()
323 |             logger.info(f"小说 TXT 导入成功: {item.path} -> EBook {result.ebook.id}" + 
324 |                        (f", TTS Job 已创建" if tts_job_created else ""))
    |                         ^^^^^^^^^^^^^^^^^^^
325 |             return "handled:novel_txt" + (":tts_job_created" if tts_job_created else "")
    |
help: Remove extraneous `f` prefix

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\inbox\service.py:13:29
   |
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 |
13 | from app.core.config import settings
   |                             ^^^^^^^^
14 | from .scanner import InboxScanner
15 | from .models import InboxItem
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `.models.InboxItem` imported but unused
  --> app\modules\inbox\service.py:15:21
   |
13 | from app.core.config import settings
14 | from .scanner import InboxScanner
15 | from .models import InboxItem
   |                     ^^^^^^^^^
16 | from .hint_resolver import attach_pt_hints
17 | from .media_detection.service import get_default_detection_service, MediaTypeDetectionService
   |
help: Remove unused import: `.models.InboxItem`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\log_center\service.py:9:32
   |
 7 | import asyncio
 8 | from typing import Dict, List, Optional, Set, Any
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from collections import deque
11 | from enum import Enum
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `fastapi.WebSocketDisconnect` imported but unused
  --> app\modules\log_center\service.py:13:32
   |
11 | from enum import Enum
12 | from loguru import logger as loguru_logger
13 | from fastapi import WebSocket, WebSocketDisconnect
   |                                ^^^^^^^^^^^^^^^^^^^
14 | from fastapi.websockets import WebSocketState
   |
help: Remove unused import: `fastapi.WebSocketDisconnect`

E741 Ambiguous variable name: `l`
   --> app\modules\log_center\service.py:165:53
    |
163 |             if isinstance(allowed_levels, str):
164 |                 allowed_levels = [allowed_levels]
165 |             if entry["level"] not in [l.upper() for l in allowed_levels]:
    |                                                     ^
166 |                 return True
    |

F541 [*] f-string without any placeholders
  --> app\modules\manga_sources\generic_http_adapter.py:39:24
   |
37 |     ) -> RemoteMangaSearchResult:
38 |         """搜索漫画系列（占位实现）"""
39 |         logger.warning(f"Generic HTTP adapter search not implemented")
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
40 |         return RemoteMangaSearchResult(
41 |             total=0,
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\manga_sources\generic_http_adapter.py:57:24
   |
55 |     ) -> Optional[RemoteMangaSeries]:
56 |         """获取漫画详情（占位实现）"""
57 |         logger.warning(f"Generic HTTP adapter get_series_detail not implemented")
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
58 |         return None
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\manga_sources\generic_http_adapter.py:65:24
   |
63 |     ) -> List[RemoteMangaChapter]:
64 |         """获取章节列表（占位实现）"""
65 |         logger.warning(f"Generic HTTP adapter list_chapters not implemented")
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
66 |         return []
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\manga_sources\generic_http_adapter.py:89:24
   |
87 |     ) -> List[RemoteMangaPage]:
88 |         """获取章节页面列表（占位实现）"""
89 |         logger.warning(f"Generic HTTP adapter list_pages not implemented")
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
90 |         return []
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\modules\manga_sources\generic_http_adapter.py:97:24
   |
95 |     ) -> bytes:
96 |         """下载页面图片内容（占位实现）"""
97 |         logger.warning(f"Generic HTTP adapter fetch_page_content not implemented")
   |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
98 |         raise NotImplementedError("Generic HTTP adapter fetch_page_content not implemented")
   |
help: Remove extraneous `f` prefix

F401 [*] `urllib.parse.urlparse` imported but unused
  --> app\modules\manga_sources\opds_adapter.py:9:35
   |
 7 | from typing import List, Optional
 8 | from xml.etree import ElementTree as ET
 9 | from urllib.parse import urljoin, urlparse, parse_qs
   |                                   ^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `urllib.parse.parse_qs` imported but unused
  --> app\modules\manga_sources\opds_adapter.py:9:45
   |
 7 | from typing import List, Optional
 8 | from xml.etree import ElementTree as ET
 9 | from urllib.parse import urljoin, urlparse, parse_qs
   |                                             ^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\modules\media_identification\service.py:8:44
   |
 6 | from typing import Dict, Optional, Any, List
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, desc, and_, or_
   |                                            ^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `json` imported but unused
  --> app\modules\media_identification\service.py:11:8
   |
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
11 | import json
   |        ^^^^
12 |
13 | from app.core.legacy_adapter import get_legacy_adapter
   |
help: Remove unused import: `json`

F401 [*] `shutil` imported but unused
 --> app\modules\media_renamer\category_helper.py:7:8
  |
5 | """
6 |
7 | import shutil
  |        ^^^^^^
8 | from pathlib import Path
9 | from typing import Union, Optional, Dict, Any, Mapping, TYPE_CHECKING
  |
help: Remove unused import: `shutil`

E722 Do not use bare `except`
   --> app\modules\media_renamer\category_helper.py:274:13
    |
272 |                 import json
273 |                 tags = json.loads(tags)
274 |             except:
    |             ^^^^^^
275 |                 tags = [t.strip() for t in tags.split(",") if t.strip()]
276 |         if isinstance(tags, list):
    |

E722 Do not use bare `except`
   --> app\modules\media_renamer\category_helper.py:334:13
    |
332 |                 import json
333 |                 tags = json.loads(tags)
334 |             except:
    |             ^^^^^^
335 |                 tags = [t.strip() for t in tags.split(",") if t.strip()]
336 |         if isinstance(tags, list):
    |

F401 [*] `asyncio` imported but unused
  --> app\modules\media_renamer\duplicate_detector.py:11:8
   |
 9 | from dataclasses import dataclass
10 | from loguru import logger
11 | import asyncio
   |        ^^^^^^^
12 | from concurrent.futures import ThreadPoolExecutor
   |
help: Remove unused import: `asyncio`

F841 Local variable `last_error` is assigned to but never used
   --> app\modules\media_renamer\identifier.py:185:17
    |
183 |                     return None
184 |             except Exception as e:
185 |                 last_error = e
    |                 ^^^^^^^^^^
186 |                 logger.error(f"查询TMDB失败: {media_info.title}, 错误: {e}")
187 |                 return None
    |
help: Remove assignment to unused variable `last_error`

F841 Local variable `last_error` is assigned to but never used
   --> app\modules\media_renamer\identifier.py:460:17
    |
458 |                     return None
459 |             except Exception as e:
460 |                 last_error = e
    |                 ^^^^^^^^^^
461 |                 logger.error(f"获取TMDB详情失败: {media_type} {tmdb_id}, 错误: {e}")
462 |                 return None
    |
help: Remove assignment to unused variable `last_error`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\media_renamer\nfo_writer.py:7:20
  |
5 | """
6 | from pathlib import Path
7 | from typing import Optional, Dict, Any
  |                    ^^^^^^^^
8 | from datetime import datetime
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\media_renamer\nfo_writer.py:8:22
   |
 6 | from pathlib import Path
 7 | from typing import Optional, Dict, Any
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 | from loguru import logger
10 | import xml.etree.ElementTree as ET
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\media_renamer\parser.py:7:30
  |
6 | import re
7 | from typing import Optional, Dict, Tuple
  |                              ^^^^
8 | from dataclasses import dataclass
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\media_renamer\parser.py:7:36
  |
6 | import re
7 | from typing import Optional, Dict, Tuple
  |                                    ^^^^^
8 | from dataclasses import dataclass
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.List` imported but unused
 --> app\modules\media_server\emby_client.py:6:20
  |
4 | """
5 |
6 | from typing import List, Dict, Any, Optional
  |                    ^^^^
7 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
 --> app\modules\media_server\emby_client.py:6:26
  |
4 | """
5 |
6 | from typing import List, Dict, Any, Optional
  |                          ^^^^
7 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\media_server\emby_client.py:6:32
  |
4 | """
5 |
6 | from typing import List, Dict, Any, Optional
  |                                ^^^
7 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\media_server\emby_client.py:6:37
  |
4 | """
5 |
6 | from typing import List, Dict, Any, Optional
  |                                     ^^^^^^^^
7 | from loguru import logger
  |
help: Remove unused import

E722 Do not use bare `except`
   --> app\modules\media_server\jellyfin_client.py:308:13
    |
306 |             try:
307 |                 last_played = datetime.fromisoformat(user_data["LastPlayedDate"].replace("Z", "+00:00"))
308 |             except:
    |             ^^^^^^
309 |                 pass
    |

E722 Do not use bare `except`
   --> app\modules\media_server\jellyfin_client.py:315:13
    |
313 |             try:
314 |                 watched_at = datetime.fromisoformat(user_data["PlayedDate"].replace("Z", "+00:00"))
315 |             except:
    |             ^^^^^^
316 |                 pass
    |

E722 Do not use bare `except`
   --> app\modules\media_server\jellyfin_client.py:323:13
    |
321 |             try:
322 |                 year = int(item_data["ProductionYear"])
323 |             except:
    |             ^^^^^^
324 |                 pass
    |

F401 [*] `datetime.datetime` imported but unused
 --> app\modules\media_server\plex_client.py:7:22
  |
5 | import httpx
6 | from typing import List, Dict, Any, Optional
7 | from datetime import datetime
  |                      ^^^^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `datetime.datetime`

F541 [*] f-string without any placeholders
   --> app\modules\media_server\plex_client.py:238:50
    |
236 |             if watched:
237 |                 # 标记为已观看
238 |                 response = await self.client.put(f"/:/scrobble", params={"key": item_id})
    |                                                  ^^^^^^^^^^^^^^
239 |             else:
240 |                 # 取消观看标记
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\media_server\plex_client.py:241:50
    |
239 |             else:
240 |                 # 取消观看标记
241 |                 response = await self.client.put(f"/:/unscrobble", params={"key": item_id})
    |                                                  ^^^^^^^^^^^^^^^^
242 |             
243 |             return response.status_code == 200
    |
help: Remove extraneous `f` prefix

F401 [*] `sqlalchemy.and_` imported but unused
 --> app\modules\media_server\service.py:6:32
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_
  |                                ^^^^
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\media_server\service.py:6:38
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_
  |                                      ^^^
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `app.models.media_server.MediaServerItem` imported but unused
  --> app\modules\media_server\service.py:11:74
   |
 9 | from loguru import logger
10 |
11 | from app.models.media_server import MediaServer, MediaServerSyncHistory, MediaServerItem, MediaServerPlaybackSession
   |                                                                          ^^^^^^^^^^^^^^^
12 | from app.modules.media_server.base_client import MediaServerConfig, MediaServerError
13 | from app.modules.media_server.plex_client import PlexClient
   |
help: Remove unused import: `app.models.media_server.MediaServerItem`

F401 [*] `app.modules.media_server.base_client.MediaServerError` imported but unused
  --> app\modules\media_server\service.py:12:69
   |
11 | from app.models.media_server import MediaServer, MediaServerSyncHistory, MediaServerItem, MediaServerPlaybackSession
12 | from app.modules.media_server.base_client import MediaServerConfig, MediaServerError
   |                                                                     ^^^^^^^^^^^^^^^^
13 | from app.modules.media_server.plex_client import PlexClient
14 | from app.modules.media_server.jellyfin_client import JellyfinClient
   |
help: Remove unused import: `app.modules.media_server.base_client.MediaServerError`

F401 [*] `datetime.timedelta` imported but unused
 --> app\modules\monitoring\api_monitor.py:7:32
  |
6 | from typing import Dict, List, Optional
7 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
8 | from collections import deque, defaultdict
9 | from loguru import logger
  |
help: Remove unused import: `datetime.timedelta`

F401 [*] `loguru.logger` imported but unused
  --> app\modules\monitoring\api_monitor.py:9:20
   |
 7 | from datetime import datetime, timedelta
 8 | from collections import deque, defaultdict
 9 | from loguru import logger
   |                    ^^^^^^
10 |
11 | from app.core.middleware import PerformanceMonitoringMiddleware
   |
help: Remove unused import: `loguru.logger`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\monitoring\system_monitor.py:9:32
   |
 7 | import platform
 8 | from typing import Dict, List, Optional
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from collections import deque
11 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.Any` imported but unused
 --> app\modules\multimodal\alert_system.py:5:42
  |
3 | """
4 |
5 | from typing import Dict, List, Optional, Any
  |                                          ^^^
6 | from datetime import datetime, timedelta
7 | from enum import Enum
  |
help: Remove unused import: `typing.Any`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\modules\multimodal\alert_system.py:11:28
   |
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_, desc
11 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
12 |
13 | from app.models.multimodal_metrics import MultimodalPerformanceAlert
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

E712 Avoid equality comparisons to `False`; use `not MultimodalPerformanceAlert.resolved:` for false checks
   --> app\modules\multimodal\alert_system.py:213:25
    |
211 |                         MultimodalPerformanceAlert.operation == operation,
212 |                         MultimodalPerformanceAlert.alert_type == alert_type.value,
213 |                         MultimodalPerformanceAlert.resolved == False,
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
214 |                         MultimodalPerformanceAlert.timestamp >= five_minutes_ago
215 |                     )
    |
help: Replace with `not MultimodalPerformanceAlert.resolved`

F401 [*] `typing.List` imported but unused
 --> app\modules\multimodal\audio_analyzer.py:6:26
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                          ^^^^
7 | from pathlib import Path
8 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\multimodal\audio_analyzer.py:7:21
  |
6 | from typing import Dict, List, Optional, Any
7 | from pathlib import Path
  |                     ^^^^
8 | from loguru import logger
9 | import subprocess
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `hashlib` imported but unused
  --> app\modules\multimodal\audio_analyzer.py:13:8
   |
11 | import os
12 | from datetime import datetime
13 | import hashlib
   |        ^^^^^^^
14 | import asyncio
15 | import time
   |
help: Remove unused import: `hashlib`

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\multimodal\audio_analyzer.py:227:29
    |
225 |                 finally:
226 |                     self._current_concurrent -= 1
227 |         except Exception as e:
    |                             ^
228 |             if METRICS_AVAILABLE:
229 |                 duration = time.time() - start_time
    |
help: Remove assignment to unused variable `e`

F401 [*] `typing.List` imported but unused
 --> app\modules\multimodal\auto_optimizer.py:6:26
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                          ^^^^
7 | from datetime import datetime, timedelta
8 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `asyncio` imported but unused
 --> app\modules\multimodal\cache_optimizer.py:8:8
  |
6 | from typing import Dict, List, Optional, Any
7 | from loguru import logger
8 | import asyncio
  |        ^^^^^^^
9 | from datetime import datetime, timedelta
  |
help: Remove unused import: `asyncio`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\multimodal\cache_optimizer.py:9:22
   |
 7 | from loguru import logger
 8 | import asyncio
 9 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
10 |
11 | try:
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\multimodal\cache_optimizer.py:9:32
   |
 7 | from loguru import logger
 8 | import asyncio
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 |
11 | try:
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
 --> app\modules\multimodal\concurrency_optimizer.py:6:26
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                          ^^^^
7 | from loguru import logger
8 | import asyncio
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\multimodal\concurrency_optimizer.py:6:32
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                                ^^^^^^^^
7 | from loguru import logger
8 | import asyncio
  |
help: Remove unused import

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\multimodal\concurrency_optimizer.py:10:22
   |
 8 | import asyncio
 9 | import time
10 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
11 |
12 | try:
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\multimodal\concurrency_optimizer.py:10:32
   |
 8 | import asyncio
 9 | import time
10 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
11 |
12 | try:
   |
help: Remove unused import

F841 Local variable `start_time` is assigned to but never used
   --> app\modules\multimodal\concurrency_optimizer.py:180:13
    |
179 |         try:
180 |             start_time = time.time()
    |             ^^^^^^^^^^
181 |             metrics_start = MultimodalMetrics.get_metrics(operation)
    |
help: Remove assignment to unused variable `start_time`

F401 [*] `typing.List` imported but unused
 --> app\modules\multimodal\fusion.py:6:26
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any, Tuple
  |                          ^^^^
7 | from loguru import logger
8 | import numpy as np
  |
help: Remove unused import

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\multimodal\fusion.py:6:47
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any, Tuple
  |                                               ^^^^^
7 | from loguru import logger
8 | import numpy as np
  |
help: Remove unused import

F401 `sklearn.preprocessing.MinMaxScaler` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\modules\multimodal\fusion.py:15:55
   |
13 | # 可选依赖：sklearn用于特征缩放和降维
14 | try:
15 |     from sklearn.preprocessing import StandardScaler, MinMaxScaler
   |                                                       ^^^^^^^^^^^^
16 |     from sklearn.decomposition import PCA
17 |     from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
   |
help: Remove unused import: `sklearn.preprocessing.MinMaxScaler`

F401 `sklearn.decomposition.PCA` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\modules\multimodal\fusion.py:16:39
   |
14 | try:
15 |     from sklearn.preprocessing import StandardScaler, MinMaxScaler
16 |     from sklearn.decomposition import PCA
   |                                       ^^^
17 |     from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
18 |     SKLEARN_AVAILABLE = True
   |
help: Remove unused import: `sklearn.decomposition.PCA`

F841 Local variable `cache_hit` is assigned to but never used
   --> app\modules\multimodal\fusion.py:379:17
    |
377 |             if cached_result is not None:
378 |                 logger.debug("从缓存获取相似度计算结果")
379 |                 cache_hit = True
    |                 ^^^^^^^^^
380 |                 # 记录性能指标
381 |                 if METRICS_AVAILABLE:
    |
help: Remove assignment to unused variable `cache_hit`

F401 [*] `collections.defaultdict` imported but unused
  --> app\modules\multimodal\metrics.py:8:25
   |
 6 | from typing import Dict, List, Optional, Any
 7 | from datetime import datetime, timedelta
 8 | from collections import defaultdict
   |                         ^^^^^^^^^^^
 9 | from loguru import logger
10 | import time
   |
help: Remove unused import: `collections.defaultdict`

F401 [*] `asyncio` imported but unused
  --> app\modules\multimodal\metrics.py:11:8
   |
 9 | from loguru import logger
10 | import time
11 | import asyncio
   |        ^^^^^^^
12 | from threading import Lock
   |
help: Remove unused import: `asyncio`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\modules\multimodal\metrics_storage.py:10:28
   |
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, func, and_, desc
10 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
11 |
12 | from app.models.multimodal_metrics import (
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F401 [*] `app.models.multimodal_metrics.MultimodalPerformanceAlert` imported but unused
  --> app\modules\multimodal\metrics_storage.py:14:5
   |
12 | from app.models.multimodal_metrics import (
13 |     MultimodalPerformanceMetric,
14 |     MultimodalPerformanceAlert,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^
15 |     MultimodalOptimizationHistory
16 | )
   |
help: Remove unused import

F401 [*] `app.models.multimodal_metrics.MultimodalOptimizationHistory` imported but unused
  --> app\modules\multimodal\metrics_storage.py:15:5
   |
13 |     MultimodalPerformanceMetric,
14 |     MultimodalPerformanceAlert,
15 |     MultimodalOptimizationHistory
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | )
17 | from app.modules.multimodal.metrics import MultimodalMetrics
   |
help: Remove unused import

F401 [*] `app.modules.multimodal.metrics.MultimodalMetrics` imported but unused
  --> app\modules\multimodal\metrics_storage.py:17:44
   |
15 |     MultimodalOptimizationHistory
16 | )
17 | from app.modules.multimodal.metrics import MultimodalMetrics
   |                                            ^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.modules.multimodal.metrics.MultimodalMetrics`

F821 Undefined name `Integer`
   --> app\modules\multimodal\metrics_storage.py:134:75
    |
132 |                 MultimodalPerformanceMetric.operation,
133 |                 func.count(MultimodalPerformanceMetric.id).label('total_count'),
134 |                 func.sum(func.cast(MultimodalPerformanceMetric.cache_hit, Integer)).label('cache_hits'),
    |                                                                           ^^^^^^^
135 |                 func.avg(MultimodalPerformanceMetric.duration).label('avg_duration'),
136 |                 func.min(MultimodalPerformanceMetric.duration).label('min_duration'),
    |

F821 Undefined name `Integer`
   --> app\modules\multimodal\metrics_storage.py:138:71
    |
136 |                 func.min(MultimodalPerformanceMetric.duration).label('min_duration'),
137 |                 func.max(MultimodalPerformanceMetric.duration).label('max_duration'),
138 |                 func.sum(func.cast(MultimodalPerformanceMetric.error, Integer)).label('error_count'),
    |                                                                       ^^^^^^^
139 |                 func.max(MultimodalPerformanceMetric.concurrent).label('max_concurrent')
140 |             )
    |

F401 [*] `typing.Optional` imported but unused
 --> app\modules\multimodal\text_analyzer.py:6:32
  |
4 | """
5 |
6 | from typing import Dict, List, Optional, Any
  |                                ^^^^^^^^
7 | from pathlib import Path
8 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\multimodal\text_analyzer.py:7:21
  |
6 | from typing import Dict, List, Optional, Any
7 | from pathlib import Path
  |                     ^^^^
8 | from loguru import logger
9 | import re
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\multimodal\video_analyzer.py:7:21
  |
6 | from typing import Dict, List, Optional, Any
7 | from pathlib import Path
  |                     ^^^^
8 | from loguru import logger
9 | import subprocess
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `functools.lru_cache` imported but unused
  --> app\modules\multimodal\video_analyzer.py:15:23
   |
13 | from datetime import datetime
14 | import hashlib
15 | from functools import lru_cache
   |                       ^^^^^^^^^
16 |
17 | # 可选依赖：OpenCV用于视频场景检测
   |
help: Remove unused import: `functools.lru_cache`

F401 `numpy` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\modules\multimodal\video_analyzer.py:20:21
   |
18 | try:
19 |     import cv2
20 |     import numpy as np
   |                     ^^
21 |     OPENCV_AVAILABLE = True
22 | except ImportError:
   |
help: Remove unused import: `numpy`

F821 Undefined name `time`
   --> app\modules\multimodal\video_analyzer.py:147:22
    |
145 |             分析结果字典
146 |         """
147 |         start_time = time.time()
    |                      ^^^^
148 |         cache_hit = False
149 |         error_occurred = False
    |

F821 Undefined name `time`
   --> app\modules\multimodal\video_analyzer.py:164:36
    |
162 |                     # 记录性能指标（异步）
163 |                     if METRICS_AVAILABLE:
164 |                         duration = time.time() - start_time
    |                                    ^^^^
165 |                         # 使用异步方法记录（如果支持数据库存储）
166 |                         try:
    |

E722 Do not use bare `except`
   --> app\modules\multimodal\video_analyzer.py:174:25
    |
172 |                                 concurrent=0
173 |                             )
174 |                         except:
    |                         ^^^^^^
175 |                             # 回退到同步方法
176 |                             MultimodalMetrics.record_request(
    |

F821 Undefined name `time`
   --> app\modules\multimodal\video_analyzer.py:222:36
    |
220 |                     # 记录性能指标
221 |                     if METRICS_AVAILABLE:
222 |                         duration = time.time() - start_time
    |                                    ^^^^
223 |                         MultimodalMetrics.record_request(
224 |                             operation="video_analysis",
    |

F821 Undefined name `time`
   --> app\modules\multimodal\video_analyzer.py:238:36
    |
236 |                     # 记录错误
237 |                     if METRICS_AVAILABLE:
238 |                         duration = time.time() - start_time
    |                                    ^^^^
239 |                         MultimodalMetrics.record_request(
240 |                             operation="video_analysis",
    |

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\multimodal\video_analyzer.py:253:29
    |
251 |                 finally:
252 |                     self._current_concurrent -= 1
253 |         except Exception as e:
    |                             ^
254 |             error_occurred = True
255 |             # 记录错误
    |
help: Remove assignment to unused variable `e`

F841 Local variable `error_occurred` is assigned to but never used
   --> app\modules\multimodal\video_analyzer.py:254:13
    |
252 |                     self._current_concurrent -= 1
253 |         except Exception as e:
254 |             error_occurred = True
    |             ^^^^^^^^^^^^^^
255 |             # 记录错误
256 |             if METRICS_AVAILABLE:
    |
help: Remove assignment to unused variable `error_occurred`

F821 Undefined name `time`
   --> app\modules\multimodal\video_analyzer.py:257:28
    |
255 |             # 记录错误
256 |             if METRICS_AVAILABLE:
257 |                 duration = time.time() - start_time
    |                            ^^^^
258 |                 MultimodalMetrics.record_request(
259 |                     operation="video_analysis",
    |

F401 [*] `typing.Dict` imported but unused
  --> app\modules\music\cover_downloader.py:9:30
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Optional, Dict, Any
   |                              ^^^^
10 | from loguru import logger
11 | from app.core.cache import get_cache
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\modules\music\cover_downloader.py:9:36
   |
 7 | import os
 8 | from pathlib import Path
 9 | from typing import Optional, Dict, Any
   |                                    ^^^
10 | from loguru import logger
11 | from app.core.cache import get_cache
   |
help: Remove unused import

F401 [*] `os` imported but unused
 --> app\modules\music\importer.py:7:8
  |
5 | """
6 |
7 | import os
  |        ^^
8 | import shutil
9 | import re
  |
help: Remove unused import: `os`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\music\importer.py:12:22
   |
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any
12 | from datetime import datetime
   |                      ^^^^^^^^
13 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.modules.inbox.models.InboxItem` imported but unused
  --> app\modules\music\importer.py:22:38
   |
20 | from app.modules.media_renamer.category_helper import CategoryHelper
21 | from app.modules.audiobook.media_info import probe_audio_file
22 | from app.modules.inbox.models import InboxItem
   |                                      ^^^^^^^^^
   |
help: Remove unused import: `app.modules.inbox.models.InboxItem`

F401 `mutagen.id3.ID3NoHeaderError` imported but unused; consider using `importlib.util.find_spec` to test for availability
   --> app\modules\music\importer.py:127:37
    |
125 |         try:
126 |             import mutagen
127 |             from mutagen.id3 import ID3NoHeaderError
    |                                     ^^^^^^^^^^^^^^^^
128 |         except ImportError:
129 |             logger.debug(f"mutagen 未安装，跳过音频元数据解析: {file_path}")
    |
help: Remove unused import: `mutagen.id3.ID3NoHeaderError`

F601 Dictionary key literal `'format'` repeated
   --> app\modules\music\lyrics_fetcher.py:167:21
    |
165 |                     'loginUin': 0,
166 |                     'hostUin': 0,
167 |                     'format': 'json',
    |                     ^^^^^^^^
168 |                     'inCharset': 'utf8',
169 |                     'outCharset': 'utf-8',
    |
help: Remove repeated key literal `'format'`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\music\metadata_extractor.py:7:21
  |
6 | import os
7 | from pathlib import Path
  |                     ^^^^
8 | from typing import Dict, Optional, Any
9 | from loguru import logger
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `mutagen.id3.APIC` imported but unused
   --> app\modules\music\metadata_extractor.py:158:50
    |
156 |                 # MP3文件：从ID3标签提取APIC
157 |                 try:
158 |                     from mutagen.id3 import ID3, APIC
    |                                                  ^^^^
159 |                     id3 = ID3(audio_file.filename)
160 |                     if 'APIC:' in id3:
    |
help: Remove unused import: `mutagen.id3.APIC`

F401 [*] `json` imported but unused
 --> app\modules\music\scraper.py:7:8
  |
6 | import os
7 | import json
  |        ^^^^
8 | import asyncio
9 | from typing import Dict, List, Any, Optional
  |
help: Remove unused import: `json`

F401 [*] `sqlalchemy.text` imported but unused
 --> app\modules\music\service.py:5:46
  |
3 | """
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, delete, func, text, desc, and_
  |                                              ^^^^
6 | from typing import List, Optional, Dict, Any, Tuple
7 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.text`

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\music\service.py:6:47
  |
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, delete, func, text, desc, and_
6 | from typing import List, Optional, Dict, Any, Tuple
  |                                               ^^^^^
7 | from datetime import datetime
8 | from uuid import uuid4
  |
help: Remove unused import: `typing.Tuple`

F401 [*] `app.models.music.MusicPlaylist` imported but unused
  --> app\modules\music\service.py:16:5
   |
14 |     MusicSubscription,
15 |     MusicTrack,
16 |     MusicPlaylist,
   |     ^^^^^^^^^^^^^
17 |     MusicLibrary,
18 |     MusicChartRecord,
   |
help: Remove unused import: `app.models.music.MusicPlaylist`

F401 [*] `app.modules.music.schemas.MusicChartEntry` imported but unused
  --> app\modules\music\service.py:28:39
   |
26 | from app.modules.music.lyrics_fetcher import LyricsFetcher
27 | from app.modules.music.cover_downloader import CoverDownloader
28 | from app.modules.music.schemas import MusicChartEntry
   |                                       ^^^^^^^^^^^^^^^
29 | from app.modules.music import query_builder
30 | from app.modules.music.schema_utils import ensure_music_schema
   |
help: Remove unused import: `app.modules.music.schemas.MusicChartEntry`

F841 Local variable `settings_service` is assigned to but never used
  --> app\modules\music\service.py:64:17
   |
62 |         try:
63 |             if self._spotify_client is None:
64 |                 settings_service = SettingsService(self.db)
   |                 ^^^^^^^^^^^^^^^^
65 |                 # 注意：这里需要同步调用，但SettingsService是异步的
66 |                 # 我们将在实际调用时获取设置
   |
help: Remove assignment to unused variable `settings_service`

F401 [*] `os` imported but unused
   --> app\modules\music\service.py:774:16
    |
772 |     ) -> Dict:
773 |         """扫描音乐库"""
774 |         import os
    |                ^^
775 |         from pathlib import Path
    |
help: Remove unused import: `os`

F401 [*] `re` imported but unused
 --> app\modules\music\work_resolver.py:7:8
  |
5 | """
6 |
7 | import re
  |        ^^
8 | from typing import Optional
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `re`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\music_charts\apple_music_fetcher.py:8:20
   |
 7 | from datetime import datetime
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 |
10 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\music_charts\factory.py:8:20
   |
 6 | """
 7 |
 8 | from typing import Optional, Type
   |                    ^^^^^^^^
 9 |
10 | from app.models.music_chart_source import MusicChartSource
   |
help: Remove unused import: `typing.Optional`

F401 [*] `typing.List` imported but unused
  --> app\modules\music_charts\netease_fetcher.py:20:20
   |
18 | """
19 |
20 | from typing import List, Optional
   |                    ^^^^
21 | from datetime import datetime
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\modules\music_charts\netease_fetcher.py:20:26
   |
18 | """
19 |
20 | from typing import List, Optional
   |                          ^^^^^^^^
21 | from datetime import datetime
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\music_charts\rss_fetcher.py:8:20
  |
7 | from datetime import datetime
8 | from typing import Optional
  |                    ^^^^^^^^
9 | import re
  |
help: Remove unused import: `typing.Optional`

F401 [*] `re` imported but unused
  --> app\modules\music_charts\rss_fetcher.py:9:8
   |
 7 | from datetime import datetime
 8 | from typing import Optional
 9 | import re
   |        ^^
10 |
11 | from loguru import logger
   |
help: Remove unused import: `re`

F401 [*] `typing.List` imported but unused
  --> app\modules\music_charts\spotify_fetcher.py:20:20
   |
18 | """
19 |
20 | from typing import List, Optional
   |                    ^^^^
21 | from datetime import datetime
   |
help: Remove unused import: `typing.List`

E402 Module level import not at top of file
   --> app\modules\music_charts\spotify_fetcher.py:216:1
    |
215 | # 需要导入 timedelta
216 | from datetime import timedelta
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |

F401 [*] `loguru.logger` imported but unused
 --> app\modules\notification\channels\base.py:6:20
  |
4 | from abc import ABC, abstractmethod
5 | from typing import Dict, Optional, Any
6 | from loguru import logger
  |                    ^^^^^^
  |
help: Remove unused import: `loguru.logger`

F401 [*] `sqlalchemy.update` imported but unused
 --> app\modules\notification\service.py:5:32
  |
3 | """
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, update
  |                                ^^^^^^
6 | from typing import List, Optional, Dict
7 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.update`

E712 Avoid equality comparisons to `False`; use `not Notification.is_read:` for false checks
   --> app\modules\notification\service.py:101:33
    |
100 |         if unread_only:
101 |             query = query.where(Notification.is_read == False)
    |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
102 |         
103 |         query = query.order_by(Notification.created_at.desc()).limit(limit)
    |
help: Replace with `not Notification.is_read`

E712 Avoid equality comparisons to `False`; use `not Notification.is_read:` for false checks
   --> app\modules\notification\service.py:132:44
    |
130 |     async def mark_all_as_read(self, notification_type: Optional[str] = None) -> int:
131 |         """标记所有通知为已读"""
132 |         query = select(Notification).where(Notification.is_read == False)
    |                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
133 |         
134 |         if notification_type:
    |
help: Replace with `not Notification.is_read`

E712 Avoid equality comparisons to `False`; use `not Notification.is_read:` for false checks
   --> app\modules\notification\service.py:155:59
    |
153 |         from sqlalchemy import func
154 |         
155 |         query = select(func.count(Notification.id)).where(Notification.is_read == False)
    |                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
156 |         
157 |         if notification_type:
    |
help: Replace with `not Notification.is_read`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\novel\inbox_service.py:9:22
   |
 7 | from typing import Optional, List
 8 | from dataclasses import dataclass
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\novel\pipeline.py:315:37
    |
313 |                     generated_chapters += 1
314 |                     logger.debug(f"章节 {idx} TTS 完成: {result.audio_path}")
315 |                 except Exception as e:
    |                                     ^
316 |                     logger.exception(f"TTS synth failed for ebook_id={ebook.id} chapter={idx}")
317 |                     # 合成失败不计入 generated，但也不计入 rate_limited
    |
help: Remove assignment to unused variable `e`

F841 [*] Local variable `e` is assigned to but never used
   --> app\modules\novel\pipeline.py:346:33
    |
344 |                     audiobook_files.append(af)
345 |                     logger.debug(f"有声书文件导入成功: {audio_path} (TTS: {hints['tts_provider']})")
346 |             except Exception as e:
    |                                 ^
347 |                 logger.exception(f"Audiobook import failed for {audio_path}")
    |
help: Remove assignment to unused variable `e`

F401 [*] `app.modules.novel.reader_service.get_chapter_content` imported but unused
  --> app\modules\novel\search_service.py:12:71
   |
10 | from app.models.ebook import EBook
11 | from app.schemas.novel_reader import NovelSearchHit
12 | from app.modules.novel.reader_service import get_chapters_from_ebook, get_chapter_content
   |                                                                       ^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.modules.novel.reader_service.get_chapter_content`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\novel\sources\local_txt.py:10:36
   |
 8 | import re
 9 | from pathlib import Path
10 | from typing import Iterable, List, Optional
   |                                    ^^^^^^^^
11 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.func` imported but unused
 --> app\modules\ocr\statistics.py:7:32
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_, desc
  |                                ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\ocr\statistics.py:7:44
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_, desc
  |                                            ^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `OCRRecord.success:` for truth checks
   --> app\modules\ocr\statistics.py:218:21
    |
216 |                 and_(
217 |                     OCRRecord.image_hash == image_hash,
218 |                     OCRRecord.success == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^
219 |                 )
220 |             ).order_by(desc(OCRRecord.created_at)).limit(1)
    |
help: Replace with `OCRRecord.success`

F401 [*] `math` imported but unused
  --> app\modules\recommendation\algorithms.py:10:8
   |
 8 | from dataclasses import dataclass
 9 | from loguru import logger
10 | import math
   |        ^^^^
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, func
   |
help: Remove unused import: `math`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\recommendation\algorithms.py:13:22
   |
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, func
13 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
14 |
15 | from app.models.subscription import Subscription
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\recommendation\algorithms.py:13:32
   |
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, func
13 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
14 |
15 | from app.models.subscription import Subscription
   |
help: Remove unused import

F401 [*] `app.models.download.DownloadTask` imported but unused
  --> app\modules\recommendation\algorithms.py:16:33
   |
15 | from app.models.subscription import Subscription
16 | from app.models.download import DownloadTask
   |                                 ^^^^^^^^^^^^
   |
help: Remove unused import: `app.models.download.DownloadTask`

F541 [*] f-string without any placeholders
   --> app\modules\recommendation\deep_learning\gpu_utils.py:105:34
    |
103 |         info["gpu_available"] = True
104 |         info["device_count"] = torch.cuda.device_count()
105 |         info["current_device"] = f"cuda:0"
    |                                  ^^^^^^^^^
106 |         info["device_name"] = torch.cuda.get_device_name(0)
    |
help: Remove extraneous `f` prefix

F401 [*] `typing.Dict` imported but unused
 --> app\modules\recommendation\deep_learning\predictor.py:5:26
  |
3 | """
4 |
5 | from typing import List, Dict, Optional, Tuple
  |                          ^^^^
6 | from loguru import logger
7 | import numpy as np
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\recommendation\deep_learning\predictor.py:5:32
  |
3 | """
4 |
5 | from typing import List, Dict, Optional, Tuple
  |                                ^^^^^^^^
6 | from loguru import logger
7 | import numpy as np
  |
help: Remove unused import

F401 [*] `numpy` imported but unused
 --> app\modules\recommendation\deep_learning\predictor.py:7:17
  |
5 | from typing import List, Dict, Optional, Tuple
6 | from loguru import logger
7 | import numpy as np
  |                 ^^
8 |
9 | try:
  |
help: Remove unused import: `numpy`

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\recommendation\deep_learning\trainer.py:6:47
  |
5 | import asyncio
6 | from typing import Dict, List, Optional, Any, Tuple
  |                                               ^^^^^
7 | from datetime import datetime
8 | from loguru import logger
  |
help: Remove unused import: `typing.Tuple`

F401 [*] `numpy` imported but unused
  --> app\modules\recommendation\deep_learning\trainer.py:10:17
   |
 8 | from loguru import logger
 9 | import pandas as pd
10 | import numpy as np
   |                 ^^
11 |
12 | try:
   |
help: Remove unused import: `numpy`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\recommendation\deep_learning_recommender.py:6:32
  |
4 | """
5 |
6 | from typing import List, Dict, Optional, Any
  |                                ^^^^^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `asyncio` imported but unused
  --> app\modules\recommendation\deep_learning_recommender.py:10:8
   |
 8 | from loguru import logger
 9 | import pandas as pd
10 | import asyncio
   |        ^^^^^^^
11 | from datetime import datetime
   |
help: Remove unused import: `asyncio`

F401 [*] `app.modules.recommendation.deep_learning.gpu_utils.check_gpu_available` imported but unused
  --> app\modules\recommendation\deep_learning_recommender.py:16:64
   |
14 | from app.modules.recommendation.deep_learning.trainer import DeepLearningTrainer
15 | from app.modules.recommendation.deep_learning.predictor import DeepLearningPredictor
16 | from app.modules.recommendation.deep_learning.gpu_utils import check_gpu_available, get_device_info
   |                                                                ^^^^^^^^^^^^^^^^^^^
17 | from app.core.config import settings
18 | from app.models.subscription import Subscription
   |
help: Remove unused import

F401 [*] `app.modules.recommendation.deep_learning.gpu_utils.get_device_info` imported but unused
  --> app\modules\recommendation\deep_learning_recommender.py:16:85
   |
14 | from app.modules.recommendation.deep_learning.trainer import DeepLearningTrainer
15 | from app.modules.recommendation.deep_learning.predictor import DeepLearningPredictor
16 | from app.modules.recommendation.deep_learning.gpu_utils import check_gpu_available, get_device_info
   |                                                                                     ^^^^^^^^^^^^^^^
17 | from app.core.config import settings
18 | from app.models.subscription import Subscription
   |
help: Remove unused import

F401 `torch` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\modules\recommendation\deep_learning_recommender.py:44:24
   |
42 |             # 检查PyTorch是否可用
43 |             try:
44 |                 import torch
   |                        ^^^^^
45 |             except ImportError:
46 |                 logger.warning("PyTorch is not installed, deep learning recommender will not work")
   |
help: Remove unused import: `torch`

F811 [*] Redefinition of unused `get_device_info` from line 16
   --> app\modules\recommendation\deep_learning_recommender.py:285:72
    |
283 |         info = self.trainer.get_model_info()
284 |         info["enabled"] = True
285 |         from app.modules.recommendation.deep_learning.gpu_utils import get_device_info
    |                                                                        ^^^^^^^^^^^^^^^ `get_device_info` redefined here
286 |         info["device_info"] = get_device_info()
    |
   ::: app\modules\recommendation\deep_learning_recommender.py:16:85
    |
 14 | from app.modules.recommendation.deep_learning.trainer import DeepLearningTrainer
 15 | from app.modules.recommendation.deep_learning.predictor import DeepLearningPredictor
 16 | from app.modules.recommendation.deep_learning.gpu_utils import check_gpu_available, get_device_info
    |                                                                                     --------------- previous definition of `get_device_info` here
 17 | from app.core.config import settings
 18 | from app.models.subscription import Subscription
    |
help: Remove definition: `get_device_info`

F401 [*] `asyncio` imported but unused
 --> app\modules\recommendation\realtime\ab_testing.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | from typing import Dict, List, Optional, Any, Tuple
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `asyncio`

F401 [*] `typing.Tuple` imported but unused
 --> app\modules\recommendation\realtime\ab_testing.py:7:47
  |
6 | import asyncio
7 | from typing import Dict, List, Optional, Any, Tuple
  |                                               ^^^^^
8 | from datetime import datetime, timedelta
9 | from dataclasses import dataclass, field
  |
help: Remove unused import: `typing.Tuple`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\recommendation\realtime\ab_testing.py:8:32
   |
 6 | import asyncio
 7 | from typing import Dict, List, Optional, Any, Tuple
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from dataclasses import dataclass, field
10 | from enum import Enum
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `math` imported but unused
  --> app\modules\recommendation\realtime\ab_testing.py:13:8
   |
11 | from collections import defaultdict
12 | from loguru import logger
13 | import math
   |        ^^^^
14 |
15 | from app.modules.recommendation.algorithms import RecommendationResult
   |
help: Remove unused import: `math`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\recommendation\realtime\feature_updater.py:7:32
  |
6 | import asyncio
7 | from typing import Dict, List, Optional, Any
  |                                ^^^^^^^^
8 | from datetime import datetime, timedelta
9 | from collections import defaultdict
  |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\recommendation\realtime\feature_updater.py:8:32
   |
 6 | import asyncio
 7 | from typing import Dict, List, Optional, Any
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from collections import defaultdict
10 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `asyncio` imported but unused
 --> app\modules\recommendation\realtime\stream_processor.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | from typing import Dict, List, Optional, Any, Set
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `asyncio`

F401 [*] `app.modules.recommendation.realtime.ab_testing.Experiment` imported but unused
  --> app\modules\recommendation\realtime_service.py:18:5
   |
16 | from app.modules.recommendation.realtime.ab_testing import (
17 |     ABTestingFramework,
18 |     Experiment,
   |     ^^^^^^^^^^
19 |     ExperimentVariant,
20 |     ExperimentStatus
   |
help: Remove unused import

F401 [*] `app.modules.recommendation.realtime.ab_testing.ExperimentStatus` imported but unused
  --> app\modules\recommendation\realtime_service.py:20:5
   |
18 |     Experiment,
19 |     ExperimentVariant,
20 |     ExperimentStatus
   |     ^^^^^^^^^^^^^^^^
21 | )
22 | from app.modules.recommendation.service import RecommendationService
   |
help: Remove unused import

F401 [*] `app.modules.recommendation.algorithms.RecommendationResult` imported but unused
  --> app\modules\recommendation\service.py:16:5
   |
14 |     ContentBasedRecommender,
15 |     PopularityBasedRecommender,
16 |     RecommendationResult
   |     ^^^^^^^^^^^^^^^^^^^^
17 | )
18 | from app.core.bangumi_client import BangumiClient
   |
help: Remove unused import: `app.modules.recommendation.algorithms.RecommendationResult`

F401 [*] `typing.List` imported but unused
 --> app\modules\remote_playback\remote_115_service.py:6:26
  |
4 | 提供 115 视频播放相关的统一封装
5 | """
6 | from typing import Dict, List, Optional, Any
  |                          ^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select
  |
help: Remove unused import: `typing.List`

F401 [*] `..media_renamer.parser.MediaInfo` imported but unused
  --> app\modules\rss\media_extractor.py:11:52
   |
 9 | from loguru import logger
10 |
11 | from ..media_renamer.parser import FilenameParser, MediaInfo
   |                                                    ^^^^^^^^^
   |
help: Remove unused import: `..media_renamer.parser.MediaInfo`

F401 [*] `typing.List` imported but unused
 --> app\modules\rss\rule_engine.py:7:31
  |
6 | import re
7 | from typing import Any, Dict, List, Optional
  |                               ^^^^
8 |
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\rss\rule_engine.py:7:37
  |
6 | import re
7 | from typing import Any, Dict, List, Optional
  |                                     ^^^^^^^^
8 |
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `loguru.logger` imported but unused
  --> app\modules\rss\rule_engine.py:9:20
   |
 7 | from typing import Any, Dict, List, Optional
 8 |
 9 | from loguru import logger
   |                    ^^^^^^
10 |
11 | from app.constants.media_types import is_tv_like
   |
help: Remove unused import: `loguru.logger`

F541 [*] f-string without any placeholders
   --> app\modules\rss\rule_engine.py:116:38
    |
114 |                 failed_rules.append(f"触发排除规则: {subscription.exclude}")
115 |             else:
116 |                 matched_rules.append(f"排除规则通过")
    |                                      ^^^^^^^^^^^^^^^
117 |                 score += 0.15
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\rss\rule_engine.py:125:38
    |
123 |                 failed_rules.append(f"发布组不匹配: {subscription.filter_groups}")
124 |             else:
125 |                 matched_rules.append(f"发布组匹配")
    |                                      ^^^^^^^^^^^^^
126 |                 score += 0.1
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\modules\rss\rule_engine.py:152:38
    |
150 |                 failed_rules.append(f"搜索规则不匹配: {subscription.search_rules}")
151 |             else:
152 |                 matched_rules.append(f"搜索规则匹配")
    |                                      ^^^^^^^^^^^^^^^
153 |                 score += 0.1
    |
help: Remove extraneous `f` prefix

F401 [*] `sqlalchemy.update` imported but unused
 --> app\modules\rss\service.py:6:32
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, update, delete, func, and_, or_
  |                                ^^^^^^
7 | from typing import List, Optional, Dict, Tuple
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `sqlalchemy.update`

F401 [*] `app.modules.search.service.SearchService` imported but unused
  --> app\modules\rss\service.py:16:40
   |
14 | from app.modules.rss.media_extractor import RSSMediaExtractor, ExtractedMediaInfo
15 | from app.modules.rss.rule_engine import RSSRuleEngine
16 | from app.modules.search.service import SearchService
   |                                        ^^^^^^^^^^^^^
17 | from app.modules.download.service import DownloadService
18 | from app.modules.subscription.service import SubscriptionService
   |
help: Remove unused import: `app.modules.search.service.SearchService`

F811 [*] Redefinition of unused `or_` from line 6
  --> app\modules\rss\service.py:20:24
   |
18 | from app.modules.subscription.service import SubscriptionService
19 | from app.models.subscription import Subscription
20 | from sqlalchemy import or_, and_
   |                        ^^^ `or_` redefined here
21 | import re
22 | from copy import deepcopy
   |
  ::: app\modules\rss\service.py:6:60
   |
 5 | from sqlalchemy.ext.asyncio import AsyncSession
 6 | from sqlalchemy import select, update, delete, func, and_, or_
   |                                                            --- previous definition of `or_` here
 7 | from typing import List, Optional, Dict, Tuple
 8 | from datetime import datetime, timedelta
   |
help: Remove definition: `or_`

F811 [*] Redefinition of unused `and_` from line 6
  --> app\modules\rss\service.py:20:29
   |
18 | from app.modules.subscription.service import SubscriptionService
19 | from app.models.subscription import Subscription
20 | from sqlalchemy import or_, and_
   |                             ^^^^ `and_` redefined here
21 | import re
22 | from copy import deepcopy
   |
  ::: app\modules\rss\service.py:6:54
   |
 5 | from sqlalchemy.ext.asyncio import AsyncSession
 6 | from sqlalchemy import select, update, delete, func, and_, or_
   |                                                      ---- previous definition of `and_` here
 7 | from typing import List, Optional, Dict, Tuple
 8 | from datetime import datetime, timedelta
   |
help: Remove definition: `and_`

F401 [*] `re` imported but unused
  --> app\modules\rss\service.py:21:8
   |
19 | from app.models.subscription import Subscription
20 | from sqlalchemy import or_, and_
21 | import re
   |        ^^
22 | from copy import deepcopy
23 | from app.constants.media_types import is_tv_like
   |
help: Remove unused import: `re`

E712 Avoid equality comparisons to `True`; use `Subscription.auto_download:` for truth checks
   --> app\modules\rss\service.py:600:17
    |
598 |             query = select(Subscription).where(
599 |                 Subscription.status == "active",
600 |                 Subscription.auto_download == True
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
601 |             )
    |
help: Replace with `Subscription.auto_download`

E712 Avoid equality comparisons to `True`; use `RSSItem.processed:` for truth checks
   --> app\modules\rss\service.py:798:46
    |
797 |         # 已处理数量
798 |         processed_conditions = conditions + [RSSItem.processed == True]
    |                                              ^^^^^^^^^^^^^^^^^^^^^^^^^
799 |         processed_query = select(func.count(RSSItem.id)).where(and_(*processed_conditions))
800 |         processed_result = await self.db.execute(processed_query)
    |
help: Replace with `RSSItem.processed`

E712 Avoid equality comparisons to `True`; use `RSSItem.downloaded:` for truth checks
   --> app\modules\rss\service.py:804:47
    |
803 |         # 已下载数量
804 |         downloaded_conditions = conditions + [RSSItem.downloaded == True]
    |                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
805 |         downloaded_query = select(func.count(RSSItem.id)).where(and_(*downloaded_conditions))
806 |         downloaded_result = await self.db.execute(downloaded_query)
    |
help: Replace with `RSSItem.downloaded`

F401 [*] `os` imported but unused
 --> app\modules\rsshub\config_loader.py:7:8
  |
6 | import json
7 | import os
  |        ^^
8 | from pathlib import Path
9 | from typing import List, Dict, Optional
  |
help: Remove unused import: `os`

F401 [*] `app.core.database.Base` imported but unused
  --> app\modules\rsshub\config_loader.py:15:31
   |
14 | from app.models.rsshub import RSSHubSource, RSSHubComposite
15 | from app.core.database import Base
   |                               ^^^^
   |
help: Remove unused import: `app.core.database.Base`

F401 [*] `loguru.logger` imported but unused
 --> app\modules\rsshub\media_extractor.py:8:20
  |
6 | import re
7 | from typing import Dict, Optional
8 | from loguru import logger
  |                    ^^^^^^
  |
help: Remove unused import: `loguru.logger`

F401 [*] `re` imported but unused
 --> app\modules\rsshub\scheduler.py:6:8
  |
5 | import hashlib
6 | import re
  |        ^^
7 | from typing import List, Dict, Set, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `re`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\rsshub\scheduler.py:8:32
   |
 6 | import re
 7 | from typing import List, Dict, Set, Optional
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\modules\rsshub\scheduler.py:10:32
   |
 8 | from datetime import datetime, timedelta
 9 | from sqlalchemy.ext.asyncio import AsyncSession
10 | from sqlalchemy import select, and_
   |                                ^^^^
11 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.and_`

E402 Module level import not at top of file
   --> app\modules\rsshub\scheduler.py:450:1
    |
449 | # 导入RSSHubService（避免循环导入）
450 | from app.modules.rsshub.service import RSSHubService
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\rsshub\service.py:6:38
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_
  |                                      ^^^
7 | from typing import List, Optional, Dict
8 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `app.modules.rsshub.constants.RSSHUB_ERROR_MISSING_TARGET` imported but unused
  --> app\modules\rsshub\service.py:18:5
   |
16 | from app.modules.rsshub.constants import (
17 |     LEGACY_PLACEHOLDER_IDS,
18 |     RSSHUB_ERROR_MISSING_TARGET,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | )
20 | from app.modules.rsshub.schema_utils import ensure_subscription_health_columns
   |
help: Remove unused import: `app.modules.rsshub.constants.RSSHUB_ERROR_MISSING_TARGET`

E712 Avoid equality comparisons to `True`; use `UserRSSHubSubscription.enabled:` for truth checks
   --> app\modules\rsshub\service.py:279:33
    |
278 |         if enabled_only:
279 |             query = query.where(UserRSSHubSubscription.enabled == True)
    |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
280 |         
281 |         result = await self.db.execute(query)
    |
help: Replace with `UserRSSHubSubscription.enabled`

E712 Avoid equality comparisons to `False`; use `not UserRSSHubSubscription.enabled:` for false checks
   --> app\modules\rsshub\service.py:299:20
    |
297 |             select(UserRSSHubSubscription, User)
298 |             .join(User, User.id == UserRSSHubSubscription.user_id)
299 |             .where(UserRSSHubSubscription.enabled == False)
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
300 |             .order_by(UserRSSHubSubscription.updated_at.desc())
301 |         )
    |
help: Replace with `not UserRSSHubSubscription.enabled`

F821 Undefined name `hr_case`
   --> app\modules\safety\engine.py:157:76
    |
155 |         )
156 |     
157 |     async def _evaluate_delete(self, ctx: SafetyContext, hr_case: Optional[hr_case],
    |                                                                            ^^^^^^^
158 |                               global_settings: GlobalSafetySettings,
159 |                               site_settings: Optional[SiteSafetySettings],
    |

F821 Undefined name `hr_case`
   --> app\modules\safety\engine.py:190:74
    |
188 |         )
189 |     
190 |     async def _evaluate_move(self, ctx: SafetyContext, hr_case: Optional[hr_case],
    |                                                                          ^^^^^^^
191 |                             global_settings: GlobalSafetySettings,
192 |                             site_settings: Optional[SiteSafetySettings],
    |

F821 Undefined name `hr_case`
   --> app\modules\safety\engine.py:228:84
    |
226 |         )
227 |     
228 |     async def _evaluate_upload_cleanup(self, ctx: SafetyContext, hr_case: Optional[hr_case],
    |                                                                                    ^^^^^^^
229 |                                       global_settings: GlobalSafetySettings,
230 |                                       site_settings: Optional[SiteSafetySettings],
    |

F821 Undefined name `hr_case`
   --> app\modules\safety\engine.py:249:83
    |
247 |         )
248 |     
249 |     async def _evaluate_generate_strm(self, ctx: SafetyContext, hr_case: Optional[hr_case],
    |                                                                                   ^^^^^^^
250 |                                      global_settings: GlobalSafetySettings,
251 |                                      site_settings: Optional[SiteSafetySettings],
    |

F401 [*] `asyncio` imported but unused
  --> app\modules\safety\settings.py:8:8
   |
 6 | from __future__ import annotations
 7 |
 8 | import asyncio
   |        ^^^^^^^
 9 | from datetime import datetime, timedelta
10 | from typing import Any, Dict, List, Optional
   |
help: Remove unused import: `asyncio`

F401 [*] `sqlalchemy.select` imported but unused
  --> app\modules\safety\settings.py:12:24
   |
10 | from typing import Any, Dict, List, Optional
11 |
12 | from sqlalchemy import select
   |                        ^^^^^^
13 | from sqlalchemy.orm import Session
   |
help: Remove unused import: `sqlalchemy.select`

F401 [*] `sqlalchemy.orm.Session` imported but unused
  --> app\modules\safety\settings.py:13:28
   |
12 | from sqlalchemy import select
13 | from sqlalchemy.orm import Session
   |                            ^^^^^^^
14 |
15 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `sqlalchemy.orm.Session`

F841 Local variable `session` is assigned to but never used
  --> app\modules\safety\settings.py:72:47
   |
71 |         # 从数据库获取站点设置
72 |         async with self._session_factory() as session:
   |                                               ^^^^^^^
73 |             # 这里需要创建站点安全设置的数据库表
74 |             # 暂时返回基于站点键的默认设置
   |
help: Remove assignment to unused variable `session`

F841 Local variable `session` is assigned to but never used
  --> app\modules\safety\settings.py:92:47
   |
91 |         # 从数据库获取订阅设置
92 |         async with self._session_factory() as session:
   |                                               ^^^^^^^
93 |             # 这里需要创建订阅安全设置的数据库表
94 |             # 暂时返回基于订阅ID的默认设置
   |
help: Remove assignment to unused variable `session`

F401 [*] `sqlalchemy.and_` imported but unused
 --> app\modules\scheduler\monitor.py:6:32
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_, desc, func
  |                                ^^^^
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\scheduler\monitor.py:6:38
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_, desc, func
  |                                      ^^^
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
 --> app\modules\scheduler\monitor.py:6:49
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, and_, or_, desc, func
  |                                                 ^^^^
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
 --> app\modules\scheduler\monitor.py:8:32
  |
6 | from sqlalchemy import select, and_, or_, desc, func
7 | from typing import List, Dict, Any, Optional
8 | from datetime import datetime, timedelta
  |                                ^^^^^^^^^
9 | from loguru import logger
  |
help: Remove unused import: `datetime.timedelta`

E722 Do not use bare `except`
   --> app\modules\scheduler\monitor.py:329:9
    |
327 |                     "trigger": str(trigger)
328 |                 }
329 |         except:
    |         ^^^^^^
330 |             return {
331 |                 "type": "unknown",
    |

F401 [*] `datetime.datetime` imported but unused
 --> app\modules\search\indexer_manager.py:7:22
  |
6 | from typing import List, Optional, Dict, Any
7 | from datetime import datetime
  |                      ^^^^^^^^
8 | import asyncio
9 | from loguru import logger
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\search\indexer_manager.py:11:29
   |
 9 | from loguru import logger
10 |
11 | from app.core.config import settings
   |                             ^^^^^^^^
12 |
13 | from .indexers.base import IndexerBase, IndexerConfig
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `.indexers.private_indexer.PrivateIndexer` imported but unused
  --> app\modules\search\indexer_manager.py:15:39
   |
13 | from .indexers.base import IndexerBase, IndexerConfig
14 | from .indexers.public_indexer import PublicIndexer
15 | from .indexers.private_indexer import PrivateIndexer
   |                                       ^^^^^^^^^^^^^^
   |
help: Remove unused import: `.indexers.private_indexer.PrivateIndexer`

F401 [*] `re` imported but unused
 --> app\modules\search\indexers\private_indexer.py:6:8
  |
4 | """
5 |
6 | import re
  |        ^^
7 | import httpx
8 | from typing import List, Optional, Dict, Any
  |
help: Remove unused import: `re`

F811 [*] Redefinition of unused `re` from line 6
   --> app\modules\search\indexers\private_indexer.py:247:16
    |
245 |     def _extract_info_hash(self, magnet_link: str) -> Optional[str]:
246 |         """从磁力链接提取info_hash"""
247 |         import re
    |                ^^ `re` redefined here
248 |         if not magnet_link:
249 |             return None
    |
   ::: app\modules\search\indexers\private_indexer.py:6:8
    |
  4 | """
  5 |
  6 | import re
    |        -- previous definition of `re` here
  7 | import httpx
  8 | from typing import List, Optional, Dict, Any
    |
help: Remove definition: `re`

F401 [*] `loguru.logger` imported but unused
 --> app\modules\search\parsers\base.py:6:20
  |
4 | from abc import ABC, abstractmethod
5 | from typing import List, Dict, Any, Optional
6 | from loguru import logger
  |                    ^^^^^^
  |
help: Remove unused import: `loguru.logger`

F401 [*] `re` imported but unused
   --> app\modules\search\parsers\base.py:130:16
    |
128 |         """
129 |         from datetime import datetime
130 |         import re
    |                ^^
131 |         
132 |         if not date_str:
    |
help: Remove unused import: `re`

F401 [*] `urllib.parse.urlparse` imported but unused
  --> app\modules\search\parsers\gazelle.py:9:35
   |
 7 | from loguru import logger
 8 | import re
 9 | from urllib.parse import urljoin, urlparse
   |                                   ^^^^^^^^
10 |
11 | from .base import ParserBase
   |
help: Remove unused import: `urllib.parse.urlparse`

E722 Do not use bare `except`
   --> app\modules\search\result_aggregator.py:189:21
    |
187 |                     try:
188 |                         upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
189 |                     except:
    |                     ^^^^^^
190 |                         upload_date = None
    |

E722 Do not use bare `except`
   --> app\modules\search\result_aggregator.py:323:17
    |
321 |                 try:
322 |                     date1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
323 |                 except:
    |                 ^^^^^^
324 |                     date1 = None
325 |             if isinstance(date2, str):
    |

E722 Do not use bare `except`
   --> app\modules\search\result_aggregator.py:328:17
    |
326 |                 try:
327 |                     date2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
328 |                 except:
    |                 ^^^^^^
329 |                     date2 = None
    |

F401 [*] `sqlalchemy.select` imported but unused
 --> app\modules\search\service.py:7:24
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, desc
  |                        ^^^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime
  |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
 --> app\modules\search\service.py:7:32
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, desc
  |                                ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime
  |
help: Remove unused import

F401 [*] `sqlalchemy.desc` imported but unused
 --> app\modules\search\service.py:7:38
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, desc
  |                                      ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime
  |
help: Remove unused import

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\search\service.py:9:22
   |
 7 | from sqlalchemy import select, func, desc
 8 | from typing import List, Optional, Dict, Any
 9 | from datetime import datetime
   |                      ^^^^^^^^
10 | import json
11 | import hashlib
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\search\service.py:21:29
   |
19 | from app.models.search_history import SearchHistory
20 | from app.core.cache import get_cache
21 | from app.core.config import settings
   |                             ^^^^^^^^
22 | from app.core.intel.service import get_intel_service, IntelService
23 | from app.modules.global_rules import GlobalRulesService
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `sqlalchemy.func` imported but unused
 --> app\modules\seeding\service.py:7:32
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_
  |                                ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.and_` imported but unused
 --> app\modules\seeding\service.py:7:38
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_
  |                                      ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\seeding\service.py:7:44
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_
  |                                            ^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\modules\seeding\statistics.py:8:32
   |
 6 | from sqlalchemy.ext.asyncio import AsyncSession
 7 | from sqlalchemy import select, func, and_, case
 8 | from typing import Dict, List, Optional, Any
   |                                ^^^^^^^^
 9 | from datetime import datetime, timedelta
10 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F841 Local variable `cutoff_date` is assigned to but never used
  --> app\modules\seeding\statistics.py:47:13
   |
46 |             statistics = []
47 |             cutoff_date = datetime.utcnow() - timedelta(days=days)
   |             ^^^^^^^^^^^
48 |             
49 |             # 获取每日完成的下载任务
   |
help: Remove assignment to unused variable `cutoff_date`

F401 [*] `sqlalchemy.update` imported but unused
 --> app\modules\settings\service.py:5:32
  |
3 | """
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, update
  |                                ^^^^^^
6 | from typing import Dict, Optional, List, Any
7 | from datetime import datetime
  |
help: Remove unused import: `sqlalchemy.update`

F401 [*] `typing.List` imported but unused
 --> app\modules\settings\service.py:6:36
  |
4 | from sqlalchemy.ext.asyncio import AsyncSession
5 | from sqlalchemy import select, update
6 | from typing import Dict, Optional, List, Any
  |                                    ^^^^
7 | from datetime import datetime
8 | from loguru import logger
  |
help: Remove unused import: `typing.List`

F401 [*] `loguru.logger` imported but unused
 --> app\modules\settings\service.py:8:20
  |
6 | from typing import Dict, Optional, List, Any
7 | from datetime import datetime
8 | from loguru import logger
  |                    ^^^^^^
9 | import json
  |
help: Remove unused import: `loguru.logger`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\site\checkin.py:10:20
   |
 8 | import asyncio
 9 | import httpx
10 | from typing import Optional, Dict, Any
   |                    ^^^^^^^^
11 | from datetime import datetime
12 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\site\checkin.py:11:22
   |
 9 | import httpx
10 | from typing import Optional, Dict, Any
11 | from datetime import datetime
   |                      ^^^^^^^^
12 | from loguru import logger
13 | from bs4 import BeautifulSoup
   |
help: Remove unused import: `datetime.datetime`

F821 Undefined name `logger`
  --> app\modules\site\service.py:28:13
   |
26 |                 return best_domain
27 |         except Exception as e:
28 |             logger.debug(f"获取站点最佳域名失败，使用原始URL: {e}")
   |             ^^^^^^
29 |         
30 |         return site.url
   |

E712 Avoid equality comparisons to `True`; use `Site.is_active:` for truth checks
  --> app\modules\site\service.py:56:33
   |
54 |         # 支持两种参数名
55 |         if active_only or active:
56 |             query = query.where(Site.is_active == True)
   |                                 ^^^^^^^^^^^^^^^^^^^^^^
57 |         
58 |         query = query.order_by(Site.name)
   |
help: Replace with `Site.is_active`

E722 Do not use bare `except`
   --> app\modules\site\service.py:349:25
    |
347 |                                 "download": None  # 需要从HTML中提取
348 |                             }
349 |                         except:
    |                         ^^^^^^
350 |                             pass
    |

F401 [*] `os` imported but unused
 --> app\modules\site_icon\resource_loader.py:6:8
  |
4 | """
5 |
6 | import os
  |        ^^
7 | import json
8 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\site_manager\integration_hooks.py:6:26
  |
4 | """
5 |
6 | from typing import List, Optional, Callable, Dict, Any
  |                          ^^^^^^^^
7 | from datetime import datetime
8 | from enum import Enum
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\site_manager\integration_hooks.py:6:52
  |
4 | """
5 |
6 | from typing import List, Optional, Callable, Dict, Any
  |                                                    ^^^
7 | from datetime import datetime
8 | from enum import Enum
  |
help: Remove unused import

F401 [*] `datetime.datetime` imported but unused
 --> app\modules\site_manager\integration_hooks.py:7:22
  |
6 | from typing import List, Optional, Callable, Dict, Any
7 | from datetime import datetime
  |                      ^^^^^^^^
8 | from enum import Enum
9 | from loguru import logger
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.schemas.site_manager.SiteBrief` imported but unused
  --> app\modules\site_manager\integration_hooks.py:12:50
   |
10 | import asyncio
11 |
12 | from app.schemas.site_manager import SiteDetail, SiteBrief, HealthStatus
   |                                                  ^^^^^^^^^
   |
help: Remove unused import: `app.schemas.site_manager.SiteBrief`

F841 Local variable `sync_service` is assigned to but never used
  --> app\modules\site_manager\integration_hooks.py:74:9
   |
73 |         # 创建同步服务
74 |         sync_service = CookieCloudSyncService(db)
   |         ^^^^^^^^^^^^
75 |         
76 |         # 使用fire-and-forget模式，避免阻塞主事务
   |
help: Remove assignment to unused variable `sync_service`

F401 [*] `json` imported but unused
 --> app\modules\site_manager\service.py:7:8
  |
6 | import asyncio
7 | import json
  |        ^^^^
8 | import time
9 | from typing import List, Optional, Dict, Any, Tuple
  |
help: Remove unused import: `json`

F401 [*] `typing.Dict` imported but unused
  --> app\modules\site_manager\service.py:9:36
   |
 7 | import json
 8 | import time
 9 | from typing import List, Optional, Dict, Any, Tuple
   |                                    ^^^^
10 | from datetime import datetime, timedelta
11 | from sqlalchemy import select, update, delete, func, and_, or_
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\modules\site_manager\service.py:9:42
   |
 7 | import json
 8 | import time
 9 | from typing import List, Optional, Dict, Any, Tuple
   |                                          ^^^
10 | from datetime import datetime, timedelta
11 | from sqlalchemy import select, update, delete, func, and_, or_
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\site_manager\service.py:10:32
   |
 8 | import time
 9 | from typing import List, Optional, Dict, Any, Tuple
10 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
11 | from sqlalchemy import select, update, delete, func, and_, or_
12 | from sqlalchemy.orm import selectinload, joinedload
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\modules\site_manager\service.py:11:48
   |
 9 | from typing import List, Optional, Dict, Any, Tuple
10 | from datetime import datetime, timedelta
11 | from sqlalchemy import select, update, delete, func, and_, or_
   |                                                ^^^^
12 | from sqlalchemy.orm import selectinload, joinedload
13 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `sqlalchemy.orm.joinedload` imported but unused
  --> app\modules\site_manager\service.py:12:42
   |
10 | from datetime import datetime, timedelta
11 | from sqlalchemy import select, update, delete, func, and_, or_
12 | from sqlalchemy.orm import selectinload, joinedload
   |                                          ^^^^^^^^^^
13 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.orm.joinedload`

F401 [*] `app.core.database.get_db` imported but unused
  --> app\modules\site_manager\service.py:15:31
   |
13 | from loguru import logger
14 |
15 | from app.core.database import get_db
   |                               ^^^^^^
16 | from app.models.site import Site, SiteStats, SiteAccessConfig, SiteCategory, SiteHealthCheck
17 | from app.schemas.site_manager import (
   |
help: Remove unused import: `app.core.database.get_db`

F401 [*] `app.models.site.SiteCategory` imported but unused
  --> app\modules\site_manager\service.py:16:64
   |
15 | from app.core.database import get_db
16 | from app.models.site import Site, SiteStats, SiteAccessConfig, SiteCategory, SiteHealthCheck
   |                                                                ^^^^^^^^^^^^
17 | from app.schemas.site_manager import (
18 |     SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
   |
help: Remove unused import: `app.models.site.SiteCategory`

F841 Local variable `start_time` is assigned to but never used
   --> app\modules\site_manager\service.py:225:9
    |
223 |             raise ValueError(f"站点不存在: {site_id}")
224 |         
225 |         start_time = time.time()
    |         ^^^^^^^^^^
226 |         status = HealthStatus.OK
227 |         error_message = None
    |
help: Remove assignment to unused variable `start_time`

F401 [*] `os` imported but unused
 --> app\modules\site_profile\loader.py:6:8
  |
4 | """
5 |
6 | import os
  |        ^^
7 | import yaml
8 | from pathlib import Path
  |
help: Remove unused import: `os`

E722 Do not use bare `except`
   --> app\modules\site_profile\parser.py:194:13
    |
192 |             try:
193 |                 return int(re.sub(r'[^\d]', '', value))
194 |             except:
    |             ^^^^^^
195 |                 return 0
196 |         elif transform_type == "float":
    |

E722 Do not use bare `except`
   --> app\modules\site_profile\parser.py:200:13
    |
198 |             try:
199 |                 return float(re.sub(r'[^\d.]', '', value))
200 |             except:
    |             ^^^^^^
201 |                 return 0.0
202 |         elif transform_type == "date":
    |

F401 [*] `sqlalchemy.desc` imported but unused
 --> app\modules\storage_monitor\service.py:6:44
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, func, and_, desc
  |                                            ^^^^
7 | from typing import Optional, Dict, List
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `sqlalchemy.desc`

F401 [*] `pathlib.Path` imported but unused
  --> app\modules\storage_monitor\service.py:11:21
   |
 9 | import psutil
10 | import os
11 | from pathlib import Path
   |                     ^^^^
12 |
13 | from app.models.storage_monitor import StorageDirectory, StorageUsageHistory, StorageAlert
   |
help: Remove unused import: `pathlib.Path`

E712 Avoid equality comparisons to `False`; use `not StorageAlert.resolved:` for false checks
   --> app\modules\storage_monitor\service.py:175:25
    |
173 |                     and_(
174 |                         StorageAlert.directory_id == directory_id,
175 |                         StorageAlert.resolved == False,
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
176 |                         StorageAlert.alert_type == "threshold_exceeded"
177 |                     )
    |
help: Replace with `not StorageAlert.resolved`

E712 Avoid equality comparisons to `True`; use `StorageDirectory.enabled:` for truth checks
   --> app\modules\storage_monitor\service.py:336:59
    |
334 |         # 获取启用的目录数
335 |         enabled_dirs = await self.db.execute(
336 |             select(func.count(StorageDirectory.id)).where(StorageDirectory.enabled == True)
    |                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
337 |         )
338 |         enabled_directories = enabled_dirs.scalar() or 0
    |
help: Replace with `StorageDirectory.enabled`

E712 Avoid equality comparisons to `False`; use `not StorageAlert.resolved:` for false checks
   --> app\modules\storage_monitor\service.py:342:55
    |
340 |         # 获取未解决的预警数
341 |         unresolved_alerts = await self.db.execute(
342 |             select(func.count(StorageAlert.id)).where(StorageAlert.resolved == False)
    |                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
343 |         )
344 |         unresolved_count = unresolved_alerts.scalar() or 0
    |
help: Replace with `not StorageAlert.resolved`

F401 [*] `typing.Any` imported but unused
 --> app\modules\strm\config.py:7:42
  |
5 | import os
6 | from pydantic import BaseModel, Field
7 | from typing import List, Optional, Dict, Any
  |                                          ^^^
8 | from .file_operation_mode import FileOperationMode, MediaLibraryDestination, STRMSyncConfig
  |
help: Remove unused import: `typing.Any`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\strm\file_handler.py:10:20
   |
 8 | import shutil
 9 | from pathlib import Path
10 | from typing import Optional, Dict, Any
   |                    ^^^^^^^^
11 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `.file_operation_mode.MediaLibraryDestination` imported but unused
  --> app\modules\strm\file_handler.py:13:53
   |
11 | from loguru import logger
12 |
13 | from .file_operation_mode import FileOperationMode, MediaLibraryDestination, FileOperationConfig
   |                                                     ^^^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `.file_operation_mode.MediaLibraryDestination`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\strm\file_operation_mode.py:7:30
  |
6 | from enum import Enum
7 | from typing import Optional, Dict, Any, TYPE_CHECKING
  |                              ^^^^
8 | from pydantic import BaseModel, Field
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\strm\file_operation_mode.py:7:36
  |
6 | from enum import Enum
7 | from typing import Optional, Dict, Any, TYPE_CHECKING
  |                                    ^^^
8 | from pydantic import BaseModel, Field
  |
help: Remove unused import

F401 [*] `typing.ForwardRef` imported but unused
  --> app\modules\strm\file_operation_mode.py:11:24
   |
10 | if TYPE_CHECKING:
11 |     from typing import ForwardRef
   |                        ^^^^^^^^^^
   |
help: Remove unused import: `typing.ForwardRef`

F401 [*] `app.models.strm.STRMFileTree` imported but unused
  --> app\modules\strm\file_tree_manager.py:12:29
   |
10 | from loguru import logger
11 |
12 | from app.models.strm import STRMFileTree, STRMLifeEvent
   |                             ^^^^^^^^^^^^
   |
help: Remove unused import

F401 [*] `app.models.strm.STRMLifeEvent` imported but unused
  --> app\modules\strm\file_tree_manager.py:12:43
   |
10 | from loguru import logger
11 |
12 | from app.models.strm import STRMFileTree, STRMLifeEvent
   |                                           ^^^^^^^^^^^^^
   |
help: Remove unused import

F821 Undefined name `media_info`
   --> app\modules\strm\generator.py:206:26
    |
204 |             elif media_type == 'music' or media_type == 'audio':
205 |                 # 音乐：使用Artist/Album结构
206 |                 artist = media_info.get('artist', 'Unknown Artist')
    |                          ^^^^^^^^^^
207 |                 album = media_info.get('album', 'Unknown Album')
208 |                 if album and album != 'Unknown Album':
    |

F821 Undefined name `media_info`
   --> app\modules\strm\generator.py:207:25
    |
205 |                 # 音乐：使用Artist/Album结构
206 |                 artist = media_info.get('artist', 'Unknown Artist')
207 |                 album = media_info.get('album', 'Unknown Album')
    |                         ^^^^^^^^^^
208 |                 if album and album != 'Unknown Album':
209 |                     return f"{artist}/{album}"
    |

F821 Undefined name `request`
   --> app\modules\strm\generator.py:232:95
    |
231 |         # 生成STRM文件URL（智能适配内外网）
232 |         strm_url = await self._generate_strm_url(cloud_file_id, cloud_storage, cloud_115_api, request)
    |                                                                                               ^^^^^^^
233 |         
234 |         # 生成STRM文件内容（包含元数据注释）
    |

F541 [*] f-string without any placeholders
   --> app\modules\strm\generator.py:359:24
    |
358 |         # 如果获取失败，回退到本地重定向模式
359 |         logger.warning(f"无法获取115网盘直接下载地址，回退到本地重定向模式")
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
360 |         return self._get_local_redirect_url(cloud_file_id, cloud_storage, None)
    |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
 --> app\modules\strm\scheduler_service.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | from typing import Optional, Dict, Any
8 | from datetime import datetime, timedelta
  |
help: Remove unused import: `asyncio`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\strm\scheduler_service.py:7:30
  |
6 | import asyncio
7 | from typing import Optional, Dict, Any
  |                              ^^^^
8 | from datetime import datetime, timedelta
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\strm\scheduler_service.py:7:36
  |
6 | import asyncio
7 | from typing import Optional, Dict, Any
  |                                    ^^^
8 | from datetime import datetime, timedelta
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\strm\scheduler_service.py:8:32
   |
 6 | import asyncio
 7 | from typing import Optional, Dict, Any
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from loguru import logger
10 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\strm\scrape_config.py:7:36
  |
6 | from pydantic import BaseModel, Field
7 | from typing import List, Optional, Dict, Any
  |                                    ^^^^
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\strm\scrape_config.py:7:42
  |
6 | from pydantic import BaseModel, Field
7 | from typing import List, Optional, Dict, Any
  |                                          ^^^
  |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
 --> app\modules\strm\service.py:6:30
  |
4 | """
5 |
6 | from typing import Optional, Dict, Any
  |                              ^^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\strm\service.py:6:36
  |
4 | """
5 |
6 | from typing import Optional, Dict, Any
  |                                    ^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select
  |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
  --> app\modules\strm\service.py:47:28
   |
45 |                     select(CloudStorage)
46 |                     .where(CloudStorage.provider == "115")
47 |                     .where(CloudStorage.enabled == True)
   |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
48 |                     .limit(1)
49 |                 )
   |
help: Replace with `CloudStorage.enabled`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
   --> app\modules\strm\service.py:122:28
    |
120 |                     select(CloudStorage)
121 |                     .where(CloudStorage.provider == "115")
122 |                     .where(CloudStorage.enabled == True)
    |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
123 |                     .limit(1)
124 |                 )
    |
help: Replace with `CloudStorage.enabled`

F401 [*] `app.models.strm.STRMLifeEvent` imported but unused
  --> app\modules\strm\sync_manager.py:20:43
   |
18 | from .config import STRMConfig
19 | from .lifecycle_tracker import LifecycleTracker
20 | from app.models.strm import STRMFileTree, STRMLifeEvent, STRMFile
   |                                           ^^^^^^^^^^^^^
   |
help: Remove unused import: `app.models.strm.STRMLifeEvent`

E712 Avoid equality comparisons to `False`; use `not STRMFileTree.is_dir:` for false checks
   --> app\modules\strm\sync_manager.py:210:24
    |
208 |                 select(STRMFileTree)
209 |                 .where(STRMFileTree.cloud_storage == self.cloud_storage)
210 |                 .where(STRMFileTree.is_dir == False)  # 只获取文件，不获取文件夹
    |                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
211 |             )
212 |             file_trees = result.scalars().all()
    |
help: Replace with `not STRMFileTree.is_dir`

F841 Local variable `strm_path` is assigned to but never used
   --> app\modules\strm\sync_manager.py:697:21
    |
696 |                 if strm_file:
697 |                     strm_path = strm_file.strm_path
    |                     ^^^^^^^^^
698 |                     
699 |                     # 删除本地STRM文件
    |
help: Remove assignment to unused variable `strm_path`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\subscription\defaults.py:5:32
  |
3 | """
4 |
5 | from typing import Dict, List, Optional
  |                                ^^^^^^^^
6 | from pydantic import BaseModel, Field
7 | from datetime import datetime
  |
help: Remove unused import: `typing.Optional`

F823 Local variable `select` referenced before assignment
  --> app\modules\subscription\refresh_engine.py:46:21
   |
44 |         try:
45 |             # 构建查询条件
46 |             query = select(Subscription).where(
   |                     ^^^^^^
47 |                 Subscription.status == "active",
48 |                 Subscription.auto_download == True
   |

E712 Avoid equality comparisons to `True`; use `Subscription.auto_download:` for truth checks
  --> app\modules\subscription\refresh_engine.py:48:17
   |
46 |             query = select(Subscription).where(
47 |                 Subscription.status == "active",
48 |                 Subscription.auto_download == True
   |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
49 |             )
   |
help: Replace with `Subscription.auto_download`

F401 [*] `app.models.intel_local.SiteGuardEvent` imported but unused
   --> app\modules\subscription\refresh_engine.py:123:74
    |
121 |                 if settings.INTEL_ENABLED and intel_enabled and intel_subscription_respect_site_guard:
122 |                     from app.core.intel_local.scheduler_hooks import before_pt_scan
123 |                     from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
    |                                                                          ^^^^^^^^^^^^^^^^^^^
124 |                     from sqlalchemy import select, func
    |
help: Remove unused import: `app.models.intel_local.SiteGuardEvent`

F401 [*] `sqlalchemy.select` imported but unused
   --> app\modules\subscription\refresh_engine.py:124:44
    |
122 |                     from app.core.intel_local.scheduler_hooks import before_pt_scan
123 |                     from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
124 |                     from sqlalchemy import select, func
    |                                            ^^^^^^
125 |                     
126 |                     # 检查每个订阅关联的站点是否被限流
    |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
   --> app\modules\subscription\refresh_engine.py:124:52
    |
122 |                     from app.core.intel_local.scheduler_hooks import before_pt_scan
123 |                     from app.models.intel_local import SiteGuardEvent as SiteGuardEventModel
124 |                     from sqlalchemy import select, func
    |                                                    ^^^^
125 |                     
126 |                     # 检查每个订阅关联的站点是否被限流
    |
help: Remove unused import

F841 Local variable `start_time` is assigned to but never used
   --> app\modules\subscription\refresh_engine.py:303:9
    |
301 |         monitor = SubscriptionRefreshMonitor(self.db)
302 |         refresh_history = None
303 |         start_time = time.time()
    |         ^^^^^^^^^^
304 |         
305 |         try:
    |
help: Remove assignment to unused variable `start_time`

F401 [*] `sqlalchemy.func` imported but unused
 --> app\modules\subscription\refresh_monitor.py:7:32
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_, desc, update
  |                                ^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
 --> app\modules\subscription\refresh_monitor.py:7:44
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_, desc, update
  |                                            ^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.update` imported but unused
 --> app\modules\subscription\refresh_monitor.py:7:55
  |
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, and_, or_, desc, update
  |                                                       ^^^^^^
8 | from typing import List, Optional, Dict, Any
9 | from datetime import datetime, timedelta
  |
help: Remove unused import

F401 [*] `sqlalchemy.update` imported but unused
  --> app\modules\subscription\service.py:10:40
   |
 9 | from loguru import logger
10 | from sqlalchemy import delete, select, update
   |                                        ^^^^^^
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `sqlalchemy.update`

F401 [*] `pathlib.Path` imported but unused
 --> app\modules\subtitle\matcher.py:7:21
  |
6 | from typing import List, Optional
7 | from pathlib import Path
  |                     ^^^^
8 | from loguru import logger
9 | import hashlib
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `sqlalchemy.delete` imported but unused
 --> app\modules\subtitle\service.py:6:32
  |
5 | from sqlalchemy.ext.asyncio import AsyncSession
6 | from sqlalchemy import select, delete
  |                                ^^^^^^
7 | from typing import List, Optional
8 | from pathlib import Path
  |
help: Remove unused import: `sqlalchemy.delete`

F401 [*] `shutil` imported but unused
  --> app\modules\subtitle\service.py:10:8
   |
 8 | from pathlib import Path
 9 | from loguru import logger
10 | import shutil
   |        ^^^^^^
11 | import asyncio
12 | from app.core.cache import get_cache
   |
help: Remove unused import: `shutil`

F401 [*] `asyncio` imported but unused
  --> app\modules\subtitle\service.py:11:8
   |
 9 | from loguru import logger
10 | import shutil
11 | import asyncio
   |        ^^^^^^^
12 | from app.core.cache import get_cache
   |
help: Remove unused import: `asyncio`

F401 [*] `.sources.SubHDClient` imported but unused
  --> app\modules\subtitle\service.py:17:43
   |
15 | from app.modules.settings.service import SettingsService
16 | from .matcher import SubtitleMatcher
17 | from .sources import OpenSubtitlesClient, SubHDClient, SubtitleInfo
   |                                           ^^^^^^^^^^^
18 | from .sources_shooter import ShooterClient
19 | from ..media_renamer.identifier import MediaIdentifier
   |
help: Remove unused import: `.sources.SubHDClient`

F401 [*] `..media_renamer.parser.MediaInfo` imported but unused
  --> app\modules\subtitle\service.py:20:36
   |
18 | from .sources_shooter import ShooterClient
19 | from ..media_renamer.identifier import MediaIdentifier
20 | from ..media_renamer.parser import MediaInfo
   |                                    ^^^^^^^^^
21 | from app.core.config import settings
   |
help: Remove unused import: `..media_renamer.parser.MediaInfo`

F401 [*] `typing.Dict` imported but unused
 --> app\modules\subtitle\sources.py:7:36
  |
6 | from abc import ABC, abstractmethod
7 | from typing import List, Optional, Dict, Any
  |                                    ^^^^
8 | from dataclasses import dataclass
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\modules\subtitle\sources.py:7:42
  |
6 | from abc import ABC, abstractmethod
7 | from typing import List, Optional, Dict, Any
  |                                          ^^^
8 | from dataclasses import dataclass
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `hashlib` imported but unused
  --> app\modules\subtitle\sources.py:11:8
   |
 9 | from loguru import logger
10 | import httpx
11 | import hashlib
   |        ^^^^^^^
12 | import os
   |
help: Remove unused import: `hashlib`

F401 [*] `os` imported but unused
  --> app\modules\subtitle\sources.py:12:8
   |
10 | import httpx
11 | import hashlib
12 | import os
   |        ^^
   |
help: Remove unused import: `os`

F401 [*] `subprocess` imported but unused
  --> app\modules\system\update_manager.py:8:8
   |
 6 | """
 7 |
 8 | import subprocess
   |        ^^^^^^^^^^
 9 | import asyncio
10 | import os
   |
help: Remove unused import: `subprocess`

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\system\update_manager.py:14:22
   |
12 | from typing import Optional, Dict, Any, List
13 | from enum import Enum
14 | from datetime import datetime
   |                      ^^^^^^^^
15 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\system\update_manager.py:17:29
   |
15 | from loguru import logger
16 |
17 | from app.core.config import settings
   |                             ^^^^^^^^
   |
help: Remove unused import: `app.core.config.settings`

F401 `typing.Union` imported but unused
 --> app\modules\thetvdb\__init__.py:7:37
  |
5 | """
6 | from threading import Lock
7 | from typing import Optional, Tuple, Union, List
  |                                     ^^^^^
8 | from loguru import logger
  |
help: Remove unused import: `typing.Union`

F401 [*] `loguru.logger` imported but unused
  --> app\modules\thetvdb\tvdb_v4_official.py:11:20
   |
 9 | from typing import Optional, Dict, Any, List, Union
10 | import httpx
11 | from loguru import logger
   |                    ^^^^^^
12 |
13 | from app.core.cache import get_cache
   |
help: Remove unused import: `loguru.logger`

F401 [*] `app.core.config.settings` imported but unused
  --> app\modules\thetvdb\tvdb_v4_official.py:14:29
   |
13 | from app.core.cache import get_cache
14 | from app.core.config import settings
   |                             ^^^^^^^^
   |
help: Remove unused import: `app.core.config.settings`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\modules\transfer_history\service.py:9:28
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, func, or_, delete
 9 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\tts\dummy.py:8:20
   |
 7 | from pathlib import Path
 8 | from typing import Optional
   |                    ^^^^^^^^
 9 | from loguru import logger
10 | import wave
   |
help: Remove unused import: `typing.Optional`

F401 [*] `.base.TTSEngine` imported but unused
  --> app\modules\tts\dummy.py:13:42
   |
11 | import struct
12 |
13 | from .base import TTSRequest, TTSResult, TTSEngine
   |                                          ^^^^^^^^^
14 | from .usage_tracker import record_success, record_error
   |
help: Remove unused import: `.base.TTSEngine`

F401 [*] `loguru.logger` imported but unused
  --> app\modules\tts\factory.py:8:20
   |
 7 | from typing import Optional, TYPE_CHECKING
 8 | from loguru import logger
   |                    ^^^^^^
 9 |
10 | from app.core.config import Settings
   |
help: Remove unused import: `loguru.logger`

F401 [*] `.http_provider.HttpTTSEngine` imported but unused
  --> app\modules\tts\factory.py:15:32
   |
14 | if TYPE_CHECKING:
15 |     from .http_provider import HttpTTSEngine
   |                                ^^^^^^^^^^^^^
   |
help: Remove unused import: `.http_provider.HttpTTSEngine`

F401 [*] `uuid` imported but unused
  --> app\modules\tts\http_provider.py:9:8
   |
 7 | import json
 8 | import base64
 9 | import uuid
   |        ^^^^
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any
   |
help: Remove unused import: `uuid`

F401 [*] `typing.Optional` imported but unused
  --> app\modules\tts\http_provider.py:11:20
   |
 9 | import uuid
10 | from pathlib import Path
11 | from typing import Optional, Dict, Any
   |                    ^^^^^^^^
12 | from loguru import logger
13 | import httpx
   |
help: Remove unused import: `typing.Optional`

F401 [*] `.base.TTSEngine` imported but unused
  --> app\modules\tts\http_provider.py:16:19
   |
15 | from app.core.config import Settings
16 | from .base import TTSEngine, TTSRequest, TTSResult
   |                   ^^^^^^^^^
17 | from .usage_tracker import record_success, record_error
   |
help: Remove unused import: `.base.TTSEngine`

F401 [*] `.usage_tracker.record_success` imported but unused
  --> app\modules\tts\http_provider.py:17:28
   |
15 | from app.core.config import Settings
16 | from .base import TTSEngine, TTSRequest, TTSResult
17 | from .usage_tracker import record_success, record_error
   |                            ^^^^^^^^^^^^^^
   |
help: Remove unused import: `.usage_tracker.record_success`

F401 [*] `app.modules.tts.rate_limiter.get_state` imported but unused
  --> app\modules\tts\job_service.py:22:55
   |
20 | from app.modules.novel.epub_builder import EpubBuilder
21 | from app.modules.ebook.importer import EBookImporter
22 | from app.modules.tts.rate_limiter import get_state as get_rate_limit_state
   |                                                       ^^^^^^^^^^^^^^^^^^^^
23 | from app.core.config import Settings
   |
help: Remove unused import: `app.modules.tts.rate_limiter.get_state`

F401 [*] `app.models.tts_voice_preset.TTSVoicePreset` imported but unused
  --> app\modules\tts\profile_service.py:15:41
   |
13 | from app.models.ebook import EBook
14 | from app.models.tts_work_profile import TTSWorkProfile
15 | from app.models.tts_voice_preset import TTSVoicePreset
   |                                         ^^^^^^^^^^^^^^
16 | from app.core.config import Settings
17 | from loguru import logger
   |
help: Remove unused import: `app.models.tts_voice_preset.TTSVoicePreset`

F401 [*] `datetime.timedelta` imported but unused
  --> app\modules\tts\storage_runner.py:8:32
   |
 6 | from dataclasses import dataclass
 7 | from typing import Optional
 8 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
 9 | from pathlib import Path
10 | from loguru import logger
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `app.modules.tts.storage_policy.TTSStorageCategoryPolicy` imported but unused
  --> app\modules\tts\storage_service.py:13:62
   |
11 | from loguru import logger
12 |
13 | from app.modules.tts.storage_policy import TTSStoragePolicy, TTSStorageCategoryPolicy
   |                                                              ^^^^^^^^^^^^^^^^^^^^^^^^
14 |
15 | TTSFileCategory = Literal["job", "playground", "other"]
   |
help: Remove unused import: `app.modules.tts.storage_policy.TTSStorageCategoryPolicy`

F401 [*] `typing.List` imported but unused
 --> app\modules\tts\user_batch_service.py:7:20
  |
5 | """
6 |
7 | from typing import List, Optional, Any
  |                    ^^^^
8 | from sqlalchemy.ext.asyncio import AsyncSession
9 | from sqlalchemy import select, func, or_, and_, desc
  |
help: Remove unused import: `typing.List`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\modules\tts\user_batch_service.py:9:32
   |
 7 | from typing import List, Optional, Any
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, func, or_, and_, desc
   |                                ^^^^
10 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

E712 Avoid equality comparisons to `False`; use `not AudiobookFile.is_deleted:` for false checks
  --> app\modules\tts\user_batch_service.py:82:16
   |
80 |         select(AudiobookFile.ebook_id, AudiobookFile.is_tts_generated)
81 |         .where(AudiobookFile.ebook_id.in_(ebook_ids))
82 |         .where(AudiobookFile.is_deleted == False)
   |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
83 |     )
84 |     all_audiobooks = all_audiobooks_result.all()
   |
help: Replace with `not AudiobookFile.is_deleted`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\tts\work_batch_service.py:7:26
  |
5 | """
6 |
7 | from typing import List, Optional
  |                          ^^^^^^^^
8 | from sqlalchemy.ext.asyncio import AsyncSession
9 | from sqlalchemy import select, and_, or_, func, case
  |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\modules\tts\work_batch_service.py:9:38
   |
 7 | from typing import List, Optional
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, and_, or_, func, case
   |                                      ^^^
10 | from sqlalchemy.orm import joinedload, aliased
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
  --> app\modules\tts\work_batch_service.py:9:43
   |
 7 | from typing import List, Optional
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, and_, or_, func, case
   |                                           ^^^^
10 | from sqlalchemy.orm import joinedload, aliased
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.case` imported but unused
  --> app\modules\tts\work_batch_service.py:9:49
   |
 7 | from typing import List, Optional
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, and_, or_, func, case
   |                                                 ^^^^
10 | from sqlalchemy.orm import joinedload, aliased
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.orm.joinedload` imported but unused
  --> app\modules\tts\work_batch_service.py:10:28
   |
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, and_, or_, func, case
10 | from sqlalchemy.orm import joinedload, aliased
   |                            ^^^^^^^^^^
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `sqlalchemy.orm.aliased` imported but unused
  --> app\modules\tts\work_batch_service.py:10:40
   |
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from sqlalchemy import select, and_, or_, func, case
10 | from sqlalchemy.orm import joinedload, aliased
   |                                        ^^^^^^^
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `datetime.datetime` imported but unused
  --> app\modules\tts\work_regen_service.py:10:22
   |
 8 | from typing import Optional, Literal
 9 | from loguru import logger
10 | from datetime import datetime
   |                      ^^^^^^^^
11 |
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `typing.Optional` imported but unused
 --> app\modules\upload\cleanup.py:7:20
  |
6 | from datetime import datetime, timedelta
7 | from typing import Optional
  |                    ^^^^^^^^
8 | from loguru import logger
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import: `typing.Optional`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\modules\upload\cleanup.py:9:36
   |
 7 | from typing import Optional
 8 | from loguru import logger
 9 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
10 | from sqlalchemy import select, delete, and_
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `time` imported but unused
 --> app\modules\upload\task_manager.py:7:8
  |
6 | import asyncio
7 | import time
  |        ^^^^
8 | from typing import Dict, Optional, Any, List, Callable
9 | from datetime import datetime
  |
help: Remove unused import: `time`

F401 [*] `typing.Callable` imported but unused
  --> app\modules\upload\task_manager.py:8:47
   |
 6 | import asyncio
 7 | import time
 8 | from typing import Dict, Optional, Any, List, Callable
   |                                               ^^^^^^^^
 9 | from datetime import datetime
10 | from uuid import UUID
   |
help: Remove unused import: `typing.Callable`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\modules\upload\task_manager.py:12:36
   |
10 | from uuid import UUID
11 | from loguru import logger
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
13 | from sqlalchemy import select, update, and_
14 | from sqlalchemy.orm import selectinload
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\modules\upload\task_manager.py:14:28
   |
12 | from sqlalchemy.ext.asyncio import AsyncSession
13 | from sqlalchemy import select, update, and_
14 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
15 |
16 | from app.core.database import get_db
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

F401 [*] `app.core.cloud_storage.providers.cloud_115_oss_resume.Cloud115OSSResume` imported but unused
  --> app\modules\upload\task_manager.py:20:67
   |
18 | from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
19 | from app.core.cloud_storage.providers.cloud_115_upload import Cloud115UploadManager
20 | from app.core.cloud_storage.providers.cloud_115_oss_resume import Cloud115OSSResume
   |                                                                   ^^^^^^^^^^^^^^^^^
21 | from app.modules.upload.verification import verify_upload_complete
   |
help: Remove unused import: `app.core.cloud_storage.providers.cloud_115_oss_resume.Cloud115OSSResume`

F401 [*] `os` imported but unused
   --> app\modules\upload\task_manager.py:111:16
    |
109 |             任务ID
110 |         """
111 |         import os
    |                ^^
112 |         from pathlib import Path
    |
help: Remove unused import: `os`

F821 Undefined name `current_speed`
   --> app\modules\upload\task_manager.py:590:35
    |
588 |                     uploaded_bytes=uploaded,
589 |                     total_bytes=total,
590 |                     current_speed=current_speed,
    |                                   ^^^^^^^^^^^^^
591 |                     updated_at=datetime.utcnow()
592 |                 )
    |

F821 Undefined name `task`
   --> app\modules\upload\task_manager.py:597:16
    |
595 |             # 记录进度历史（每5%记录一次，或每10秒记录一次）
596 |             should_record = False
597 |             if task.progress is None:
    |                ^^^^
598 |                 should_record = True
599 |             elif abs(progress - task.progress) >= 5.0:
    |

F821 Undefined name `task`
   --> app\modules\upload\task_manager.py:599:33
    |
597 |             if task.progress is None:
598 |                 should_record = True
599 |             elif abs(progress - task.progress) >= 5.0:
    |                                 ^^^^
600 |                 should_record = True
601 |             else:
    |

F821 Undefined name `current_speed`
   --> app\modules\upload\task_manager.py:618:35
    |
616 |                     total_bytes=total,
617 |                     progress=progress,
618 |                     current_speed=current_speed,
    |                                   ^^^^^^^^^^^^^
619 |                     elapsed_time=elapsed_time,
620 |                     estimated_remaining=estimated_remaining
    |

F821 Undefined name `elapsed_time`
   --> app\modules\upload\task_manager.py:619:34
    |
617 |                     progress=progress,
618 |                     current_speed=current_speed,
619 |                     elapsed_time=elapsed_time,
    |                                  ^^^^^^^^^^^^
620 |                     estimated_remaining=estimated_remaining
621 |                 )
    |

F821 Undefined name `estimated_remaining`
   --> app\modules\upload\task_manager.py:620:41
    |
618 |                     current_speed=current_speed,
619 |                     elapsed_time=elapsed_time,
620 |                     estimated_remaining=estimated_remaining
    |                                         ^^^^^^^^^^^^^^^^^^^
621 |                 )
622 |                 db.add(progress_record)
    |

F401 [*] `pathlib.Path` imported but unused
  --> app\modules\upload\verification.py:9:21
   |
 7 | import os
 8 | from typing import Dict, Optional, Any
 9 | from pathlib import Path
   |                     ^^^^
10 | from loguru import logger
   |
help: Remove unused import: `pathlib.Path`

F401 `oss2` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\modules\upload\verification.py:13:12
   |
12 | try:
13 |     import oss2
   |            ^^^^
14 |     OSS2_AVAILABLE = True
15 | except ImportError:
   |
help: Remove unused import: `oss2`

F401 [*] `app.schemas.notify_actions.NotificationActionType` imported but unused
  --> app\modules\user_notify_channels\base.py:13:60
   |
12 | from app.models.user_notify_channel import UserNotifyChannel
13 | from app.schemas.notify_actions import NotificationAction, NotificationActionType
   |                                                            ^^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.schemas.notify_actions.NotificationActionType`

F401 [*] `app.modules.user_notify_channels.base.ChannelCapabilities` imported but unused
  --> app\modules\user_notify_channels\factory.py:15:5
   |
13 | from app.modules.user_notify_channels.base import (
14 |     get_adapter_for_channel,
15 |     ChannelCapabilities,
   |     ^^^^^^^^^^^^^^^^^^^
16 | )
   |
help: Remove unused import: `app.modules.user_notify_channels.base.ChannelCapabilities`

F541 [*] f-string without any placeholders
   --> app\modules\user_notify_channels\factory.py:391:25
    |
389 |             resp = await client.post(bark_url, json=payload)
390 |             resp.raise_for_status()
391 |             logger.info(f"[user-notify] sent bark notification")
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
392 |             return True
393 |     except httpx.HTTPError as e:
    |
help: Remove extraneous `f` prefix

F401 [*] `typing.List` imported but unused
 --> app\modules\workflow\engine.py:4:26
  |
2 | 工作流引擎
3 | """
4 | from typing import Dict, List, Optional, Any
  |                          ^^^^
5 | from loguru import logger
6 | import asyncio
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\modules\workflow\engine.py:4:32
  |
2 | 工作流引擎
3 | """
4 | from typing import Dict, List, Optional, Any
  |                                ^^^^^^^^
5 | from loguru import logger
6 | import asyncio
  |
help: Remove unused import

F841 Local variable `magnet_link` is assigned to but never used
   --> app\modules\workflow\engine.py:172:9
    |
170 |         # TODO: 实现下载创建逻辑
171 |         title = config.get("title") or context.get("title", "")
172 |         magnet_link = config.get("magnet_link") or context.get("magnet_link", "")
    |         ^^^^^^^^^^^
173 |         downloader = config.get("downloader", "qBittorrent")
    |
help: Remove assignment to unused variable `magnet_link`

F841 Local variable `match_mode` is assigned to but never used
   --> app\modules\workflow\engine.py:315:13
    |
314 |             media_type = config.get("media_type", "movie")
315 |             match_mode = config.get("match_mode", "title_year")
    |             ^^^^^^^^^^
316 |             auto_download = config.get("auto_download", True)
317 |             quality_rules = config.get("quality_rules", {})
    |
help: Remove assignment to unused variable `match_mode`

F841 Local variable `match_mode` is assigned to but never used
   --> app\modules\workflow\engine.py:379:13
    |
377 |             from app.modules.music.service import MusicService
378 |             
379 |             match_mode = config.get("match_mode", "title_artist")
    |             ^^^^^^^^^^
380 |             auto_download = config.get("auto_download", False)
381 |             platform = config.get("platform", "all")
    |
help: Remove assignment to unused variable `match_mode`

F841 Local variable `media_type` is assigned to but never used
   --> app\modules\workflow\engine.py:545:9
    |
543 |         # 从上下文获取信息
544 |         title = context.get('title', '')
545 |         media_type = context.get('media_type', 'video')
    |         ^^^^^^^^^^
546 |         
547 |         logger.info(f"RSSHub工作流添加到队列: {title} (类型: {queue_type}, 标签: {tag})")
    |
help: Remove assignment to unused variable `media_type`

E712 Avoid equality comparisons to `True`; use `Workflow.is_active:` for truth checks
  --> app\modules\workflow\service.py:43:33
   |
42 |         if active_only:
43 |             query = query.where(Workflow.is_active == True)
   |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
44 |         
45 |         query = query.order_by(Workflow.created_at.desc())
   |
help: Replace with `Workflow.is_active`

F401 [*] `app.plugin_sdk.config_client.ConfigClient` imported but unused
  --> app\plugin_sdk\api.py:23:46
   |
21 |     from app.plugin_sdk.media import MediaClient
22 |     from app.plugin_sdk.cloud115 import Cloud115Client
23 |     from app.plugin_sdk.config_client import ConfigClient
   |                                              ^^^^^^^^^^^^
   |
help: Remove unused import: `app.plugin_sdk.config_client.ConfigClient`

F821 Undefined name `Any`
   --> app\plugin_sdk\api.py:223:63
    |
221 |             )
222 |     
223 |     def _audit(self, action: str, payload: Optional[dict[str, Any]] = None) -> None:
    |                                                               ^^^
224 |         """
225 |         记录审计日志（PLUGIN-SAFETY-1）
    |

F401 [*] `loguru.logger` imported but unused
  --> app\plugin_sdk\cloud115.py:11:20
   |
10 | from typing import Any, Optional, TYPE_CHECKING
11 | from loguru import logger
   |                    ^^^^^^
12 |
13 | from app.plugin_sdk.types import PluginCapability
   |
help: Remove unused import: `loguru.logger`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
  --> app\plugin_sdk\cloud115.py:65:21
   |
63 |                 stmt = select(CloudStorage).where(
64 |                     CloudStorage.provider == "115",
65 |                     CloudStorage.enabled == True
   |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
66 |                 ).limit(1)
67 |                 result = await session.execute(stmt)
   |
help: Replace with `CloudStorage.enabled`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
   --> app\plugin_sdk\cloud115.py:114:21
    |
112 |                 stmt = select(CloudStorage).where(
113 |                     CloudStorage.provider == "115",
114 |                     CloudStorage.enabled == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
115 |                 ).limit(1)
116 |                 result = await session.execute(stmt)
    |
help: Replace with `CloudStorage.enabled`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
   --> app\plugin_sdk\cloud115.py:178:21
    |
176 |                 stmt = select(CloudStorage).where(
177 |                     CloudStorage.provider == "115",
178 |                     CloudStorage.enabled == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
179 |                 ).limit(1)
180 |                 result = await session.execute(stmt)
    |
help: Replace with `CloudStorage.enabled`

E712 Avoid equality comparisons to `True`; use `CloudStorage.enabled:` for truth checks
   --> app\plugin_sdk\cloud115.py:232:21
    |
230 |                 stmt = select(CloudStorage).where(
231 |                     CloudStorage.provider == "115",
232 |                     CloudStorage.enabled == True
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
233 |                 ).limit(1)
234 |                 result = await session.execute(stmt)
    |
help: Replace with `CloudStorage.enabled`

F401 [*] `loguru.logger` imported but unused
  --> app\plugin_sdk\download.py:11:20
   |
10 | from typing import Any, Optional, TYPE_CHECKING
11 | from loguru import logger
   |                    ^^^^^^
12 |
13 | from app.plugin_sdk.types import PluginCapability
   |
help: Remove unused import: `loguru.logger`

F821 Undefined name `e`
   --> app\plugin_sdk\events.py:257:50
    |
255 | …                     {
256 | …                         "event": event.value,
257 | …                         "error": str(e),
    |                                        ^
258 | …                         "source": f"event_handler:{event.value}",
259 | …                         "payload": payload  # 原始 payload 参数（不含元数据）
    |

F401 [*] `loguru.logger` imported but unused
  --> app\plugin_sdk\http_client.py:9:20
   |
 7 | from typing import Any, Optional
 8 | import httpx
 9 | from loguru import logger
   |                    ^^^^^^
10 |
11 | from app.plugin_sdk.context import PluginContext
   |
help: Remove unused import: `loguru.logger`

F401 [*] `loguru.logger` imported but unused
  --> app\plugin_sdk\media.py:10:20
   |
 9 | from typing import Any, Optional, TYPE_CHECKING
10 | from loguru import logger
   |                    ^^^^^^
11 |
12 | from app.plugin_sdk.types import PluginCapability
   |
help: Remove unused import: `loguru.logger`

F401 [*] `sqlalchemy.or_` imported but unused
   --> app\plugin_sdk\media.py:197:44
    |
195 |             from app.core.database import get_session
196 |             from app.models.audiobook import Audiobook
197 |             from sqlalchemy import select, or_
    |                                            ^^^
198 |             
199 |             async for session in get_session():
    |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `sqlalchemy.or_` imported but unused
   --> app\plugin_sdk\media.py:241:44
    |
239 |             from app.core.database import get_session
240 |             from app.models.manga_series_local import MangaSeriesLocal
241 |             from sqlalchemy import select, or_
    |                                            ^^^
242 |             
243 |             async for session in get_session():
    |
help: Remove unused import: `sqlalchemy.or_`

E712 Avoid equality comparisons to `True`; use `User.is_active:` for truth checks
   --> app\plugin_sdk\notify.py:166:46
    |
164 |             async for session in get_session():
165 |                 # 获取所有活跃用户
166 |                 stmt = select(User.id).where(User.is_active == True)
    |                                              ^^^^^^^^^^^^^^^^^^^^^^
167 |                 result = await session.execute(stmt)
168 |                 user_ids = [row[0] for row in result.fetchall()]
    |
help: Replace with `User.is_active`

F401 [*] `typing.Protocol` imported but unused
  --> app\plugin_sdk\types.py:10:46
   |
 9 | from enum import Enum
10 | from typing import Any, TypedDict, Optional, Protocol
   |                                              ^^^^^^^^
11 | from datetime import datetime
   |
help: Remove unused import: `typing.Protocol`

F401 [*] `datetime.datetime` imported but unused
  --> app\plugin_sdk\types.py:11:22
   |
 9 | from enum import Enum
10 | from typing import Any, TypedDict, Optional, Protocol
11 | from datetime import datetime
   |                      ^^^^^^^^
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.models.music.MusicFile` imported but unused
   --> app\runners\demo_seed.py:184:41
    |
182 | async def seed_music(session):
183 |     """创建 Demo 音乐"""
184 |     from app.models.music import Music, MusicFile
    |                                         ^^^^^^^^^
185 |     from sqlalchemy import select
    |
help: Remove unused import: `app.models.music.MusicFile`

F401 [*] `typing.List` imported but unused
  --> app\runners\manga_download_worker.py:9:20
   |
 8 | import asyncio
 9 | from typing import List, Optional
   |                    ^^^^
10 | from datetime import datetime
   |
help: Remove unused import: `typing.List`

F401 [*] `datetime.datetime` imported but unused
  --> app\runners\manga_download_worker.py:10:22
   |
 8 | import asyncio
 9 | from typing import List, Optional
10 | from datetime import datetime
   |                      ^^^^^^^^
11 |
12 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.models.manga_source.MangaSource` imported but unused
  --> app\runners\manga_download_worker.py:24:37
   |
22 | from app.models.manga_series_local import MangaSeriesLocal
23 | from app.models.manga_chapter_local import MangaChapterLocal
24 | from app.models.manga_source import MangaSource
   |                                     ^^^^^^^^^^^
25 | from app.services.manga_download_job_service import MangaDownloadJobService
26 | from app.services.manga_import_service import (
   |
help: Remove unused import: `app.models.manga_source.MangaSource`

F401 [*] `app.services.manga_import_service.bulk_download_pending_chapters` imported but unused
  --> app\runners\manga_download_worker.py:29:5
   |
27 |     download_chapter,
28 |     import_series_from_remote,
29 |     bulk_download_pending_chapters,
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
30 | )
31 | from app.services.runner_heartbeat import runner_context
   |
help: Remove unused import: `app.services.manga_import_service.bulk_download_pending_chapters`

F401 [*] `datetime.datetime` imported but unused
  --> app\runners\manga_follow_sync.py:19:22
   |
17 | import asyncio
18 | from collections import defaultdict
19 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
20 | from typing import Dict, List, Optional
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\runners\manga_follow_sync.py:19:32
   |
17 | import asyncio
18 | from collections import defaultdict
19 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
20 | from typing import Dict, List, Optional
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\runners\manga_follow_sync.py:20:32
   |
18 | from collections import defaultdict
19 | from datetime import datetime, timedelta
20 | from typing import Dict, List, Optional
   |                                ^^^^^^^^
21 |
22 | from loguru import logger
   |
help: Remove unused import: `typing.Optional`

F401 [*] `typing.Optional` imported but unused
  --> app\runners\music_download_dispatcher.py:17:20
   |
15 | import sys
16 | from pathlib import Path
17 | from typing import Optional
   |                    ^^^^^^^^
18 | from datetime import datetime
   |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
  --> app\runners\music_download_dispatcher.py:18:22
   |
16 | from pathlib import Path
17 | from typing import Optional
18 | from datetime import datetime
   |                      ^^^^^^^^
19 |
20 | # 添加项目根目录到 Python 路径
   |
help: Remove unused import: `datetime.datetime`

F821 Undefined name `MusicDownloadJob`
   --> app\runners\music_download_dispatcher.py:128:11
    |
126 | async def _submit_to_downloader(
127 |     session,
128 |     job: "MusicDownloadJob",
    |           ^^^^^^^^^^^^^^^^
129 |     download_link: str,
130 |     client: str,
    |

F401 [*] `typing.Optional` imported but unused
  --> app\runners\music_download_status_sync.py:17:20
   |
15 | import sys
16 | from pathlib import Path
17 | from typing import Optional, List
   |                    ^^^^^^^^
18 | from datetime import datetime
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
  --> app\runners\music_download_status_sync.py:17:30
   |
15 | import sys
16 | from pathlib import Path
17 | from typing import Optional, List
   |                              ^^^^
18 | from datetime import datetime
   |
help: Remove unused import

F821 Undefined name `MusicDownloadJob`
  --> app\runners\music_download_status_sync.py:95:11
   |
93 | async def _sync_job_from_task(
94 |     session,
95 |     job: "MusicDownloadJob",
   |           ^^^^^^^^^^^^^^^^
96 |     task: "DownloadTask",
97 | ):
   |

F821 Undefined name `DownloadTask`
  --> app\runners\music_download_status_sync.py:96:12
   |
94 |     session,
95 |     job: "MusicDownloadJob",
96 |     task: "DownloadTask",
   |            ^^^^^^^^^^^^
97 | ):
98 |     """
   |

F821 Undefined name `MusicDownloadJob`
   --> app\runners\music_download_status_sync.py:148:11
    |
146 | async def _import_music_files(
147 |     session,
148 |     job: "MusicDownloadJob",
    |           ^^^^^^^^^^^^^^^^
149 |     task: "DownloadTask",
150 | ) -> dict:
    |

F821 Undefined name `DownloadTask`
   --> app\runners\music_download_status_sync.py:149:12
    |
147 |     session,
148 |     job: "MusicDownloadJob",
149 |     task: "DownloadTask",
    |            ^^^^^^^^^^^^
150 | ) -> dict:
151 |     """
    |

F401 [*] `datetime.datetime` imported but unused
  --> app\runners\music_import.py:17:22
   |
15 | from pathlib import Path
16 | from typing import Optional, Dict, Any, List
17 | from datetime import datetime
   |                      ^^^^^^^^
18 |
19 | # 添加项目根目录到 Python 路径
   |
help: Remove unused import: `datetime.datetime`

F401 `mutagen.mp3.MP3` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\runners\music_import.py:85:33
   |
83 |     try:
84 |         from mutagen import File as MutagenFile
85 |         from mutagen.mp3 import MP3
   |                                 ^^^
86 |         from mutagen.flac import FLAC
87 |         from mutagen.mp4 import MP4
   |
help: Remove unused import: `mutagen.mp3.MP3`

F401 `mutagen.flac.FLAC` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\runners\music_import.py:86:34
   |
84 |         from mutagen import File as MutagenFile
85 |         from mutagen.mp3 import MP3
86 |         from mutagen.flac import FLAC
   |                                  ^^^^
87 |         from mutagen.mp4 import MP4
   |
help: Remove unused import: `mutagen.flac.FLAC`

F401 `mutagen.mp4.MP4` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\runners\music_import.py:87:33
   |
85 |         from mutagen.mp3 import MP3
86 |         from mutagen.flac import FLAC
87 |         from mutagen.mp4 import MP4
   |                                 ^^^
88 |         
89 |         audio = MutagenFile(file_path)
   |
help: Remove unused import: `mutagen.mp4.MP4`

E722 Do not use bare `except`
   --> app\runners\music_import.py:154:21
    |
152 |                     try:
153 |                         metadata['year'] = int(str(tags['TDRC'])[:4])
154 |                     except:
    |                     ^^^^^^
155 |                         pass
156 |                 elif 'date' in tags:
    |

E722 Do not use bare `except`
   --> app\runners\music_import.py:159:21
    |
157 |                     try:
158 |                         metadata['year'] = int(str(tags['date'][0])[:4])
159 |                     except:
    |                     ^^^^^^
160 |                         pass
    |

E722 Do not use bare `except`
   --> app\runners\music_import.py:167:21
    |
165 |                         track_str = str(tags['TRCK'])
166 |                         metadata['track_number'] = int(track_str.split('/')[0])
167 |                     except:
    |                     ^^^^^^
168 |                         pass
169 |                 elif 'tracknumber' in tags:
    |

E722 Do not use bare `except`
   --> app\runners\music_import.py:173:21
    |
171 |                         track_str = str(tags['tracknumber'][0])
172 |                         metadata['track_number'] = int(track_str.split('/')[0])
173 |                     except:
    |                     ^^^^^^
174 |                         pass
    |

E722 Do not use bare `except`
   --> app\runners\music_import.py:181:21
    |
179 |                         disc_str = str(tags['TPOS'])
180 |                         metadata['disc_number'] = int(disc_str.split('/')[0])
181 |                     except:
    |                     ^^^^^^
182 |                         pass
183 |                 elif 'discnumber' in tags:
    |

E722 Do not use bare `except`
   --> app\runners\music_import.py:187:21
    |
185 |                         disc_str = str(tags['discnumber'][0])
186 |                         metadata['disc_number'] = int(disc_str.split('/')[0])
187 |                     except:
    |                     ^^^^^^
188 |                         pass
    |

F401 [*] `app.models.user_music_subscription.MusicSubscriptionType` imported but unused
  --> app\runners\music_subscription_checker.py:17:71
   |
15 | from sqlalchemy import select, and_, or_
16 |
17 | from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
   |                                                                       ^^^^^^^^^^^^^^^^^^^^^
18 | from app.services.music_subscription_service import run_subscription_once
19 | from app.core.config import settings
   |
help: Remove unused import: `app.models.user_music_subscription.MusicSubscriptionType`

F401 [*] `app.services.music_subscription_service.run_subscription_once` imported but unused
  --> app\runners\music_subscription_checker.py:18:53
   |
17 | from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
18 | from app.services.music_subscription_service import run_subscription_once
   |                                                     ^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.config import settings
20 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `app.services.music_subscription_service.run_subscription_once`

F401 [*] `app.core.config.settings` imported but unused
  --> app\runners\music_subscription_checker.py:19:29
   |
17 | from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
18 | from app.services.music_subscription_service import run_subscription_once
19 | from app.core.config import settings
   |                             ^^^^^^^^
20 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `app.core.config.settings`

F821 Undefined name `run_music_subscription_once`
   --> app\runners\music_subscription_checker.py:102:32
    |
101 |             # 调用音乐订阅服务
102 |             run_result = await run_music_subscription_once(
    |                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^
103 |                 db,
104 |                 subscription,
    |

F841 Local variable `result` is assigned to but never used
   --> app\runners\music_subscription_checker.py:206:13
    |
204 |             start_time = datetime.utcnow()
205 |             
206 |             result = await run_once(
    |             ^^^^^^
207 |                 max_subscriptions=max_subscriptions,
208 |                 cooldown_minutes=cooldown_minutes,
    |
help: Remove assignment to unused variable `result`

F541 [*] f-string without any placeholders
   --> app\runners\music_subscription_checker.py:287:19
    |
285 |             ))
286 |             
287 |             print(f"\n✅ 音乐订阅检查完成:")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^
288 |             print(f"   总计订阅: {result.total_subscriptions}")
289 |             print(f"   已检查: {result.checked_subscriptions}")
    |
help: Remove extraneous `f` prefix

F841 Local variable `checks` is assigned to but never used
  --> app\runners\ops_health_check.py:26:9
   |
25 |     async with async_session_factory() as session:
26 |         checks = await run_all_health_checks(session)
   |         ^^^^^^
27 |         summary = await get_health_summary(session)
   |
help: Remove assignment to unused variable `checks`

F401 [*] `sys` imported but unused
  --> app\runners\qa_self_check.py:16:8
   |
14 | import asyncio
15 | import json
16 | import sys
   |        ^^^
17 | from datetime import datetime
   |
help: Remove unused import: `sys`

F401 [*] `datetime.datetime` imported but unused
  --> app\runners\qa_self_check.py:17:22
   |
15 | import json
16 | import sys
17 | from datetime import datetime
   |                      ^^^^^^^^
18 |
19 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.config.settings` imported but unused
  --> app\runners\subscription_checker.py:19:29
   |
17 | from app.models.subscription import Subscription
18 | from app.modules.subscription.service import SubscriptionService as ExistingSubscriptionService
19 | from app.core.config import settings
   |                             ^^^^^^^^
20 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `app.core.config.settings`

F541 [*] f-string without any placeholders
   --> app\runners\subscription_checker.py:232:15
    |
231 |         # 输出详细结果
232 |         print(f"\n=== 订阅检查结果 ===")
    |               ^^^^^^^^^^^^^^^^^^^^^^^^^
233 |         print(f"订阅ID: {subscription_id}")
234 |         print(f"标题: {subscription.title}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> app\runners\telegram_bot_polling.py:86:17
   |
84 | async def main(timeout: int = 30):
85 |     """主入口"""
86 |     logger.info(f"[telegram-bot] Runner starting...")
   |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
87 |     
88 |     async with runner_context(RUNNER_NAME, runner_type="bot"):
   |
help: Remove extraneous `f` prefix

F401 [*] `typing.Any` imported but unused
 --> app\schemas\common.py:5:54
  |
3 | """
4 |
5 | from typing import Generic, TypeVar, List, Optional, Any
  |                                                      ^^^
6 | from pydantic import BaseModel, Field
  |
help: Remove unused import: `typing.Any`

F401 [*] `typing.Literal` imported but unused
 --> app\schemas\home_dashboard.py:6:36
  |
4 | """
5 | from datetime import datetime
6 | from typing import Optional, List, Literal
  |                                    ^^^^^^^
7 | from pydantic import BaseModel
  |
help: Remove unused import: `typing.Literal`

F401 [*] `pydantic.HttpUrl` imported but unused
 --> app\schemas\manga_local.py:6:33
  |
4 | from datetime import datetime
5 | from typing import Any, List, Optional
6 | from pydantic import BaseModel, HttpUrl
  |                                 ^^^^^^^
7 |
8 | from app.models.manga_chapter_local import MangaChapterStatus
  |
help: Remove unused import: `pydantic.HttpUrl`

F401 [*] `typing.Dict` imported but unused
 --> app\schemas\manga_remote.py:5:36
  |
3 | """
4 | from datetime import datetime
5 | from typing import List, Optional, Dict
  |                                    ^^^^
6 |
7 | from pydantic import AnyHttpUrl, BaseModel
  |
help: Remove unused import: `typing.Dict`

F401 [*] `enum.Enum` imported but unused
 --> app\schemas\music.py:7:18
  |
5 | from typing import Optional, List, Dict, Any
6 | from datetime import datetime
7 | from enum import Enum
  |                  ^^^^
8 |
9 | class MusicArtistRead(BaseModel):
  |
help: Remove unused import: `enum.Enum`

F401 [*] `typing.List` imported but unused
 --> app\schemas\reading_hub.py:5:50
  |
3 | """
4 | from datetime import datetime
5 | from typing import Optional, Dict, Any, Literal, List
  |                                                  ^^^^
6 | from pydantic import BaseModel
  |
help: Remove unused import: `typing.List`

F401 [*] `enum.Enum` imported but unused
 --> app\schemas\reading_status.py:9:18
  |
8 | from typing import Literal, Optional
9 | from enum import Enum
  |                  ^^^^
  |
help: Remove unused import: `enum.Enum`

F401 [*] `pydantic.HttpUrl` imported but unused
 --> app\schemas\remote_115.py:5:33
  |
3 | """
4 | from typing import List, Optional
5 | from pydantic import BaseModel, HttpUrl, Field
  |                                 ^^^^^^^
  |
help: Remove unused import: `pydantic.HttpUrl`

F401 [*] `typing.Optional` imported but unused
 --> app\schemas\user_favorite_media.py:6:20
  |
5 | from datetime import datetime
6 | from typing import Optional
  |                    ^^^^^^^^
7 |
8 | from pydantic import BaseModel
  |
help: Remove unused import: `typing.Optional`

F401 [*] `app.schemas.ai_log_doctor.DiagnosisSeverity` imported but unused
  --> app\services\ai_log_doctor.py:18:5
   |
16 |     DiagnosisTimeWindow,
17 |     DiagnosisFocus,
18 |     DiagnosisSeverity,
   |     ^^^^^^^^^^^^^^^^^
19 |     DiagnosisItem,
20 |     DiagnosisPlanStep,
   |
help: Remove unused import

F401 [*] `app.schemas.ai_log_doctor.DiagnosisItem` imported but unused
  --> app\services\ai_log_doctor.py:19:5
   |
17 |     DiagnosisFocus,
18 |     DiagnosisSeverity,
19 |     DiagnosisItem,
   |     ^^^^^^^^^^^^^
20 |     DiagnosisPlanStep,
21 | )
   |
help: Remove unused import

F401 [*] `app.schemas.ai_log_doctor.DiagnosisPlanStep` imported but unused
  --> app\services\ai_log_doctor.py:20:5
   |
18 |     DiagnosisSeverity,
19 |     DiagnosisItem,
20 |     DiagnosisPlanStep,
   |     ^^^^^^^^^^^^^^^^^
21 | )
22 | from app.core.ai_orchestrator.service import AIOrchestratorService, OrchestratorMode
   |
help: Remove unused import

F401 [*] `app.core.ai_orchestrator.service.OrchestratorResult` imported but unused
  --> app\services\ai_subs_workflow.py:17:5
   |
15 |     AIOrchestratorService,
16 |     OrchestratorMode,
17 |     OrchestratorResult,
   |     ^^^^^^^^^^^^^^^^^^
18 | )
19 | from app.core.ai_orchestrator.tools.base import OrchestratorContext
   |
help: Remove unused import: `app.core.ai_orchestrator.service.OrchestratorResult`

F401 [*] `app.models.rsshub.UserRSSHubSubscription` imported but unused
  --> app\services\ai_subs_workflow.py:21:45
   |
19 | from app.core.ai_orchestrator.tools.base import OrchestratorContext
20 | from app.core.ai_orchestrator.factory import get_llm_client
21 | from app.models.rsshub import RSSHubSource, UserRSSHubSubscription
   |                                             ^^^^^^^^^^^^^^^^^^^^^^
22 | from app.models.site import Site
23 | from app.modules.subscription.service import SubscriptionService
   |
help: Remove unused import: `app.models.rsshub.UserRSSHubSubscription`

F401 [*] `app.models.enums.alert_channel_type.AlertChannelType` imported but unused
  --> app\services\alert_channel_service.py:13:49
   |
12 | from app.models.alert_channel import AlertChannel
13 | from app.models.enums.alert_channel_type import AlertChannelType
   |                                                 ^^^^^^^^^^^^^^^^
14 | from app.models.enums.alert_severity import AlertSeverity
15 | from app.schemas.alert_channel import AlertChannelCreate, AlertChannelUpdate
   |
help: Remove unused import: `app.models.enums.alert_channel_type.AlertChannelType`

F401 [*] `datetime.datetime` imported but unused
 --> app\services\download_search_service.py:7:22
  |
6 | import re
7 | from datetime import datetime
  |                      ^^^^^^^^
8 | from typing import List, Dict, Any, Optional, Tuple
9 | from pydantic import BaseModel
  |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.core.intel_local.repo.HRCasesRepository` imported but unused
  --> app\services\download_search_service.py:14:39
   |
12 | from app.modules.search.indexer_manager import IndexerManager
13 | from app.core.intel_local.hr_policy import evaluate_hr_for_site
14 | from app.core.intel_local.repo import HRCasesRepository
   |                                       ^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.core.intel_local.repo.HRCasesRepository`

F401 [*] `typing.Any` imported but unused
  --> app\services\global_search_service.py:9:46
   |
 7 | """
 8 | import logging
 9 | from typing import List, Protocol, Iterable, Any, Optional
   |                                              ^^^
10 |
11 | from sqlalchemy import select, or_
   |
help: Remove unused import: `typing.Any`

F401 [*] `typing.Any` imported but unused
 --> app\services\health_checks.py:7:20
  |
6 | import time
7 | from typing import Any, Optional
  |                    ^^^
8 | from sqlalchemy import text
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
 --> app\services\health_checks.py:7:25
  |
6 | import time
7 | from typing import Any, Optional
  |                         ^^^^^^^^
8 | from sqlalchemy import text
9 | from sqlalchemy.ext.asyncio import AsyncSession
  |
help: Remove unused import

F401 [*] `sqlalchemy.select` imported but unused
   --> app\services\health_checks.py:114:32
    |
112 |     try:
113 |         # 检查是否有配置的外部索引器
114 |         from sqlalchemy import select, func
    |                                ^^^^^^
115 |         
116 |         # 尝试查询 ext_indexer 表（如果存在）
    |
help: Remove unused import

F401 [*] `sqlalchemy.func` imported but unused
   --> app\services\health_checks.py:114:40
    |
112 |     try:
113 |         # 检查是否有配置的外部索引器
114 |         from sqlalchemy import select, func
    |                                        ^^^^
115 |         
116 |         # 尝试查询 ext_indexer 表（如果存在）
    |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\services\home_dashboard_service.py:9:26
   |
 7 | import logging
 8 | from datetime import datetime, timedelta
 9 | from typing import List, Optional
   |                          ^^^^^^^^
10 |
11 | from sqlalchemy import select, func, desc, and_, or_
   |
help: Remove unused import: `typing.Optional`

F401 [*] `app.models.music.MusicFile` imported but unused
  --> app\services\home_dashboard_service.py:16:37
   |
14 | from app.models.user import User
15 | from app.models.ebook import EBook
16 | from app.models.music import Music, MusicFile
   |                                     ^^^^^^^^^
17 | from app.models.manga_series_local import MangaSeriesLocal
18 | from app.models.tts_job import TTSJob
   |
help: Remove unused import: `app.models.music.MusicFile`

F401 [*] `app.models.manga_chapter_local.MangaChapterLocal` imported but unused
  --> app\services\manga_download_job_service.py:16:44
   |
14 | )
15 | from app.models.manga_series_local import MangaSeriesLocal
16 | from app.models.manga_chapter_local import MangaChapterLocal
   |                                            ^^^^^^^^^^^^^^^^^
17 | from app.models.manga_source import MangaSource
   |
help: Remove unused import: `app.models.manga_chapter_local.MangaChapterLocal`

F401 [*] `app.modules.manga_sources.factory.get_manga_source_adapter` imported but unused
  --> app\services\manga_follow_service.py:24:47
   |
22 | )
23 | from app.services.manga_remote_service import get_series_detail
24 | from app.modules.manga_sources.factory import get_manga_source_adapter
   |                                               ^^^^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.modules.manga_sources.factory.get_manga_source_adapter`

F401 [*] `os` imported but unused
 --> app\services\manga_import_service.py:7:8
  |
5 | 下载章节图片并保存为本地文件
6 | """
7 | import os
  |        ^^
8 | import json
9 | import re
  |
help: Remove unused import: `os`

F401 [*] `json` imported but unused
  --> app\services\manga_import_service.py:8:8
   |
 6 | """
 7 | import os
 8 | import json
   |        ^^^^
 9 | import re
10 | from pathlib import Path
   |
help: Remove unused import: `json`

F401 [*] `sqlalchemy.func` imported but unused
 --> app\services\manga_progress_service.py:7:32
  |
5 | from datetime import datetime
6 | from sqlalchemy.ext.asyncio import AsyncSession
7 | from sqlalchemy import select, func, desc
  |                                ^^^^
8 | from loguru import logger
  |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `loguru.logger` imported but unused
  --> app\services\manga_progress_service.py:8:20
   |
 6 | from sqlalchemy.ext.asyncio import AsyncSession
 7 | from sqlalchemy import select, func, desc
 8 | from loguru import logger
   |                    ^^^^^^
 9 |
10 | from app.models.manga_reading_progress import MangaReadingProgress
   |
help: Remove unused import: `loguru.logger`

F401 [*] `typing.List` imported but unused
 --> app\services\manga_sync_service.py:7:20
  |
5 | """
6 | from datetime import datetime
7 | from typing import List
  |                    ^^^^
8 | from sqlalchemy.ext.asyncio import AsyncSession
9 | from sqlalchemy import select
  |
help: Remove unused import: `typing.List`

F401 [*] `app.models.enums.notification_type.NotificationType` imported but unused
  --> app\services\manga_sync_service.py:15:48
   |
13 | from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
14 | from app.models.manga_source import MangaSource
15 | from app.models.enums.notification_type import NotificationType
   |                                                ^^^^^^^^^^^^^^^^
16 | from app.models.enums.reading_media_type import ReadingMediaType
17 | from app.services.manga_remote_service import list_chapters
   |
help: Remove unused import: `app.models.enums.notification_type.NotificationType`

F401 [*] `app.models.enums.reading_media_type.ReadingMediaType` imported but unused
  --> app\services\manga_sync_service.py:16:49
   |
14 | from app.models.manga_source import MangaSource
15 | from app.models.enums.notification_type import NotificationType
16 | from app.models.enums.reading_media_type import ReadingMediaType
   |                                                 ^^^^^^^^^^^^^^^^
17 | from app.services.manga_remote_service import list_chapters
18 | from app.services.manga_import_service import download_chapter
   |
help: Remove unused import: `app.models.enums.reading_media_type.ReadingMediaType`

F401 [*] `app.services.notification_service.create_notifications_for_users` imported but unused
  --> app\services\manga_sync_service.py:19:47
   |
17 | from app.services.manga_remote_service import list_chapters
18 | from app.services.manga_import_service import download_chapter
19 | from app.services.notification_service import create_notifications_for_users, get_user_ids_for_manga_series, notify_manga_updated, not…
   |                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.schemas.manga_remote import RemoteMangaChapter
   |
help: Remove unused import: `app.services.notification_service.create_notifications_for_users`

F401 [*] `app.schemas.manga_remote.RemoteMangaChapter` imported but unused
  --> app\services\manga_sync_service.py:20:38
   |
18 | from app.services.manga_import_service import download_chapter
19 | from app.services.notification_service import create_notifications_for_users, get_user_ids_for_manga_series, notify_manga_updated, not…
20 | from app.schemas.manga_remote import RemoteMangaChapter
   |                                      ^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.schemas.manga_remote.RemoteMangaChapter`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\services\music_chart_service.py:12:32
   |
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, func, and_
   |                                ^^^^
13 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `app.modules.music_charts.base.MusicChartItemPayload` imported but unused
  --> app\services\music_chart_service.py:19:43
   |
17 | from app.models.music_chart_item import MusicChartItem
18 | from app.modules.music_charts.factory import get_chart_fetcher
19 | from app.modules.music_charts.base import MusicChartItemPayload
   |                                           ^^^^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `app.modules.music_charts.base.MusicChartItemPayload`

E712 Avoid equality comparisons to `True`; use `MusicChart.is_enabled:` for truth checks
   --> app\services\music_chart_service.py:162:38
    |
160 |     """
161 |     # 构建查询
162 |     query = select(MusicChart).where(MusicChart.is_enabled == True)
    |                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
163 |     
164 |     if source_id:
    |
help: Replace with `MusicChart.is_enabled`

E711 Comparison to `None` should be `cond is None`
   --> app\services\music_chart_service.py:171:44
    |
169 | …     now = datetime.utcnow()
170 | …     query = query.where(
171 | …         (MusicChart.last_fetched_at == None) |
    |                                          ^^^^
172 | …         (MusicChart.last_fetched_at < now - timedelta(minutes=1))  # 临时使用 1 分钟，实际应该用 fetch_interval_minutes
173 | …     )
    |
help: Replace with `cond is None`

F401 [*] `typing.Dict` imported but unused
  --> app\services\music_import_service.py:17:30
   |
16 | import os
17 | from typing import Optional, Dict, Any, List
   |                              ^^^^
18 | from dataclasses import dataclass
19 | from datetime import datetime
   |
help: Remove unused import: `typing.Dict`

F401 [*] `datetime.datetime` imported but unused
  --> app\services\music_import_service.py:19:22
   |
17 | from typing import Optional, Dict, Any, List
18 | from dataclasses import dataclass
19 | from datetime import datetime
   |                      ^^^^^^^^
20 | from pathlib import Path
   |
help: Remove unused import: `datetime.datetime`

F401 `mutagen.easyid3.EasyID3` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:87:37
   |
85 |     try:
86 |         import mutagen
87 |         from mutagen.easyid3 import EasyID3
   |                                     ^^^^^^^
88 |         from mutagen.flac import FLAC
89 |         from mutagen.mp3 import MP3
   |
help: Remove unused import: `mutagen.easyid3.EasyID3`

F401 `mutagen.flac.FLAC` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:88:34
   |
86 |         import mutagen
87 |         from mutagen.easyid3 import EasyID3
88 |         from mutagen.flac import FLAC
   |                                  ^^^^
89 |         from mutagen.mp3 import MP3
90 |         from mutagen.mp4 import MP4
   |
help: Remove unused import: `mutagen.flac.FLAC`

F401 `mutagen.mp3.MP3` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:89:33
   |
87 |         from mutagen.easyid3 import EasyID3
88 |         from mutagen.flac import FLAC
89 |         from mutagen.mp3 import MP3
   |                                 ^^^
90 |         from mutagen.mp4 import MP4
91 |         from mutagen.oggvorbis import OggVorbis
   |
help: Remove unused import: `mutagen.mp3.MP3`

F401 `mutagen.mp4.MP4` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:90:33
   |
88 |         from mutagen.flac import FLAC
89 |         from mutagen.mp3 import MP3
90 |         from mutagen.mp4 import MP4
   |                                 ^^^
91 |         from mutagen.oggvorbis import OggVorbis
92 |         from mutagen.apev2 import APEv2
   |
help: Remove unused import: `mutagen.mp4.MP4`

F401 `mutagen.oggvorbis.OggVorbis` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:91:39
   |
89 |         from mutagen.mp3 import MP3
90 |         from mutagen.mp4 import MP4
91 |         from mutagen.oggvorbis import OggVorbis
   |                                       ^^^^^^^^^
92 |         from mutagen.apev2 import APEv2
93 |     except ImportError:
   |
help: Remove unused import: `mutagen.oggvorbis.OggVorbis`

F401 `mutagen.apev2.APEv2` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> app\services\music_import_service.py:92:35
   |
90 |         from mutagen.mp4 import MP4
91 |         from mutagen.oggvorbis import OggVorbis
92 |         from mutagen.apev2 import APEv2
   |                                   ^^^^^
93 |     except ImportError:
94 |         logger.warning("mutagen 库未安装，无法解析音频元数据")
   |
help: Remove unused import: `mutagen.apev2.APEv2`

E722 Do not use bare `except`
   --> app\services\music_import_service.py:205:9
    |
203 |                     return str(value[0]) if value else None
204 |                 return str(value)
205 |         except:
    |         ^^^^^^
206 |             pass
207 |     return None
    |

E712 Avoid equality comparisons to `True`; use `MusicFile.is_preferred:` for truth checks
   --> app\services\music_import_service.py:357:21
    |
355 |                 and_(
356 |                     MusicFile.music_id == existing_music.id,
357 |                     MusicFile.is_preferred == True,
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
358 |                 )
359 |             )
    |
help: Replace with `MusicFile.is_preferred`

F401 [*] `dataclasses.dataclass` imported but unused
  --> app\services\music_indexer_service.py:15:25
   |
14 | from typing import List, Optional, Dict, Any
15 | from dataclasses import dataclass
   |                         ^^^^^^^^^
16 | from datetime import datetime
   |
help: Remove unused import: `dataclasses.dataclass`

F401 [*] `datetime.datetime` imported but unused
  --> app\services\music_indexer_service.py:16:22
   |
14 | from typing import List, Optional, Dict, Any
15 | from dataclasses import dataclass
16 | from datetime import datetime
   |                      ^^^^^^^^
17 |
18 | from loguru import logger
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\services\music_subscription_service.py:13:32
   |
12 | from sqlalchemy.ext.asyncio import AsyncSession
13 | from sqlalchemy import select, func, and_
   |                                ^^^^
14 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `app.schemas.music.UserMusicSubscriptionCreate` imported but unused
  --> app\services\music_subscription_service.py:21:54
   |
19 | from app.models.music_download_job import MusicDownloadJob, MusicDownloadJobSource
20 | from app.models.user import User
21 | from app.schemas.music import SubscriptionRunResult, UserMusicSubscriptionCreate, MusicAutoLoopResult
   |                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from app.services.music_indexer_service import get_music_indexer_service, MusicTorrentCandidate
   |
help: Remove unused import: `app.schemas.music.UserMusicSubscriptionCreate`

F821 Undefined name `MusicChart`
  --> app\services\music_subscription_service.py:96:16
   |
94 |     # 获取榜单
95 |     chart_result = await session.execute(
96 |         select(MusicChart).where(MusicChart.id == subscription.chart_id)
   |                ^^^^^^^^^^
97 |     )
98 |     chart = chart_result.scalar_one_or_none()
   |

F821 Undefined name `MusicChart`
  --> app\services\music_subscription_service.py:96:34
   |
94 |     # 获取榜单
95 |     chart_result = await session.execute(
96 |         select(MusicChart).where(MusicChart.id == subscription.chart_id)
   |                                  ^^^^^^^^^^
97 |     )
98 |     chart = chart_result.scalar_one_or_none()
   |

E711 Comparison to `None` should be `cond is not None`
   --> app\services\music_subscription_service.py:109:51
    |
107 |             and_(
108 |                 MusicDownloadJob.subscription_id == subscription.id,
109 |                 MusicDownloadJob.chart_item_id != None
    |                                                   ^^^^
110 |             )
111 |         )
    |
help: Replace with `cond is not None`

F811 Redefinition of unused `check_keyword_subscription` from line 387
   --> app\services\music_subscription_service.py:666:11
    |
666 | async def check_keyword_subscription(
    |           ^^^^^^^^^^^^^^^^^^^^^^^^^^ `check_keyword_subscription` redefined here
667 |     session: AsyncSession,
668 |     subscription: UserMusicSubscription,
    |
   ::: app\services\music_subscription_service.py:387:11
    |
387 | async def check_keyword_subscription(
    |           -------------------------- previous definition of `check_keyword_subscription` here
388 |     session: AsyncSession,
389 |     subscription: UserMusicSubscription,
    |
help: Remove definition: `check_keyword_subscription`

F841 Local variable `filtered_candidates` is assigned to but never used
   --> app\services\music_subscription_service.py:745:13
    |
743 |         if subscription.music_quality or subscription.quality_preference:
744 |             quality_pref = subscription.music_quality or subscription.quality_preference
745 |             filtered_candidates = _filter_by_quality_preference(candidates, quality_pref)
    |             ^^^^^^^^^^^^^^^^^^^
746 |         
747 |         # 应用安全策略过滤（HR/H3H5/Free）
    |
help: Remove assignment to unused variable `filtered_candidates`

F401 [*] `sqlalchemy.orm.selectinload` imported but unused
  --> app\services\notification_service.py:9:28
   |
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, update, func
 9 | from sqlalchemy.orm import selectinload
   |                            ^^^^^^^^^^^^
10 |
11 | from app.models.user_notification import UserNotification
   |
help: Remove unused import: `sqlalchemy.orm.selectinload`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
  --> app\services\notification_service.py:72:17
   |
70 |             .where(
71 |                 UserNotification.user_id == user_id,
72 |                 UserNotification.is_read == False
   |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
73 |             )
74 |         )
   |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\services\notification_service.py:125:17
    |
123 |                 UserNotification.id == notification_id,
124 |                 UserNotification.user_id == user_id,
125 |                 UserNotification.is_read == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
126 |             )
127 |             .values(is_read=True, read_at=datetime.utcnow())
    |
help: Replace with `not UserNotification.is_read`

E712 Avoid equality comparisons to `False`; use `not UserNotification.is_read:` for false checks
   --> app\services\notification_service.py:156:17
    |
154 |             .where(
155 |                 UserNotification.user_id == user_id,
156 |                 UserNotification.is_read == False
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
157 |             )
158 |             .values(is_read=True, read_at=datetime.utcnow())
    |
help: Replace with `not UserNotification.is_read`

F541 [*] f-string without any placeholders
   --> app\services\notification_service.py:308:15
    |
306 |     """
307 |     title = f"《{series_title}》更新了 {new_chapters} 话"
308 |     message = f"漫画系列有新章节更新，快去看看吧！"
    |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
309 |     
310 |     payload = {
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\services\notification_service.py:604:15
    |
602 |     """
603 |     title = f"《{payload['title']}》更新了 {payload['total_new_count']} 话"
604 |     message = f"你追更的漫画有新章节更新，快去看看吧！"
    |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
605 |     
606 |     notification_data = UserNotificationCreate(
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\services\notification_service.py:889:19
    |
887 |     # 根据风险等级构建不同的消息
888 |     if risk_level == 'H&R':
889 |         message = f"站点标记为 H&R，请避免删除原始数据并保持做种"
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
890 |     elif risk_level == 'HR':
891 |         message = f"需要保种 {payload.get('min_seed_time_hours', 72)} 小时，请勿删除原始数据"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\services\notification_service.py:895:19
    |
893 |         message = f"站点特殊要求（{risk_level}），请查看具体保种规则"
894 |     else:
895 |         message = f"下载任务存在保种要求，请注意及时处理"
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
896 |     
897 |     if payload.get('reason'):
    |
help: Remove extraneous `f` prefix

F401 [*] `datetime.datetime` imported but unused
  --> app\services\notify_music.py:8:22
   |
 7 | from typing import List, Optional
 8 | from datetime import datetime
   |                      ^^^^^^^^
 9 |
10 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `datetime.datetime`

F541 [*] f-string without any placeholders
  --> app\services\notify_music.py:89:19
   |
87 |             media_type="music",
88 |             target_id=chart_id,
89 |             title=f"新音乐任务已排队",
   |                   ^^^^^^^^^^^^^^^^^^^
90 |             message=f"来自 {chart_name} 的 {track_count} 首曲目已加入搜索队列",
91 |             payload={
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> app\services\notify_music.py:138:19
    |
136 |             media_type="music",
137 |             target_id=chart_id,
138 |             title=f"新音乐已就绪",
    |                   ^^^^^^^^^^^^^^^
139 |             message=f"{tracks_preview} 已下载完成",
140 |             payload={
    |
help: Remove extraneous `f` prefix

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\services\notify_preference_service.py:10:38
   |
 8 | from datetime import datetime, timedelta
 9 | from typing import Optional
10 | from sqlalchemy import select, and_, or_
   |                                      ^^^
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.or_`

F401 [*] `app.schemas.notify_preferences.UserNotifySnoozeUpdate` imported but unused
  --> app\services\notify_preference_service.py:23:5
   |
21 |     UserNotifyPreferenceRead,
22 |     UserNotifySnoozeRead,
23 |     UserNotifySnoozeUpdate,
   |     ^^^^^^^^^^^^^^^^^^^^^^
24 |     UserNotifyPreferenceMatrix,
25 |     NotificationTypeInfo,
   |
help: Remove unused import: `app.schemas.notify_preferences.UserNotifySnoozeUpdate`

F401 [*] `app.schemas.user_notification.UserNotificationCreate` imported but unused
  --> app\services\notify_user_service.py:21:43
   |
19 | from app.models.enums.reading_media_type import ReadingMediaType
20 | from app.models.enums.user_notify_channel_type import UserNotifyChannelType
21 | from app.schemas.user_notification import UserNotificationCreate
   |                                           ^^^^^^^^^^^^^^^^^^^^^^
22 | from app.services.user_notify_channel_service import get_enabled_channels_for_user
23 | from app.modules.user_notify_channels import send_user_channel_message
   |
help: Remove unused import: `app.schemas.user_notification.UserNotificationCreate`

F841 Local variable `should_send_web` is assigned to but never used
  --> app\services\notify_user_service.py:90:5
   |
88 |     # 1. 写入 Web 通知（UserNotification 表）
89 |     should_store = decision.store_in_user_notification if decision else True
90 |     should_send_web = decision.allowed_web if decision else True
   |     ^^^^^^^^^^^^^^^
91 |     
92 |     if not skip_web and should_store:
   |
help: Remove assignment to unused variable `should_send_web`

F821 Undefined name `NotificationDeliveryDecision`
   --> app\services\notify_user_service.py:145:16
    |
143 | def _is_channel_allowed(
144 |     channel_type: UserNotifyChannelType,
145 |     decision: "NotificationDeliveryDecision",
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
146 | ) -> bool:
147 |     """检查某渠道是否被用户偏好允许"""
    |

F401 [*] `app.schemas.notify_preferences.NotificationDeliveryDecision` imported but unused
   --> app\services\notify_user_service.py:148:48
    |
146 | ) -> bool:
147 |     """检查某渠道是否被用户偏好允许"""
148 |     from app.schemas.notify_preferences import NotificationDeliveryDecision
    |                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
149 |     
150 |     match channel_type:
    |
help: Remove unused import: `app.schemas.notify_preferences.NotificationDeliveryDecision`

F401 [*] `typing.Set` imported but unused
 --> app\services\player_wall_aggregation_service.py:6:32
  |
4 | 批量预加载 + 内存聚合方案，避免N+1查询问题
5 | """
6 | from typing import List, Dict, Set, Optional, Tuple
  |                                ^^^
7 | from sqlalchemy.ext.asyncio import AsyncSession
8 | from sqlalchemy import select, and_, func
  |
help: Remove unused import: `typing.Set`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\services\player_wall_aggregation_service.py:8:38
   |
 6 | from typing import List, Dict, Set, Optional, Tuple
 7 | from sqlalchemy.ext.asyncio import AsyncSession
 8 | from sqlalchemy import select, and_, func
   |                                      ^^^^
 9 | from dataclasses import dataclass
10 | from datetime import datetime
   |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `datetime.datetime` imported but unused
  --> app\services\player_wall_aggregation_service.py:10:22
   |
 8 | from sqlalchemy import select, and_, func
 9 | from dataclasses import dataclass
10 | from datetime import datetime
   |                      ^^^^^^^^
11 |
12 | from app.models.media import Media
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.models.download.DownloadTask` imported but unused
  --> app\services\player_wall_aggregation_service.py:17:33
   |
15 | from app.models.user_video_progress import UserVideoProgress
16 | from app.models.subscription import Subscription
17 | from app.models.download import DownloadTask
   |                                 ^^^^^^^^^^^^
18 | from app.core.intel_local.repo.sqlalchemy import SqlAlchemyHRCasesRepository
19 | from app.core.intel_local.repo.hr_cases_repo import HRCasesRepository
   |
help: Remove unused import: `app.models.download.DownloadTask`

F821 Undefined name `refresh_plugin_index`
    --> app\services\plugin_hub_service.py:1036:11
     |
1035 |     # 更新远程索引（如果需要）
1036 |     await refresh_plugin_index(session, force_refresh=force_refresh)
     |           ^^^^^^^^^^^^^^^^^^^^
1037 |     
1038 |     # 获取本地插件
     |

F821 Undefined name `get_plugin_by_id`
    --> app\services\plugin_hub_service.py:1047:31
     |
1046 |         # 查找远程插件信息
1047 |         remote_plugin = await get_plugin_by_id(session, local_plugin.hub_id)
     |                               ^^^^^^^^^^^^^^^^
1048 |         if not remote_plugin:
1049 |             continue
     |

F401 [*] `sqlalchemy.delete` imported but unused
  --> app\services\plugin_install_service.py:11:32
   |
 9 | from typing import Optional
10 |
11 | from sqlalchemy import select, delete
   |                                ^^^^^^
12 | from sqlalchemy.ext.asyncio import AsyncSession
13 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.delete`

F401 [*] `app.services.plugin_git_service.PluginUninstallError` imported but unused
  --> app\services\plugin_install_service.py:20:5
   |
18 |     PluginInstallError,
19 |     PluginUpdateError,
20 |     PluginUninstallError,
   |     ^^^^^^^^^^^^^^^^^^^^
21 |     get_plugin_dir,
22 |     git_clone,
   |
help: Remove unused import

F401 [*] `app.services.plugin_git_service.git_remote_url` imported but unused
  --> app\services\plugin_install_service.py:25:5
   |
23 |     git_pull,
24 |     git_current_rev,
25 |     git_remote_url,
   |     ^^^^^^^^^^^^^^
26 |     remove_plugin_dir,
27 | )
   |
help: Remove unused import

F401 [*] `app.services.plugin_hub_service.get_plugin_hub_index` imported but unused
  --> app\services\plugin_install_service.py:29:5
   |
27 | )
28 | from app.services.plugin_hub_service import (
29 |     get_plugin_hub_index,
   |     ^^^^^^^^^^^^^^^^^^^^
30 |     get_remote_plugin_detail,
31 | )
   |
help: Remove unused import: `app.services.plugin_hub_service.get_plugin_hub_index`

F401 [*] `pathlib.Path` imported but unused
  --> app\services\plugin_install_service.py:87:25
   |
85 |     """
86 |     import json
87 |     from pathlib import Path
   |                         ^^^^
88 |     from app.services.plugin_service import _parse_ui_panels
   |
help: Remove unused import: `pathlib.Path`

F541 [*] f-string without any placeholders
   --> app\services\plugin_install_service.py:111:22
    |
109 |     name = config.get("id") or config.get("name")
110 |     if not name:
111 |         logger.error(f"[plugin-install] Plugin config missing 'id' or 'name'")
    |                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
112 |         return None
    |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
  --> app\services\plugin_registry.py:11:8
   |
 9 | """
10 |
11 | import asyncio
   |        ^^^^^^^
12 | import importlib
13 | import inspect
   |
help: Remove unused import: `asyncio`

F401 [*] `time` imported but unused
  --> app\services\plugin_registry.py:14:8
   |
12 | import importlib
13 | import inspect
14 | import time
   |        ^^^^
15 | from dataclasses import dataclass, field
16 | from types import ModuleType
   |
help: Remove unused import: `time`

F401 [*] `types.ModuleType` imported but unused
  --> app\services\plugin_registry.py:16:19
   |
14 | import time
15 | from dataclasses import dataclass, field
16 | from types import ModuleType
   |                   ^^^^^^^^^^
17 | from typing import Any, Callable, Awaitable, Iterable, Optional, Protocol
   |
help: Remove unused import: `types.ModuleType`

F401 [*] `typing.Callable` imported but unused
  --> app\services\plugin_registry.py:17:25
   |
15 | from dataclasses import dataclass, field
16 | from types import ModuleType
17 | from typing import Any, Callable, Awaitable, Iterable, Optional, Protocol
   |                         ^^^^^^^^
18 |
19 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `typing.Awaitable` imported but unused
  --> app\services\plugin_registry.py:17:35
   |
15 | from dataclasses import dataclass, field
16 | from types import ModuleType
17 | from typing import Any, Callable, Awaitable, Iterable, Optional, Protocol
   |                                   ^^^^^^^^^
18 |
19 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `Plugin.is_quarantined:` for truth checks
   --> app\services\plugin_registry.py:355:46
    |
354 |         try:
355 |             stmt = select(Plugin.name).where(Plugin.is_quarantined == True)
    |                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
356 |             result = await session.execute(stmt)
357 |             quarantined_names = {row[0] for row in result.fetchall()}
    |
help: Replace with `Plugin.is_quarantined`

F401 [*] `app.services.plugin_service.add_plugin_to_path` imported but unused
   --> app\services\plugin_registry.py:376:70
    |
374 |             session: 数据库会话
375 |         """
376 |         from app.services.plugin_service import get_enabled_plugins, add_plugin_to_path, set_plugin_status
    |                                                                      ^^^^^^^^^^^^^^^^^^
377 |         
378 |         if self._initialized:
    |
help: Remove unused import

F401 [*] `app.services.plugin_service.set_plugin_status` imported but unused
   --> app\services\plugin_registry.py:376:90
    |
374 |             session: 数据库会话
375 |         """
376 |         from app.services.plugin_service import get_enabled_plugins, add_plugin_to_path, set_plugin_status
    |                                                                                          ^^^^^^^^^^^^^^^^^
377 |         
378 |         if self._initialized:
    |
help: Remove unused import

F541 [*] f-string without any placeholders
   --> app\services\plugin_registry.py:447:34
    |
445 |                         await result
446 |                     
447 |                     sdk.log.info(f"setup_plugin completed")
    |                                  ^^^^^^^^^^^^^^^^^^^^^^^^^
448 |                 except Exception as e:
449 |                     sdk.log.error(f"setup_plugin failed: {e}")
    |
help: Remove extraneous `f` prefix

F401 [*] `re` imported but unused
  --> app\services\plugin_security_service.py:8:8
   |
 6 | """
 7 |
 8 | import re
   |        ^^
 9 | from typing import Optional, Dict, Any, List
10 | from urllib.parse import urlparse
   |
help: Remove unused import: `re`

F821 Undefined name `PluginContext`
  --> app\services\plugin_service.py:32:46
   |
30 | # ============== PLUGIN-SDK-1：插件上下文构建 ==============
31 |
32 | def build_plugin_context(plugin: Plugin) -> "PluginContext":
   |                                              ^^^^^^^^^^^^^
33 |     """
34 |     为插件构建运行时上下文
   |

F401 [*] `sqlalchemy.func` imported but unused
  --> app\services\plugin_statistics_service.py:11:40
   |
 9 | from typing import Optional, Dict, Any, List
10 | from sqlalchemy.ext.asyncio import AsyncSession
11 | from sqlalchemy import select, update, func
   |                                        ^^^^
12 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.func`

F401 [*] `app.models.plugin.PluginType` imported but unused
  --> app\services\plugin_statistics_service.py:14:39
   |
12 | from loguru import logger
13 |
14 | from app.models.plugin import Plugin, PluginType
   |                                       ^^^^^^^^^^
   |
help: Remove unused import: `app.models.plugin.PluginType`

F401 [*] `datetime.datetime` imported but unused
  --> app\services\plugin_token_service.py:9:22
   |
 8 | import secrets
 9 | from datetime import datetime, timedelta
   |                      ^^^^^^^^
10 | from typing import Optional, Dict, Any, List
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `datetime.timedelta` imported but unused
  --> app\services\plugin_token_service.py:9:32
   |
 8 | import secrets
 9 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
10 | from typing import Optional, Dict, Any, List
11 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `typing.Dict` imported but unused
  --> app\services\plugin_token_service.py:10:30
   |
 8 | import secrets
 9 | from datetime import datetime, timedelta
10 | from typing import Optional, Dict, Any, List
   |                              ^^^^
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, update
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> app\services\plugin_token_service.py:10:36
   |
 8 | import secrets
 9 | from datetime import datetime, timedelta
10 | from typing import Optional, Dict, Any, List
   |                                    ^^^
11 | from sqlalchemy.ext.asyncio import AsyncSession
12 | from sqlalchemy import select, update
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> app\services\reading_control_service.py:17:20
   |
15 | 所有操作都通过现有的 Service 层进行，确保数据一致性。
16 | """
17 | from typing import Optional
   |                    ^^^^^^^^
18 | from datetime import datetime
19 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `typing.Optional`

F401 [*] `datetime.datetime` imported but unused
  --> app\services\reading_control_service.py:18:22
   |
16 | """
17 | from typing import Optional
18 | from datetime import datetime
   |                      ^^^^^^^^
19 | from sqlalchemy.ext.asyncio import AsyncSession
20 | from sqlalchemy import select, and_
   |
help: Remove unused import: `datetime.datetime`

F401 [*] `app.services.reading_favorite_service.remove_favorite` imported but unused
  --> app\services\reading_control_service.py:29:65
   |
27 | from app.models.manga_reading_progress import MangaReadingProgress
28 | from app.schemas.reading_hub import ReadingOngoingItem, ReadingShelfItem
29 | from app.services.reading_favorite_service import add_favorite, remove_favorite, UserFavoriteMediaCreate
   |                                                                 ^^^^^^^^^^^^^^^
30 | from app.utils.time import utcnow
   |
help: Remove unused import: `app.services.reading_favorite_service.remove_favorite`

F841 Local variable `favorite_item` is assigned to but never used
   --> app\services\reading_control_service.py:200:9
    |
199 |         # 调用现有的收藏服务，直接返回结果
200 |         favorite_item = await add_favorite(session, user_id, favorite_data)
    |         ^^^^^^^^^^^^^
201 |         
202 |         # 转换为 ReadingShelfItem（使用 reading_favorite_service 的构建逻辑）
    |
help: Remove assignment to unused variable `favorite_item`

F401 [*] `app.models.audiobook.AudiobookFile` imported but unused
  --> app\services\reading_favorite_service.py:12:34
   |
10 | from app.models.enums.reading_media_type import ReadingMediaType
11 | from app.models.ebook import EBook
12 | from app.models.audiobook import AudiobookFile
   |                                  ^^^^^^^^^^^^^
13 | from app.models.manga_series_local import MangaSeriesLocal
14 | from app.schemas.user_favorite_media import UserFavoriteMediaCreate, UserFavoriteMediaRead
   |
help: Remove unused import: `app.models.audiobook.AudiobookFile`

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> app\services\remote_plugin_dispatcher.py:10:36
   |
 8 | from datetime import datetime
 9 | from typing import Any, Dict, List, Optional
10 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
11 | from sqlalchemy import select
12 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

F401 [*] `app.plugin_sdk.remote_protocol.RemotePluginResponse` imported but unused
  --> app\services\remote_plugin_dispatcher.py:18:5
   |
16 |     RemotePluginClient, 
17 |     RemotePluginEvent, 
18 |     RemotePluginResponse,
   |     ^^^^^^^^^^^^^^^^^^^^
19 |     create_remote_client
20 | )
   |
help: Remove unused import: `app.plugin_sdk.remote_protocol.RemotePluginResponse`

F401 [*] `app.services.system_health_service.get_runner_status` imported but unused
  --> app\services\runner_heartbeat.py:22:5
   |
20 |     runner_heartbeat_start,
21 |     runner_heartbeat_finish,
22 |     get_runner_status,
   |     ^^^^^^^^^^^^^^^^^
23 | )
   |
help: Remove unused import: `app.services.system_health_service.get_runner_status`

F401 [*] `tempfile` imported but unused
  --> app\services\self_check_service.py:10:8
   |
 8 | import time
 9 | import os
10 | import tempfile
   |        ^^^^^^^^
11 | from datetime import datetime, timedelta
12 | from typing import Any, Awaitable, Callable, Optional
   |
help: Remove unused import: `tempfile`

F401 [*] `datetime.timedelta` imported but unused
  --> app\services\self_check_service.py:11:32
   |
 9 | import os
10 | import tempfile
11 | from datetime import datetime, timedelta
   |                                ^^^^^^^^^
12 | from typing import Any, Awaitable, Callable, Optional
13 | from sqlalchemy import select, text
   |
help: Remove unused import: `datetime.timedelta`

F401 [*] `typing.Optional` imported but unused
  --> app\services\self_check_service.py:12:46
   |
10 | import tempfile
11 | from datetime import datetime, timedelta
12 | from typing import Any, Awaitable, Callable, Optional
   |                                              ^^^^^^^^
13 | from sqlalchemy import select, text
14 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import: `typing.Optional`

F401 [*] `app.schemas.system_health.SystemHealthCheckRead` imported but unused
  --> app\services\system_health_notify.py:11:60
   |
 9 | from loguru import logger
10 |
11 | from app.schemas.system_health import SystemHealthSummary, SystemHealthCheckRead
   |                                                            ^^^^^^^^^^^^^^^^^^^^^
12 | from app.models.enums.alert_severity import AlertSeverity
   |
help: Remove unused import: `app.schemas.system_health.SystemHealthCheckRead`

F841 Local variable `severity_emoji` is assigned to but never used
  --> app\services\system_health_notify.py:27:5
   |
25 |         (title, body) 元组
26 |     """
27 |     severity_emoji = "❌" if status == "error" else "⚠️"
   |     ^^^^^^^^^^^^^^
28 |     severity_text = "错误" if status == "error" else "警告"
   |
help: Remove assignment to unused variable `severity_emoji`

F841 Local variable `check_level` is assigned to but never used
   --> app\services\system_health_notify.py:179:17
    |
177 |         for check in summary.checks:
178 |             if check.status in ("error", "warning"):
179 |                 check_level: Literal["warning", "error"] = "error" if check.status == "error" else "warning"
    |                 ^^^^^^^^^^^
180 |                 title, body = format_health_alert_message(
181 |                     check.key,
    |
help: Remove assignment to unused variable `check_level`

F401 [*] `typing.Optional` imported but unused
 --> app\services\system_health_report_service.py:7:34
  |
6 | from datetime import datetime
7 | from typing import Literal, Any, Optional
  |                                  ^^^^^^^^
8 | from sqlalchemy.ext.asyncio import AsyncSession
9 | from loguru import logger
  |
help: Remove unused import: `typing.Optional`

F401 [*] `loguru.logger` imported but unused
  --> app\services\system_health_report_service.py:9:20
   |
 7 | from typing import Literal, Any, Optional
 8 | from sqlalchemy.ext.asyncio import AsyncSession
 9 | from loguru import logger
   |                    ^^^^^^
10 |
11 | from app.services.system_health_service import get_health_summary
   |
help: Remove unused import: `loguru.logger`

F401 [*] `sqlalchemy.func` imported but unused
  --> app\services\task_center_service.py:11:32
   |
 9 | from typing import Optional, List
10 |
11 | from sqlalchemy import select, func, desc, and_, or_
   |                                ^^^^
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `sqlalchemy.and_` imported but unused
  --> app\services\task_center_service.py:11:44
   |
 9 | from typing import Optional, List
10 |
11 | from sqlalchemy import select, func, desc, and_, or_
   |                                            ^^^^
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

F401 [*] `sqlalchemy.or_` imported but unused
  --> app\services\task_center_service.py:11:50
   |
 9 | from typing import Optional, List
10 |
11 | from sqlalchemy import select, func, desc, and_, or_
   |                                                  ^^^
12 | from sqlalchemy.ext.asyncio import AsyncSession
   |
help: Remove unused import

E712 Avoid equality comparisons to `True`; use `UserNotifyChannel.is_enabled:` for truth checks
   --> app\services\user_notify_channel_service.py:169:13
    |
167 |         select(UserNotifyChannel).where(
168 |             UserNotifyChannel.user_id == user_id,
169 |             UserNotifyChannel.is_enabled == True,
    |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
170 |         )
171 |     )
    |
help: Replace with `UserNotifyChannel.is_enabled`

F401 [*] `typing.List` imported but unused
  --> app\utils\doh.py:13:36
   |
11 | import urllib.error
12 | from threading import Lock
13 | from typing import Dict, Optional, List, Any
   |                                    ^^^^
14 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `typing.Dict` imported but unused
 --> app\utils\http_client.py:7:30
  |
5 | """
6 |
7 | from typing import Optional, Dict, Any
  |                              ^^^^
8 | import httpx
9 | from loguru import logger
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> app\utils\http_client.py:7:36
  |
5 | """
6 |
7 | from typing import Optional, Dict, Any
  |                                    ^^^
8 | import httpx
9 | from loguru import logger
  |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\add_vabhub_labels.py:14:1
   |
12 | sys.path.insert(0, str(backend_dir))
13 |
14 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.downloaders import DownloaderClient, DownloaderType
16 | from app.modules.settings.service import SettingsService
   |

E402 Module level import not at top of file
  --> scripts\add_vabhub_labels.py:15:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.core.downloaders import DownloaderClient, DownloaderType
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.settings.service import SettingsService
17 | from app.models.download import DownloadTask
   |

E402 Module level import not at top of file
  --> scripts\add_vabhub_labels.py:16:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.core.downloaders import DownloaderClient, DownloaderType
16 | from app.modules.settings.service import SettingsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.models.download import DownloadTask
18 | from sqlalchemy import select
   |

E402 Module level import not at top of file
  --> scripts\add_vabhub_labels.py:17:1
   |
15 | from app.core.downloaders import DownloaderClient, DownloaderType
16 | from app.modules.settings.service import SettingsService
17 | from app.models.download import DownloadTask
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from sqlalchemy import select
   |

E402 Module level import not at top of file
  --> scripts\add_vabhub_labels.py:18:1
   |
16 | from app.modules.settings.service import SettingsService
17 | from app.models.download import DownloadTask
18 | from sqlalchemy import select
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |
20 | async def add_vabhub_labels():
   |

F401 [*] `datetime.datetime` imported but unused
 --> scripts\check_backend_health.py:8:22
  |
6 | import httpx
7 | import sys
8 | from datetime import datetime
  |                      ^^^^^^^^
  |
help: Remove unused import: `datetime.datetime`

F541 [*] f-string without any placeholders
  --> scripts\check_backend_health.py:49:27
   |
47 |                     print()
48 |                 except httpx.ConnectError:
49 |                     print(f"  [FAIL] 无法连接到后端服务")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
50 |                     print(f"  请确保后端服务正在运行: python main.py")
51 |                     return False
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\check_backend_health.py:50:27
   |
48 |                 except httpx.ConnectError:
49 |                     print(f"  [FAIL] 无法连接到后端服务")
50 |                     print(f"  请确保后端服务正在运行: python main.py")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
51 |                     return False
52 |                 except httpx.TimeoutException:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\check_backend_health.py:53:27
   |
51 |                     return False
52 |                 except httpx.TimeoutException:
53 |                     print(f"  [FAIL] 请求超时")
   |                           ^^^^^^^^^^^^^^^^^^^^
54 |                     return False
55 |                 except Exception as e:
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\check_backend_logs.py:15:1
   |
13 | sys.path.insert(0, str(backend_dir))
14 |
15 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E722 Do not use bare `except`
  --> scripts\check_backend_logs.py:71:13
   |
69 |                     # 如果没有时间戳，包含所有行
70 |                     filtered_lines.append(line)
71 |             except:
   |             ^^^^^^
72 |                 # 如果解析失败，包含该行
73 |                 filtered_lines.append(line)
   |

E722 Do not use bare `except`
   --> scripts\check_backend_logs.py:128:25
    |
126 |                                 if log_time >= cutoff_time:
127 |                                     matches.append((log_file.name, line.rstrip()))
128 |                         except:
    |                         ^^^^^^
129 |                             matches.append((log_file.name, line.rstrip()))
130 |         except Exception as e:
    |

F841 Local variable `downloads` is assigned to but never used
  --> scripts\check_download_status.py:93:5
   |
92 |     # 检查所有下载任务
93 |     downloads = await check_downloads()
   |     ^^^^^^^^^
94 |     
95 |     # 如果有任务ID文件，检查这些任务
   |
help: Remove assignment to unused variable `downloads`

E402 Module level import not at top of file
  --> scripts\check_health.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.health import get_health_checker
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\check_health.py:19:1
   |
18 | from app.core.health import get_health_checker
19 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\check_service_status.py:16:1
   |
14 | sys.path.insert(0, str(project_root / "backend"))
15 |
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | # 配置日志（修复Windows编码问题）
   |

E402 Module level import not at top of file
  --> scripts\check_service_status.py:19:1
   |
18 | # 配置日志（修复Windows编码问题）
19 | import io
   | ^^^^^^^^^
20 | import sys
   |

E402 Module level import not at top of file
  --> scripts\check_service_status.py:20:1
   |
18 | # 配置日志（修复Windows编码问题）
19 | import io
20 | import sys
   | ^^^^^^^^^^
21 |
22 | # 设置标准输出编码为UTF-8
   |

E722 Do not use bare `except`
  --> scripts\check_service_status.py:27:5
   |
25 |         sys.stdout.reconfigure(encoding='utf-8', errors='replace')
26 |         sys.stderr.reconfigure(encoding='utf-8', errors='replace')
27 |     except:
   |     ^^^^^^
28 |         # 如果reconfigure不可用，使用TextIOWrapper
29 |         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
   |

E402 Module level import not at top of file
  --> scripts\check_transmission_labels.py:14:1
   |
12 | sys.path.insert(0, str(backend_dir))
13 |
14 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.downloaders import DownloaderClient, DownloaderType
16 | from app.modules.settings.service import SettingsService
   |

E402 Module level import not at top of file
  --> scripts\check_transmission_labels.py:15:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.core.downloaders import DownloaderClient, DownloaderType
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.settings.service import SettingsService
   |

E402 Module level import not at top of file
  --> scripts\check_transmission_labels.py:16:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.core.downloaders import DownloaderClient, DownloaderType
16 | from app.modules.settings.service import SettingsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | async def check_transmission_labels():
   |

F841 Local variable `torrent_hash` is assigned to but never used
  --> scripts\check_transmission_labels.py:94:17
   |
92 |             for i, torrent in enumerate(torrents[:20], 1):  # 只显示前20个
93 |                 torrent_name = torrent.get("name", "未知")
94 |                 torrent_hash = torrent.get("hashString", "")
   |                 ^^^^^^^^^^^^
95 |                 labels = torrent.get("labels", [])
   |
help: Remove assignment to unused variable `torrent_hash`

F541 [*] f-string without any placeholders
   --> scripts\check_transmission_labels.py:111:33
    |
109 |                     tasks_without_labels += 1
110 |                     logger.info(f"{i}. {torrent_name[:60]}")
111 |                     logger.info(f"   标签: 无标签")
    |                                 ^^^^^^^^^^^^^^^^^^
112 |                 logger.info("")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\create_admin.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.database import AsyncSessionLocal, close_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.models.user import User
20 | from app.core.auth import get_password_hash
   |

E402 Module level import not at top of file
  --> scripts\create_admin.py:19:1
   |
18 | from app.core.database import AsyncSessionLocal, close_db
19 | from app.models.user import User
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.core.auth import get_password_hash
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\create_admin.py:20:1
   |
18 | from app.core.database import AsyncSessionLocal, close_db
19 | from app.models.user import User
20 | from app.core.auth import get_password_hash
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\create_admin.py:21:1
   |
19 | from app.models.user import User
20 | from app.core.auth import get_password_hash
21 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `os` imported but unused
 --> scripts\create_indexes.py:7:8
  |
6 | import sys
7 | import os
  |        ^^
8 | from pathlib import Path
  |
help: Remove unused import: `os`

E402 Module level import not at top of file
  --> scripts\create_indexes.py:14:1
   |
12 | sys.path.insert(0, str(backend_dir))
13 |
14 | import asyncio
   | ^^^^^^^^^^^^^^
15 | from sqlalchemy import text
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\create_indexes.py:15:1
   |
14 | import asyncio
15 | from sqlalchemy import text
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\create_indexes.py:16:1
   |
14 | import asyncio
15 | from sqlalchemy import text
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | from app.core.database import engine
   |

E402 Module level import not at top of file
  --> scripts\create_indexes.py:18:1
   |
16 | from loguru import logger
17 |
18 | from app.core.database import engine
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E722 Do not use bare `except`
   --> scripts\create_test_downloads.py:124:17
    |
122 |                         connected = True
123 |                         break
124 |                 except:
    |                 ^^^^^^
125 |                     continue
    |

E402 Module level import not at top of file
  --> scripts\create_test_user_simple.py:15:1
   |
13 |     sys.path.insert(0, str(backend_dir))
14 |
15 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.models.user import User
17 | from app.core.security import get_password_hash
   |

E402 Module level import not at top of file
  --> scripts\create_test_user_simple.py:16:1
   |
15 | from app.core.database import AsyncSessionLocal
16 | from app.models.user import User
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.core.security import get_password_hash
   |

E402 Module level import not at top of file
  --> scripts\create_test_user_simple.py:17:1
   |
15 | from app.core.database import AsyncSessionLocal
16 | from app.models.user import User
17 | from app.core.security import get_password_hash
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\create_test_user_simple.py:44:15
   |
43 |         await user.save(db)
44 |         print(f"[OK] 测试用户创建成功")
   |               ^^^^^^^^^^^^^^^^^^^^^^^^
45 |         print(f"     用户名: {username}")
46 |         print(f"     邮箱: {email}")
   |
help: Remove extraneous `f` prefix

E722 Do not use bare `except`
  --> scripts\diagnose_service.py:17:5
   |
15 |         sys.stdout.reconfigure(encoding='utf-8', errors='replace')
16 |         sys.stderr.reconfigure(encoding='utf-8', errors='replace')
17 |     except:
   |     ^^^^^^
18 |         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
19 |         sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
   |

E722 Do not use bare `except`
  --> scripts\diagnose_service.py:76:25
   |
74 |                                 if process_info:
75 |                                     print(f"  [INFO] 进程名称: {process_info[0]}")
76 |                         except:
   |                         ^^^^^^
77 |                             pass
   |

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:117:19
    |
115 |         db_url = settings.DATABASE_URL
116 |         if db_url.startswith("sqlite"):
117 |             print(f"  [INFO] 数据库类型: SQLite")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
118 |             print(f"  [INFO] 数据库URL: {db_url}")
119 |             # 检查SQLite文件是否存在
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:127:27
    |
125 |                 else:
126 |                     print(f"  [WARNING] 数据库文件不存在: {db_file}")
127 |                     print(f"  [INFO] 将在首次运行时自动创建")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
128 |         elif db_url.startswith("postgresql"):
129 |             print(f"  [INFO] 数据库类型: PostgreSQL")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:129:19
    |
127 |                     print(f"  [INFO] 将在首次运行时自动创建")
128 |         elif db_url.startswith("postgresql"):
129 |             print(f"  [INFO] 数据库类型: PostgreSQL")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130 |             print(f"  [INFO] 数据库URL: {db_url.split('@')[1] if '@' in db_url else '已配置'}")
131 |             print(f"  [WARNING] 需要检查PostgreSQL服务是否运行")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:131:19
    |
129 |             print(f"  [INFO] 数据库类型: PostgreSQL")
130 |             print(f"  [INFO] 数据库URL: {db_url.split('@')[1] if '@' in db_url else '已配置'}")
131 |             print(f"  [WARNING] 需要检查PostgreSQL服务是否运行")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
132 |         else:
133 |             print(f"  [INFO] 数据库类型: 未知")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:133:19
    |
131 |             print(f"  [WARNING] 需要检查PostgreSQL服务是否运行")
132 |         else:
133 |             print(f"  [INFO] 数据库类型: 未知")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
134 |             print(f"  [INFO] 数据库URL: {db_url}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:161:19
    |
160 |         if pid:
161 |             print(f"[建议] 如果服务无响应，可以尝试:")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
162 |             print(f"  1. 终止进程: taskkill /PID {pid} /F (Windows)")
163 |             print(f"  2. 重新启动服务: python backend/scripts/start.py")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\diagnose_service.py:163:19
    |
161 |             print(f"[建议] 如果服务无响应，可以尝试:")
162 |             print(f"  1. 终止进程: taskkill /PID {pid} /F (Windows)")
163 |             print(f"  2. 重新启动服务: python backend/scripts/start.py")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
164 |     else:
165 |         print("[建议] 端口未被占用，可以启动服务:")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\fix_issues.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.database import init_db, engine, Base
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from loguru import logger
   |

F401 [*] `app.core.database.init_db` imported but unused
  --> scripts\fix_issues.py:13:31
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.database import init_db, engine, Base
   |                               ^^^^^^^
14 | from loguru import logger
   |
help: Remove unused import: `app.core.database.init_db`

E402 Module level import not at top of file
  --> scripts\fix_issues.py:14:1
   |
13 | from app.core.database import init_db, engine, Base
14 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `app.models.user.User` imported but unused
  --> scripts\fix_issues.py:25:37
   |
23 |     try:
24 |         # 导入所有模型以确保它们被注册到Base.metadata
25 |         from app.models.user import User
   |                                     ^^^^
26 |         from app.models.media import Media, MediaFile
27 |         from app.models.subscription import Subscription
   |
help: Remove unused import: `app.models.user.User`

F401 [*] `app.models.media.Media` imported but unused
  --> scripts\fix_issues.py:26:38
   |
24 |         # 导入所有模型以确保它们被注册到Base.metadata
25 |         from app.models.user import User
26 |         from app.models.media import Media, MediaFile
   |                                      ^^^^^
27 |         from app.models.subscription import Subscription
28 |         from app.models.download import DownloadTask
   |
help: Remove unused import

F401 [*] `app.models.media.MediaFile` imported but unused
  --> scripts\fix_issues.py:26:45
   |
24 |         # 导入所有模型以确保它们被注册到Base.metadata
25 |         from app.models.user import User
26 |         from app.models.media import Media, MediaFile
   |                                             ^^^^^^^^^
27 |         from app.models.subscription import Subscription
28 |         from app.models.download import DownloadTask
   |
help: Remove unused import

F401 [*] `app.models.subscription.Subscription` imported but unused
  --> scripts\fix_issues.py:27:45
   |
25 |         from app.models.user import User
26 |         from app.models.media import Media, MediaFile
27 |         from app.models.subscription import Subscription
   |                                             ^^^^^^^^^^^^
28 |         from app.models.download import DownloadTask
29 |         from app.models.cache import CacheEntry  # 确保缓存表被注册
   |
help: Remove unused import: `app.models.subscription.Subscription`

F401 [*] `app.models.download.DownloadTask` imported but unused
  --> scripts\fix_issues.py:28:41
   |
26 |         from app.models.media import Media, MediaFile
27 |         from app.models.subscription import Subscription
28 |         from app.models.download import DownloadTask
   |                                         ^^^^^^^^^^^^
29 |         from app.models.cache import CacheEntry  # 确保缓存表被注册
30 |         # 导入其他模型...
   |
help: Remove unused import: `app.models.download.DownloadTask`

F811 [*] Redefinition of unused `CacheEntry` from line 29
  --> scripts\fix_issues.py:41:38
   |
39 |         from sqlalchemy import inspect
40 |         from app.core.database import AsyncSessionLocal
41 |         from app.models.cache import CacheEntry
   |                                      ^^^^^^^^^^ `CacheEntry` redefined here
42 |         
43 |         async with AsyncSessionLocal() as session:
   |
  ::: scripts\fix_issues.py:29:38
   |
27 |         from app.models.subscription import Subscription
28 |         from app.models.download import DownloadTask
29 |         from app.models.cache import CacheEntry  # 确保缓存表被注册
   |                                      ---------- previous definition of `CacheEntry` here
30 |         # 导入其他模型...
   |
help: Remove definition: `CacheEntry`

F401 [*] `app.models.cache.CacheEntry` imported but unused
  --> scripts\fix_issues.py:41:38
   |
39 |         from sqlalchemy import inspect
40 |         from app.core.database import AsyncSessionLocal
41 |         from app.models.cache import CacheEntry
   |                                      ^^^^^^^^^^
42 |         
43 |         async with AsyncSessionLocal() as session:
   |
help: Remove unused import: `app.models.cache.CacheEntry`

F841 Local variable `session` is assigned to but never used
  --> scripts\fix_issues.py:43:43
   |
41 |         from app.models.cache import CacheEntry
42 |         
43 |         async with AsyncSessionLocal() as session:
   |                                           ^^^^^^^
44 |             inspector = inspect(engine.sync_engine)
45 |             tables = inspector.get_table_names()
   |
help: Remove assignment to unused variable `session`

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:19:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from loguru import logger
21 | import qrcode
   |

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:20:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
21 | import qrcode
22 | from io import BytesIO
   |

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:21:1
   |
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
21 | import qrcode
   | ^^^^^^^^^^^^^
22 | from io import BytesIO
23 | import base64
   |

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:22:1
   |
20 | from loguru import logger
21 | import qrcode
22 | from io import BytesIO
   | ^^^^^^^^^^^^^^^^^^^^^^
23 | import base64
24 | from PIL import Image
   |

F401 [*] `io.BytesIO` imported but unused
  --> scripts\generate_115_qrcode.py:22:16
   |
20 | from loguru import logger
21 | import qrcode
22 | from io import BytesIO
   |                ^^^^^^^
23 | import base64
24 | from PIL import Image
   |
help: Remove unused import: `io.BytesIO`

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:23:1
   |
21 | import qrcode
22 | from io import BytesIO
23 | import base64
   | ^^^^^^^^^^^^^
24 | from PIL import Image
   |

F401 [*] `base64` imported but unused
  --> scripts\generate_115_qrcode.py:23:8
   |
21 | import qrcode
22 | from io import BytesIO
23 | import base64
   |        ^^^^^^
24 | from PIL import Image
   |
help: Remove unused import: `base64`

E402 Module level import not at top of file
  --> scripts\generate_115_qrcode.py:24:1
   |
22 | from io import BytesIO
23 | import base64
24 | from PIL import Image
   | ^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `PIL.Image` imported but unused
  --> scripts\generate_115_qrcode.py:24:17
   |
22 | from io import BytesIO
23 | import base64
24 | from PIL import Image
   |                 ^^^^^
   |
help: Remove unused import: `PIL.Image`

E722 Do not use bare `except`
  --> scripts\generate_115_qrcode.py:46:9
   |
44 |             # 使用qrcode的终端显示功能
45 |             qr.print_ascii(invert=True)
46 |         except:
   |         ^^^^^^
47 |             # 如果终端不支持，保存为文件
48 |             qr_file = Path(__file__).parent.parent.parent / "115_qrcode.png"
   |

E402 Module level import not at top of file
  --> scripts\init_cloud_storage.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\init_cloud_storage.py:19:1
   |
18 | from app.core.cloud_key_manager import get_key_manager
19 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\init_db.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.database import init_db, close_db, engine
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.config import settings
20 | from app.core.cache import get_cache
   |

E402 Module level import not at top of file
  --> scripts\init_db.py:19:1
   |
18 | from app.core.database import init_db, close_db, engine
19 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.core.cache import get_cache
21 | from app.modules.settings.service import SettingsService
   |

E402 Module level import not at top of file
  --> scripts\init_db.py:20:1
   |
18 | from app.core.database import init_db, close_db, engine
19 | from app.core.config import settings
20 | from app.core.cache import get_cache
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.modules.settings.service import SettingsService
22 | from app.core.database import AsyncSessionLocal
   |

F401 [*] `app.core.cache.get_cache` imported but unused
  --> scripts\init_db.py:20:28
   |
18 | from app.core.database import init_db, close_db, engine
19 | from app.core.config import settings
20 | from app.core.cache import get_cache
   |                            ^^^^^^^^^
21 | from app.modules.settings.service import SettingsService
22 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `app.core.cache.get_cache`

E402 Module level import not at top of file
  --> scripts\init_db.py:21:1
   |
19 | from app.core.config import settings
20 | from app.core.cache import get_cache
21 | from app.modules.settings.service import SettingsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from app.core.database import AsyncSessionLocal
23 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\init_db.py:22:1
   |
20 | from app.core.cache import get_cache
21 | from app.modules.settings.service import SettingsService
22 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\init_db.py:23:1
   |
21 | from app.modules.settings.service import SettingsService
22 | from app.core.database import AsyncSessionLocal
23 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `app.models.cache.CacheEntry` imported but unused
  --> scripts\init_db.py:44:46
   |
42 |         if not settings.DATABASE_URL.startswith("sqlite"):
43 |             try:
44 |                 from app.models.cache import CacheEntry
   |                                              ^^^^^^^^^^
45 |                 async with AsyncSessionLocal() as session:
46 |                     # 检查表是否已存在
   |
help: Remove unused import: `app.models.cache.CacheEntry`

F401 [*] `asyncio` imported but unused
 --> scripts\integrate_chart_row.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import sys
8 | from pathlib import Path
  |
help: Remove unused import: `asyncio`

E402 Module level import not at top of file
  --> scripts\integrate_chart_row.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | from app.modules.charts.providers.chart_row import ChartRow
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\integrate_chart_row.py:15:1
   |
14 | from app.modules.charts.providers.chart_row import ChartRow
15 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `typing.List` imported but unused
  --> scripts\migrate.py:16:31
   |
14 | import json
15 | from datetime import datetime
16 | from typing import Any, Dict, List
   |                               ^^^^
17 |
18 | from loguru import logger
   |
help: Remove unused import: `typing.List`

F401 [*] `loguru.logger` imported but unused
  --> scripts\migrate.py:18:20
   |
16 | from typing import Any, Dict, List
17 |
18 | from loguru import logger
   |                    ^^^^^^
19 |
20 | from app.core.migrations import run_migrations
   |
help: Remove unused import: `loguru.logger`

E402 Module level import not at top of file
  --> scripts\migrate_add_downloader_hash.py:14:1
   |
12 |     sys.path.insert(0, str(backend_dir))
13 |
14 | from sqlalchemy import text
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.database import AsyncSessionLocal
16 | from loguru import logger
   |

F401 [*] `sqlalchemy.text` imported but unused
  --> scripts\migrate_add_downloader_hash.py:14:24
   |
12 |     sys.path.insert(0, str(backend_dir))
13 |
14 | from sqlalchemy import text
   |                        ^^^^
15 | from app.core.database import AsyncSessionLocal
16 | from loguru import logger
   |
help: Remove unused import: `sqlalchemy.text`

E402 Module level import not at top of file
  --> scripts\migrate_add_downloader_hash.py:15:1
   |
14 | from sqlalchemy import text
15 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |

F401 [*] `app.core.database.AsyncSessionLocal` imported but unused
  --> scripts\migrate_add_downloader_hash.py:15:31
   |
14 | from sqlalchemy import text
15 | from app.core.database import AsyncSessionLocal
   |                               ^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |
help: Remove unused import: `app.core.database.AsyncSessionLocal`

E402 Module level import not at top of file
  --> scripts\migrate_add_downloader_hash.py:16:1
   |
14 | from sqlalchemy import text
15 | from app.core.database import AsyncSessionLocal
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\migrate_ai_site_adapter_schema.py:22:1
   |
20 | sys.path.insert(0, str(project_root))
21 |
22 | from app.core.database import AsyncSessionLocal, engine
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `app.core.database.engine` imported but unused
  --> scripts\migrate_ai_site_adapter_schema.py:22:50
   |
20 | sys.path.insert(0, str(project_root))
21 |
22 | from app.core.database import AsyncSessionLocal, engine
   |                                                  ^^^^^^
   |
help: Remove unused import: `app.core.database.engine`

E712 Avoid equality comparisons to `True`; use `Directory.enable_strm:` for truth checks
  --> scripts\migrate_directory_strm_for_books.py:25:21
   |
23 |                 .where(
24 |                     Directory.media_type == MediaType.BOOK,
25 |                     Directory.enable_strm == True
   |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
26 |                 )
27 |                 .values(enable_strm=False)
   |
help: Replace with `Directory.enable_strm`

F401 [*] `app.core.database.engine` imported but unused
  --> scripts\migrate_local_intel_schema.py:15:50
   |
13 | from sqlalchemy.ext.asyncio import AsyncSession
14 |
15 | from app.core.database import AsyncSessionLocal, engine
   |                                                  ^^^^^^
   |
help: Remove unused import: `app.core.database.engine`

F401 [*] `subprocess` imported but unused
  --> scripts\quick_test.py:9:8
   |
 7 | import httpx
 8 | import sys
 9 | import subprocess
   |        ^^^^^^^^^^
10 | import time
11 | from pathlib import Path
   |
help: Remove unused import: `subprocess`

F401 [*] `time` imported but unused
  --> scripts\quick_test.py:10:8
   |
 8 | import sys
 9 | import subprocess
10 | import time
   |        ^^^^
11 | from pathlib import Path
   |
help: Remove unused import: `time`

E402 Module level import not at top of file
  --> scripts\quick_test.py:18:1
   |
16 |     sys.path.insert(0, str(backend_dir))
17 |
18 | from scripts.api_test_config import API_BASE_URL, API_PREFIX, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |
20 | BASE_URL = API_BASE_URL
   |

F541 [*] f-string without any placeholders
  --> scripts\quick_test.py:65:27
   |
63 |                 if "data" in data and "access_token" in data.get("data", {}):
64 |                     auth_token = data["data"]["access_token"]
65 |                     print(f"[OK] 登录成功，获取Token")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
66 |                 else:
67 |                     print(f"[WARNING] 登录响应格式异常: {data}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\quick_test.py:71:23
   |
69 |             else:
70 |                 print(f"[WARNING] 登录失败: {response.status_code}")
71 |                 print(f"     尝试注册新用户...")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^
72 |                 # 尝试注册
73 |                 response = await client.post(
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\quick_test.py:83:27
   |
81 |                 )
82 |                 if response.status_code in [200, 201]:
83 |                     print(f"[OK] 用户注册成功，重新登录...")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
84 |                     await asyncio.sleep(1)
85 |                     response = await client.post(
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\quick_test.py:96:35
   |
94 |                         if "data" in data and "access_token" in data.get("data", {}):
95 |                             auth_token = data["data"]["access_token"]
96 |                             print(f"[OK] 登录成功，获取Token")
   |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
97 |                         else:
98 |                             print(f"[ERROR] 登录响应格式异常")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:98:35
    |
 96 |                             print(f"[OK] 登录成功，获取Token")
 97 |                         else:
 98 |                             print(f"[ERROR] 登录响应格式异常")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
 99 |                             return False
100 |                     else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:134:27
    |
132 |                 # 检查响应格式
133 |                 if "success" in data:
134 |                     print(f"[OK] 创建订阅成功，响应格式正确")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
135 |                     print(f"     success: {data.get('success')}")
136 |                     if "data" in data:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:137:31
    |
135 |                     print(f"     success: {data.get('success')}")
136 |                     if "data" in data:
137 |                         print(f"     data字段存在: [OK]")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
138 |                     else:
139 |                         print(f"     data字段缺失: [ERROR]")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:139:31
    |
137 |                         print(f"     data字段存在: [OK]")
138 |                     else:
139 |                         print(f"     data字段缺失: [ERROR]")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
140 |                     return True
141 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:142:27
    |
140 |                     return True
141 |                 else:
142 |                     print(f"[ERROR] 响应格式错误，缺少'success'字段")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
143 |                     print(f"     Response: {data}")
144 |                     return False
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:165:27
    |
163 |                 data = response.json()
164 |                 if "success" in data:
165 |                     print(f"[OK] 获取订阅列表成功，响应格式正确")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
166 |                     print(f"     success: {data.get('success')}")
167 |                     if "data" in data:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:168:31
    |
166 |                     print(f"     success: {data.get('success')}")
167 |                     if "data" in data:
168 |                         print(f"     data字段存在: [OK]")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
169 |                         if isinstance(data.get("data"), dict) and "items" in data.get("data", {}):
170 |                             print(f"     items字段存在: [OK]")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:170:35
    |
168 |                         print(f"     data字段存在: [OK]")
169 |                         if isinstance(data.get("data"), dict) and "items" in data.get("data", {}):
170 |                             print(f"     items字段存在: [OK]")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
171 |                     else:
172 |                         print(f"     data字段缺失: [ERROR]")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:172:31
    |
170 |                             print(f"     items字段存在: [OK]")
171 |                     else:
172 |                         print(f"     data字段缺失: [ERROR]")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
173 |                     return True
174 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\quick_test.py:175:27
    |
173 |                     return True
174 |                 else:
175 |                     print(f"[ERROR] 响应格式错误，缺少'success'字段")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
176 |                     print(f"     Response: {data}")
177 |                     return False
    |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
 --> scripts\run_all_tests.py:5:8
  |
3 | """
4 |
5 | import asyncio
  |        ^^^^^^^
6 | import sys
7 | import subprocess
  |
help: Remove unused import: `asyncio`

F401 [*] `time` imported but unused
  --> scripts\run_tests.py:10:8
   |
 8 | import sys
 9 | import subprocess
10 | import time
   |        ^^^^
11 | from pathlib import Path
   |
help: Remove unused import: `time`

E402 Module level import not at top of file
  --> scripts\setup_115_keys.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\setup_115_keys.py:19:1
   |
18 | from app.core.cloud_key_manager import get_key_manager
19 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\setup_115_keys.py:83:17
   |
81 |     logger.info("")
82 |     logger.info("📁 存储位置:")
83 |     logger.info(f"   加密文件: ~/.vabhub/cloud_keys.encrypted")
   |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
84 |     logger.info(f"   主密钥: ~/.vabhub/.master_key")
85 |     logger.info("")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\setup_115_keys.py:84:17
   |
82 |     logger.info("📁 存储位置:")
83 |     logger.info(f"   加密文件: ~/.vabhub/cloud_keys.encrypted")
84 |     logger.info(f"   主密钥: ~/.vabhub/.master_key")
   |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
85 |     logger.info("")
86 |     logger.info("🔒 安全提示:")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\setup_test_environment.py:65:29
   |
63 |             )
64 |             if response.status_code == 200:
65 |                 logger.info(f"✓ TMDB API密钥已配置")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^
66 |             else:
67 |                 logger.warning(f"✗ TMDB API密钥配置失败: {response.status_code}")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\start.py:19:1
   |
17 |     sys.path.insert(0, str(backend_root))
18 |
19 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.core.database import AsyncSessionLocal
21 | from app.core.cache import get_cache
   |

E402 Module level import not at top of file
  --> scripts\start.py:20:1
   |
19 | from app.core.config import settings
20 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.core.cache import get_cache
22 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\start.py:21:1
   |
19 | from app.core.config import settings
20 | from app.core.database import AsyncSessionLocal
21 | from app.core.cache import get_cache
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from loguru import logger
23 | from sqlalchemy import text
   |

E402 Module level import not at top of file
  --> scripts\start.py:22:1
   |
20 | from app.core.database import AsyncSessionLocal
21 | from app.core.cache import get_cache
22 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
23 | from sqlalchemy import text
   |

E402 Module level import not at top of file
  --> scripts\start.py:23:1
   |
21 | from app.core.cache import get_cache
22 | from loguru import logger
23 | from sqlalchemy import text
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `httpx` imported but unused
 --> scripts\sync_downloader_tasks.py:7:8
  |
6 | import asyncio
7 | import httpx
  |        ^^^^^
8 | import sys
9 | from pathlib import Path
  |
help: Remove unused import: `httpx`

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:17:1
   |
15 | sys.path.insert(0, str(backend_dir))
16 |
17 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.core.downloaders import DownloaderClient, DownloaderType
19 | from app.constants.media_types import MEDIA_TYPE_UNKNOWN
   |

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:18:1
   |
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.core.downloaders import DownloaderClient, DownloaderType
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.constants.media_types import MEDIA_TYPE_UNKNOWN
20 | from app.modules.settings.service import SettingsService
   |

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:19:1
   |
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.core.downloaders import DownloaderClient, DownloaderType
19 | from app.constants.media_types import MEDIA_TYPE_UNKNOWN
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.modules.settings.service import SettingsService
21 | from app.models.download import DownloadTask
   |

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:20:1
   |
18 | from app.core.downloaders import DownloaderClient, DownloaderType
19 | from app.constants.media_types import MEDIA_TYPE_UNKNOWN
20 | from app.modules.settings.service import SettingsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.models.download import DownloadTask
22 | from sqlalchemy import select
   |

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:21:1
   |
19 | from app.constants.media_types import MEDIA_TYPE_UNKNOWN
20 | from app.modules.settings.service import SettingsService
21 | from app.models.download import DownloadTask
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from sqlalchemy import select
   |

E402 Module level import not at top of file
  --> scripts\sync_downloader_tasks.py:22:1
   |
20 | from app.modules.settings.service import SettingsService
21 | from app.models.download import DownloadTask
22 | from sqlalchemy import select
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 |
24 | BASE_URL = "http://localhost:8001/api"
   |

E722 Do not use bare `except`
  --> scripts\sync_downloader_tasks.py:47:17
   |
45 |                 try:
46 |                     host = json.loads(host_raw)
47 |                 except:
   |                 ^^^^^^
48 |                     host = host_raw.strip()
49 |             else:
   |

E722 Do not use bare `except`
  --> scripts\sync_downloader_tasks.py:62:13
   |
60 |             try:
61 |                 port = int(port_raw)
62 |             except:
   |             ^^^^^^
63 |                 port = 8080
64 |         elif isinstance(port_raw, int):
   |

E722 Do not use bare `except`
   --> scripts\sync_downloader_tasks.py:226:17
    |
224 |                 try:
225 |                     host = json.loads(host_raw)
226 |                 except:
    |                 ^^^^^^
227 |                     host = host_raw.strip()
228 |             else:
    |

E722 Do not use bare `except`
   --> scripts\sync_downloader_tasks.py:241:13
    |
239 |             try:
240 |                 port = int(port_raw)
241 |             except:
    |             ^^^^^^
242 |                 port = 9091
243 |         elif isinstance(port_raw, int):
    |

E402 Module level import not at top of file
  --> scripts\test_115_file_operations.py:20:1
   |
18 |     sys.path.insert(0, str(backend_root))
19 |
20 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.core.cloud_key_manager import get_key_manager
22 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_file_operations.py:21:1
   |
20 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
21 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_file_operations.py:22:1
   |
20 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
21 | from app.core.cloud_key_manager import get_key_manager
22 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:19:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from loguru import logger
21 | import qrcode
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:20:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
21 | import qrcode
22 | from io import BytesIO
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:21:1
   |
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
21 | import qrcode
   | ^^^^^^^^^^^^^
22 | from io import BytesIO
23 | import base64
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:22:1
   |
20 | from loguru import logger
21 | import qrcode
22 | from io import BytesIO
   | ^^^^^^^^^^^^^^^^^^^^^^
23 | import base64
   |

E402 Module level import not at top of file
  --> scripts\test_115_qrcode.py:23:1
   |
21 | import qrcode
22 | from io import BytesIO
23 | import base64
   | ^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_115_token_persist.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.modules.cloud_storage.service import CloudStorageService
20 | from app.core.cloud_key_manager import get_key_manager
   |

E402 Module level import not at top of file
  --> scripts\test_115_token_persist.py:19:1
   |
18 | from app.core.database import AsyncSessionLocal
19 | from app.modules.cloud_storage.service import CloudStorageService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.core.cloud_key_manager import get_key_manager
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_token_persist.py:20:1
   |
18 | from app.core.database import AsyncSessionLocal
19 | from app.modules.cloud_storage.service import CloudStorageService
20 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_token_persist.py:21:1
   |
19 | from app.modules.cloud_storage.service import CloudStorageService
20 | from app.core.cloud_key_manager import get_key_manager
21 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\test_115_token_persist.py:92:33
   |
90 |                 provider = service._get_provider(storage)
91 |                 if provider.access_token:
92 |                     logger.info(f"✅ Token已从数据库加载")
   |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^
93 |                     logger.info(f"   Access Token: {provider.access_token[:30]}...")
94 |                     logger.info(f"   User ID: {provider.user_id}")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_115_upload.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_upload.py:19:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_upload.py:20:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_115_user_info.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_115_user_info.py:19:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from loguru import logger
21 | import aiohttp
   |

E402 Module level import not at top of file
  --> scripts\test_115_user_info.py:20:1
   |
18 | from app.core.cloud_storage.providers.cloud_115 import Cloud115Provider
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
21 | import aiohttp
22 | import json
   |

E402 Module level import not at top of file
  --> scripts\test_115_user_info.py:21:1
   |
19 | from app.core.cloud_key_manager import get_key_manager
20 | from loguru import logger
21 | import aiohttp
   | ^^^^^^^^^^^^^^
22 | import json
   |

E402 Module level import not at top of file
  --> scripts\test_115_user_info.py:22:1
   |
20 | from loguru import logger
21 | import aiohttp
22 | import json
   | ^^^^^^^^^^^
   |

E722 Do not use bare `except`
   --> scripts\test_115_user_info.py:109:29
    |
107 |                                 result = json.loads(response_text)
108 |                                 logger.info(f"   JSON解析成功: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
109 |                             except:
    |                             ^^^^^^
110 |                                 logger.warning(f"   响应不是JSON格式")
111 |                 except Exception as e:
    |

F541 [*] f-string without any placeholders
   --> scripts\test_115_user_info.py:110:48
    |
108 |                                 logger.info(f"   JSON解析成功: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
109 |                             except:
110 |                                 logger.warning(f"   响应不是JSON格式")
    |                                                ^^^^^^^^^^^^^^^^^^^^^^
111 |                 except Exception as e:
112 |                     logger.error(f"   请求失败: {e}")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_all_chains.py:18:1
   |
16 |     sys.path.insert(0, str(backend_root))
17 |
18 | from app.chain.manager import get_chain_manager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_all_chains.py:19:1
   |
18 | from app.chain.manager import get_chain_manager
19 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_api_endpoints.py:16:1
   |
14 |     sys.path.insert(0, str(backend_dir))
15 |
16 | from scripts.api_test_config import API_BASE_URL, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | BASE_URL = API_BASE_URL
   |

E722 Do not use bare `except`
  --> scripts\test_api_endpoints.py:50:17
   |
48 |                         if "message" in data:
49 |                             print(f"     Message: {data.get('message')}")
50 |                 except:
   |                 ^^^^^^
51 |                     pass
52 |                 return True
   |

E722 Do not use bare `except`
  --> scripts\test_api_endpoints.py:58:17
   |
56 |                     error_data = response.json()
57 |                     print(f"     Error: {error_data}")
58 |                 except:
   |                 ^^^^^^
59 |                     print(f"     Response: {response.text[:200]}")
60 |                 return False
   |

E402 Module level import not at top of file
  --> scripts\test_architecture.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | from app.core.cache import get_cache, cached
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.health import get_health_checker
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_architecture.py:15:1
   |
14 | from app.core.cache import get_cache, cached
15 | from app.core.health import get_health_checker
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_architecture.py:16:1
   |
14 | from app.core.cache import get_cache, cached
15 | from app.core.health import get_health_checker
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `loguru.logger` imported but unused
  --> scripts\test_architecture.py:16:20
   |
14 | from app.core.cache import get_cache, cached
15 | from app.core.health import get_health_checker
16 | from loguru import logger
   |                    ^^^^^^
   |
help: Remove unused import: `loguru.logger`

E402 Module level import not at top of file
  --> scripts\test_backend_basic.py:15:1
   |
13 | sys.path.insert(0, str(project_root / "backend"))
14 |
15 | import httpx
   | ^^^^^^^^^^^^
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_backend_basic.py:16:1
   |
15 | import httpx
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | from scripts.api_test_config import API_BASE_URL, api_url
   |

E402 Module level import not at top of file
  --> scripts\test_backend_basic.py:18:1
   |
16 | from loguru import logger
17 |
18 | from scripts.api_test_config import API_BASE_URL, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |
20 | # 配置日志
   |

E402 Module level import not at top of file
  --> scripts\test_chart_row_integration.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.charts.service import ChartsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.core.database import AsyncSessionLocal
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_chart_row_integration.py:14:1
   |
13 | from app.modules.charts.service import ChartsService
14 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_chart_row_integration.py:15:1
   |
13 | from app.modules.charts.service import ChartsService
14 | from app.core.database import AsyncSessionLocal
15 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `time` imported but unused
  --> scripts\test_comprehensive.py:10:8
   |
 8 | from pathlib import Path
 9 | import subprocess
10 | import time
   |        ^^^^
11 |
12 | # 添加backend目录到路径
   |
help: Remove unused import: `time`

E402 Module level import not at top of file
  --> scripts\test_douban_fallback.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.media_identification.service import MediaIdentificationService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.core.database import AsyncSessionLocal
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_douban_fallback.py:14:1
   |
13 | from app.modules.media_identification.service import MediaIdentificationService
14 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_douban_fallback.py:15:1
   |
13 | from app.modules.media_identification.service import MediaIdentificationService
14 | from app.core.database import AsyncSessionLocal
15 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\test_douban_fallback.py:62:27
   |
60 |                     year = result.get("year", "未知")
61 |                     
62 |                     print(f"✅ 识别成功")
   |                           ^^^^^^^^^^^^^^
63 |                     print(f"   标题: {title}")
64 |                     print(f"   年份: {year}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_douban_fallback.py:79:35
   |
77 |                             print(f"   ✅ 豆瓣ID: {douban_id}")
78 |                         else:
79 |                             print(f"   ⚠️  缺少豆瓣ID")
   |                                   ^^^^^^^^^^^^^^^^^^^
80 |                         
81 |                         rating = result.get("rating")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_download_chain.py:17:1
   |
15 |     sys.path.insert(0, str(backend_root))
16 |
17 | from app.chain.download import DownloadChain
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_download_chain.py:18:1
   |
17 | from app.chain.download import DownloadChain
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `json` imported but unused
  --> scripts\test_download_features.py:8:8
   |
 6 | import asyncio
 7 | import httpx
 8 | import json
   |        ^^^^
 9 | from typing import Dict, List, Any
10 | from pathlib import Path
   |
help: Remove unused import: `json`

F401 [*] `typing.Dict` imported but unused
  --> scripts\test_download_features.py:9:20
   |
 7 | import httpx
 8 | import json
 9 | from typing import Dict, List, Any
   |                    ^^^^
10 | from pathlib import Path
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.List` imported but unused
  --> scripts\test_download_features.py:9:26
   |
 7 | import httpx
 8 | import json
 9 | from typing import Dict, List, Any
   |                          ^^^^
10 | from pathlib import Path
11 | from loguru import logger
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> scripts\test_download_features.py:9:32
   |
 7 | import httpx
 8 | import json
 9 | from typing import Dict, List, Any
   |                                ^^^
10 | from pathlib import Path
11 | from loguru import logger
   |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\test_extended.py:17:1
   |
15 | sys.path.insert(0, str(project_root))
16 |
17 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `app.core.schemas.BaseResponse` imported but unused
   --> scripts\test_extended.py:108:17
    |
106 |         try:
107 |             from app.core.schemas import (
108 |                 BaseResponse,
    |                 ^^^^^^^^^^^^
109 |                 success_response,
110 |                 error_response,
    |
help: Remove unused import

F401 [*] `app.core.schemas.PaginatedResponse` imported but unused
   --> scripts\test_extended.py:111:17
    |
109 |                 success_response,
110 |                 error_response,
111 |                 PaginatedResponse
    |                 ^^^^^^^^^^^^^^^^^
112 |             )
    |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:12:1
   |
10 | sys.path.insert(0, str(project_root))
11 |
12 | from app.modules.media_identification.service import MediaIdentificationService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
13 | from app.modules.media_renamer.nfo_writer import NFOWriter
14 | from app.modules.fanart import FanartModule
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:13:1
   |
12 | from app.modules.media_identification.service import MediaIdentificationService
13 | from app.modules.media_renamer.nfo_writer import NFOWriter
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.fanart import FanartModule
15 | from app.core.database import AsyncSessionLocal
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:14:1
   |
12 | from app.modules.media_identification.service import MediaIdentificationService
13 | from app.modules.media_renamer.nfo_writer import NFOWriter
14 | from app.modules.fanart import FanartModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:15:1
   |
13 | from app.modules.media_renamer.nfo_writer import NFOWriter
14 | from app.modules.fanart import FanartModule
15 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.core.config import settings
17 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:16:1
   |
14 | from app.modules.fanart import FanartModule
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from loguru import logger
18 | import tempfile
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:17:1
   |
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
17 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
18 | import tempfile
19 | import os
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:18:1
   |
16 | from app.core.config import settings
17 | from loguru import logger
18 | import tempfile
   | ^^^^^^^^^^^^^^^
19 | import os
   |

E402 Module level import not at top of file
  --> scripts\test_fanart_nfo.py:19:1
   |
17 | from loguru import logger
18 | import tempfile
19 | import os
   | ^^^^^^^^^
   |

F841 Local variable `fanart_images_1` is assigned to but never used
  --> scripts\test_fanart_nfo.py:79:9
   |
77 |         import time
78 |         start_time = time.time()
79 |         fanart_images_1 = await fanart_module.obtain_images(
   |         ^^^^^^^^^^^^^^^
80 |             media_type="tv",
81 |             tvdb_id=355730
   |
help: Remove assignment to unused variable `fanart_images_1`

F841 Local variable `fanart_images_2` is assigned to but never used
  --> scripts\test_fanart_nfo.py:86:9
   |
85 |         start_time = time.time()
86 |         fanart_images_2 = await fanart_module.obtain_images(
   |         ^^^^^^^^^^^^^^^
87 |             media_type="tv",
88 |             tvdb_id=355730
   |
help: Remove assignment to unused variable `fanart_images_2`

E722 Do not use bare `except`
   --> scripts\test_fanart_nfo.py:338:9
    |
336 |             shutil.rmtree(temp_dir)
337 |             print(f"\n[OK] 临时目录已清理: {temp_dir}")
338 |         except:
    |         ^^^^^^
339 |             pass
    |

E402 Module level import not at top of file
  --> scripts\test_functional.py:16:1
   |
14 |     sys.path.insert(0, str(backend_dir))
15 |
16 | from scripts.api_test_config import API_BASE_URL, API_PREFIX, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | BASE_URL = API_BASE_URL
   |

F401 [*] `scripts.api_test_config.API_PREFIX` imported but unused
  --> scripts\test_functional.py:16:51
   |
14 |     sys.path.insert(0, str(backend_dir))
15 |
16 | from scripts.api_test_config import API_BASE_URL, API_PREFIX, api_url
   |                                                   ^^^^^^^^^^
17 |
18 | BASE_URL = API_BASE_URL
   |
help: Remove unused import: `scripts.api_test_config.API_PREFIX`

F541 [*] f-string without any placeholders
  --> scripts\test_functional.py:52:23
   |
50 |                 print(f"[OK] 用户注册成功: {response.status_code}")
51 |                 # 注册后需要登录获取token
52 |                 print(f"[INFO] 注册成功，尝试登录获取Token")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
53 |                 return await test_user_login()
54 |             elif response.status_code == 400:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_functional.py:57:27
   |
55 |                 data = response.json()
56 |                 if "已存在" in str(data.get("message", "")) or "USERNAME_EXISTS" in str(data) or "EMAIL_EXISTS" in str(data):
57 |                     print(f"[INFO] 用户已存在，尝试登录")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
58 |                     return await test_user_login()
59 |                 else:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_functional.py:69:15
   |
67 |     except httpx.ConnectError as e:
68 |         print(f"[ERROR] 无法连接到服务: {e}")
69 |         print(f"     请确保后端服务已启动: python backend/run_server.py")
   |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
70 |         return False
71 |     except httpx.ReadTimeout as e:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_functional.py:103:27
    |
101 |                     global auth_token
102 |                     auth_token = data["data"]["access_token"]
103 |                     print(f"     Token已获取")
    |                           ^^^^^^^^^^^^^^^^^^^
104 |                     return True
105 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_functional.py:106:27
    |
104 |                     return True
105 |                 else:
106 |                     print(f"[WARNING] 未获取到Token")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
107 |                     return False
108 |             else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_functional.py:114:15
    |
112 |     except httpx.ConnectError as e:
113 |         print(f"[ERROR] 无法连接到服务: {e}")
114 |         print(f"     请确保后端服务已启动: python backend/run_server.py")
    |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
115 |         return None
116 |     except httpx.ReadTimeout as e:
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_hmac_signature.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.strm.hmac_signer import STRMHMACSigner, get_hmac_signer
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from loguru import logger
   |

F401 [*] `app.modules.strm.hmac_signer.STRMHMACSigner` imported but unused
  --> scripts\test_hmac_signature.py:13:42
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.strm.hmac_signer import STRMHMACSigner, get_hmac_signer
   |                                          ^^^^^^^^^^^^^^
14 | from loguru import logger
   |
help: Remove unused import: `app.modules.strm.hmac_signer.STRMHMACSigner`

E402 Module level import not at top of file
  --> scripts\test_hmac_signature.py:14:1
   |
13 | from app.modules.strm.hmac_signer import STRMHMACSigner, get_hmac_signer
14 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_integration.py:16:1
   |
14 |     sys.path.insert(0, str(backend_dir))
15 |
16 | from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | BASE_URL = API_BASE_URL
   |

F541 [*] f-string without any placeholders
  --> scripts\test_integration.py:56:27
   |
54 |                 if "data" in data and "access_token" in data.get("data", {}):
55 |                     auth_token = data["data"]["access_token"]
56 |                     print(f"[OK] 登录成功，Token已获取")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
57 |                     return True
58 |                 else:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_integration.py:59:27
   |
57 |                     return True
58 |                 else:
59 |                     print(f"[ERROR] 未获取到Token")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^
60 |                     return False
61 |             else:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:105:27
    |
103 |                     print(f"     [OK] 订阅创建成功，ID: {subscription_id}")
104 |                 else:
105 |                     print(f"     [ERROR] 未获取到订阅ID")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
106 |                     return False
107 |             else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:125:27
    |
123 |                     print(f"     [OK] 获取订阅列表成功，数量: {len(items)}")
124 |                 else:
125 |                     print(f"     [ERROR] 订阅列表数据格式错误")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
126 |                     return False
127 |             else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:142:31
    |
140 |                     data = response.json()
141 |                     if "data" in data:
142 |                         print(f"     [OK] 获取订阅详情成功")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
143 |                     else:
144 |                         print(f"     [ERROR] 订阅详情数据格式错误")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:144:31
    |
142 |                         print(f"     [OK] 获取订阅详情成功")
143 |                     else:
144 |                         print(f"     [ERROR] 订阅详情数据格式错误")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
145 |                         return False
146 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:181:27
    |
179 |                 if "data" in data:
180 |                     dashboard_data = data["data"]
181 |                     print(f"[OK] 获取仪表盘数据成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
182 |                     print(f"     数据键: {list(dashboard_data.keys())[:5]}")
183 |                     return True
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:185:27
    |
183 |                     return True
184 |                 else:
185 |                     print(f"[ERROR] 仪表盘数据格式错误")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
186 |                     return False
187 |             else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:226:27
    |
224 |                     return True
225 |                 else:
226 |                     print(f"[ERROR] 设置数据格式错误")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
227 |                     return False
228 |             else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:260:27
    |
258 |                 data = response.json()
259 |                 if "data" in data:
260 |                     print(f"[OK] 搜索成功")
    |                           ^^^^^^^^^^^^^^^^
261 |                     return True
262 |                 else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_integration.py:263:27
    |
261 |                     return True
262 |                 else:
263 |                     print(f"[ERROR] 搜索数据格式错误")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
264 |                     return False
265 |             else:
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_intel_stage1.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.intel.service import get_intel_service, LocalIntelService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_intel_stage1.py:14:1
   |
13 | from app.core.intel.service import get_intel_service, LocalIntelService
14 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `loguru.logger` imported but unused
  --> scripts\test_intel_stage1.py:14:20
   |
13 | from app.core.intel.service import get_intel_service, LocalIntelService
14 | from loguru import logger
   |                    ^^^^^^
   |
help: Remove unused import: `loguru.logger`

F541 [*] f-string without any placeholders
  --> scripts\test_intel_stage1.py:88:19
   |
86 |         if isinstance(intel, LocalIntelService):
87 |             await intel._ensure_loaded()
88 |             print(f"  [OK] 数据加载完成")
   |                   ^^^^^^^^^^^^^^^^^^^^^^
89 |             print(f"  [INFO] 别名数量: {len(intel._aliases)}")
90 |             print(f"  [INFO] 索引数量: {len(intel._index)}")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_intel_stage3.py:13:1
   |
11 |   sys.path.insert(0, str(project_root))
12 |
13 | / from app.core.intel.service import (
14 | |     get_intel_service,
15 | |     LocalIntelService,
16 | |     CloudIntelService,
17 | |     HybridIntelService,
18 | | )
   | |_^
19 |   from app.core.config import settings
20 |   from loguru import logger
   |

F401 [*] `app.core.intel.service.get_intel_service` imported but unused
  --> scripts\test_intel_stage3.py:14:5
   |
13 | from app.core.intel.service import (
14 |     get_intel_service,
   |     ^^^^^^^^^^^^^^^^^
15 |     LocalIntelService,
16 |     CloudIntelService,
   |
help: Remove unused import: `app.core.intel.service.get_intel_service`

E402 Module level import not at top of file
  --> scripts\test_intel_stage3.py:19:1
   |
17 |     HybridIntelService,
18 | )
19 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_intel_stage3.py:20:1
   |
18 | )
19 | from app.core.config import settings
20 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `loguru.logger` imported but unused
  --> scripts\test_intel_stage3.py:20:20
   |
18 | )
19 | from app.core.config import settings
20 | from loguru import logger
   |                    ^^^^^^
   |
help: Remove unused import: `loguru.logger`

F541 [*] f-string without any placeholders
  --> scripts\test_intel_stage3.py:34:15
   |
32 |     try:
33 |         cloud_intel = CloudIntelService()
34 |         print(f"  [OK] CloudIntelService创建成功")
   |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
35 |         print(f"  [INFO] Intel端点: {settings.INTEL_INTEL_ENDPOINT}")
36 |     except Exception as e:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_intel_stage3.py:87:15
   |
85 |         cloud = CloudIntelService()
86 |         hybrid = HybridIntelService(local=local, cloud=cloud)
87 |         print(f"  [OK] HybridIntelService创建成功")
   |               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
88 |         print(f"  [INFO] 降级配置: {settings.INTEL_FALLBACK_TO_LOCAL}")
89 |     except Exception as e:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_intel_stage3.py:100:19
    |
 98 |         if result:
 99 |             print(f"  [OK] 返回结果: {result}")
100 |             print(f"  [INFO] 来源: 本地（云端不可用，自动降级）")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
101 |         else:
102 |             print("  [WARN] 返回None（本地和云端都无数据）")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_intel_stage3.py:115:19
    |
113 |         if result.get("sites"):
114 |             print(f"  [INFO] 找到 {len(result.get('sites', []))} 个站点")
115 |             print(f"  [INFO] 来源: 本地（云端不可用，自动降级）")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
116 |         else:
117 |             print("  [INFO] 无站点数据（本地和云端都无数据）")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_intel_stage3.py:219:11
    |
217 |     print("=" * 60)
218 |     print()
219 |     print(f"当前配置:")
    |           ^^^^^^^^^^^^
220 |     print(f"  INTEL_ENABLED: {settings.INTEL_ENABLED}")
221 |     print(f"  INTEL_MODE: {settings.INTEL_MODE}")
    |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> scripts\test_legacy_adapter.py:7:8
  |
6 | import sys
7 | import os
  |        ^^
8 | from pathlib import Path
  |
help: Remove unused import: `os`

E402 Module level import not at top of file
  --> scripts\test_legacy_adapter.py:14:1
   |
12 | sys.path.insert(0, str(project_root / "VabHub" / "backend"))
13 |
14 | from app.core.legacy_validator import validate_legacy_functions
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.legacy_adapter import get_legacy_adapter
   |

E402 Module level import not at top of file
  --> scripts\test_legacy_adapter.py:15:1
   |
14 | from app.core.legacy_validator import validate_legacy_functions
15 | from app.core.legacy_adapter import get_legacy_adapter
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_media_bangumi_api.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.utils.http_client import create_httpx_client
15 | from loguru import logger
   |

F401 [*] `app.core.config.settings` imported but unused
  --> scripts\test_media_bangumi_api.py:13:29
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.config import settings
   |                             ^^^^^^^^
14 | from app.utils.http_client import create_httpx_client
15 | from loguru import logger
   |
help: Remove unused import: `app.core.config.settings`

E402 Module level import not at top of file
  --> scripts\test_media_bangumi_api.py:14:1
   |
13 | from app.core.config import settings
14 | from app.utils.http_client import create_httpx_client
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_media_bangumi_api.py:15:1
   |
13 | from app.core.config import settings
14 | from app.utils.http_client import create_httpx_client
15 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
16 |
17 | # 用户提供的TMDB API key
   |

F541 [*] f-string without any placeholders
   --> scripts\test_media_bangumi_api.py:109:19
    |
107 |         if movie_details and movie_details.get('similar'):
108 |             similar = movie_details.get('similar', {}).get('results', [])
109 |             print(f"[OK] 类似推荐获取成功")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^
110 |             print(f"   - 推荐数量: {len(similar)}")
111 |             if len(similar) > 0:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_media_bangumi_api.py:179:23
    |
177 |             calendar = await bangumi_client.get_calendar()
178 |             if calendar:
179 |                 print(f"[OK] 每日放送获取成功")
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^
180 |                 # 按星期分组
181 |                 weekday_groups = {}
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_media_bangumi_api.py:205:23
    |
203 |             popular = await bangumi_client.get_popular_anime(limit=10)
204 |             if popular:
205 |                 print(f"[OK] 热门动漫获取成功")
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^
206 |                 print(f"   - 数量: {len(popular)}")
207 |                 if len(popular) > 0:
    |
help: Remove extraneous `f` prefix

F401 [*] `json` imported but unused
 --> scripts\test_monitoring_api.py:7:8
  |
5 | import asyncio
6 | import httpx
7 | import json
  |        ^^^^
  |
help: Remove unused import: `json`

F541 [*] f-string without any placeholders
  --> scripts\test_monitoring_api.py:28:27
   |
26 |                     data = response.json()
27 |                     resources = data.get("data", {})
28 |                     print(f"  [OK] 系统资源获取成功")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
29 |                     print(f"    CPU使用率: {resources.get('cpu', {}).get('usage_percent', 0)}%")
30 |                     print(f"    内存使用率: {resources.get('memory', {}).get('usage_percent', 0)}%")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_monitoring_api.py:48:27
   |
46 |                     metrics = data.get("data", {})
47 |                     summary = metrics.get("summary", {})
48 |                     print(f"  [OK] API性能指标获取成功")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
49 |                     print(f"    总请求数: {summary.get('total_requests', 0)}")
50 |                     print(f"    总错误数: {summary.get('total_errors', 0)}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_monitoring_api.py:66:27
   |
64 |                     data = response.json()
65 |                     statistics = data.get("data", {})
66 |                     print(f"  [OK] 统计信息获取成功")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
67 |                     cpu_stats = statistics.get("cpu", {})
68 |                     print(f"    CPU统计: 平均={cpu_stats.get('avg', 0)}%")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_multimodal.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | from app.modules.multimodal.video_analyzer import VideoAnalyzer
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.multimodal.audio_analyzer import AudioAnalyzer
16 | from app.modules.multimodal.text_analyzer import TextAnalyzer
   |

E402 Module level import not at top of file
  --> scripts\test_multimodal.py:15:1
   |
14 | from app.modules.multimodal.video_analyzer import VideoAnalyzer
15 | from app.modules.multimodal.audio_analyzer import AudioAnalyzer
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.multimodal.text_analyzer import TextAnalyzer
17 | from app.modules.multimodal.fusion import MultimodalFeatureFusion
   |

E402 Module level import not at top of file
  --> scripts\test_multimodal.py:16:1
   |
14 | from app.modules.multimodal.video_analyzer import VideoAnalyzer
15 | from app.modules.multimodal.audio_analyzer import AudioAnalyzer
16 | from app.modules.multimodal.text_analyzer import TextAnalyzer
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.modules.multimodal.fusion import MultimodalFeatureFusion
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_multimodal.py:17:1
   |
15 | from app.modules.multimodal.audio_analyzer import AudioAnalyzer
16 | from app.modules.multimodal.text_analyzer import TextAnalyzer
17 | from app.modules.multimodal.fusion import MultimodalFeatureFusion
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_multimodal.py:18:1
   |
16 | from app.modules.multimodal.text_analyzer import TextAnalyzer
17 | from app.modules.multimodal.fusion import MultimodalFeatureFusion
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `os` imported but unused
  --> scripts\test_music_minimal.py:11:8
   |
 9 | import argparse
10 | import asyncio
11 | import os
   |        ^^
12 | import sys
13 | from pathlib import Path
   |
help: Remove unused import: `os`

E402 Module level import not at top of file
  --> scripts\test_music_minimal.py:22:1
   |
20 |     sys.path.insert(0, str(backend_dir))
21 |
22 | from scripts.api_test_config import API_BASE_URL, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `typing.List` imported but unused
  --> scripts\test_new_endpoints.py:9:26
   |
 7 | import httpx
 8 | import json
 9 | from typing import Dict, List, Any
   |                          ^^^^
10 | from loguru import logger
   |
help: Remove unused import: `typing.List`

E722 Do not use bare `except`
   --> scripts\test_new_endpoints.py:217:13
    |
215 |             try:
216 |                 result["response"] = response.json()
217 |             except:
    |             ^^^^^^
218 |                 result["response"] = response.text[:200]  # 限制长度
    |

E402 Module level import not at top of file
  --> scripts\test_new_features.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | import httpx
   | ^^^^^^^^^^^^
14 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_new_features.py:14:1
   |
13 | import httpx
14 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
15 |
16 | from scripts.api_test_config import API_BASE_URL, api_url
   |

E402 Module level import not at top of file
  --> scripts\test_new_features.py:16:1
   |
14 | from loguru import logger
15 |
16 | from scripts.api_test_config import API_BASE_URL, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | # API基础URL
   |

E402 Module level import not at top of file
  --> scripts\test_performance.py:18:1
   |
16 |     sys.path.insert(0, str(backend_dir))
17 |
18 | from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 |
20 | BASE_URL = API_BASE_URL
   |

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:114:11
    |
113 |     print(f"\n测试端点: {endpoint}")
114 |     print(f"迭代次数: 20")
    |           ^^^^^^^^^^^^^^^
115 |     
116 |     result = await test_response_time(endpoint, "GET", headers, iterations=20)
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:119:15
    |
118 |     if result:
119 |         print(f"\n结果:")
    |               ^^^^^^^^^^
120 |         print(f"  平均响应时间: {result['mean']:.2f} ms")
121 |         print(f"  中位数响应时间: {result['median']:.2f} ms")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:129:19
    |
127 |         # 分析缓存效果
128 |         if result['max'] / result['min'] > 2:
129 |             print(f"  [INFO] 响应时间变化较大，可能缓存未生效")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130 |         else:
131 |             print(f"  [INFO] 响应时间较稳定，缓存可能生效")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:131:19
    |
129 |             print(f"  [INFO] 响应时间变化较大，可能缓存未生效")
130 |         else:
131 |             print(f"  [INFO] 响应时间较稳定，缓存可能生效")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
132 |     
133 |     return result
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:153:11
    |
152 |     print(f"\n测试端点: {endpoint}")
153 |     print(f"迭代次数: 10")
    |           ^^^^^^^^^^^^^^^
154 |     
155 |     result = await test_response_time(endpoint, "GET", headers, iterations=10)
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:158:15
    |
157 |     if result:
158 |         print(f"\n结果:")
    |               ^^^^^^^^^^
159 |         print(f"  平均响应时间: {result['mean']:.2f} ms")
160 |         print(f"  中位数响应时间: {result['median']:.2f} ms")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:168:19
    |
166 |         # 性能评估
167 |         if result['mean'] < 100:
168 |             print(f"  [OK] 响应时间优秀 (< 100ms)")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
169 |         elif result['mean'] < 500:
170 |             print(f"  [OK] 响应时间良好 (< 500ms)")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:170:19
    |
168 |             print(f"  [OK] 响应时间优秀 (< 100ms)")
169 |         elif result['mean'] < 500:
170 |             print(f"  [OK] 响应时间良好 (< 500ms)")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
171 |         else:
172 |             print(f"  [WARNING] 响应时间较慢 (> 500ms)")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:172:19
    |
170 |             print(f"  [OK] 响应时间良好 (< 500ms)")
171 |         else:
172 |             print(f"  [WARNING] 响应时间较慢 (> 500ms)")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
173 |     
174 |     return result
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:242:15
    |
241 |     if results.get("cache"):
242 |         print(f"\n缓存性能:")
    |               ^^^^^^^^^^^^^^
243 |         print(f"  平均响应时间: {results['cache']['mean']:.2f} ms")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:246:15
    |
245 |     if results.get("database"):
246 |         print(f"\n数据库查询性能:")
    |               ^^^^^^^^^^^^^^^^^^^^
247 |         print(f"  平均响应时间: {results['database']['mean']:.2f} ms")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_performance.py:250:15
    |
249 |     if results.get("endpoints"):
250 |         print(f"\nAPI端点性能:")
    |               ^^^^^^^^^^^^^^^^^
251 |         for result in results["endpoints"]:
252 |             print(f"  {result['endpoint']}: {result['mean']:.2f} ms")
    |
help: Remove extraneous `f` prefix

F401 [*] `typing.List` imported but unused
  --> scripts\test_reading_recent_commands.py:11:20
   |
 9 | import os
10 | from datetime import datetime, timedelta
11 | from typing import List
   |                    ^^^^
12 |
13 | # 添加项目路径
   |
help: Remove unused import: `typing.List`

F401 [*] `app.modules.bots.telegram_bot_state.UserReadingActivityState` imported but unused
  --> scripts\test_reading_recent_commands.py:16:73
   |
14 | sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
15 |
16 | from app.modules.bots.telegram_bot_state import reading_activity_cache, UserReadingActivityState
   |                                                                         ^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.schemas.reading_hub import ReadingActivityItem
18 | from app.models.enums.reading_media_type import ReadingMediaType
   |
help: Remove unused import: `app.modules.bots.telegram_bot_state.UserReadingActivityState`

F541 [*] f-string without any placeholders
  --> scripts\test_reading_recent_commands.py:51:37
   |
49 |         else:
50 |             assert result != "未知时间", f"Expected not '未知时间', got '{result}'"
51 |             assert len(result) > 0, f"Expected non-empty result"
   |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
52 |     
53 |     print("✅ 相对时间格式化测试通过\n")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_reading_recent_commands.py:106:55
    |
104 |         # 验证格式
105 |         assert formatted.startswith(f"[{idx}]"), f"Expected to start with '[{idx}]'"
106 |         assert "《" in formatted and "》" in formatted, f"Expected title brackets"
    |                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
107 |         assert "·" in formatted, f"Expected separator"
108 |         assert len(formatted) > 20, f"Expected reasonable length"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_reading_recent_commands.py:107:34
    |
105 |         assert formatted.startswith(f"[{idx}]"), f"Expected to start with '[{idx}]'"
106 |         assert "《" in formatted and "》" in formatted, f"Expected title brackets"
107 |         assert "·" in formatted, f"Expected separator"
    |                                  ^^^^^^^^^^^^^^^^^^^^^
108 |         assert len(formatted) > 20, f"Expected reasonable length"
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_reading_recent_commands.py:108:37
    |
106 |         assert "《" in formatted and "》" in formatted, f"Expected title brackets"
107 |         assert "·" in formatted, f"Expected separator"
108 |         assert len(formatted) > 20, f"Expected reasonable length"
    |                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
109 |     
110 |     print("✅ 活动条目格式化测试通过\n")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_real_site.py:16:1
   |
14 | sys.path.insert(0, str(project_root))
15 |
16 | from app.modules.site_profile.service import SiteProfileService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.modules.site_profile.verifier import SiteVerifier
18 | from app.modules.site_profile.parser import SiteParser
   |

E402 Module level import not at top of file
  --> scripts\test_real_site.py:17:1
   |
16 | from app.modules.site_profile.service import SiteProfileService
17 | from app.modules.site_profile.verifier import SiteVerifier
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.modules.site_profile.parser import SiteParser
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_real_site.py:18:1
   |
16 | from app.modules.site_profile.service import SiteProfileService
17 | from app.modules.site_profile.verifier import SiteVerifier
18 | from app.modules.site_profile.parser import SiteParser
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_real_site.py:19:1
   |
17 | from app.modules.site_profile.verifier import SiteVerifier
18 | from app.modules.site_profile.parser import SiteParser
19 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\test_real_site.py:48:19
   |
46 |         if profile:
47 |             meta = profile.get("meta", {})
48 |             print(f"[OK] 站点识别成功!")
   |                   ^^^^^^^^^^^^^^^^^^^^^
49 |             print(f"  配置文件ID: {meta.get('id')}")
50 |             print(f"  站点名称: {meta.get('name')}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_real_site.py:130:23
    |
128 |             print(f"[OK] 解析成功! 找到 {len(items)} 个种子")
129 |             if items:
130 |                 print(f"[INFO] 第一个种子示例:")
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^
131 |                 first_item = items[0]
132 |                 for key, value in first_item.items():
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_register.py:15:1
   |
13 |     sys.path.insert(0, str(backend_dir))
14 |
15 | from scripts.api_test_config import API_BASE_URL, api_url
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 |
17 | async def test_register():
   |

F841 Local variable `BASE_URL` is assigned to but never used
  --> scripts\test_register.py:19:5
   |
17 | async def test_register():
18 |     """测试用户注册"""
19 |     BASE_URL = API_BASE_URL
   |     ^^^^^^^^
20 |     
21 |     # 测试新用户注册
   |
help: Remove assignment to unused variable `BASE_URL`

E402 Module level import not at top of file
  --> scripts\test_search_intel_integration.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.search.service import SearchService
15 | from app.core.config import settings
   |

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> scripts\test_search_intel_integration.py:13:36
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
   |                                    ^^^^^^^^^^^^
14 | from app.modules.search.service import SearchService
15 | from app.core.config import settings
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

E402 Module level import not at top of file
  --> scripts\test_search_intel_integration.py:14:1
   |
13 | from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
14 | from app.modules.search.service import SearchService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.config import settings
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_search_intel_integration.py:15:1
   |
13 | from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
14 | from app.modules.search.service import SearchService
15 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_search_intel_integration.py:16:1
   |
14 | from app.modules.search.service import SearchService
15 | from app.core.config import settings
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `loguru.logger` imported but unused
  --> scripts\test_search_intel_integration.py:16:20
   |
14 | from app.modules.search.service import SearchService
15 | from app.core.config import settings
16 | from loguru import logger
   |                    ^^^^^^
   |
help: Remove unused import: `loguru.logger`

F541 [*] f-string without any placeholders
  --> scripts\test_search_intel_integration.py:26:11
   |
24 |     print()
25 |     
26 |     print(f"当前配置:")
   |           ^^^^^^^^^^^^
27 |     print(f"  INTEL_ENABLED: {settings.INTEL_ENABLED}")
28 |     print(f"  INTEL_MODE: {settings.INTEL_MODE}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_search_intel_integration.py:61:23
   |
59 |                 )
60 |                 print(f"  [OK] 搜索完成，返回 {len(results)} 条结果")
61 |                 print(f"  [INFO] Intel服务已集成到搜索流程")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
62 |             except Exception as e:
63 |                 print(f"  [WARN] 搜索测试失败（可能是搜索引擎未配置）: {e}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_search_intel_integration.py:64:23
   |
62 |             except Exception as e:
63 |                 print(f"  [WARN] 搜索测试失败（可能是搜索引擎未配置）: {e}")
64 |                 print(f"  [INFO] 但Intel服务集成正常（已注入到SearchService）")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
65 |             print()
   |
help: Remove extraneous `f` prefix

F401 [*] `asyncio` imported but unused
  --> scripts\test_secret_manager.py:9:8
   |
 7 | import sys
 8 | import json
 9 | import asyncio
   |        ^^^^^^^
10 | from pathlib import Path
11 | from typing import Dict, Optional
   |
help: Remove unused import: `asyncio`

F401 [*] `typing.Dict` imported but unused
  --> scripts\test_secret_manager.py:11:20
   |
 9 | import asyncio
10 | from pathlib import Path
11 | from typing import Dict, Optional
   |                    ^^^^
12 |
13 | # 添加项目根目录到路径
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> scripts\test_secret_manager.py:11:26
   |
 9 | import asyncio
10 | from pathlib import Path
11 | from typing import Dict, Optional
   |                          ^^^^^^^^
12 |
13 | # 添加项目根目录到路径
   |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\test_secret_manager.py:17:1
   |
15 | sys.path.insert(0, str(project_root))
16 |
17 | from app.core.secret_manager import SecretManager, get_secret_manager, initialize_secrets
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.core.config import settings
   |

F401 [*] `app.core.secret_manager.get_secret_manager` imported but unused
  --> scripts\test_secret_manager.py:17:52
   |
15 | sys.path.insert(0, str(project_root))
16 |
17 | from app.core.secret_manager import SecretManager, get_secret_manager, initialize_secrets
   |                                                    ^^^^^^^^^^^^^^^^^^
18 | from app.core.config import settings
   |
help: Remove unused import: `app.core.secret_manager.get_secret_manager`

E402 Module level import not at top of file
  --> scripts\test_secret_manager.py:18:1
   |
17 | from app.core.secret_manager import SecretManager, get_secret_manager, initialize_secrets
18 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F841 Local variable `original_secrets` is assigned to but never used
  --> scripts\test_secret_manager.py:46:13
   |
44 |         # 保存原始密钥用于后续测试
45 |         with open(secrets_file, 'r', encoding='utf-8') as f:
46 |             original_secrets = json.load(f)
   |             ^^^^^^^^^^^^^^^^
47 |         print(f"备份现有密钥文件: {secrets_file}")
48 |         secrets_file.unlink()
   |
help: Remove assignment to unused variable `original_secrets`

E722 Do not use bare `except`
  --> scripts\test_simple.py:22:5
   |
20 |         sys.stdout.reconfigure(encoding='utf-8', errors='replace')
21 |         sys.stderr.reconfigure(encoding='utf-8', errors='replace')
22 |     except:
   |     ^^^^^^
23 |         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
24 |         sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
   |

F541 [*] f-string without any placeholders
  --> scripts\test_simple.py:74:23
   |
72 |             if response.status_code == 200:
73 |                 print("[OK] API文档可访问")
74 |                 print(f"  URL: http://localhost:8000/docs")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
75 |                 return True
76 |             else:
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:15:1
   |
13 | sys.path.insert(0, str(project_root))
14 |
15 | from sqlalchemy.ext.asyncio import AsyncSession
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.core.database import AsyncSessionLocal, init_db
17 | from app.models.site import Site
   |

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> scripts\test_site_domain_and_logo.py:15:36
   |
13 | sys.path.insert(0, str(project_root))
14 |
15 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
16 | from app.core.database import AsyncSessionLocal, init_db
17 | from app.models.site import Site
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:16:1
   |
15 | from sqlalchemy.ext.asyncio import AsyncSession
16 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.models.site import Site
18 | from app.modules.site_domain.service import SiteDomainService
   |

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:17:1
   |
15 | from sqlalchemy.ext.asyncio import AsyncSession
16 | from app.core.database import AsyncSessionLocal, init_db
17 | from app.models.site import Site
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.modules.site_domain.service import SiteDomainService
19 | from app.modules.site_icon.service import SiteIconService
   |

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:18:1
   |
16 | from app.core.database import AsyncSessionLocal, init_db
17 | from app.models.site import Site
18 | from app.modules.site_domain.service import SiteDomainService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.modules.site_icon.service import SiteIconService
20 | from app.modules.site_icon.resource_loader import SiteLogoResourceLoader
   |

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:19:1
   |
17 | from app.models.site import Site
18 | from app.modules.site_domain.service import SiteDomainService
19 | from app.modules.site_icon.service import SiteIconService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.modules.site_icon.resource_loader import SiteLogoResourceLoader
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:20:1
   |
18 | from app.modules.site_domain.service import SiteDomainService
19 | from app.modules.site_icon.service import SiteIconService
20 | from app.modules.site_icon.resource_loader import SiteLogoResourceLoader
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_site_domain_and_logo.py:21:1
   |
19 | from app.modules.site_icon.service import SiteIconService
20 | from app.modules.site_icon.resource_loader import SiteLogoResourceLoader
21 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:16:1
   |
14 | sys.path.insert(0, str(project_root))
15 |
16 | from sqlalchemy.ext.asyncio import AsyncSession
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.models.site import Site
   |

F401 [*] `sqlalchemy.ext.asyncio.AsyncSession` imported but unused
  --> scripts\test_site_profile_system.py:16:36
   |
14 | sys.path.insert(0, str(project_root))
15 |
16 | from sqlalchemy.ext.asyncio import AsyncSession
   |                                    ^^^^^^^^^^^^
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.models.site import Site
   |
help: Remove unused import: `sqlalchemy.ext.asyncio.AsyncSession`

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:17:1
   |
16 | from sqlalchemy.ext.asyncio import AsyncSession
17 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.models.site import Site
19 | from app.modules.site_profile.loader import SiteProfileLoader
   |

F401 [*] `app.core.database.AsyncSessionLocal` imported but unused
  --> scripts\test_site_profile_system.py:17:31
   |
16 | from sqlalchemy.ext.asyncio import AsyncSession
17 | from app.core.database import AsyncSessionLocal, init_db
   |                               ^^^^^^^^^^^^^^^^^
18 | from app.models.site import Site
19 | from app.modules.site_profile.loader import SiteProfileLoader
   |
help: Remove unused import

F401 [*] `app.core.database.init_db` imported but unused
  --> scripts\test_site_profile_system.py:17:50
   |
16 | from sqlalchemy.ext.asyncio import AsyncSession
17 | from app.core.database import AsyncSessionLocal, init_db
   |                                                  ^^^^^^^
18 | from app.models.site import Site
19 | from app.modules.site_profile.loader import SiteProfileLoader
   |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:18:1
   |
16 | from sqlalchemy.ext.asyncio import AsyncSession
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.models.site import Site
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.modules.site_profile.loader import SiteProfileLoader
20 | from app.modules.site_profile.verifier import SiteVerifier
   |

F401 [*] `app.models.site.Site` imported but unused
  --> scripts\test_site_profile_system.py:18:29
   |
16 | from sqlalchemy.ext.asyncio import AsyncSession
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.models.site import Site
   |                             ^^^^
19 | from app.modules.site_profile.loader import SiteProfileLoader
20 | from app.modules.site_profile.verifier import SiteVerifier
   |
help: Remove unused import: `app.models.site.Site`

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:19:1
   |
17 | from app.core.database import AsyncSessionLocal, init_db
18 | from app.models.site import Site
19 | from app.modules.site_profile.loader import SiteProfileLoader
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
20 | from app.modules.site_profile.verifier import SiteVerifier
21 | from app.modules.site_profile.parser import SiteParser
   |

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:20:1
   |
18 | from app.models.site import Site
19 | from app.modules.site_profile.loader import SiteProfileLoader
20 | from app.modules.site_profile.verifier import SiteVerifier
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 | from app.modules.site_profile.parser import SiteParser
22 | from app.modules.site_profile.service import SiteProfileService
   |

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:21:1
   |
19 | from app.modules.site_profile.loader import SiteProfileLoader
20 | from app.modules.site_profile.verifier import SiteVerifier
21 | from app.modules.site_profile.parser import SiteParser
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
22 | from app.modules.site_profile.service import SiteProfileService
23 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:22:1
   |
20 | from app.modules.site_profile.verifier import SiteVerifier
21 | from app.modules.site_profile.parser import SiteParser
22 | from app.modules.site_profile.service import SiteProfileService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
23 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_site_profile_system.py:23:1
   |
21 | from app.modules.site_profile.parser import SiteParser
22 | from app.modules.site_profile.service import SiteProfileService
23 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\test_site_profile_system.py:87:11
   |
85 |     # 注意：实际识别需要访问真实站点，这里只测试逻辑
86 |     print("[INFO] 站点识别需要访问真实站点，跳过实际验证")
87 |     print(f"[OK] 站点识别服务初始化成功")
   |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
88 |     
89 |     # 测试获取站点类型
   |
help: Remove extraneous `f` prefix

F841 Local variable `verifier` is assigned to but never used
   --> scripts\test_site_profile_system.py:101:5
    |
100 |     # 创建验证器（使用测试URL）
101 |     verifier = SiteVerifier("https://test.example.com")
    |     ^^^^^^^^
102 |     
103 |     # 测试规则配置
    |
help: Remove assignment to unused variable `verifier`

E402 Module level import not at top of file
  --> scripts\test_speed_limit.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.download.service import DownloadService
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_speed_limit.py:14:1
   |
13 | from app.core.database import AsyncSessionLocal, init_db
14 | from app.modules.download.service import DownloadService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_speed_limit.py:15:1
   |
13 | from app.core.database import AsyncSessionLocal, init_db
14 | from app.modules.download.service import DownloadService
15 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
16 |
17 | async def test_speed_limit():
   |

F401 [*] `json` imported but unused
 --> scripts\test_sse_search.py:7:8
  |
5 | import asyncio
6 | import sys
7 | import json
  |        ^^^^
8 | from pathlib import Path
  |
help: Remove unused import: `json`

E402 Module level import not at top of file
  --> scripts\test_sse_search.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.search.service import SearchService
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_sse_search.py:15:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.modules.search.service import SearchService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_sse_search.py:16:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.modules.search.service import SearchService
16 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | async def test_sse_search():
   |

E402 Module level import not at top of file
  --> scripts\test_storage_chain.py:17:1
   |
15 |     sys.path.insert(0, str(backend_root))
16 |
17 | from app.chain.storage import StorageChain
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_storage_chain.py:18:1
   |
17 | from app.chain.storage import StorageChain
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `os` imported but unused
 --> scripts\test_strm_system.py:6:8
  |
4 | """
5 |
6 | import os
  |        ^^
7 | import sys
8 | import asyncio
  |
help: Remove unused import: `os`

F401 [*] `typing.Dict` imported but unused
  --> scripts\test_strm_system.py:10:20
   |
 8 | import asyncio
 9 | from pathlib import Path
10 | from typing import Dict, Any, Optional
   |                    ^^^^
11 |
12 | # 添加项目根目录到路径
   |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
  --> scripts\test_strm_system.py:10:26
   |
 8 | import asyncio
 9 | from pathlib import Path
10 | from typing import Dict, Any, Optional
   |                          ^^^
11 |
12 | # 添加项目根目录到路径
   |
help: Remove unused import

F401 [*] `typing.Optional` imported but unused
  --> scripts\test_strm_system.py:10:31
   |
 8 | import asyncio
 9 | from pathlib import Path
10 | from typing import Dict, Any, Optional
   |                               ^^^^^^^^
11 |
12 | # 添加项目根目录到路径
   |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\test_strm_system.py:16:1
   |
14 | sys.path.insert(0, str(project_root))
15 |
16 | from app.modules.strm.config import STRMConfig
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.modules.strm.generator import STRMGenerator
18 | from app.core.database import AsyncSessionLocal, init_db, close_db
   |

E402 Module level import not at top of file
  --> scripts\test_strm_system.py:17:1
   |
16 | from app.modules.strm.config import STRMConfig
17 | from app.modules.strm.generator import STRMGenerator
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from app.core.database import AsyncSessionLocal, init_db, close_db
19 | from app.core.config import settings
   |

E402 Module level import not at top of file
  --> scripts\test_strm_system.py:18:1
   |
16 | from app.modules.strm.config import STRMConfig
17 | from app.modules.strm.generator import STRMGenerator
18 | from app.core.database import AsyncSessionLocal, init_db, close_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
19 | from app.core.config import settings
   |

E402 Module level import not at top of file
  --> scripts\test_strm_system.py:19:1
   |
17 | from app.modules.strm.generator import STRMGenerator
18 | from app.core.database import AsyncSessionLocal, init_db, close_db
19 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F841 Local variable `has_token` is assigned to but never used
  --> scripts\test_strm_system.py:88:17
   |
86 |                 # 检查是否包含local_redirect URL
87 |                 has_redirect_url = "api/strm/stream" in strm_content
88 |                 has_token = "TOKEN" in strm_content or len(strm_content.split("/")) > 5
   |                 ^^^^^^^^^
89 |                 passed_2 = has_redirect_url
90 |                 print_result("STRM文件内容", passed_2, f"内容: {strm_content[:100]}...")
   |
help: Remove assignment to unused variable `has_token`

F841 Local variable `config` is assigned to but never used
   --> scripts\test_strm_system.py:135:9
    |
134 |         # 创建STRM配置
135 |         config = STRMConfig()
    |         ^^^^^^
136 |         
137 |         # 创建测试pickcode和token
    |
help: Remove assignment to unused variable `config`

F841 Local variable `passed_3` is assigned to but never used
   --> scripts\test_strm_system.py:194:17
    |
192 |                     print_result("115 API客户端获取", True, "未配置115（跳过）")
193 |             except Exception as e:
194 |                 passed_3 = True  # 如果没有配置115，不算失败
    |                 ^^^^^^^^
195 |                 print_result("115 API客户端获取", True, f"未配置115: {e}")
    |
help: Remove assignment to unused variable `passed_3`

F841 Local variable `test_media_info` is assigned to but never used
   --> scripts\test_strm_system.py:222:13
    |
220 |             # 测试数据
221 |             test_pickcode = "test_pickcode_storage_67890"
222 |             test_media_info = {
    |             ^^^^^^^^^^^^^^^
223 |                 "type": "tv",
224 |                 "title": "测试电视剧",
    |
help: Remove assignment to unused variable `test_media_info`

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.strm.task_manager import get_sync_task_manager, SyncTaskStatus
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.strm.sync_manager import STRMSyncManager
15 | from app.modules.strm.config import STRMConfig
   |

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:14:1
   |
13 | from app.modules.strm.task_manager import get_sync_task_manager, SyncTaskStatus
14 | from app.modules.strm.sync_manager import STRMSyncManager
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
   |

F401 [*] `app.modules.strm.sync_manager.STRMSyncManager` imported but unused
  --> scripts\test_strm_task_manager.py:14:43
   |
13 | from app.modules.strm.task_manager import get_sync_task_manager, SyncTaskStatus
14 | from app.modules.strm.sync_manager import STRMSyncManager
   |                                           ^^^^^^^^^^^^^^^
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
   |
help: Remove unused import: `app.modules.strm.sync_manager.STRMSyncManager`

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:15:1
   |
13 | from app.modules.strm.task_manager import get_sync_task_manager, SyncTaskStatus
14 | from app.modules.strm.sync_manager import STRMSyncManager
15 | from app.modules.strm.config import STRMConfig
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
17 | from app.core.database import AsyncSessionLocal
   |

F401 [*] `app.modules.strm.config.STRMConfig` imported but unused
  --> scripts\test_strm_task_manager.py:15:37
   |
13 | from app.modules.strm.task_manager import get_sync_task_manager, SyncTaskStatus
14 | from app.modules.strm.sync_manager import STRMSyncManager
15 | from app.modules.strm.config import STRMConfig
   |                                     ^^^^^^^^^^
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
17 | from app.core.database import AsyncSessionLocal
   |
help: Remove unused import: `app.modules.strm.config.STRMConfig`

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:16:1
   |
14 | from app.modules.strm.sync_manager import STRMSyncManager
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.core.database import AsyncSessionLocal
18 | from loguru import logger
   |

F401 [*] `app.modules.strm.file_operation_mode.STRMSyncConfig` imported but unused
  --> scripts\test_strm_task_manager.py:16:50
   |
14 | from app.modules.strm.sync_manager import STRMSyncManager
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
   |                                                  ^^^^^^^^^^^^^^
17 | from app.core.database import AsyncSessionLocal
18 | from loguru import logger
   |
help: Remove unused import: `app.modules.strm.file_operation_mode.STRMSyncConfig`

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:17:1
   |
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
17 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

F401 [*] `app.core.database.AsyncSessionLocal` imported but unused
  --> scripts\test_strm_task_manager.py:17:31
   |
15 | from app.modules.strm.config import STRMConfig
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
17 | from app.core.database import AsyncSessionLocal
   |                               ^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |
help: Remove unused import: `app.core.database.AsyncSessionLocal`

E402 Module level import not at top of file
  --> scripts\test_strm_task_manager.py:18:1
   |
16 | from app.modules.strm.file_operation_mode import STRMSyncConfig
17 | from app.core.database import AsyncSessionLocal
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

E402 Module level import not at top of file
  --> scripts\test_subscribe_chain.py:17:1
   |
15 |     sys.path.insert(0, str(backend_root))
16 |
17 | from app.chain.subscribe import SubscribeChain
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_subscribe_chain.py:18:1
   |
17 | from app.chain.subscribe import SubscribeChain
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `json` imported but unused
 --> scripts\test_subscription_history.py:7:8
  |
5 | import asyncio
6 | import httpx
7 | import json
  |        ^^^^
8 | from datetime import datetime
  |
help: Remove unused import: `json`

F401 [*] `datetime.datetime` imported but unused
 --> scripts\test_subscription_history.py:8:22
  |
6 | import httpx
7 | import json
8 | from datetime import datetime
  |                      ^^^^^^^^
  |
help: Remove unused import: `datetime.datetime`

F541 [*] f-string without any placeholders
  --> scripts\test_subscription_history.py:27:27
   |
25 |                 response = await client.get("http://localhost:8092/health")
26 |                 if response.status_code == 200:
27 |                     print(f"  [OK] 后端服务运行正常")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
28 |                 else:
29 |                     print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_subscription_history.py:74:35
   |
72 |                         create_history = [h for h in history_list if h.get("action") == "create"]
73 |                         if create_history:
74 |                             print(f"  [OK] 创建历史记录已保存")
   |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
75 |                             print(f"    描述: {create_history[0].get('description')}")
76 |                         else:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_subscription_history.py:77:35
   |
75 |                             print(f"    描述: {create_history[0].get('description')}")
76 |                         else:
77 |                             print(f"  [WARN] 未找到创建历史记录")
   |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
78 |                     else:
79 |                         print(f"  [WARN] 获取历史记录失败: {history_response.status_code}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:104:27
    |
102 |                 )
103 |                 if response.status_code == 200:
104 |                     print(f"  [OK] 订阅更新成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^
105 |                     
106 |                     # 等待一下
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:121:35
    |
119 |                         update_history = [h for h in history_list if h.get("action") == "update"]
120 |                         if update_history:
121 |                             print(f"  [OK] 更新历史记录已保存")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
122 |                             print(f"    描述: {update_history[0].get('description')}")
123 |                             print(f"    旧值: {update_history[0].get('old_value')}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:126:35
    |
124 |                             print(f"    新值: {update_history[0].get('new_value')}")
125 |                         else:
126 |                             print(f"  [WARN] 未找到更新历史记录")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
127 |             except Exception as e:
128 |                 print(f"  [FAIL] 更新订阅异常: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:139:27
    |
137 |                 )
138 |                 if response.status_code == 200:
139 |                     print(f"  [OK] 订阅禁用成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^
140 |                     
141 |                     # 等待一下
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:156:35
    |
154 |                         disable_history = [h for h in history_list if h.get("action") == "disable"]
155 |                         if disable_history:
156 |                             print(f"  [OK] 禁用历史记录已保存")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
157 |                             print(f"    描述: {disable_history[0].get('description')}")
158 |                             print(f"    状态变更: {disable_history[0].get('old_value')} -> {disable_history[0].get('new_value')}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:160:35
    |
158 |                             print(f"    状态变更: {disable_history[0].get('old_value')} -> {disable_history[0].get('new_value')}")
159 |                         else:
160 |                             print(f"  [WARN] 未找到禁用历史记录")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
161 |             except Exception as e:
162 |                 print(f"  [FAIL] 禁用订阅异常: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:176:27
    |
174 |                 )
175 |                 if response.status_code == 200:
176 |                     print(f"  [OK] 搜索执行成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^
177 |                     
178 |                     # 等待一下
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:193:35
    |
191 |                         search_history = [h for h in history_list if h.get("action") == "search"]
192 |                         if search_history:
193 |                             print(f"  [OK] 搜索历史记录已保存")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
194 |                             print(f"    描述: {search_history[0].get('description')}")
195 |                             print(f"    搜索关键词: {search_history[0].get('search_query')}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:198:35
    |
196 |                             print(f"    结果数量: {search_history[0].get('search_results_count')}")
197 |                         else:
198 |                             print(f"  [WARN] 未找到搜索历史记录")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
199 |             except Exception as e:
200 |                 print(f"  [FAIL] 执行搜索异常: {e}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:222:27
    |
220 |                         action_counts[action] = action_counts.get(action, 0) + 1
221 |                     
222 |                     print(f"  操作类型统计:")
    |                           ^^^^^^^^^^^^^^^^^^
223 |                     for action, count in action_counts.items():
224 |                         print(f"    - {action}: {count} 条")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_history.py:257:27
    |
255 |                 )
256 |                 if response.status_code == 200:
257 |                     print(f"  [OK] 订阅删除成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^
258 |                 else:
259 |                     print(f"  [WARN] 订阅删除失败: {response.status_code}")
    |
help: Remove extraneous `f` prefix

F401 [*] `json` imported but unused
 --> scripts\test_subscription_rule_engine.py:7:8
  |
5 | import asyncio
6 | import httpx
7 | import json
  |        ^^^^
8 | from typing import Dict, Any
  |
help: Remove unused import: `json`

F401 [*] `typing.Dict` imported but unused
 --> scripts\test_subscription_rule_engine.py:8:20
  |
6 | import httpx
7 | import json
8 | from typing import Dict, Any
  |                    ^^^^
  |
help: Remove unused import

F401 [*] `typing.Any` imported but unused
 --> scripts\test_subscription_rule_engine.py:8:26
  |
6 | import httpx
7 | import json
8 | from typing import Dict, Any
  |                          ^^^
  |
help: Remove unused import

F841 Local variable `test_results` is assigned to but never used
  --> scripts\test_subscription_rule_engine.py:21:5
   |
20 |     # 测试用例：搜索结果
21 |     test_results = [
   |     ^^^^^^^^^^^^
22 |         {
23 |             "title": "Movie Name 2023 1080p HDR CHD",
   |
help: Remove assignment to unused variable `test_results`

F541 [*] f-string without any placeholders
  --> scripts\test_subscription_status.py:25:27
   |
23 |                 response = await client.get("http://localhost:8092/health")
24 |                 if response.status_code == 200:
25 |                     print(f"  [OK] 后端服务运行正常")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
26 |                 else:
27 |                     print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_subscription_status.py:82:31
   |
81 |                     if status == "paused":
82 |                         print(f"  [OK] 订阅禁用成功，状态已变更为 paused")
   |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
83 |                     else:
84 |                         print(f"  [FAIL] 订阅禁用后状态为 {status} (期望: paused)")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:104:31
    |
103 |                     if status == "active":
104 |                         print(f"  [OK] 订阅启用成功，状态已变更为 active")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
105 |                     else:
106 |                         print(f"  [FAIL] 订阅启用后状态为 {status} (期望: active)")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:132:31
    |
131 |                     if enable_history and disable_history:
132 |                         print(f"  [OK] 状态变更历史记录已保存")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
133 |                         print(f"    启用记录: {len(enable_history)} 条")
134 |                         print(f"    禁用记录: {len(disable_history)} 条")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:141:31
    |
139 |                             print(f"    最新启用: {latest.get('old_value')} -> {latest.get('new_value')}")
140 |                     else:
141 |                         print(f"  [WARN] 未找到完整的状态变更历史记录")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
142 |                 else:
143 |                     print(f"  [FAIL] 获取历史记录失败: {response.status_code}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:166:31
    |
165 |                     if not success and "无法执行搜索" in message:
166 |                         print(f"  [OK] 暂停状态下的搜索被正确阻止")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
167 |                         print(f"    消息: {message}")
168 |                     else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:169:31
    |
167 |                         print(f"    消息: {message}")
168 |                     else:
169 |                         print(f"  [WARN] 暂停状态下的搜索未被阻止")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
170 |                 else:
171 |                     print(f"  [INFO] 搜索请求返回: {response.status_code}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_subscription_status.py:184:27
    |
182 |                 )
183 |                 if response.status_code == 200:
184 |                     print(f"  [OK] 订阅删除成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^
185 |                 else:
186 |                     print(f"  [WARN] 订阅删除失败: {response.status_code}")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_system_comprehensive.py:17:1
   |
15 | sys.path.insert(0, str(project_root))
16 |
17 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F401 [*] `json` imported but unused
 --> scripts\test_system_monitoring.py:7:8
  |
5 | import asyncio
6 | import httpx
7 | import json
  |        ^^^^
  |
help: Remove unused import: `json`

F541 [*] f-string without any placeholders
  --> scripts\test_system_monitoring.py:26:27
   |
24 |                 response = await client.get("http://localhost:8092/health")
25 |                 if response.status_code == 200:
26 |                     print(f"  [OK] 后端服务运行正常")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
27 |                 else:
28 |                     print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_system_monitoring.py:45:27
   |
43 |                     resources = data.get("data", {})
44 |                     
45 |                     print(f"  [OK] 系统资源获取成功")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
46 |                     print(f"    CPU使用率: {resources.get('cpu', {}).get('usage_percent', 0)}%")
47 |                     print(f"    内存使用率: {resources.get('memory', {}).get('usage_percent', 0)}%")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_system_monitoring.py:90:27
   |
88 |                     statistics = data.get("data", {})
89 |                     
90 |                     print(f"  [OK] 统计信息获取成功")
   |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^
91 |                     cpu_stats = statistics.get("cpu", {})
92 |                     memory_stats = statistics.get("memory", {})
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_system_monitoring.py:114:27
    |
112 |                     summary = metrics.get("summary", {})
113 |                     
114 |                     print(f"  [OK] API性能指标获取成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
115 |                     print(f"    总请求数: {summary.get('total_requests', 0)}")
116 |                     print(f"    总错误数: {summary.get('total_errors', 0)}")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_system_monitoring.py:190:27
    |
188 |                     request_counts = history.get("request_counts", {})
189 |                     
190 |                     print(f"  [OK] API性能历史记录获取成功")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
191 |                     print(f"    响应时间历史: {len(response_times)} 个端点")
192 |                     print(f"    错误历史: {len(errors)} 条")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_tmdb_fanart_with_key.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.fanart import FanartModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.media_identification.service import MediaIdentificationService
15 | from app.core.database import AsyncSessionLocal
   |

E402 Module level import not at top of file
  --> scripts\test_tmdb_fanart_with_key.py:14:1
   |
13 | from app.modules.fanart import FanartModule
14 | from app.modules.media_identification.service import MediaIdentificationService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
   |

E402 Module level import not at top of file
  --> scripts\test_tmdb_fanart_with_key.py:15:1
   |
13 | from app.modules.fanart import FanartModule
14 | from app.modules.media_identification.service import MediaIdentificationService
15 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.core.config import settings
17 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_tmdb_fanart_with_key.py:16:1
   |
14 | from app.modules.media_identification.service import MediaIdentificationService
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from loguru import logger
   |

F401 [*] `app.core.config.settings` imported but unused
  --> scripts\test_tmdb_fanart_with_key.py:16:29
   |
14 | from app.modules.media_identification.service import MediaIdentificationService
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
   |                             ^^^^^^^^
17 | from loguru import logger
   |
help: Remove unused import: `app.core.config.settings`

E402 Module level import not at top of file
  --> scripts\test_tmdb_fanart_with_key.py:17:1
   |
15 | from app.core.database import AsyncSessionLocal
16 | from app.core.config import settings
17 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
18 |
19 | # 用户提供的TMDB API key（仅用于测试，不写入系统）
   |

F841 Local variable `identification_service` is assigned to but never used
  --> scripts\test_tmdb_fanart_with_key.py:40:13
   |
38 |     try:
39 |         async with AsyncSessionLocal() as session:
40 |             identification_service = MediaIdentificationService(session)
   |             ^^^^^^^^^^^^^^^^^^^^^^
41 |             
42 |             # 测试搜索电影
   |
help: Remove assignment to unused variable `identification_service`

F541 [*] f-string without any placeholders
   --> scripts\test_tmdb_fanart_with_key.py:108:19
    |
107 | …     if details:
108 | …         print(f"[OK] 获取TMDB详情成功")
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^
109 | …         print(f"   - 标题: {details.get('title') or details.get('name', 'N/A')}")
110 | …         print(f"   - 年份: {details.get('release_date', 'N/A')[:4] if details.get('release_date') else details.get('first_air_date', …
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_tmdb_simple.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | import httpx
   | ^^^^^^^^^^^^
15 | from app.core.config import settings
16 | from app.utils.http_client import create_httpx_client
   |

F401 [*] `httpx` imported but unused
  --> scripts\test_tmdb_simple.py:14:8
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | import httpx
   |        ^^^^^
15 | from app.core.config import settings
16 | from app.utils.http_client import create_httpx_client
   |
help: Remove unused import: `httpx`

E402 Module level import not at top of file
  --> scripts\test_tmdb_simple.py:15:1
   |
14 | import httpx
15 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.utils.http_client import create_httpx_client
   |

F401 [*] `app.core.config.settings` imported but unused
  --> scripts\test_tmdb_simple.py:15:29
   |
14 | import httpx
15 | from app.core.config import settings
   |                             ^^^^^^^^
16 | from app.utils.http_client import create_httpx_client
   |
help: Remove unused import: `app.core.config.settings`

E402 Module level import not at top of file
  --> scripts\test_tmdb_simple.py:16:1
   |
14 | import httpx
15 | from app.core.config import settings
16 | from app.utils.http_client import create_httpx_client
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | # 用户提供的TMDB API key
   |

F541 [*] f-string without any placeholders
   --> scripts\test_tmdb_simple.py:115:19
    |
113 |             details = response.json()
114 |             
115 |             print(f"[OK] 获取TMDB详情成功")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^
116 |             print(f"   - 标题: {details.get('name', 'N/A')}")
117 |             print(f"   - 年份: {details.get('first_air_date', 'N/A')[:4] if details.get('first_air_date') else 'N/A'}")
    |
help: Remove extraneous `f` prefix

F841 Local variable `movie_id` is assigned to but never used
   --> scripts\test_tmdb_simple.py:196:5
    |
195 |     # 测试1: TMDB电影搜索
196 |     movie_id = await test_tmdb_search_movie()
    |     ^^^^^^^^
197 |     
198 |     # 测试2: TMDB电视剧搜索
    |
help: Remove assignment to unused variable `movie_id`

E402 Module level import not at top of file
  --> scripts\test_transmission_labels.py:14:1
   |
12 | sys.path.insert(0, str(backend_dir))
13 |
14 | from app.core.downloaders import DownloaderClient, DownloaderType
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.settings.service import SettingsService
16 | from app.core.database import AsyncSessionLocal, init_db
   |

E402 Module level import not at top of file
  --> scripts\test_transmission_labels.py:15:1
   |
14 | from app.core.downloaders import DownloaderClient, DownloaderType
15 | from app.modules.settings.service import SettingsService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.core.database import AsyncSessionLocal, init_db
   |

E402 Module level import not at top of file
  --> scripts\test_transmission_labels.py:16:1
   |
14 | from app.core.downloaders import DownloaderClient, DownloaderType
15 | from app.modules.settings.service import SettingsService
16 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | async def test_transmission_labels():
   |

F541 [*] f-string without any placeholders
  --> scripts\test_transmission_labels.py:91:33
   |
89 |                 # 尝试设置标签
90 |                 if "VABHUB" not in labels_list:
91 |                     logger.info(f"  尝试添加VABHUB标签...")
   |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^
92 |                     result = await client.client.set_torrent_labels([torrent_id], labels_list + ["VABHUB"])
93 |                     if result:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_transmission_labels.py:94:37
   |
92 |                     result = await client.client.set_torrent_labels([torrent_id], labels_list + ["VABHUB"])
93 |                     if result:
94 |                         logger.info(f"  ✓ 标签设置成功")
   |                                     ^^^^^^^^^^^^^^^^^^^
95 |                         # 重新获取任务信息验证
96 |                         updated_torrents = await client.client.get_torrents(ids=[torrent_id])
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_transmission_labels.py:101:38
    |
 99 |                             logger.info(f"  更新后标签: {updated_labels}")
100 |                     else:
101 |                         logger.error(f"  ✗ 标签设置失败")
    |                                      ^^^^^^^^^^^^^^^^^^^
102 |                 else:
103 |                     logger.info(f"  ✓ 已有VABHUB标签")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_transmission_labels.py:103:33
    |
101 |                         logger.error(f"  ✗ 标签设置失败")
102 |                 else:
103 |                     logger.info(f"  ✓ 已有VABHUB标签")
    |                                 ^^^^^^^^^^^^^^^^^^^^^
104 |                 
105 |                 logger.info("")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:13:1
   |
11 | sys.path.insert(0, str(project_root))
12 |
13 | from app.modules.thetvdb import TheTvDbModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.modules.fanart import FanartModule
15 | from app.modules.media_identification.service import MediaIdentificationService
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:14:1
   |
13 | from app.modules.thetvdb import TheTvDbModule
14 | from app.modules.fanart import FanartModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.media_identification.service import MediaIdentificationService
16 | from app.core.database import AsyncSessionLocal
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:15:1
   |
13 | from app.modules.thetvdb import TheTvDbModule
14 | from app.modules.fanart import FanartModule
15 | from app.modules.media_identification.service import MediaIdentificationService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.core.database import AsyncSessionLocal
17 | from app.core.config import settings
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:16:1
   |
14 | from app.modules.fanart import FanartModule
15 | from app.modules.media_identification.service import MediaIdentificationService
16 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.core.config import settings
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:17:1
   |
15 | from app.modules.media_identification.service import MediaIdentificationService
16 | from app.core.database import AsyncSessionLocal
17 | from app.core.config import settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_default.py:18:1
   |
16 | from app.core.database import AsyncSessionLocal
17 | from app.core.config import settings
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F541 [*] f-string without any placeholders
  --> scripts\test_tvdb_fanart_default.py:85:11
   |
83 |     print("="*60)
84 |     
85 |     print(f"\n[2.1] Fanart配置状态:")
   |           ^^^^^^^^^^^^^^^^^^^^^^^^^^
86 |     print(f"   - Fanart启用: {settings.FANART_ENABLE}")
87 |     print(f"   - Fanart API Key: {settings.FANART_API_KEY[:20] if settings.FANART_API_KEY else 'N/A'}...")
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_with_key.py:14:1
   |
12 | sys.path.insert(0, str(project_root))
13 |
14 | from app.modules.thetvdb import TheTvDbModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.fanart import FanartModule
16 | from app.modules.media_identification.service import MediaIdentificationService
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_with_key.py:15:1
   |
14 | from app.modules.thetvdb import TheTvDbModule
15 | from app.modules.fanart import FanartModule
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.media_identification.service import MediaIdentificationService
17 | from app.core.database import AsyncSessionLocal
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_with_key.py:16:1
   |
14 | from app.modules.thetvdb import TheTvDbModule
15 | from app.modules.fanart import FanartModule
16 | from app.modules.media_identification.service import MediaIdentificationService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from app.core.database import AsyncSessionLocal
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_with_key.py:17:1
   |
15 | from app.modules.fanart import FanartModule
16 | from app.modules.media_identification.service import MediaIdentificationService
17 | from app.core.database import AsyncSessionLocal
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 | from loguru import logger
   |

E402 Module level import not at top of file
  --> scripts\test_tvdb_fanart_with_key.py:18:1
   |
16 | from app.modules.media_identification.service import MediaIdentificationService
17 | from app.core.database import AsyncSessionLocal
18 | from loguru import logger
   | ^^^^^^^^^^^^^^^^^^^^^^^^^
19 |
20 | # 临时TVDB API key（仅用于测试，不写入系统）
   |

F841 Local variable `fanart_images` is assigned to but never used
   --> scripts\test_tvdb_fanart_with_key.py:238:9
    |
236 |     # 测试2: Fanart测试
237 |     if tvdb_id:
238 |         fanart_images = await test_fanart_with_tvdb_id(tvdb_id)
    |         ^^^^^^^^^^^^^
239 |     else:
240 |         print("\n[WARN] 跳过Fanart测试（缺少TVDB ID）")
    |
help: Remove assignment to unused variable `fanart_images`

F401 [*] `asyncio` imported but unused
 --> scripts\test_unified_response_api.py:6:8
  |
4 | """
5 |
6 | import asyncio
  |        ^^^^^^^
7 | import sys
8 | from pathlib import Path
  |
help: Remove unused import: `asyncio`

E402 Module level import not at top of file
  --> scripts\test_unified_response_api.py:14:1
   |
12 | sys.path.insert(0, str(backend_root))
13 |
14 | from fastapi.testclient import TestClient
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from main import app
   |

E402 Module level import not at top of file
  --> scripts\test_unified_response_api.py:15:1
   |
14 | from fastapi.testclient import TestClient
15 | from main import app
   | ^^^^^^^^^^^^^^^^^^^^
16 |
17 | client = TestClient(app)
   |

E722 Do not use bare `except`
  --> scripts\test_unified_response_api.py:50:9
   |
48 |         try:
49 |             json_data = response.json()
50 |         except:
   |         ^^^^^^
51 |             print(f"⚠️  {method} {endpoint}: 响应不是JSON格式")
52 |             return False
   |

E402 Module level import not at top of file
  --> scripts\test_vabhub_tag_filter.py:15:1
   |
13 | sys.path.insert(0, str(backend_dir))
14 |
15 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from app.modules.download.service import DownloadService
   |

E402 Module level import not at top of file
  --> scripts\test_vabhub_tag_filter.py:16:1
   |
15 | from app.core.database import AsyncSessionLocal, init_db
16 | from app.modules.download.service import DownloadService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 |
18 | # 后端API地址
   |

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter.py:52:33
   |
50 |                     items = data.get("data", {}).get("items", [])
51 |                     total = data.get("data", {}).get("total", 0)
52 |                     logger.info(f"✅ API调用成功")
   |                                 ^^^^^^^^^^^^^^^^^
53 |                     logger.info(f"   返回任务数: {len(items)}")
54 |                     logger.info(f"   总任务数: {total}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter.py:85:25
   |
83 |             # 测试只显示VABHUB标签的任务
84 |             downloads = await service.list_downloads(vabhub_only=True)
85 |             logger.info(f"✅ 服务层调用成功")
   |                         ^^^^^^^^^^^^^^^^^^^^
86 |             logger.info(f"   返回任务数: {len(downloads)}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_vabhub_tag_filter.py:112:25
    |
110 |             # 不传递vabhub_only参数，应该使用默认值True
111 |             downloads_default = await service.list_downloads()
112 |             logger.info(f"✅ 默认行为测试成功")
    |                         ^^^^^^^^^^^^^^^^^^^^^^
113 |             logger.info(f"   返回任务数: {len(downloads_default)}")
114 |             logger.info(f"   说明: 默认只显示VABHUB标签的任务")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_vabhub_tag_filter.py:114:25
    |
112 |             logger.info(f"✅ 默认行为测试成功")
113 |             logger.info(f"   返回任务数: {len(downloads_default)}")
114 |             logger.info(f"   说明: 默认只显示VABHUB标签的任务")
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
115 |         
116 |         logger.info("")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_vabhub_tag_filter.py:127:25
    |
125 |             # 传递vabhub_only=False，应该显示所有任务
126 |             downloads_all = await service.list_downloads(vabhub_only=False)
127 |             logger.info(f"✅ 显示所有任务测试成功")
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
128 |             logger.info(f"   返回任务数: {len(downloads_all)}")
129 |             logger.info(f"   说明: 显示所有任务（包括没有VABHUB标签的）")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\test_vabhub_tag_filter.py:129:25
    |
127 |             logger.info(f"✅ 显示所有任务测试成功")
128 |             logger.info(f"   返回任务数: {len(downloads_all)}")
129 |             logger.info(f"   说明: 显示所有任务（包括没有VABHUB标签的）")
    |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
130 |         
131 |         logger.info("")
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\test_vabhub_tag_filter_simple.py:14:1
   |
12 | sys.path.insert(0, str(backend_dir))
13 |
14 | from app.core.database import AsyncSessionLocal, init_db
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.modules.download.service import DownloadService
   |

E402 Module level import not at top of file
  --> scripts\test_vabhub_tag_filter_simple.py:15:1
   |
14 | from app.core.database import AsyncSessionLocal, init_db
15 | from app.modules.download.service import DownloadService
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 |
17 | async def test_vabhub_tag_filter_simple():
   |

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter_simple.py:38:29
   |
36 |             try:
37 |                 downloads_default = await service.list_downloads()
38 |                 logger.info(f"✅ 默认行为测试成功")
   |                             ^^^^^^^^^^^^^^^^^^^^^^
39 |                 logger.info(f"   返回任务数: {len(downloads_default)}")
40 |                 logger.info(f"   说明: 默认只显示VABHUB标签的任务")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter_simple.py:40:29
   |
38 |                 logger.info(f"✅ 默认行为测试成功")
39 |                 logger.info(f"   返回任务数: {len(downloads_default)}")
40 |                 logger.info(f"   说明: 默认只显示VABHUB标签的任务")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
41 |                 
42 |                 if downloads_default:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter_simple.py:61:29
   |
59 |             try:
60 |                 downloads_filtered = await service.list_downloads(vabhub_only=True)
61 |                 logger.info(f"✅ vabhub_only=True测试成功")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
62 |                 logger.info(f"   返回任务数: {len(downloads_filtered)}")
63 |             except Exception as e:
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter_simple.py:74:29
   |
72 |             try:
73 |                 downloads_all = await service.list_downloads(vabhub_only=False)
74 |                 logger.info(f"✅ vabhub_only=False测试成功")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
75 |                 logger.info(f"   返回任务数: {len(downloads_all)}")
76 |                 logger.info(f"   说明: 显示所有任务（包括没有VABHUB标签的）")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> scripts\test_vabhub_tag_filter_simple.py:76:29
   |
74 |                 logger.info(f"✅ vabhub_only=False测试成功")
75 |                 logger.info(f"   返回任务数: {len(downloads_all)}")
76 |                 logger.info(f"   说明: 显示所有任务（包括没有VABHUB标签的）")
   |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
77 |             except Exception as e:
78 |                 logger.error(f"❌ vabhub_only=False测试失败: {e}")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\update_transmission_config.py:148:48
    |
146 | …                     test_data = test_response.json()
147 | …                     if test_data.get("success"):
148 | …                         logger.success(f"✓ qBittorrent 连接测试成功")
    |                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
149 | …                         
150 | …                         # 获取统计信息
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> scripts\update_transmission_config.py:213:48
    |
211 | …                     test_data = test_response.json()
212 | …                     if test_data.get("success"):
213 | …                         logger.success(f"✓ Transmission 连接测试成功")
    |                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
214 | …                         
215 | …                         # 获取统计信息
    |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
  --> scripts\validate_legacy.py:13:1
   |
11 | sys.path.insert(0, str(project_root / "VabHub" / "backend"))
12 |
13 | from app.core.legacy_validator import LegacyValidator
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F841 Local variable `results` is assigned to but never used
  --> scripts\validate_legacy.py:25:5
   |
24 |     # 验证所有功能
25 |     results = validator.validate_all()
   |     ^^^^^^^
26 |     
27 |     # 打印报告
   |
help: Remove assignment to unused variable `results`

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:13:1
   |
11 | sys.path.insert(0, str(backend_root))
12 |
13 | from fastapi import APIRouter
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
   |

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:14:1
   |
13 | from fastapi import APIRouter
14 | from app.api import api_router
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
   |

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:15:1
   |
13 | from fastapi import APIRouter
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
16 | from inspect import getmembers, isfunction, signature
17 | import re
   |

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:16:1
   |
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | import re
   |

F401 [*] `inspect.getmembers` imported but unused
  --> scripts\verify_api_routes.py:16:21
   |
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
   |                     ^^^^^^^^^^
17 | import re
   |
help: Remove unused import

F401 [*] `inspect.isfunction` imported but unused
  --> scripts\verify_api_routes.py:16:33
   |
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
   |                                 ^^^^^^^^^^
17 | import re
   |
help: Remove unused import

F401 [*] `inspect.signature` imported but unused
  --> scripts\verify_api_routes.py:16:45
   |
14 | from app.api import api_router
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
   |                                             ^^^^^^^^^
17 | import re
   |
help: Remove unused import

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:17:1
   |
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
17 | import re
   | ^^^^^^^^^
18 |
19 | from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX
   |

F401 [*] `re` imported but unused
  --> scripts\verify_api_routes.py:17:8
   |
15 | from app.core.schemas import BaseResponse
16 | from inspect import getmembers, isfunction, signature
17 | import re
   |        ^^
18 |
19 | from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX
   |
help: Remove unused import: `re`

E402 Module level import not at top of file
  --> scripts\verify_api_routes.py:19:1
   |
17 | import re
18 |
19 | from scripts.api_test_config import API_PREFIX as CONFIG_API_PREFIX
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

Found 1834 errors.
[*] 1206 fixable with the `--fix` option (176 hidden fixes can be enabled with the `--unsafe-fixes` option).
