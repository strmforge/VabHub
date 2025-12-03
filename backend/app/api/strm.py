"""
STRM API路由
提供STRM文件重定向服务
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger
from jose import JWTError, jwt

from app.core.database import get_db
from app.modules.strm.service import STRMService
from app.modules.strm.config import STRMConfig
from app.core.schemas import error_response, BaseResponse
from app.core.config import settings


router = APIRouter(prefix="/strm", tags=["strm"])


# 获取STRM配置（单例）
_strm_config: Optional[STRMConfig] = None


def get_strm_config() -> STRMConfig:
    """获取STRM配置（单例）"""
    global _strm_config
    if _strm_config is None:
        _strm_config = STRMConfig()
    return _strm_config


@router.get("/subtitle/{storage_type}/{token}")
async def stream_subtitle(
    storage_type: str,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    STRM字幕文件流媒体重定向端点
    
    根据JWT token中的字幕pick_code获取115网盘字幕下载地址并302重定向或代理
    
    Args:
        storage_type: 云存储类型（115/123）
        token: JWT token（包含字幕pick_code等信息）
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        302重定向到115网盘字幕下载地址，或代理流式响应
    """
    try:
        # 获取STRM配置
        config = get_strm_config()
        
        # 1. 验证JWT token
        jwt_secret = config.jwt_secret
        if not jwt_secret:
            from app.core.config import settings
            jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
            if not jwt_secret:
                logger.error("JWT密钥未配置，请设置JWT_SECRET_KEY")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT密钥未配置"
                )
        
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=[config.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            logger.warning(f"STRM字幕token已过期: {token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期"
            )
        except JWTError as e:
            logger.warning(f"STRM字幕token验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token无效"
            )
        
        # 2. 提取字幕pick_code
        subtitle_pick_code = payload.get("subtitle_pick_code")
        token_storage_type = payload.get("storage_type", "115")
        
        if not subtitle_pick_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token中缺少subtitle_pick_code"
            )
        
        # 3. 验证存储类型
        if storage_type != token_storage_type:
            logger.warning(f"存储类型不匹配: {storage_type} != {token_storage_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="存储类型不匹配"
            )
        
        # 4. 获取115网盘API客户端
        if storage_type != "115":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前只支持115网盘字幕"
            )
        
        from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
        from app.core.cloud_storage.providers.cloud_115_oauth import Cloud115OAuth
        
        # 获取115认证信息
        oauth = Cloud115OAuth()
        access_token = await oauth.get_valid_access_token()
        
        if not access_token:
            logger.error("115网盘认证失败，无法获取字幕")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="115网盘认证失败"
            )
        
        cloud_115_api = Cloud115API(access_token=access_token)
        
        # 5. 获取字幕文件下载地址
        result = await cloud_115_api.get_download_url(pick_code=subtitle_pick_code)
        
        if not result.get("success"):
            logger.error(f"获取字幕下载地址失败: {result.get('message', '未知错误')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取字幕下载地址失败: {result.get('message', '未知错误')}"
            )
        
        download_url = result.get("download_url")
        if not download_url:
            logger.error("字幕下载地址为空")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="字幕下载地址为空"
            )
        
        # 6. 检查是否使用代理模式（字幕文件通常较小，直接302跳转即可）
        # 但为了兼容性，也支持代理模式
        use_proxy = (
            "range" in [h.lower() for h in request.headers.keys()] or
            "accept" in [h.lower() for h in request.headers.keys()]
        )
        
        if use_proxy:
            # 代理模式：完全控制请求头和响应
            return await _proxy_stream_request(download_url, request)
        else:
            # 302跳转模式：简单快速（字幕文件通常较小）
            return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STRM字幕重定向失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STRM字幕重定向失败: {str(e)}"
        )


