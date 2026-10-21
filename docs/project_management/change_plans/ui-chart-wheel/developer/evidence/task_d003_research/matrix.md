# TASK-D-003 — numeric matrix, independent post-audit

Full drawing/production PASS is not claimed. Fixed angle/angle collisions are included here; initial runner geometry covered movable-vs-all only.

| Fixture | CSS width | Layout | C0 / moved | Movable geometry | Fixed overlaps | Hit Q44 | Native wrong / probes | Keyboard failures / targets | Minimality |
|---|---|---|---|---|---|---|---|---|---|
| sparse | 1440 | default | 0 / 0 | True | 0 | 16/16 | 0/272 | 0/16 | ZERO_DISPLACEMENT |
| sparse | 1440 | candidate | 0 / 0 | True | 0 | 16/16 | 0/272 | 0/16 | ZERO_DISPLACEMENT |
| sparse | 768 | default | 0 / 0 | True | 0 | 16/16 | 0/272 | 0/16 | ZERO_DISPLACEMENT |
| sparse | 768 | candidate | 0 / 0 | True | 0 | 16/16 | 0/272 | 0/16 | ZERO_DISPLACEMENT |
| sparse | 360 | default | 0 / 0 | True | 0 | 8/16 | 8/272 | 0/16 | ZERO_DISPLACEMENT |
| sparse | 360 | candidate | 0 / 0 | True | 0 | 8/16 | 8/272 | 0/16 | ZERO_DISPLACEMENT |
| F1 | 1440 | default | 8 / 0 | False | 0 | 13/19 | 43/323 | 0/19 | ZERO_DISPLACEMENT |
| F1 | 1440 | candidate | 8 / 8 | False | 0 | 14/19 | 41/323 | 0/19 | UNPROVEN |
| F1 | 768 | default | 8 / 0 | False | 0 | 13/19 | 43/323 | 0/19 | ZERO_DISPLACEMENT |
| F1 | 768 | candidate | 8 / 8 | False | 0 | 14/19 | 41/323 | 0/19 | UNPROVEN |
| F1 | 360 | default | 11 / 0 | False | 0 | 7/19 | 91/323 | 0/19 | ZERO_DISPLACEMENT |
| F1 | 360 | candidate | 11 / 10 | False | 0 | 9/19 | 81/323 | 0/19 | UNPROVEN |
| F3 | 1440 | default | 13 / 0 | False | 10 | 8/18 | 113/306 | 0/18 | ZERO_DISPLACEMENT |
| F3 | 1440 | candidate | 13 / 13 | False | 10 | 16/18 | 16/306 | 0/18 | UNPROVEN |
| F3 | 768 | default | 13 / 0 | False | 10 | 8/18 | 113/306 | 0/18 | ZERO_DISPLACEMENT |
| F3 | 768 | candidate | 13 / 13 | False | 10 | 16/18 | 16/306 | 0/18 | UNPROVEN |
| F3 | 360 | default | 15 / 0 | False | 10 | 6/18 | 158/306 | 0/18 | ZERO_DISPLACEMENT |
| F3 | 360 | candidate | 15 / 15 | False | 10 | 6/18 | 74/306 | 0/18 | UNPROVEN |
| F3-max | 1440 | default | 20 / 0 | False | 10 | 2/20 | 234/340 | 0/20 | ZERO_DISPLACEMENT |
| F3-max | 1440 | candidate | 20 / 20 | True | 10 | 20/20 | 0/340 | 0/20 | FAIL_WITH_WITNESS |
| F3-max | 768 | default | 20 / 0 | False | 10 | 2/20 | 234/340 | 0/20 | ZERO_DISPLACEMENT |
| F3-max | 768 | candidate | 20 / 20 | True | 10 | 20/20 | 0/340 | 0/20 | FAIL_WITH_WITNESS |
| F3-max | 360 | default | 20 / 0 | False | 10 | 2/20 | 302/340 | 0/20 | ZERO_DISPLACEMENT |
| F3-max | 360 | candidate | 20 / 20 | False | 10 | 3/20 | 68/340 | 0/20 | FAIL_WITH_WITNESS |

All numeric records / actual coordinates / event paths / exact file hashes: [run02 index](run02/browser_matrix.json). [Drawing audit](drawing_audit.json) corrects the scope of earlier per-cell geometry verdicts.

Raw source and controls are immutable evidence of their run; a new run uses a new D003_RUN / D003_FOLLOWUP name.
