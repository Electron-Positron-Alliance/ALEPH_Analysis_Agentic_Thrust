# Collaboration Session Logs

This directory contains verbatim records of every physicist-agent session in the ALEPH e+e- analysis program.

## File naming
```
session_NNN.md    (NNN = zero-padded session number, starting from 001)
```

## Purpose
Each file is the primary full-fidelity record of one agent session: full text of all physicist messages and agent responses, in order, with session metadata. These files are the source of truth for the analysis note `App_CommunicationSummary` appendix, which contains a distilled summary with pointers back to these session files.

## What each session file contains
- Session number, date, observable, analysis stage
- Files changed and checkpoints reached (filled at end of session)
- Full verbatim conversation: every physicist message and every agent response

## How to find a specific exchange
Use the `Checkpoints reached` metadata field in each session file to locate which session contains a given checkpoint. Then search within that file for the checkpoint name.
