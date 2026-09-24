@echo off
chcp 65001 >nul
title Cai dat lan dau - Tro ly Thu tuc hanh chinh V10.5
cd /d "%~dp0"

echo.
echo  Dang chay cai dat lan dau. Cai gi co roi se duoc bo qua.
echo  Lan dau tren may moi co the mat 30-60 phut:
echo    - tai thu vien + mo hinh ngon ngu
echo    - cao ~1.350 thu tuc cap Xa/Phuong ve may (He thong 2)
echo  Du lieu thu tuc KHONG nam trong git nen may nao cung phai cao mot lan.
echo  Muon bo qua buoc cao: chay lai voi tham so -SkipScrape
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "Utility\scripts\setup.ps1" %*

echo.
pause
