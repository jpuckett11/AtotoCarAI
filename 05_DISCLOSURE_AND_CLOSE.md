# Chapters 12 and 13

> Published 2026-09-01. Disclosure status is in the front matter.

---

# Chapter 12 - Disclosure history

Recorded because the response to a finding is itself a finding.

## 12.1 Timeline

```
2026-02-03  device activated at the factory, per persist.suding.reverse.activate.time
2026-05-09  purchased at retail through Amazon
2026-05-14  GPS collection window opens (evidenced in traccar.db)
2026-05-15  Google Automotive Link credential rotated onto /qcache while owned
2026-05-19  firmware acquired over EDL, twelve sessions
2026-05-19  reported to Amazon Product Safety
2026-05-21  live /data extraction; TBI Cyber Crimes walk-in with full package
2026-06-14  Google VRP submission filed
2026-06-15  proof of concept executed
2026-06-16  overnight addendum submitted, 437-APK sweep
2026-06-17  PACCAR PSIRT, Apple Product Security and the remaining vendor
            tracks notified in writing
2026-06-23  Google releases Apple, PACCAR and ByteDance findings for
            independent disclosure, Google-specific material excluded
2026-07-31  re-examination; qcache credential detail, interface capture,
            keepalive targets, IOC sweep completed
2026-08-05  the operational certificate expires
2026-08-17  unrelated third-party publication of a UNISOC baseband exploit
            (SSD Secure Disclosure). Adjacent silicon, not this case, recorded
            because it changes the public risk picture for the modem class
2026-09-01  Google issue closed. PACCAR declines contact by telephone.
            This paper published.
```

![**Figure 6. Ownership, collection and disclosure.** The two dates in red are the ones that decide severity. The Google Automotive Link credential was written to `/qcache` on 2026-05-15, four days before the firmware was imaged and inside the window the GPS database independently covers, so the rotation happened on this device while its owner had it. The certificate it wrote expires 2026-08-05.](figures/fig4_timeline.png)

## 12.2 What each channel did

**Amazon Product Safety.** Reported 2026-05-19. Dismissed by first-line customer
service. The listing remained active.

**Tennessee Bureau of Investigation.** Walk-in on 2026-05-21 with a signed evidence
package and a one-page law enforcement summary.

**Google Vulnerability Reward Program.** Filed 2026-06-14 as issue 515507754.
Substantive engagement. Google acknowledged, requested a proof of concept, specified
sanitisation, asked that details remain confidential during assessment, and described
their work as addressing "supply-chain risks and unauthorized GMS distribution
patterns." They separately released the Apple, PACCAR and ByteDance findings for
independent disclosure while retaining the embargo on Google-specific material. The
issue is now closed.

**Federal channels.** Notified through their established intake routes. Remediation on
the federal side was addressed with urgency. The specific routes and the substance of
the response are not reproduced here: those are the agencies' to disclose, not the
researcher's.

The contrast is the point, and it is a three-way one. The federal channels moved with
urgency. The company with a published vulnerability process engaged in detail and
closed the matter. The vehicle manufacturer's product security team has not responded
in seventy-six days and disconnected a telephone call, and the retailer selling the
device dismissed it at first-line support.

**[I]** That pattern is worth more than any single finding in this paper. The
mechanisms that are supposed to work did work, where they were used. What failed was
not the existence of a process. It was two organisations declining to engage with one
they already had.

## 12.3 Scope of this document

Google's issue is closed, and its published programme terms ask for reasonable advance
notice rather than an affirmative release. This paper is published on that basis.

PACCAR and Apple were notified in writing on 2026-06-17. Neither has responded
substantively in the seventy-six days since, and PACCAR declined a telephone contact on
2026-09-01. Their product-specific findings are not reproduced here, because this paper
is an analysis of one retail device and the reference design behind it rather than a
consolidated multi-vendor report.

There is no ByteDance track. That component ships on a Chinese ROM with no published
security contact reachable from here, so no notice was possible and none is claimed.

Vehicle-safety analysis is carried in a separate case document routed to NHTSA,
Auto-ISAC and CISA, which is where it was scoped when it was written in May 2026.
Chapter 10.5 carries the summary.