@router.get("/stream/{storage_type}/{token}")
async def stream_file(
    storage_type: str,
    token: str,
    request: Request,
    ts: Optional[int] = Query(None, description="HMAC签名时间戳"),
    sig: Optional[str] = Query(None, description="HMAC签名"),
    db: AsyncSession = Depends(get_db)
):
    """
    STRM文件流媒体重定向端点
    
    根据JWT token中的pick_code获取115网盘下载地址并302重定向
    如果启用了HMAC签名，会先验证HMAC签名
    
    Args:
        storage_type: 云存储类型（115/123）
        token: JWT token（包含pick_code等信息）
        ts: HMAC签名时间戳（可选）
        sig: HMAC签名（可选）
        request: FastAPI请求对象
        db: 数据库会话
    
    Returns:
        302重定向到115网盘下载地址
    """
    try:
        # 获取STRM配置
        config = get_strm_config()
        
        # 0. 如果启用了HMAC签名，先验证HMAC签名
        if config.enable_hmac_signature:
            if not ts or not sig:
                logger.warning("HMAC签名已启用，但缺少ts或sig参数")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="HMAC签名验证失败：缺少签名参数"
                )
            
            # 构建路径（用于验证）
            path = f"{config.local_redirect_base_path}/{storage_type}/{token}"
            
            # 验证HMAC签名
            from app.modules.strm.hmac_signer import get_hmac_signer
            hmac_signer = get_hmac_signer(config.hmac_secret or None)
            
            if not hmac_signer.verify(path, ts, sig, ttl=config.hmac_ttl):
                logger.warning(f"HMAC签名验证失败: path={path}, ts={ts}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="HMAC签名验证失败"
                )
            
            logger.debug(f"HMAC签名验证通过: path={path}")
        
        # 1. 验证JWT token
        # 获取JWT密钥（使用系统配置）
        jwt_secret = config.jwt_secret
        if not jwt_secret:
            # 使用系统配置的JWT密钥
            from app.core.config import settings
            jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
            if not jwt_secret:
                logger.error("JWT密钥未配置，请设置JWT_SECRET_KEY")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="JWT密钥未配置"
                )
        
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=[config.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            logger.warning(f"STRM token已过期: {token[:20]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期"
            )
        except JWTError as e:
            logger.warning(f"STRM token验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token无效"
            )
        
        # 2. 提取pick_code和存储类型
        pick_code = payload.get("pick_code")
        token_storage_type = payload.get("storage_type")
        
        if not pick_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token中缺少pick_code"
            )
        
        # 3. 验证存储类型
        if token_storage_type != storage_type:
            logger.warning(f"存储类型不匹配: token={token_storage_type}, url={storage_type}")
            # 不强制要求完全匹配，使用token中的存储类型
        
        # 4. 根据存储类型获取下载地址
        download_url = None
        
        if storage_type == "115" or token_storage_type == "115":
            # 115网盘
            strm_service = STRMService(db)
            api_client = await strm_service.get_115_api_client()
            
            if not api_client:
                # 尝试刷新token
                await strm_service.refresh_115_token()
                api_client = await strm_service.get_115_api_client()
            
            if not api_client:
                logger.error("无法获取115网盘API客户端")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="115网盘服务不可用，请检查认证配置"
                )
            
            # 获取下载地址
            result = await api_client.get_download_url(pick_code=pick_code)
            
            if result.get("success"):
                download_url = result.get("download_url")
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(f"获取115网盘下载地址失败: {error_msg}")
                
                # 如果是认证失败，尝试刷新token
                if "401" in error_msg or "token" in error_msg.lower() or "认证" in error_msg:
                    logger.info("尝试刷新115网盘token")
                    await strm_service.refresh_115_token()
                    api_client = await strm_service.get_115_api_client()
                    
                    if api_client:
                        result = await api_client.get_download_url(pick_code=pick_code)
                        if result.get("success"):
                            download_url = result.get("download_url")
        
        elif storage_type == "123":
            # 123云盘（待实现）
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="123云盘暂未实现"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的存储类型: {storage_type}"
            )
        
        # 5. 检查是否获取到下载地址
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或无法获取下载地址"
            )
        
        # 6. 记录日志
        logger.info(f"STRM重定向: {storage_type}/{pick_code} -> {download_url[:80]}...")
        
        # 7. 检查是否使用代理模式（推荐，解决字幕和音频问题）
        # 如果请求包含Range头，使用代理模式（支持断点续传）
        # 否则使用302跳转（节省服务器资源）
        use_proxy = (
            "range" in [h.lower() for h in request.headers.keys()] or
            "accept" in [h.lower() for h in request.headers.keys()]
        )
        
        if use_proxy:
            # 代理模式：完全控制请求头和响应，解决字幕和音频问题
            return await _proxy_stream_request(download_url, request)
        else:
            # 302跳转模式：简单快速，但可能有问题
            return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STRM重定向失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STRM重定向失败: {str(e)}"
        )


