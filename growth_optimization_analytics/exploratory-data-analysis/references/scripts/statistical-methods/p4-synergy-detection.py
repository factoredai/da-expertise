"""
P4: Both-Parties-Above-Average for Synergy Detection
Business problem: Test if a combination outperforms both individual parties.
Required: Performance data for party A, party B, and combination A+B.
Output: Synergy flag and premium estimate.
"""
def test_synergy(a_avg, b_avg, ab_performance, threshold=1.10):
    if ab_performance > max(a_avg, b_avg) * threshold:
        premium = min(ab_performance / a_avg, ab_performance / b_avg)
        return True, premium
    return False, 0.0
