---
author: "luca"
pubDatetime: 2023-05-18T13:20:43+09:00
title: "Python답게"
slug: "pythonic-code"
featured: false
draft: false
tags: ["python", "pythonic", "style"]
description: "알고리즘 풀이에서 자주 쓰는 Pythonic 표현들 — divmod, zip, itertools, list comprehension, for-else 등을 모아둔 치트시트입니다."
---

> 알고리즘 문제를 풀면서 자주 쓰이는 Pythonic 한 표현을 정리한 노트입니다.

## 몫과 나머지

```python
print(*divmod(a, b))
```

참고: `divmod`는 작은 숫자에서는 느리지만 큰 숫자에서는 `a//b, a%b`보다 빠릅니다.

## n진법 문자열을 10진법으로 변환

```python
int(x, base=진법)
```

## 문자열 정렬

```python
s.ljust(n)   # 좌측 정렬
s.center(n)  # 가운데 정렬
s.rjust(n)   # 우측 정렬
```

## 알파벳 상수

```python
import string
string.ascii_lowercase  # abcdefghijklmnopqrstuvwxyz
string.ascii_uppercase  # ABCDEFGHIJKLMNOPQRSTUVWXYZ
string.digits           # 0123456789
```

## 원본 유지하며 정렬

```python
list2 = sorted(list1)
```

## ZIP 함수

여러 iterable 을 효율적으로 순회합니다.

```python
for i in zip(mylist, new_list):
    print(i)
```

병렬 리스트로부터 딕셔너리 생성:

```python
dict(zip(animals, sounds))
```

2차원 리스트 전치:

```python
list(map(list, zip(*mylist)))
```

인접 요소 비교:

```python
for n1, n2 in zip(mylist, mylist[1:]):
    print(abs(n1 - n2))
```

## 2차원 배열 회전

```python
# 시계 방향 90도
list(map(list, zip(*mylist[::-1])))

# 반시계 방향 90도
list(map(list, zip(*mylist)))[::-1]
```

## MAP — 타입 변환

```python
list2 = list(map(int, list1))
```

## JOIN — 요소 연결

```python
answer = ''.join(my_list)
```

## PRODUCT — 곱집합

```python
import itertools
list(itertools.product(iterable1, iterable2))
```

## 2D를 1D 리스트로 변환

```python
# 방법들
sum(my_list, [])
list(itertools.chain.from_iterable(my_list))
[element for array in my_list for element in array]
```

## 순열과 조합

```python
import itertools

# 순열
list(map(''.join, itertools.permutations(pool, 2)))

# 조합
list(combinations(l, 2))

# 중복 조합
list(combinations_with_replacement(l, 2))
```

## COUNTER — 빈도 세기

```python
import collections
answer = collections.Counter(my_list)
```

## List Comprehension with IF

```python
answer = [number**2 for number in mylist if number % 2 == 0]
```

## FOR-ELSE 문법

플래그 변수를 따로 둘 필요가 없습니다.

```python
for number in numbers:
    if condition:
        break
else:
    # 조건을 만족하지 않을 때 실행
    print('not found')
```

## 변수 값 교환

```python
a, b = b, a
```

## 이진 탐색

```python
import bisect
print(bisect.bisect(mylist, 3))
```

## 클래스 인스턴스 출력

```python
class Coord:
    def __str__(self):
        return '({}, {})'.format(self.x, self.y)
```

## INF — 무한수

```python
min_val = float('inf')
max_val = float('-inf')
```

## 파일 입출력

```python
with open('myfile.txt') as file:
    for line in file.readlines():
        print(line.strip().split('\t'))
```
