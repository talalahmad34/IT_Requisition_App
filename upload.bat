@echo off
echo ===================================================
echo             GIT UPLOADER SCRIPT
echo ===================================================
echo.
echo Initializing Git repository...
echo.
git init
git branch -m main
echo.
echo Linking to your GitHub repository...
echo (It's OK if this next step fails with 'origin already exists')
echo.
git remote add origin https://github.com/talalahmad34/IT_Requisition_App.git
echo.

rem -----------------------------------------------------------------
rem  THIS IS THE NEW, IMPORTANT PART. 
rem  GIT NEEDS TO KNOW WHO YOU ARE.
rem -----------------------------------------------------------------
echo Setting your Git identity...
echo.
git config user.name Talal Ahmad
git config user.email talalahmad34@gmail.com
echo.
rem -----------------------------------------------------------------

echo Adding all files to Git...
echo.
git add .
echo.
echo Committing the files...
echo.
git commit -m "Upload project files and backend"
echo.
echo Forcing the Push (uploading) to GitHub...
echo.
git push -f -u origin main
echo.
echo ===================================================
echo All done! You can check your GitHub page now.
echo ===================================================
echo.
pause