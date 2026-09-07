# What the assistant can be asked

The assistant answers from a fixed digest of the loaded log, not from the raw
event data. It is told to quote the figures exactly and never invent one, so its
range is bounded by what the analysis actually computes.

## What it is given

- Log name, activity mode, case / event / activity counts, the full activity list
- Health score, grade, and the four components, each labelled with its direction
- Median and p95 case duration
- Distinct variant count and ratio
- The five slowest activities by mean waiting time
- All eight temporal properties with their satisfaction ratios, with anything
  below 90% marked as not holding

## Suggested questions

These are the entries offered as one-click examples in the Assistant tab.

- Where is the most time being lost in this process?
- Why is the health score not higher?
- Which temporal properties fail, and what does that say about the process?
- How much rework is there, and where does it come from?
- Is this process standardised, or does every case follow its own path?
- What would you fix first?

Follow-up questions work: the last eight turns are sent back with each message,
so "why?" or "compare that to the problem logs" continues the thread.

## What it cannot answer

Nothing below is in the digest, and the assistant should say so rather than guess:

- Anything about an individual case id, employee, or support team
- Comparisons between the three logs — only the loaded one is in context
- Petri net structure, conformance metrics, or anomaly detail
- Anything requiring the raw event data rather than the summary

If an answer contains a figure that is not in the list above, treat it as a
hallucination and check it against `docs/results/`.

## A caution

A small local model will occasionally garble a number. Two prompt defects were
found exactly this way: the rework component was reported as a "rework rate"
when it means the opposite, and a property at 98.4% was called failing while the
two that genuinely fail were missed. Both are fixed, but the lesson stands —
read any generated figure against the committed results before quoting it.
