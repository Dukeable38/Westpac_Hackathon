import re

def abn_valid(value: str) -> bool:
    value = re.sub(r'\s', '', value)
    if not value.isdigit() or len(value) != 11:
        return False
    digits = list(map(int, value)); digits[0] -= 1
    return sum(a*b for a,b in zip(digits,[10,1,3,5,7,9,11,13,15,17,19])) % 89 == 0

def acn_valid(value: str) -> bool:
    value = re.sub(r'\s', '', value)
    return len(value) == 9 and value.isdigit() and (10-sum(int(a)*b for a,b in zip(value[:8],range(8,0,-1)))%10)%10 == int(value[-1])
