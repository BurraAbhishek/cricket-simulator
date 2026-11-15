RUN_RATE1 = {}
RUN_RATE2 = {}


def run_rate_to_score(run_rate, scoring_options=[0, 1, 2, 4, 6]):
    if run_rate >= 36:
        return [6]
    if run_rate <= 0:
        return [0]
    # Cache
    rr_key = str({
        "run_rate": run_rate,
        "scoring_options": sorted(scoring_options)
    })
    if rr_key in RUN_RATE1.keys():
        return RUN_RATE1[rr_key]
    # The mean of all these values, when multiplied by 6, should result in the run rate.;
    # For example, 35RR. = [4] + 11 * [6]
    run_rate = round(run_rate * 10000000) / 10000000
    rr_scaled = int(run_rate * 10)
    for n in range(1, 121):
        if (rr_scaled * n) % 60 == 0:
            target_runs = (rr_scaled * n) // 60
            # Dynamic programming
            dp = [{} for _ in range(n + 1)]
            dp[0][0] = True
            # Created dp
            for b in range(n):
                for curr_sum in dp[b]:
                    for score in scoring_options:
                        new_sum = curr_sum + score
                        if new_sum <= target_runs and new_sum not in dp[b+1]:
                            dp[b+1][new_sum] = score
            # If target runs is in dp[n], backtrack
            if target_runs in dp[n]:
                result = []
                curr = target_runs
                for b in range(n, 0, -1):
                    score = dp[b][curr]
                    result.append(score)
                    curr -= score
                RUN_RATE1[rr_key] = sorted(result)
                return sorted(result)
    return None


def run_rate_to_score_with_mandatory(run_rate, scoring_options=[0, 1, 2, 4, 6], mandatory=[]):
    if run_rate >= 36:
        return [6]
    if run_rate <= 0:
        return [0]
    # Cache
    rr_key = str({
        "run_rate": run_rate,
        "scoring_options": sorted(scoring_options),
        "mandatory": mandatory
    })
    if rr_key in RUN_RATE2.keys():
        return RUN_RATE2[rr_key]
    if len(mandatory) < 1:
        mandatory_sum = 0
    else:
        mandatory_sum = sum(mandatory)
    run_rate = round(run_rate * 10000000) / 10000000
    for n in range(1, 121):
        total_sum_needed = (run_rate * n) / 6
        if not total_sum_needed.is_integer() or total_sum_needed < mandatory_sum:
            continue
        remaining_sum = int(total_sum_needed - mandatory_sum)
        remaining_balls = n - len(mandatory)
        if remaining_sum == 0 and remaining_balls == 0:
            RUN_RATE2[rr_key] = sorted(mandatory)
            return mandatory
        if remaining_balls <= 0 and remaining_sum > 0:
            continue
        dp = [[None] * (remaining_sum + 1) for _ in range(remaining_balls + 1)]
        dp[0][0] = True
        for i in range(1, remaining_balls + 1):
            for j in range(remaining_sum + 1):
                for o in scoring_options:
                    if j >= o and dp[i-1][j-o] is not None:
                        dp[i][j] = o
                        break
        if dp[remaining_balls][remaining_sum] is not None:
            result = [] + mandatory
            curr_s, curr_n = remaining_sum, remaining_balls
            for curr_n in range(remaining_balls, 0, -1):
                score = dp[curr_n][curr_s]
                result.append(score)
                curr_s -= score
            RUN_RATE2[rr_key] = sorted(result)
            return sorted(result)
    # Fallback
    return run_rate_to_score(run_rate, scoring_options)
