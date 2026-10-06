---
author: "luca"
pubDatetime: 2023-05-18T13:20:43+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Python 표현 노트: 작은 입력과 출력으로 확인하기"
slug: "pythonic-code"
featured: false
draft: false
tags: ["학습노트", "python", "pythonic", "style"]
description: "알고리즘 풀이에서 자주 쓰는 Pythonic 표현들 — divmod, zip, itertools, list comprehension, for-else 등을 모아둔 치트시트입니다."
---

알고리즘 문제를 풀 때 자주 쓰는 Python 3 표현을 작은 입력·출력으로 정리했습니다. 짧은 문법 자체보다 입력을 덜 복사하고, 끝나는 조건이 명확한 표현을 고르는 데 초점을 뒀습니다.

## 몫·나머지와 진법

```python
assert divmod(17, 5) == (3, 2)
assert int("1011", 2) == 11
```

`divmod`는 몫과 나머지를 함께 구한다는 의도를 드러냅니다. 숫자 크기에 따라 항상 더 빠르다는 성능 규칙으로 외우지는 않습니다.

## 순서대로 묶고 행과 열을 바꾸기

```python
animals = ["cat", "dog"]
sounds = ["meow", "woof"]
assert dict(zip(animals, sounds)) == {"cat": "meow", "dog": "woof"}

matrix = [[1, 2, 3], [4, 5, 6]]
assert list(map(list, zip(*matrix))) == [[1, 4], [2, 5], [3, 6]]
assert list(map(list, zip(*matrix[::-1]))) == [[4, 1], [5, 2], [6, 3]]
```

마지막 줄은 직사각형 행렬을 시계 방향으로 90도 회전합니다. `zip`은 기본적으로 가장 짧은 입력에서 끝나므로 행 길이가 다르면 값이 빠질 수 있습니다. 길이가 같아야 하는 입력은 검증하거나 Python 3.10 이상의 `zip(..., strict=True)`를 사용합니다.

## 이어 붙이기와 조합

```python
from itertools import chain, combinations, combinations_with_replacement, permutations

rows = [[1, 2], [3], [4, 5]]
assert list(chain.from_iterable(rows)) == [1, 2, 3, 4, 5]
assert [value for row in rows for value in row] == [1, 2, 3, 4, 5]
assert list(combinations("ABC", 2)) == [("A", "B"), ("A", "C"), ("B", "C")]
assert list(permutations("AB", 2)) == [("A", "B"), ("B", "A")]
assert list(combinations_with_replacement("AB", 2)) == [("A", "A"), ("A", "B"), ("B", "B")]
```

`sum(rows, [])`도 리스트를 합칠 수 있지만, 중간 리스트를 계속 복사합니다. 작은 리스트가 많이 붙으면 누적 복사량이 커지므로 `chain.from_iterable`이나 comprehension이 적합합니다. `chain` 자체는 지연 순회하지만, 위처럼 `list`로 감싸면 최종 결과는 메모리에 만듭니다.

## 빈도와 정렬된 목록의 삽입 위치

```python
from bisect import bisect_left, bisect_right
from collections import Counter

assert Counter("banana")["a"] == 3
values = [1, 3, 3, 5]
assert bisect_left(values, 3) == 1
assert bisect_right(values, 3) == 3
assert sorted([3, 1, 2]) == [1, 2, 3]
```

`bisect`는 입력이 정렬되어 있다는 전제가 있습니다. 반환하는 것은 같은 값의 존재 여부가 아니라 정렬을 유지할 삽입 위치입니다.

## for-else는 break 없이 끝났을 때

```python
numbers = [1, 3, 5]
for number in numbers:
    if number % 2 == 0:
        print(number)
        break
else:
    print("even number not found")
```

이 예제는 `even number not found`를 출력합니다. `else`는 반복문이 `break`로 중단되지 않고 끝났을 때 실행되므로, 빈 목록에서도 실행됩니다.

나머지 자주 쓰는 표현은 `"".join(strings)`, `list(map(int, strings))`, `a, b = b, a`입니다. 파일은 `with open(...)`으로 열고 파일 객체를 직접 순회하면 전체 줄을 한꺼번에 읽지 않아도 됩니다. 반복자 도구의 입력 조건은 [Python itertools 문서](https://docs.python.org/3/library/itertools.html)에서 확인할 수 있습니다.
