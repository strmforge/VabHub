"""
分析慢查询脚本
从性能监控数据中识别和优化慢查询
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# 慢查询阈值（秒）
SLOW_QUERY_THRESHOLD = 1.0


def analyze_performance_data(performance_data: Dict[str, Any]) -> Dict[str, Any]:
    """分析性能数据，识别慢查询"""
    slow_queries = []
    slow_endpoints = []
    
    # 分析慢查询
    if "slow_queries" in performance_data:
        for query in performance_data["slow_queries"]:
            if query.get("duration", 0) > SLOW_QUERY_THRESHOLD:
                slow_queries.append(query)
    
    # 分析端点响应时间
    if "endpoints" in performance_data:
        for endpoint, stats in performance_data["endpoints"].items():
            avg_time = stats.get("avg_response_time", 0)
            max_time = stats.get("max_response_time", 0)
            
            if avg_time > SLOW_QUERY_THRESHOLD or max_time > SLOW_QUERY_THRESHOLD * 2:
                slow_endpoints.append({
                    "endpoint": endpoint,
                    "avg_response_time": avg_time,
                    "max_response_time": max_time,
                    "request_count": stats.get("request_count", 0),
                    "error_count": stats.get("error_count", 0)
                })
    
    # 按响应时间排序
    slow_endpoints.sort(key=lambda x: x["avg_response_time"], reverse=True)
    slow_queries.sort(key=lambda x: x.get("duration", 0), reverse=True)
    
    return {
        "slow_queries": slow_queries,
        "slow_endpoints": slow_endpoints,
        "total_slow_queries": len(slow_queries),
        "total_slow_endpoints": len(slow_endpoints)
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """生成优化建议"""
    recommendations = []
    
    if analysis["total_slow_endpoints"] > 0:
        recommendations.append(f"发现 {analysis['total_slow_endpoints']} 个慢端点，建议优化：")
        for endpoint in analysis["slow_endpoints"][:5]:  # 只显示前5个
            recommendations.append(
                f"  - {endpoint['endpoint']}: 平均响应时间 {endpoint['avg_response_time']:.3f}s, "
                f"最大响应时间 {endpoint['max_response_time']:.3f}s"
            )
            recommendations.append("    建议：添加缓存、优化数据库查询、使用异步处理")
    
    if analysis["total_slow_queries"] > 0:
        recommendations.append(f"\n发现 {analysis['total_slow_queries']} 个慢查询，建议优化：")
        for query in analysis["slow_queries"][:5]:  # 只显示前5个
            recommendations.append(
                f"  - 操作: {query.get('operation', 'unknown')}, "
                f"耗时: {query.get('duration', 0):.3f}s"
            )
            recommendations.append("    建议：添加数据库索引、优化查询语句、使用连接池")
    
    if not recommendations:
        recommendations.append("未发现慢查询，系统性能良好！")
    
    return recommendations


def main():
    """主函数"""
    # 尝试从性能监控API获取数据
    try:
        import httpx
        response = httpx.get("http://localhost:8001/api/performance/metrics", timeout=5.0)
        if response.status_code == 200:
            performance_data = response.json()
            if isinstance(performance_data, dict) and "data" in performance_data:
                performance_data = performance_data["data"]
        else:
            logger.warning("无法从API获取性能数据，使用空数据")
            performance_data = {}
    except Exception as e:
        logger.warning(f"无法连接到API: {e}，使用空数据")
        performance_data = {}
    
    # 分析性能数据
    logger.info("分析性能数据...")
    analysis = analyze_performance_data(performance_data)
    
    # 生成建议
    recommendations = generate_recommendations(analysis)
    
    # 输出结果
    print("\n" + "="*60)
    print("慢查询分析报告")
    print("="*60)
    print(f"慢端点数量: {analysis['total_slow_endpoints']}")
    print(f"慢查询数量: {analysis['total_slow_queries']}")
    print("\n优化建议:")
    for rec in recommendations:
        print(rec)
    
    # 保存详细报告
    report = {
        "analysis": analysis,
        "recommendations": recommendations,
        "threshold": SLOW_QUERY_THRESHOLD
    }
    
    output_file = Path("slow_queries_analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"详细报告已保存到: {output_file}")
    
    # 返回退出码
    if analysis["total_slow_endpoints"] > 0 or analysis["total_slow_queries"] > 0:
        return 1  # 有慢查询
    return 0  # 无慢查询


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

