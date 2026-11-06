# Progress prototypes (Tamarin 1.10, SAPIC+, options: translation-progress), no liveness restrictions

hop_progress_onchain.spthy (S -> F -> R)
  Redeem_Possible E 15, Refund_Possible E 16, Intermediary_Safe A 403, Intermediary_Claims A 317 -- all verified
hop_noprogress_control.spthy (same, progress OFF)
  Intermediary_Safe verified (23); Intermediary_Claims FALSIFIED -> claiming is due to progress
twohop_progress.spthy (S -> F1 -> F2 -> R)
  Payment_Completes E 16, Payment_Refunded E 20, F1_Safe A 2976, F2_Safe A 911,
  F2_Claims A 3087/3082, F1_Claims A 3687, Atomicity A 6759 -- all verified
Remaining wellformedness warnings: only "facts on LHS never produced" for dead
translation rules (parallel-composition leftovers); they cannot fire, so add no traces.
