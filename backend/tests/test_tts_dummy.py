"""
Dummy TTS 引擎测试
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.modules.tts.dummy import DummyTTSEngine
from app.modules.tts.base import TTSRequest


@pytest.mark.asyncio
async def test_dummy_tts_creates_file():
    """测试 DummyTTSEngine.synthesize 后目标路径存在"""
    engine = DummyTTSEngine()
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        
        request = TTSRequest(
            text="测试文本",
            language="zh-CN",
            ebook_id=123,
            chapter_index=1,
            chapter_title="第一章"
        )
        
        result = await engine.synthesize(request, target_path)
        
        # 验证文件已创建
        assert target_path.exists(), "TTS 输出文件应该存在"
        assert result.audio_path == target_path, "返回的路径应该与目标路径一致"


@pytest.mark.asyncio
async def test_dummy_tts_returns_result():
    """测试返回的 audio_path 正确、duration_seconds 为 None 或有效值"""
    engine = DummyTTSEngine()
    
    with TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_output.wav"
        
        request = TTSRequest(
            text="测试文本",
            language="zh-CN"
        )
        
        result = await engine.synthesize(request, target_path)
        
        # 验证返回结果
        assert result.audio_path == target_path
        # duration_seconds 可能是 None 或有效值（1 秒）
        assert result.duration_seconds is None or result.duration_seconds > 0

