"""
多模态分析功能测试脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.modules.multimodal.video_analyzer import VideoAnalyzer
from app.modules.multimodal.audio_analyzer import AudioAnalyzer
from app.modules.multimodal.text_analyzer import TextAnalyzer
from app.modules.multimodal.fusion import MultimodalFeatureFusion
from loguru import logger


async def test_text_analysis():
    """测试文本分析"""
    print("\n" + "="*50)
    print("测试文本分析")
    print("="*50)
    
    analyzer = TextAnalyzer()
    
    # 测试文本
    test_text = "这是一部非常棒的电影！演员表演出色，剧情扣人心弦。"
    
    result = await analyzer.analyze_text(test_text)
    print(f"文本: {test_text}")
    print(f"关键词: {result.get('keywords', [])}")
    print(f"情感: {result.get('sentiment', {})}")
    print(f"语言: {result.get('language', 'unknown')}")
    print(f"摘要: {result.get('summary', '')}")
    print(f"字数: {result.get('word_count', 0)}")
    print(f"字符数: {result.get('character_count', 0)}")


async def test_video_analysis():
    """测试视频分析"""
    print("\n" + "="*50)
    print("测试视频分析")
    print("="*50)
    
    analyzer = VideoAnalyzer()
    
    # 测试视频路径（需要用户提供）
    video_path = input("请输入视频文件路径（留空跳过）: ").strip()
    
    if not video_path or not os.path.exists(video_path):
        print("视频文件不存在，跳过测试")
        return
    
    result = await analyzer.analyze_video(video_path)
    print(f"视频路径: {video_path}")
    print(f"视频信息: {result.get('video_info', {})}")
    print(f"质量评分: {result.get('quality_score', 0)}")
    print(f"场景数量: {len(result.get('scenes', []))}")
    
    if result.get('scenes'):
        print("前3个场景:")
        for scene in result.get('scenes', [])[:3]:
            print(f"  - {scene.get('description', '')}: {scene.get('start_time', 0):.2f}s - {scene.get('end_time', 0):.2f}s")


async def test_audio_analysis():
    """测试音频分析"""
    print("\n" + "="*50)
    print("测试音频分析")
    print("="*50)
    
    analyzer = AudioAnalyzer()
    
    # 测试音频路径（需要用户提供）
    audio_path = input("请输入音频文件路径（留空跳过）: ").strip()
    
    if not audio_path or not os.path.exists(audio_path):
        print("音频文件不存在，跳过测试")
        return
    
    result = await analyzer.analyze_audio(audio_path)
    print(f"音频路径: {audio_path}")
    print(f"音频信息: {result.get('audio_info', {})}")
    print(f"质量评分: {result.get('quality_score', 0)}")
    
    features = result.get('features', {})
    if features:
        print("音频特征:")
        print(f"  - 节拍: {features.get('tempo', 0):.2f} BPM")
        print(f"  - 调性: {features.get('key', 'unknown')} {features.get('mode', 'unknown')}")
        print(f"  - 能量: {features.get('energy', 0):.4f}")
        print(f"  - 响度: {features.get('loudness', 0):.2f} dB")


async def test_multimodal_fusion():
    """测试多模态特征融合"""
    print("\n" + "="*50)
    print("测试多模态特征融合")
    print("="*50)
    
    fusion = MultimodalFeatureFusion()
    
    # 创建测试特征
    video_features = {
        "video_info": {
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "bitrate": 8000000,
            "duration": 3600
        },
        "quality_score": 85.0,
        "scenes": [
            {"confidence": 0.9},
            {"confidence": 0.8}
        ]
    }
    
    audio_features = {
        "audio_info": {
            "sample_rate": 44100,
            "channels": 2,
            "bitrate": 320000,
            "duration": 3600
        },
        "quality_score": 90.0,
        "features": {
            "tempo": 120.0,
            "energy": 0.8,
            "loudness": -10.0,
            "speechiness": 0.2,
            "acousticness": 0.7,
            "instrumentalness": 0.8,
            "valence": 0.6,
            "arousal": 0.7
        }
    }
    
    text_features = {
        "word_count": 100,
        "character_count": 500,
        "sentiment": {
            "score": 0.8,
            "polarity": 0.6,
            "subjectivity": 0.7,
            "confidence": 0.9
        },
        "keywords": [
            {"score": 0.1},
            {"score": 0.08}
        ]
    }
    
    # 融合特征
    fused = fusion.fuse_features(
        video_features=video_features,
        audio_features=audio_features,
        text_features=text_features
    )
    
    print(f"融合特征: {fused.get('modalities', [])}")
    print(f"置信度: {fused.get('confidence', 0):.2f}")
    print(f"融合向量长度: {len(fused.get('combined', []))}")
    
    # 计算相似度
    features1 = {
        "video": video_features,
        "audio": audio_features,
        "text": text_features
    }
    
    features2 = {
        "video": video_features,
        "audio": audio_features,
        "text": text_features
    }
    
    similarity = fusion.calculate_similarity(features1, features2, method="cosine")
    print(f"相似度（相同特征）: {similarity:.4f}")


async def main():
    """主函数"""
    print("="*50)
    print("多模态分析功能测试")
    print("="*50)
    
    try:
        # 测试文本分析
        await test_text_analysis()
        
        # 测试视频分析
        await test_video_analysis()
        
        # 测试音频分析
        await test_audio_analysis()
        
        # 测试多模态特征融合
        await test_multimodal_fusion()
        
        print("\n" + "="*50)
        print("测试完成")
        print("="*50)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

