#!/bin/bash

source venv/bin/activate
cd lambda
zip -r index.zip .
cd ..
aws lambda update-function-code --function-name=SmartShelvesLambda --zip-file fileb://lambda/index.zip
rm lambda/index.zip
deactivate
