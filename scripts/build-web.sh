APPNAME="Snowball Effect - GJ Version"
ROOT=./src

mkdir $ROOT/assets
cp -r ./assets/ $ROOT/assets

./venv/bin/pygbag \
    --template toolshed.tmpl \
    --app_name "$APPNAME" \
    --title "$APPNAME" \
    --package "$APPNAME" \
    --icon ./assets/icon.png \
    $ROOT
    # --build \
    
