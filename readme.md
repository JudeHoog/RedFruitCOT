# RedFruitCOT

Openai's strawberry is just a simple chain of thought (COT) autonomous gradeing loop. Here is a crude exaple with aws bedrock and llama 3.1 70b.

#### Usage

You need boto3 and a aws cli key config file
```sh
python3 redfruit.py
```
Use htmlize.py to make a human readable html file from response.txt (outputted from redfruit.py)
```sh
python3 htmlize.py
```