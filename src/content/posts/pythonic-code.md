---
author: "luca"
pubDatetime: 2023-05-18T13:20:43+09:00
modDatetime: 2026-10-13T15:32:55+09:00
title: "예제로 익히는 Python 반복과 컬렉션 처리"
slug: "pythonic-code"
featured: false
draft: false
tags: ["학습노트", "python", "pythonic", "style"]
description: "행렬을 돌리거나 중첩 목록을 합칠 때 자주 찾는 Python 문법을 모았습니다. 짧은 표현이 성립하는 입력 조건도 함께 확인합니다."
---

알고리즘 문제를 풀다 보면 매번 비슷한 반복문을 작성하게 됩니다. 몫과 나머지를 따로 구하거나, 두 목록을 인덱스로 맞추거나, 중첩 리스트를 하나로 합치는 코드가 그렇습니다. Python에서 이런 의도를 짧게 표현하는 방법을 작은 예제로 모았습니다.

짧게 쓴다는 이유만으로 더 좋은 코드는 아닙니다. 아래에서는 결과뿐 아니라 어떤 입력을 가정하는지도 같이 봅니다.

## 두 결과가 함께 필요할 때

```python
assert divmod(17, 5) == (3, 2)
assert int("1011", 2) == 11
```

17개를 한 묶음에 5개씩 나눈다면 3묶음과 나머지 2개가 필요합니다. `divmod`는 이 두 값을 함께 구한다는 의도를 보여 줍니다. 항상 더 빠른 문법이라고 외우기보다는 필요한 결과가 무엇인지 드러내는 표현으로 쓰면 됩니다. `int`의 두 번째 인자는 문자열을 읽을 진법입니다.

## 같은 위치의 값을 묶기

```python
animals = ["cat", "dog"]
sounds = ["meow", "woof"]
assert dict(zip(animals, sounds)) == {"cat": "meow", "dog": "woof"}

matrix = [[1, 2, 3], [4, 5, 6]]
assert list(map(list, zip(*matrix))) == [[1, 4], [2, 5], [3, 6]]
assert list(map(list, zip(*matrix[::-1]))) == [[4, 1], [5, 2], [6, 3]]
```

`zip`은 각 입력에서 같은 위치의 값을 꺼내 묶습니다. 행렬의 각 행을 입력으로 풀어 주면 같은 열에 있던 값이 묶이므로 전치가 됩니다. 행의 순서를 뒤집은 뒤 묶은 마지막 예제는 시계 방향 90도 회전입니다.

주의할 점은 `zip`이 기본적으로 가장 짧은 입력에서 끝난다는 것입니다. 길이가 다른 두 목록을 묶으면 긴 쪽의 남은 값은 결과에 들어가지 않습니다. 길이가 반드시 같아야 한다면 별도로 검사하거나 Python 3.10 이상에서 `strict=True`를 사용할 수 있습니다.

## 중첩 목록을 합치거나 조합 만들기

```python
from itertools import chain, combinations, combinations_with_replacement, permutations

rows = [[1, 2], [3], [4, 5]]
assert list(chain.from_iterable(rows)) == [1, 2, 3, 4, 5]
assert [value for row in rows for value in row] == [1, 2, 3, 4, 5]
assert list(combinations("ABC", 2)) == [("A", "B"), ("A", "C"), ("B", "C")]
assert list(permutations("AB", 2)) == [("A", "B"), ("B", "A")]
assert list(combinations_with_replacement("AB", 2)) == [("A", "A"), ("A", "B"), ("B", "B")]
```

중첩 리스트를 합칠 때 `sum(rows, [])`를 쓰면 중간 리스트를 계속 복사하게 됩니다. 여러 묶음을 차례로 순회하려는 목적이라면 `chain.from_iterable`이 더 직접적입니다. 다만 예제처럼 `list`로 감싸면 최종 결과 전체는 메모리에 만듭니다.

조합은 순서를 구분하지 않고, 순열은 순서를 구분합니다. `combinations_with_replacement`는 같은 원소를 다시 고르는 경우도 포함합니다. 문제에서 “같은 항목을 두 번 골라도 되는가”를 먼저 확인하면 사용할 함수를 고르기 쉽습니다.

## 개수와 삽입 위치 찾기

```python
from bisect import bisect_left, bisect_right
from collections import Counter

assert Counter("banana")["a"] == 3
values = [1, 3, 3, 5]
assert bisect_left(values, 3) == 1
assert bisect_right(values, 3) == 3
```

`Counter`는 등장 횟수를 셉니다. `bisect`는 정렬된 목록에서 삽입할 위치를 찾습니다. 예제의 두 3 앞에 넣을 위치는 1이고, 뒤에 넣을 위치는 3입니다. 같은 값이 있는지 알려 주는 함수로 생각하면 반환값을 잘못 사용할 수 있습니다. 입력이 정렬돼 있어야 한다는 조건도 필요합니다.

## 찾지 못한 경우를 for-else로 표현하기

```python
numbers = [1, 3, 5]
for number in numbers:
    if number % 2 == 0:
        print(number)
        break
else:
    print("even number not found")
```

여기서는 짝수를 찾지 못해 `else`가 실행됩니다. `else`는 반복문이 `break` 없이 끝났을 때 실행되므로 빈 목록에서도 동작합니다. 검색 성공 여부를 별도 변수에 저장하던 코드를 이 방식으로 표현할 수 있습니다.

문법을 줄인 뒤 의미를 다시 풀어 써야 한다면 오히려 읽기 어려워진 것일 수 있습니다. 입력 조건과 결과를 예제 하나로 확인할 수 있는 정도로 사용하는 것이 좋겠습니다. 반복자 함수의 자세한 조건은 [Python itertools 문서](https://docs.python.org/3/library/itertools.html)에 정리돼 있습니다.