async def _proxy_stream_request(download_url: str, request: Request) -> StreamingResponse:
    """
    代理流媒体请求（支持Range请求和所有HTTP头）
    
    解决302跳转的问题：
    1. 传递Range请求头（支持断点续传）
    2. 传递Accept头（告诉服务器客户端支持的格式）
    3. 传递User-Agent等关键头信息
    4. 完全控制响应头（Content-Type、Content-Range等）
    
    Args:
        download_url: 115网盘下载地址
        request: FastAPI请求对象
    
    Returns:
        流式响应
    """
    try:
        import httpx
        
        # 1. 构建请求头（传递原始请求的关键头信息）
        headers = {}
        
        # Range请求（关键！视频播放必需）
        if "range" in request.headers:
            headers["range"] = request.headers["range"]
        
        # Accept头（告诉服务器客户端支持的格式）
        if "accept" in request.headers:
            headers["accept"] = request.headers["accept"]
        else:
            headers["accept"] = "video/mp4, audio/mp4, */*"
        
        # User-Agent
        if "user-agent" in request.headers:
            headers["user-agent"] = request.headers["user-agent"]
        
        # Referer（某些服务器需要）
        if "referer" in request.headers:
            headers["referer"] = request.headers["referer"]
        
        # 2. 代理请求
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=30.0),  # 视频流需要更长的超时
            follow_redirects=True
        ) as client:
            response = await client.get(
                download_url,
                headers=headers
            )
            
            # 3. 构建响应头
            response_headers = {}
            
            # 传递关键响应头
            if "content-type" in response.headers:
                response_headers["content-type"] = response.headers["content-type"]
            if "content-length" in response.headers:
                response_headers["content-length"] = response.headers["content-length"]
            if "content-range" in response.headers:
                response_headers["content-range"] = response.headers["content-range"]
            if "accept-ranges" in response.headers:
                response_headers["accept-ranges"] = response.headers["accept-ranges"]
            
            # 4. 返回流式响应
            return StreamingResponse(
                response.iter_bytes(),
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "video/mp4")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理流媒体请求失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代理请求失败: {str(e)}"
        )


class EmitSTRMRequest(BaseModel):
    """生成STRM文件请求"""
    cloud_file_id: str
    cloud_storage: str = "115"
    local_path: Optional[str] = None


@router.post("/emit", response_model=BaseResponse)
async def emit_strm(
    request_data: EmitSTRMRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    生成STRM文件（手动触发）
    
    Args:
        cloud_file_id: 云存储文件ID（pick_code）
        cloud_storage: 云存储类型（115/123）
        local_path: 本地路径（可选，如果不提供则使用配置的媒体库路径）
        request: FastAPI请求对象（用于生成URL）
    
    Returns:
        生成结果
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.generator import STRMGenerator
        from app.modules.strm.service import STRMService
        
        # 获取STRM配置
        config = get_strm_config()
        
        # 获取115 API客户端
        strm_service = STRMService(db)
        api_client = await strm_service.get_115_api_client()
        
        if not api_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="115网盘服务不可用，请检查认证配置"
            )
        
        # 创建STRM生成器
        strm_generator = STRMGenerator(
            config=config,
            db=db,
            cloud_115_api=api_client
        )
        
        # 生成STRM文件
        result = await strm_generator.generate_strm_file(
            cloud_file_id=request_data.cloud_file_id,
            cloud_storage=request_data.cloud_storage,
            local_path=request_data.local_path,
            request=request
        )
        
        if result.get("success"):
            return success_response(
                data=result,
                message="STRM文件生成成功"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="STRM_GENERATION_FAILED",
                    error_message=result.get("error", "STRM文件生成失败")
                ).model_dump()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成STRM文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"生成STRM文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/config", response_model=BaseResponse)
