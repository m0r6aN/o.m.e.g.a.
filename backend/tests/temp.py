# Given an array A of N integers and an integer K, rotate the array to the right K times.
# Each rotation moves the last element to the front.

# Optimized Version: Use Modulo & Slicing (O(1) Insert)
def cyclic_rotation(A, K):
    if not A:
        return []
    K = K % len(A)
    return A[-K:] + A[:-K]


# A non-empty array A consisting of N integers is given. The array contains an odd number of elements, and each element occurs an even number of times, except for one element that occurs exactly once.
# Using XOR (The Pro Move)
def find_unpaired(A):
    result = 0
    for num in A:
        result ^= num
    return result


#A frog wants to cross a river. She can jump to the other side only after leaves have fallen on every position from 1 to X (inclusive).

# You’re given:
# an integer X (the far bank)
# an array A where A[i] represents the position a leaf falls at time i
# Return the earliest time when all positions 1..X are covered by at least one leaf. If it's not possible, return -1.
def frog_river_one(X, A):
    positions = set()
    for i, pos in enumerate(A):
        positions.add(pos)
        if len(positions) == X:
            return i
    return -1

# Tests
assert frog_river_one(5, [1, 3, 1, 4, 2, 3, 5, 4]) == 6
assert frog_river_one(1, [1]) == 0
assert frog_river_one(3, [1, 1, 1, 1]) == -1
assert frog_river_one(3, [1, 3, 2]) == 2
assert frog_river_one(2, []) == -1

# An array A of N integers represents numbers on a tape.
# You can cut the tape at any position P (1 ≤ P < N) to divide it into two parts:

# Left: A[0] + ... + A[P-1]
# Right: A[P] + ... + A[N-1]

# Your task:
# Return the minimum absolute difference between the sum of the two parts for any valid P.
def tape_equilibrium(A):
    left_sum = 0
    right_sum = sum(A)
    min_diff = float('inf')
    for i in range(len(A) - 1):
        left_sum += A[i]
        right_sum -= A[i]
        diff = abs(left_sum - right_sum)
        min_diff = min(min_diff, diff)
    return min_diff

# Test
assert tape_equilibrium([3, 1, 2, 4, 3]) == 1
assert tape_equilibrium([1, 2]) == 1
assert tape_equilibrium([-1000, 1000]) == 2000
assert tape_equilibrium([10, -10, 10, -10, 10]) == 10

# You’re given a list of stock prices A, where A[i] is the stock price on day i.
# You must buy once and sell once (after you buy).
# Return the maximum profit possible. If no profit can be made, return 0.
def max_profit(A):
    min_price = float('inf')
    max_profit = 0
    for price in A:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit

# Test cases
assert max_profit([23171, 21011, 21123, 21366, 21013, 21367]) == 356
assert max_profit([5, 4, 3, 2, 1]) == 0  # No profit
assert max_profit([1, 2, 3, 4, 5]) == 4  # Buy at 1, sell at 5
assert max_profit([100]) == 0  # Not enough data
assert max_profit([]) == 0  # No data at all


# Kadane’s Algorithm — “Maximum Subarray Sum”
# (aka: Find the biggest chunk of happiness in an array of emotional rollercoasters)

# Problem Statement:
# Given an array A of integers (positive, negative, or zero), find the maximum sum of any contiguous subarray.
def max_subarray_sum(A):
    max_current = max_global = A[0]
    for num in A[1:]:
        max_current = max(num, max_current + num)
        if max_current > max_global:
            max_global = max_current
    return max_global

# Test cases
assert max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
assert max_subarray_sum([1]) == 1
assert max_subarray_sum([5, 4, -1, 7, 8]) == 23
assert max_subarray_sum([-1, -2, -3, -4]) == -1
assert max_subarray_sum([]) == 0

# Why Kadane Matters:
# It’s used everywhere:
# Financial gain/loss analysis
# Energy/power consumption windows
# Game scoring analysis
# Even in DP + matrix problems like "max submatrix sum"

