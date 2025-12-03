@echo off
chcp 65001 > nul
echo ================================================
echo VabHub - 漫画收藏自动追更
echo ================================================
echo.

cd /d "%~dp0backend"

echo 开始执行漫画收藏追更...
python sync_favorite_manga.py

echo.
echo 任务完成，按任意键退出...
pause > nul