async def get_strm_config_endpoint(db: AsyncSession = Depends(get_db)):
    """
    获取STRM配置
    
    优先从数据库读取，如果数据库中没有则使用默认配置
    
    Returns:
        STRM配置信息
    """
    try:
        from app.core.schemas import success_response
        from app.modules.settings.service import SettingsService
        
        global _strm_config
        
        # 尝试从数据库读取配置
        settings_service = SettingsService(db)
        strm_settings = await settings_service.get_settings_by_category("strm")
        
        # 如果数据库中有配置，使用数据库中的配置
        if strm_settings:
            config_dict = {}
            for key, value in strm_settings.items():
                # 移除 "strm_" 前缀
                if key.startswith("strm_"):
                    config_key = key[5:]  # 移除 "strm_" 前缀
                    config_dict[config_key] = value
                else:
                    config_dict[key] = value
            
            # 创建配置对象
            _strm_config = STRMConfig(**config_dict)
        else:
            # 如果数据库中没有配置，使用默认配置
            config = get_strm_config()
            config_dict = config.model_dump()
        
        return success_response(data=config_dict, message="获取STRM配置成功")
    except Exception as e:
        logger.error(f"获取STRM配置失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取STRM配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/config", response_model=BaseResponse)
async def update_strm_config_endpoint(
    config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    更新STRM配置
    
    Args:
        config_data: STRM配置数据（字典格式）
    
    Returns:
        更新结果
    """
    try:
        from app.core.schemas import success_response
        
        global _strm_config
        
        # 更新配置
        if _strm_config is None:
            _strm_config = STRMConfig()
        
        # 更新配置字段
        for key, value in config_data.items():
            if hasattr(_strm_config, key):
                setattr(_strm_config, key, value)
        
        # 将配置保存到数据库的 settings 表中
        from app.modules.settings.service import SettingsService
        settings_service = SettingsService(db)
        for key, value in config_data.items():
            setting_key = f"strm_{key}"
            await settings_service.set_setting(setting_key, value, category="strm")
        
        logger.info("STRM配置已更新并保存到数据库")
        return success_response(
            data=_strm_config.model_dump(),
            message="更新STRM配置成功"
        )
    except Exception as e:
        logger.error(f"更新STRM配置失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新STRM配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "strm"}


@router.get("/network-info", response_model=BaseResponse)
async def get_network_info():
    """
    获取网络信息（用于Local Redirect模式自动配置）
    
    自动检测内网IP和端口，帮助用户快速配置内外网访问
    
    Returns:
        网络信息（内网IP、端口、外网配置建议、重定向URL示例等）
    """
    try:
        from app.core.schemas import success_response
        from app.utils.network import get_local_ip, get_all_local_ips
        
        # 获取内网IP
        primary_ip = get_local_ip()
        all_ips = get_all_local_ips()
        
        # 获取系统端口
        system_port = settings.PORT if hasattr(settings, 'PORT') else 8092
        
        # 获取STRM配置，检查外网配置
        config = get_strm_config()
        
        # 构建内网重定向URL示例
        internal_url_example = None
        if primary_ip:
            internal_port = config.local_redirect_port if config.local_redirect_port > 0 else system_port
            # 如果端口是默认值，建议使用Emby默认端口8096
            if internal_port == system_port and system_port == 8092:
                internal_port = 8096  # Emby默认端口
            internal_url_example = f"http://{primary_ip}:{internal_port}/api/strm/stream/115/TOKEN"
        
        # 构建外网重定向URL示例
        external_url_example = None
        if config.external_redirect_host:
            protocol = "https" if config.use_https else "http"
            
            # 提取主机和端口（支持域名中带端口号）
            external_host = config.external_redirect_host
            external_port = config.external_redirect_port
            
            # 如果域名中包含端口号，提取出来
            if ':' in external_host:
                host_part, port_part = external_host.rsplit(':', 1)
                try:
                    port_from_host = int(port_part)
                    external_host = host_part
                    if external_port == 0:  # 如果未配置端口，使用域名中的端口
                        external_port = port_from_host
                except ValueError:
                    pass  # 域名格式错误，忽略
            
            # 如果仍未确定端口，使用默认端口
            if external_port == 0:
                external_port = 443 if config.use_https else 80
            
            # 构建URL（始终显示端口，因为家庭宽带通常关闭80/443）
            external_url_example = f"{protocol}://{external_host}:{external_port}/api/strm/stream/115/TOKEN"
        
        network_info = {
            "primary_ip": primary_ip or "localhost",
            "all_ips": all_ips or ["localhost"],
            "port": system_port,
            "internal_url_example": internal_url_example,
            "external_url_example": external_url_example,
            "external_configured": bool(config.external_redirect_host),
            "auto_adapt_enabled": config.auto_adapt_network,
            "suggestions": {
                "internal_port": "建议使用系统端口或自定义内网端口。常见媒体库默认端口：Emby/Jellyfin: 8096, Plex: 32400",
                "external_domain": "外网访问建议使用域名（解决公网IP跳动问题），支持带端口号，例如：vabhub.example.com:8096 或 frp.example.com:6000（注意：如果使用默认端口映射，建议配置为 domain.com:端口号，端口号应与媒体库默认端口一致：Emby/Jellyfin: 8096, Plex: 32400，这样客户端只需填写域名即可连接）",
                "external_port": "外网端口建议：如果域名中已包含端口号，此配置可留空；否则建议使用媒体库默认端口（Emby/Jellyfin: 8096, Plex: 32400，如果使用默认端口映射），或自定义端口（例如：6000等），因为家庭宽带通常关闭443和80端口",
                "auto_adapt": "启用自动适配后，系统会根据请求来源自动选择内网/外网地址"
            }
        }
        
        return success_response(
            data=network_info,
            message="获取网络信息成功"
        )
    except Exception as e:
        logger.error(f"获取网络信息失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取网络信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/incremental-sync", response_model=BaseResponse)
async def incremental_sync_alias(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    增量同步STRM文件（别名端点）
    
    映射到 /sync/incremental
    """
    return await incremental_sync(cloud_storage, db)


@router.post("/full-sync", response_model=BaseResponse)
async def full_sync_alias(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    全量同步STRM文件（别名端点）
    
    映射到 /sync/full
    """
    return await full_sync(cloud_storage, db)


@router.post("/sync/incremental", response_model=BaseResponse)
async def incremental_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    增量同步STRM文件
    
    只同步新增和变更的文件，提高同步效率
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        同步结果
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.config import STRMConfig
        from app.modules.strm.file_operation_mode import STRMSyncConfig
        from app.modules.strm.sync_manager import STRMSyncManager
        from app.modules.strm.service import STRMService
        
        # 获取STRM配置
        config = get_strm_config()
        
        # 获取同步配置
        sync_config = STRMSyncConfig(
            enabled=True,
            auto_sync=False,  # 手动触发，不自动同步
            sync_interval=3600,
            realtime_compare=False,  # 手动触发，不实时对比
            compare_interval=300,
            auto_delete_on_cloud_delete=True
        )
        
        # 获取115 API客户端
        strm_service = STRMService(db)
        api_client = await strm_service.get_115_api_client()
        
        if not api_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="115网盘服务不可用，请检查认证配置"
            )
        
        # 创建同步管理器
        sync_manager = STRMSyncManager(
            db=db,
            sync_config=sync_config,
            strm_config=config,
            cloud_storage=cloud_storage,
            cloud_115_api=api_client
        )
        
        # 使用任务管理器启动同步任务
        from app.modules.strm.task_manager import get_sync_task_manager
        task_manager = get_sync_task_manager()
        
        # 启动同步任务（异步执行）
        task_id = await task_manager.start_sync_task(
            sync_type="incremental",
            cloud_storage=cloud_storage,
            sync_manager=sync_manager
        )
        
        return success_response(
            data={"task_id": task_id, "status": "started"},
            message=f"增量同步任务已启动，任务ID: {task_id}"
        )
    except Exception as e:
        logger.error(f"增量同步失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"增量同步失败: {str(e)}"
            ).model_dump()
        )


@router.post("/sync/full", response_model=BaseResponse)
async def full_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    全量同步STRM文件
    
    扫描所有文件并生成STRM文件，用于初始化或修复
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        同步结果
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.config import STRMConfig
        from app.modules.strm.file_operation_mode import STRMSyncConfig
        from app.modules.strm.sync_manager import STRMSyncManager
        from app.modules.strm.service import STRMService
        
        # 获取STRM配置
        config = get_strm_config()
        
        # 获取同步配置
        sync_config = STRMSyncConfig(
            enabled=True,
            auto_sync=False,  # 手动触发，不自动同步
            sync_interval=3600,
            realtime_compare=False,  # 手动触发，不实时对比
            compare_interval=300,
            auto_delete_on_cloud_delete=True
        )
        
        # 获取115 API客户端
        strm_service = STRMService(db)
        api_client = await strm_service.get_115_api_client()
        
        if not api_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="115网盘服务不可用，请检查认证配置"
            )
        
        # 创建同步管理器
        sync_manager = STRMSyncManager(
            db=db,
            sync_config=sync_config,
            strm_config=config,
            cloud_storage=cloud_storage,
            cloud_115_api=api_client
        )
        
        # 使用任务管理器启动同步任务
        from app.modules.strm.task_manager import get_sync_task_manager
        task_manager = get_sync_task_manager()
        
        # 启动同步任务（异步执行）
        task_id = await task_manager.start_sync_task(
            sync_type="full",
            cloud_storage=cloud_storage,
            sync_manager=sync_manager,
            cloud_media_library_path=config.cloud_media_library_path,
            check_local_missing_only=False
        )
        
        return success_response(
            data={"task_id": task_id, "status": "started"},
            message=f"全量同步任务已启动，任务ID: {task_id}"
        )
    except Exception as e:
        logger.error(f"全量同步失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"全量同步失败: {str(e)}"
            ).model_dump()
        )


@router.post("/sync/start", response_model=BaseResponse)
async def start_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    启动同步任务（手动触发，用于首次全量同步）
    
    注意：自动增量同步功能已移除，因为系统已有完整工作流（下载→上传→STRM生成）。
    此端点仅用于手动触发首次全量同步。
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        启动结果
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.config import STRMConfig
        from app.modules.strm.file_operation_mode import STRMSyncConfig
        from app.modules.strm.sync_manager import STRMSyncManager
        from app.modules.strm.service import STRMService
        
        # 获取STRM配置
        config = get_strm_config()
        
        # 获取同步配置（手动触发，不自动同步）
        sync_config = STRMSyncConfig(
            strm_library_path=config.media_library_path,
            auto_sync=False,  # 不自动同步（已移除自动增量同步功能）
            sync_interval=3600,
            realtime_compare=False,  # 不实时对比（已移除自动增量同步功能）
            compare_interval=300,
            auto_delete_on_cloud_delete=True
        )
        
        # 获取115 API客户端
        strm_service = STRMService(db)
        api_client = await strm_service.get_115_api_client()
        
        if not api_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="115网盘服务不可用，请检查认证配置"
            )
        
        # 创建同步管理器
        sync_manager = STRMSyncManager(
            db=db,
            sync_config=sync_config,
            strm_config=config,
            cloud_storage=cloud_storage,
            cloud_115_api=api_client
        )
        
        # 使用任务管理器启动同步任务
        from app.modules.strm.task_manager import get_sync_task_manager
        task_manager = get_sync_task_manager()
        
        # 启动同步任务（自动判断全量/增量）
        task_id = await task_manager.start_sync_task(
            sync_type="auto",  # 自动判断
            cloud_storage=cloud_storage,
            sync_manager=sync_manager
        )
        
        return success_response(
            data={"task_id": task_id, "status": "started"},
            message=f"同步任务已启动，任务ID: {task_id}"
        )
    except Exception as e:
        logger.error(f"启动同步任务失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"启动同步任务失败: {str(e)}"
            ).model_dump()
        )


@router.post("/sync/stop", response_model=BaseResponse)
async def stop_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    停止自动同步任务
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        停止结果
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.task_manager import get_sync_task_manager
        
        # 获取同步任务管理器
        task_manager = get_sync_task_manager()
        
        # 停止所有运行中的任务
        await task_manager.stop_all_tasks()
        
        return success_response(
            data={"status": "stopped", "stopped_count": len(task_manager.running_tasks)},
            message="所有同步任务已停止"
        )
    except Exception as e:
        logger.error(f"停止同步任务失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"停止同步任务失败: {str(e)}"
            ).model_dump()
        )


@router.get("/sync/tasks", response_model=BaseResponse)
async def list_sync_tasks(
    db: AsyncSession = Depends(get_db)
):
    """
    列出所有运行中的同步任务
    
    Returns:
        运行中的任务列表
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.task_manager import get_sync_task_manager
        
        task_manager = get_sync_task_manager()
        tasks = await task_manager.list_running_tasks()
        
        return success_response(
            data={"tasks": tasks, "count": len(tasks)},
            message=f"获取到 {len(tasks)} 个运行中的任务"
        )
    except Exception as e:
        logger.error(f"获取同步任务列表失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取同步任务列表失败: {str(e)}"
            ).model_dump()
        )


@router.get("/sync/tasks/{task_id}", response_model=BaseResponse)
async def get_sync_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取同步任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态信息
    """
    try:
        from app.core.schemas import success_response, error_response
        from app.modules.strm.task_manager import get_sync_task_manager
        
        task_manager = get_sync_task_manager()
        task_status = await task_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"任务 {task_id} 不存在"
                ).model_dump()
            )
        
        return success_response(
            data=task_status,
            message="获取任务状态成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取任务状态失败: {str(e)}"
            ).model_dump()
        )


@router.post("/sync/tasks/{task_id}/stop", response_model=BaseResponse)
async def stop_sync_task_by_id(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    停止指定的同步任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        停止结果
    """
    try:
        from app.core.schemas import success_response, error_response
        from app.modules.strm.task_manager import get_sync_task_manager
        
        task_manager = get_sync_task_manager()
        success = await task_manager.stop_sync_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"任务 {task_id} 不存在或已完成"
                ).model_dump()
            )
        
        return success_response(
            data={"task_id": task_id, "status": "stopped"},
            message=f"任务 {task_id} 已停止"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"停止任务失败: {str(e)}"
            ).model_dump()
        )


@router.get("/sync/history", response_model=BaseResponse)
async def get_sync_history(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    sync_type: Optional[str] = Query(None, description="同步类型过滤（full/incremental）"),
    status: Optional[str] = Query(None, description="状态过滤（pending/running/completed/failed/cancelled）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取同步任务历史
    
    Args:
        limit: 返回数量限制
        sync_type: 同步类型过滤（full/incremental）
        status: 状态过滤（pending/running/completed/failed/cancelled）
    
    Returns:
        任务历史列表
    """
    try:
        from app.core.schemas import success_response
        from app.modules.strm.task_manager import get_sync_task_manager
        
        task_manager = get_sync_task_manager()
        history = await task_manager.list_task_history(
            limit=limit,
            sync_type=sync_type,
            status=status
        )
        
        return success_response(
            data={"history": history, "count": len(history)},
            message=f"获取到 {len(history)} 条历史记录"
        )
    except Exception as e:
        logger.error(f"获取同步任务历史失败: {e}")
        from app.core.schemas import error_response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取同步任务历史失败: {str(e)}"
            ).model_dump()
        )