## 12.4 Who paid for this

§5.3.2 traced where the cost of the fix lands. This section completes the accounting,
because the same pattern runs one node further back and it is not visible from inside
any of the organisations involved.

**What the work cost.** The device was bought at retail with the researcher's own
money. Firmware was acquired over EDL across twelve sessions. The analysis ran from May
to September 2026. A proof of concept was built because Google asked for one, and
sanitised to a specification Google set. Findings were held under embargo from June
until September, unpublished, while the material sat on a private machine. Both devices
were surrendered to Homeland Security Investigations, which is why the prediction in
§5.3.2 cannot be tested by the person who made it.

**What it returned.** The submission was rated Moderate and routed to a feature team.
On the tracker, `ASR Severity` is populated and **`ASR Eligible` and `ASR Payment` are
blank** — not declined, unset. It was assessed under a programme whose hardware scope
covers Pixel, Nest, Home, Pixel Watch and Fitbit, which this device could never
satisfy regardless of severity. **No payment was made by any party.**

**Stated fairly, because the narrow version is the true one.** Google engaged
substantively, asked for the proof of concept, specified sanitisation, and released the
Apple, PACCAR and ByteDance findings on 2026-06-23 so they could be disclosed
independently. The remediation ticket is assigned and a fix is in flight. What did not
function was the reward track, on a device that programme was never built to cover.
This is not a claim of mistreatment.

**[I] The structural observation, which is the reason this section exists.** Follow the
cost through every node. Google's remediation is free: let a certificate expire.
The vendor's exposure ends when it is not reissued a credential. The retailer continues
selling the listing. The buyer absorbs a device that quietly stops working. The
researcher absorbs the purchase price, the months, and the risk of holding embargoed
material. **Every party with a mechanism to recover its costs recovered them. The two
parties with no mechanism, the buyer and the researcher, absorbed the entire bill.**

That is not an argument for larger bounties. It is an observation that a disclosure
system depending on unpaid individuals to find defects in products they bought
themselves has no reason to expect a supply of them, and that the incentive to say
nothing and simply keep the private key is left as an exercise for the next person who
finds one.

---

# Chapter 13 - Every check that could have caught this

Each of the following existed, was available, and would have caught at least one
finding in this paper.

**Certification.** The device carries a Qualcomm reference platform fingerprint,
asserts `release-keys` while signed with the public AOSP test key, and ships Google
Mobile Services. A certification check comparing the asserted build tag against the
actual platform signature is a string comparison and a hash lookup.

**Partner credential handling.** The Google Automotive Link private key ships
unencrypted on a partition with no Verified Boot coverage, in a directory the vendor
`chmod 777`s at every boot. Rotation writes a new credential without removing the old
one, so retail units carry every generation. Any audit of how a partner stores an
issued credential catches this immediately.

**Retail listing review.** The product was reported to Amazon with a technical package
on 2026-05-19 and dismissed by first-line support.

**Radio equipment filing.** The device contains a cellular modem and an eSIM capable of
remote reprovisioning. Cross-referencing the FCC IDs on each branded SKU against the
actual silicon is a records exercise.

**Update integrity.** OTA packages are verified against a certificate published in the
Android source tree. A single check of whether `otacerts.zip` contains a test key would
have caught it.

**Patch currency.** The build is thirty-five months behind on security bulletins with
an EOL kernel, and was rebuilt in that state in September 2025.

None of these required the work in this paper. They required someone to run a check
that already existed, on a device that was already for sale.

---

## Closing

A consumer bought an accessory to make wireless Android Auto work in an older car.
What arrived was a Qualcomm reference platform with a cellular modem, an eSIM that can
be reprovisioned remotely, six silent-install channels, an always-on microphone with a
dedicated service to restart it, a location tracker with the same protection, a
platform signed with a published key, an update path verified against another
published key, and a Google-issued private credential stored in the clear on a
partition anyone can write.

It collected 1,486 positions over 5.7 days and queued them for upload. It stored a
message about a child who had no relationship with the device or its owner.

None of it is exotic. Every finding here was recoverable with public tools, a
publicly documented protocol, and a device anyone can buy. The barrier was never
technical. It was that nobody had looked.
