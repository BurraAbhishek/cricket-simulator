# REWRITE THE COMMENTARY

For each over:
- total score (before over)
- batter1 runs (balls) [fours] [sixes] [on strike]
- batter2 runs (balls) [fours] [sixes]
- bowler overs-maidens-runs-wickets (for new bowler: 0-0-0-0)
- old commentary of all balls.

Output: array of commentaries in the same order,

# SUMMARIZE THE INNINGS

For each innings
- Batting side: Previous innings score (if any)
- current innings score

# PLAYER OF THE MATCH

For each innings
- Score
- Top 2-3 performers of winning side

Local LLM gives wrong answers. A math engine is enough.

Result:
- Math engine: Pass
- Local LLM (Gemma4 E2B): Fail|
- Cloud LLM (Gemini 1.5 Flash):

# Q/E IN GROUP STAGE

- Checks if a team qualified to next stage (usually knockout) or was eliminated in that (group) stage
- NetworkX is sufficient. An LLM may not be needed. 
- Cloud LLMs would potentially need extensive thinking tokens that would lead to higher cost.

NetworkX implementation is pending.

# PLAYER OF THE TOURNAMENT

Max POTMs may be sufficient. Else, for each innings, score and top performers of each side.
Pending implementation

# PLAY THE MATCH!

Approach 1: Play each ball. Computationally expensive, but a team for each LLM can do.
- May not be feasible beyond a T20 format
- AI must generate its own team members. They need not have names, but their batting and bowling styles are needed.
    - Ratings are not needed here, for the AI decides scorability/wicket options.

Approach 2: Scoring options and wicket probability per batter
- Computationally better
- Over context is irrelevant
- Needed for facing existing brute-force bots anyway.

# Summary of Results

|Component|Programmatic*|Local LLM****|Cloud LLM*****|
|---|---|---|---|
|Commentary|YES|NO|YES|
|Summarize Innings|NO|NO|YES|
|Player of the Match|YES**|NO|YES|
|Player of the Tournament|NO***|NO|*|
|Group Stage Q/E|YES**|NO|NO|
|Play the match itself|YES|NO***|*|

*A python code snippet without using the internet or any ai features

**Alternative approach that is closer to correct

***Not computationally feasible

****Tested using Mistral7B, Gemma4 E2B, Gemma4 E4B

*****Currently using Gemini 3.8 Flash

