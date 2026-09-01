# A Consumer Vehicle Accessory With No Working Trust Boundary

Firmware analysis of an Android automotive AI Box, and what it says about the
reference design behind it.

**Jay Puckett (Reckoner)** - Principal Security Researcher, Obsidian Watch Group
Version 1.0, published 2026-09-01

---

## This is a work in progress

Published while the investigation is still open, deliberately. Several threads are
live and several questions are unresolved, and they are marked as such throughout
rather than smoothed over. Appendix E lists what was observed but not confirmed and
what was not attempted at all.

Expect this to change. Findings may be revised, sharpened, or withdrawn as more is
learned, and any correction will be made in place with the original left visible.

If something here is wrong, the useful thing is to say so.

---

## Contents

| File | |
|---|---|
| `00_FRONT_AND_ACQUISITION.md` | Disclosure status, abstract, subject device, acquisition |
| `01_ANALYSIS_METHOD.md` | Method, and what it does not cover |
| `02_TRUST_AND_IDENTITY.md` | What the device claims to be, and the signing model |
| `03_CONTROL_AND_COLLECTION.md` | Control of the head unit, the services that persist, what was collected |
| `04_DELIVERY_SUPPLY_AND_PROOF.md` | Code delivery channels, the reference design, proof of concept |
| `05_DISCLOSURE_AND_CLOSE.md` | Disclosure history, and every check that could have caught this |
| `06_APPENDICES.md` | Indicator catalogue, evidence manifest, tooling, open items |

Read the disclosure status in the front matter before quoting anything.

---

## Thanks

**HaleHound** built the hardware that makes this kind of work possible for an
independent researcher. Purpose-built RF and wireless survey tools, priced so that
somebody without a lab budget can actually own one, and supported by people who
answer when you ask a question.

A great deal of security research never happens because the instrumentation is out
of reach. Jesse and the HaleHound team are a direct answer to that, and this paper
is one of the things that exists because they made the tools available.

Thank you.

---

## Scope

Analysis of a device purchased at retail with the researcher's own money, examined
on the researcher's own equipment. No third-party system was accessed. No production
vendor endpoint was contacted during the proof of concept.

Vehicle-safety analysis is carried in a separate case document routed to NHTSA,
Auto-ISAC and CISA. Chapter 10.5 summarizes it here.

## Reuse

Cite it, quote it, argue with it. If you reproduce a finding, reproduce the
qualification attached to it. Several of the strongest-sounding claims in this paper
are deliberately bounded, and the bounds are the reason the rest can be trusted.
