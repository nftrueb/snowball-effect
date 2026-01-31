APPNAME="Snowball Effect - GJ Version"
MAIN_SCRIPT="src/main.py"
ICON="assets/icon-1024.icns"

./venv/bin/pyinstaller --windowed \
    --noconfirm \
    --clean \
    --add-data ./assets/*.png:./assets \
    --optimize 1 \
    --icon $ICON \
    --name "$APPNAME" \
    $MAIN_SCRIPT

rm -rf /Applications/"$APPNAME".app
cp -r dist/"$APPNAME".app /Applications/

ln -s /Applications/"$APPNAME".app ~/Desktop/"$APPNAME"

echo "Successfully updated "$APPNAME".app in /Applications"