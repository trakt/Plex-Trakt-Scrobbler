coverage run --rcfile .coveragerc -m py.test Trakttv.bundle/Contents/Tests

if [ "$1" = "html" ]; then
    echo "Generating html report..."

    coverage html
else
    echo "Generating simple report..."

    coverage report
fi

echo "Done"