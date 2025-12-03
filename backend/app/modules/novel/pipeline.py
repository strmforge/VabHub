"""
小说到电子书流水线

将 NovelSourceAdapter → EpubBuilder → EBookImporter 串起来的 orchestrator。
支持可选的 TTS → AudiobookImporter 支路。
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from .source_base import NovelSourceAdapter
from .epub_builder import EpubBuilder
from .models import NovelMetadata, StandardChapter
from app.modules.ebook.importer import EBookImporter
from app.modules.audiobook.importer import AudiobookImporter
from app.modules.tts.base import TTSEngine
from app.modules.tts.base import TTSRequest
from app.modules.tts.rate_limiter import RunContext, should_allow, record_request
from app.modules.tts.profile_service import resolve_tts_profile_for_ebook
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.core.config import Settings
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile


@dataclass
class TTSSummary:
    """TTS 生成汇总信息"""
    total_chapters: int
    generated_chapters: int
    rate_limited_chapters: int
    first_rate_limited_chapter_index: Optional[int] = None


class NovelPipelineResult:
    """小说流水线结果"""
    def __init__(
        self,
        epub_path: Optional[Path] = None,
        ebook: Optional[EBook] = None,
        audiobook_files: Optional[List[AudiobookFile]] = None,
        tts_summary: Optional[TTSSummary] = None
    ):
        self.epub_path = epub_path
        self.ebook = ebook
        self.audiobook_files = audiobook_files or []
        self.tts_summary = tts_summary


class NovelToEbookPipeline:
    """
    小说到电子书的完整流水线。
    
    负责协调从小说源获取章节、构建电子书文件、导入到 VabHub 的整个流程。
    支持可选的 TTS → AudiobookImporter 支路。
    """
    
    def __init__(
        self,
        db: AsyncSession,
        ebook_importer: EBookImporter,
        epub_builder: EpubBuilder,
        tts_engine: Optional[TTSEngine] = None,
        audiobook_importer: Optional[AudiobookImporter] = None,
        settings: Optional[Settings] = None
    ):
        """
        初始化流水线。
        
        Args:
            db: 数据库会话
            ebook_importer: 电子书导入器
            epub_builder: EPUB 构建器
            tts_engine: TTS 引擎（可选）
            audiobook_importer: 有声书导入器（可选）
            settings: 应用配置（可选）
        """
        self.db = db
        self.ebook_importer = ebook_importer
        self.epub_builder = epub_builder
        self._tts_engine = tts_engine
        self._audiobook_importer = audiobook_importer
        self._settings = settings
        # 为本次 pipeline 运行创建限流上下文
        self._tts_run_context = RunContext()
        # 用于存储归档后的 TXT 路径（由外部设置）
        self._archived_txt_path: Optional[Path] = None
    
    async def run(
        self,
        source: NovelSourceAdapter,
        output_dir: Path,
        generate_audiobook: bool = False,
        start_chapter_index: int = 1
    ) -> NovelPipelineResult:
        """
        执行完整流程：
        
        1. 从 source 获取 metadata + chapters
        2. 调用 EpubBuilder 生成 EPUB 文件
        3. 调用 EBookImporter 将 EPUB 文件导入 VabHub
        4. （可选）如果 generate_audiobook=True，调用 TTS 生成有声书
        
        Args:
            source: 小说来源适配器
            output_dir: 输出目录（用于存放生成的 EPUB 文件）
            generate_audiobook: 是否生成有声书（需要 TTS 引擎和有声书导入器）
        
        Returns:
            NovelPipelineResult: 包含 epub_path、ebook 和 audiobook_files
        """
        result = NovelPipelineResult()
        
        try:
            logger.info("开始执行小说到电子书流水线")
            
            # 步骤 1: 获取元数据
            logger.debug("获取小说元数据...")
            metadata = source.get_metadata()
            logger.info(f"小说元数据: {metadata.title} - {metadata.author}")
            
            # 步骤 2: 获取章节列表
            logger.debug("获取章节列表...")
            chapters = list(source.iter_chapters())
            logger.info(f"共获取 {len(chapters)} 个章节")
            
            if not chapters:
                logger.warning("没有获取到任何章节，终止流程")
                return result
            
            # 步骤 3: 构建 EPUB 文件
            logger.debug("构建 EPUB 文件...")
            output_dir.mkdir(parents=True, exist_ok=True)
            epub_path = self.epub_builder.build_epub(
                output_dir=output_dir,
                metadata=metadata,
                chapters=chapters
            )
            logger.info(f"已生成电子书文件: {epub_path}")
            result.epub_path = epub_path
            
            # 步骤 4: 导入到 VabHub
            logger.debug("导入电子书到 VabHub...")
            ebook = await self.ebook_importer.import_ebook_from_file(
                file_path=str(epub_path),
                media_type="ebook"
            )
            
            if not ebook:
                logger.error("电子书导入失败")
                return result
            
            logger.info(f"电子书导入成功: {ebook.id} - {ebook.title}")
            result.ebook = ebook
            
            # 步骤 4.5: 持久化小说源信息到 EBook.extra_metadata
            # 如果当前 source 是 LocalTxtNovelSourceAdapter，记录源文件路径
            if isinstance(source, LocalTxtNovelSourceAdapter):
                try:
                    # 获取原始 TXT 路径
                    original_txt_path = str(source.file_path)
                    
                    # 尝试从 pipeline 参数中获取归档路径
                    # 如果 inbox router 传入了 archived_path，使用它；否则使用原始路径
                    archived_txt_path = self._archived_txt_path or Path(original_txt_path)
                    
                    # 更新 extra_metadata（保留已有内容）
                    if ebook.extra_metadata is None:
                        ebook.extra_metadata = {}
                    
                    ebook.extra_metadata["novel_source"] = {
                        "type": "local_txt",
                        "archived_txt_path": str(archived_txt_path),
                        "original_txt_path": original_txt_path,
                        "imported_at": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    # 刷新对象以保存更改
                    await self.db.flush()
                    logger.debug(f"已保存小说源信息到 EBook {ebook.id}: {archived_txt_path}")
                except Exception as e:
                    logger.warning(f"保存小说源信息失败: {e}", exc_info=True)
                    # 不影响主流程，继续执行
            
            # 步骤 5: （可选）生成有声书
            if generate_audiobook and self._tts_engine and self._audiobook_importer and ebook:
                if self._settings and self._settings.SMART_TTS_ENABLED:
                    try:
                        audiobook_files, tts_summary = await self._generate_audiobook_from_chapters(
                            ebook=ebook,
                            chapters=chapters,
                            metadata=metadata,
                            settings=self._settings,
                            start_chapter_index=start_chapter_index
                        )
                        result.audiobook_files = audiobook_files
                        result.tts_summary = tts_summary
                    except Exception as e:
                        logger.exception("生成有声书失败，但不影响电子书入库: %s", e)
                else:
                    logger.debug("TTS 未启用，跳过有声书生成")
            
            return result
            
        except Exception as e:
            logger.error(f"小说到电子书流水线执行失败: {e}", exc_info=True)
            return result
    
    async def _generate_audiobook_from_chapters(
        self,
        ebook: EBook,
        chapters: List[StandardChapter],
        metadata: NovelMetadata,
        settings: Settings,
        start_chapter_index: int = 1
    ) -> tuple[List[AudiobookFile], Optional[TTSSummary]]:
        """
        从章节生成有声书
        
        Args:
            ebook: 已导入的电子书
            chapters: 章节列表
            metadata: 小说元数据
            settings: 应用配置
            start_chapter_index: 起始章节索引（从第几章开始，默认 1）
        
        Returns:
            tuple[List[AudiobookFile], Optional[TTSSummary]]: 生成的音频文件列表和 TTS 汇总信息
        """
        logger.info(f"开始为 EBook {ebook.id} 生成有声书，从第 {start_chapter_index} 章开始")
        
        # 限制章节数量
        chapters_for_tts = chapters
        max_chapters = settings.SMART_TTS_MAX_CHAPTERS or len(chapters_for_tts)
        if len(chapters_for_tts) > max_chapters:
            logger.warning(f"章节数量 {len(chapters_for_tts)} 超过限制 {max_chapters}，只处理前 {max_chapters} 章")
            chapters_for_tts = chapters_for_tts[:max_chapters]
        
        # 创建输出目录
        output_root = Path(settings.SMART_TTS_OUTPUT_ROOT)
        output_root.mkdir(parents=True, exist_ok=True)
        
        audio_files: List[Path] = []
        
        # TTS 统计信息
        total_chapters = len(chapters_for_tts)
        generated_chapters = 0
        rate_limited_chapters = 0
        first_rate_limited_chapter_index: Optional[int] = None
        
        if settings.SMART_TTS_CHAPTER_STRATEGY == "per_chapter":
            # 解析作品级 TTS Profile
            profile = await resolve_tts_profile_for_ebook(
                db=self.db,
                ebook=ebook,
                settings=settings
            )
            logger.debug(f"EBook {ebook.id} 使用 TTS Profile: provider={profile.provider}, language={profile.language}, voice={profile.voice}, speed={profile.speed}, pitch={profile.pitch}")
            
            # 按章节生成音频文件
            for idx, ch in enumerate(chapters_for_tts, start=1):
                # 跳过 start_chapter_index 之前的章节
                if idx < start_chapter_index:
                    logger.debug(f"跳过第 {idx} 章（起始索引为 {start_chapter_index}）")
                    continue
                
                filename = f"ebook_{ebook.id}_ch{idx:03d}.wav"
                target_path = output_root / filename
                
                req = TTSRequest(
                    text=ch.content,
                    language=profile.language,
                    voice=profile.voice,
                    speed=profile.speed,
                    pitch=profile.pitch,
                    ebook_id=ebook.id,
                    chapter_index=idx,
                    chapter_title=ch.title,
                )
                
                # 检查限流
                request_chars = len(ch.content)
                if not should_allow(
                    request_chars,
                    settings=settings,
                    run_context=self._tts_run_context
                ):
                    # 被限流，跳过本章节
                    if first_rate_limited_chapter_index is None:
                        first_rate_limited_chapter_index = idx
                    rate_limited_chapters += 1
                    logger.warning(
                        f"TTS rate limited: skipping chapter {idx} for ebook_id={ebook.id}, "
                        f"chars={request_chars}, reason=rate_limit_exceeded"
                    )
                    continue
                
                try:
                    # 记录请求（在实际调用前记录，因为如果调用失败，我们仍然消耗了配额检查）
                    record_request(
                        request_chars,
                        settings=settings,
                        run_context=self._tts_run_context
                    )
                    
                    result = await self._tts_engine.synthesize(req, target_path=target_path)
                    audio_files.append(result.audio_path)
                    generated_chapters += 1
                    logger.debug(f"章节 {idx} TTS 完成: {result.audio_path}")
                except Exception as e:
                    logger.exception(f"TTS synth failed for ebook_id={ebook.id} chapter={idx}")
                    # 合成失败不计入 generated，但也不计入 rate_limited
                    continue
        else:
            # "all_in_one" 策略：将所有章节合并成一个文件
            # TODO: 可以在后续任务中优化
            logger.warning("all_in_one 策略暂未实现，跳过")
            return [], None
        
        # 将音频文件导入为 AudiobookFile
        audiobook_files = []
        for audio_path in audio_files:
            try:
                # 准备 TTS hints
                hints = {
                    "tts_generated": True,
                    "tts_provider": settings.SMART_TTS_PROVIDER or "dummy",
                }
                
                # 使用 AudiobookImporter 导入音频文件
                # 传入已知的 ebook 和 TTS hints
                af = await self._audiobook_importer.import_audiobook_from_file(
                    file_path=str(audio_path),
                    media_type="audiobook",
                    ebook=ebook,  # 传入已知的 ebook，避免重复查找
                    hints=hints  # 传入 TTS 标记
                )
                if af:
                    audiobook_files.append(af)
                    logger.debug(f"有声书文件导入成功: {audio_path} (TTS: {hints['tts_provider']})")
            except Exception as e:
                logger.exception(f"Audiobook import failed for {audio_path}")
        
        logger.info(f"有声书生成完成: EBook {ebook.id}, 共 {len(audiobook_files)} 个音频文件")
        
        # 构造 TTSSummary
        tts_summary = TTSSummary(
            total_chapters=total_chapters,
            generated_chapters=generated_chapters,
            rate_limited_chapters=rate_limited_chapters,
            first_rate_limited_chapter_index=first_rate_limited_chapter_index
        )
        
        return audiobook_files, tts_summary

