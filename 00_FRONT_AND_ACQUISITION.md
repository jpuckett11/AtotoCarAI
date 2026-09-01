# A Consumer Vehicle Accessory With No Working Trust Boundary

### Firmware analysis of an Android automotive AI Box, and what it says about the reference design behind it

**Jay Puckett (Reckoner)** - Principal Security Researcher, Obsidian Watch Group
Version 1.0, published 2026-09-01

---

> **Disclosure status.**
>
> Google issue 515507754 was opened 2026-05-27, engaged substantively, and is closed.
> Google's published Vulnerability Reward Program terms ask for reasonable advance
> notice rather than an affirmative release, and that notice was given. The findings
> in this paper are published on that basis.
>
> PACCAR PSIRT and Apple Product Security were notified in writing on 2026-06-17.
> Neither has responded substantively in the seventy-six days since. PACCAR declined
> a telephone contact on 2026-09-01.
>
> There is no ByteDance disclosure track. That component ships on a Chinese ROM with
> no published security contact reachable from here, so no notice was possible and
> none is claimed.
>
> Vehicle-safety analysis is carried in a separate case document routed to NHTSA,
> Auto-ISAC and CISA, which is where it was scoped when it was written. Chapter 10.5
> summarizes it here.

---

## Abstract

A consumer aftermarket accessory sold on Amazon, which plugs into a car's factory
head unit to add wireless Android Auto and CarPlay, was acquired at retail and its
firmware extracted in full. The device runs Android 13 on a Qualcomm SDM662.

**What the device is architecturally matters more than what it is sold as.** Wireless
projection works by terminating the session from the phone and re-presenting it to the
head unit. This accessory is not a cable and it is not a passive adapter. It
authenticates to the phone as a car and to the car as a phone, and it sits in the path
of everything that session carries: navigation, audio, notifications, contacts, call
history, messages. The Bluetooth pairing it requires adds more, independently of the
projection session, because the OEM applications ingest SMS over the Message Access
Profile.

**That position is not a vulnerability this paper discovered. It is the product.** A
device sold to make a phone talk to a car is, by construction, a machine-in-the-middle
between the two, holding credentials that let each side believe it is talking to the
other. Everything that follows is about what that position becomes when the device
occupying it has no working trust boundary, ships with a published signing key, and
accepts code from six channels.

The analysis found no functioning trust boundary at any layer examined.

The platform is signed with keys whose private halves are published in the Android
source tree. Of 354 application packages, **276 are signed with one of the five
published AOSP keys**, matched by fingerprint against upstream, including
`PackageInstaller`, `Settings`, `SystemUI` and `KeyChain`. A further 18 carry the same
AOSP distinguished name with different key material, giving 294 that bear that
identity; §5.1 sets out why a subject line is not a key and why the fingerprint is the
number that counts. Over-the-air update packages are verified against another of the
same published keys. A production private key issued
under Google's Android Auto certificate authority sits unencrypted on a world-readable
partition, and the matching certificate chains cleanly to Google's root. The root
certificate the device trusts for that relationship is refetched over cleartext HTTP
every sixty seconds from a commodity cloud host, authenticated by an MD5 digest over a
constant compiled into the application. That same trust anchor is separately writable
by any local application, because it is stored on a partition outside Verified Boot in
a directory a shipped script sets to mode 777.

None of these are defects in Android. Every one is a decision made by the vendor, and
the device carries Google Mobile Services while making them.

The pattern is not confined to one product or to this class of device. Six firmware
samples across five OEMs carry the same unauthenticated root-access chain, and two of
those are in-dash head units rather than adapters, one of them on a different Qualcomm
chipset family and a different update vendor entirely. They share no application-layer
code. The device's own firmware carries at least ten customer brand profiles selected
by a single property. The defect being examined here is not a bad product. It is a
manufacturing practice, propagating to whoever licenses it, and it cannot be
remediated one brand at a time.

---

## 1. Subject device

| | |
|---|---|
| Class | Aftermarket wireless Android Auto / CarPlay adapter |
| Acquisition | Purchased at retail through Amazon |
| SoC | Qualcomm SDM662 |
| Storage | Samsung UFS |
| OS | Android 13 (system), Android 11 (vendor) |
| Security patch level | 2023-06-05 |
| Build date | 2025-09-28 |

Build fingerprints, read from `build.prop`:

```
ro.system.build.fingerprint  qti/qssi/qssi:13/TKQ1.230627.001/longtj09282052:user/release-keys
ro.vendor.build.fingerprint  qti/bengal/bengal:11/RKQ1.230607.001/longtj09282216:user/release-keys
ro.build.version.security_patch      2023-06-05
ro.vendor.build.version.incremental  eng.longtj.20250928.221653
```

Three things are readable directly from those four lines.

**This is a Qualcomm reference platform, not an OEM device.** `brand=qti`, `device=qssi`
for the system image and `device=bengal` for the vendor image. `qssi` is Qualcomm
Single System Image. `bengal` is the SDM662 platform codename. `TKQ1.230627.001` and
`RKQ1.230607.001` are Qualcomm internal reference builds from June 2023. A device that
had gone through Google's certification program would not carry a `qti` brand and a
reference-platform device name into retail.

**The security patch baseline is 27 months stale at build time.** The system was
compiled 2025-09-28 against a June 2023 patch level.

**`release-keys` is cosmetic.** The build tag asserts a production signing key. Section
3 shows the actual platform signature is the published AOSP test key. The tag is a
string in a properties file and nothing verifies it.

The string `longtj` appears in both fingerprints and in the incremental version. That
is the account name on the build host that compiled the image.

---

## 2. Acquisition

### 2.1 Method

Extraction was performed over Qualcomm Emergency Download mode, reached by holding the
recovery control while applying power, which enumerates the SoC as USB `05c6:9008`.
EDL exposes the Sahara protocol, which accepts a signed programr binary; the
programr then exposes Firehose, which reads and writes raw storage beneath the
operating system entirely.

Nothing on the running system participates in this. No root, no ADB, no exploit. The
device is not booted.

Tooling was bkerler's `edl` client, driven by two shell wrappers written for this
work, `oneshot_dump.sh` for a single-pass eMMC read and `multi_lun_dump.sh` to walk
every logical unit on the UFS device. Both are reproduced in Appendix A.

### 2.2 The Sahara handshake, and what it disclosed before any data was read

```
Qualcomm Sahara / Firehose Client V3.62
sahara - Protocol version: 2
HWID:     0x0014d0e100000000  (MSM_ID:0x0014d0e1, OEM_ID:0x0000, MODEL_ID:0x0000)
CPU:      SDM662
PK_HASH:  0xd40eee56f3194665574109a39267724ae7944134cd53cb767e293d3c40497955
          bc8a4519ff992b031fadc6355015ac87
Serial:   0xd47e5dbc
firehose - INFO: ufs: SAMSUNG
firehose - INFO: Binary build date: Dec 18 2022 @ 21:52:52
```

Two details in that block matter more than the dump that followed.

**`OEM_ID: 0x0000` and `MODEL_ID: 0x0000`.** On a properly provisioned Qualcomm
device these fields carry the OEM's assigned identifiers, burned into fuses at
manufacture. Both are null. The device shipped to retail without OEM identity fusing.

**A generic factory programr was accepted.** The loader used,
`0014d0e100000000_d40eee56f3194665_FHPRG.bin`, is selected by matching the device's
`PK_HASH` against a public database of factory programrs. It authenticated and ran.
On a device with secure boot fused to an OEM-specific key, it would not.

Those two facts together mean the storage was readable, and writable, by anyone
holding the hardware and a publicly available tool. Everything in Sections 3 through 7
is a consequence of a device that could be read. It could equally have been written.

### 2.3 Firehose exposed write primitives, not only read

The programr advertised its capabilities on connection:

```
program   read   nop   patch   configure   setbootablestoragedrive
erase     power  firmwarewrite  getstorageinfo  benchmark
emmc      ufs    fixgpt  getsha256digest
```

`program`, `patch`, `erase` and `firmwarewrite` are write operations. `fixgpt` rewrites
the partition table. This analysis used `read` exclusively. The point is that the same
five-minute physical access that produced this dump would equally have produced a
modified device, with no cryptographic obstacle at any point.

### 2.4 Capture in fragments

The device would not hold a Firehose session long enough for a single complete pass.
Acquisition was therefore performed as twelve sessions over roughly one hour on
2026-05-19, each restarting from EDL, each taking what it could before the link
dropped.

| Session (UTC) | Files | Captured |
|---|---:|---:|
| `dump-20260519T193422Z` | 19 | 9.2 G |
| `dump-20260519T193927Z` | 2 | failed |
| `dump-20260519T194033Z` | 16 | 1.6 G |
| `dump-20260519T194348Z` | 16 | 3.0 G |
| `dump-20260519T194549Z` | 2 | failed |
| `dump-20260519T195323Z` | 16 | 4.2 G |
| `multilun-20260519T200336Z` | 16 | 2.1 G |
| `multilun-20260519T200643Z` | 16 | 3.0 G |
| `multilun-20260519T200944Z` | 16 | 1.5 G |
| `multilun-20260519T201046Z` | 23 | 1.4 G |
| `multilun-20260519T202052Z` | 23 | 2.8 G |
| `lun567-20260519T203051Z` | 74 | 1.2 G |
| **Total** | | **31 G** |

Ten sessions productive, two dropped before returning data. Sessions three minutes
apart in the log are consecutive retries.

This fragmentation is worth recording rather than smoothing over. It is why the
partition inventory was assembled across runs rather than taken from one authoritative
read, and it is the reason for the LUN-targeted session at the end.

### 2.5 Logical unit discovery

The first `multi_lun_dump.sh` passes walked LUNs 0 through 7 and returned data only on
LUN 0. Later sessions established that LUNs 5 and 6 held content the earlier walks had
missed, and a dedicated session was run against 5, 6 and 7:

```
lun0    14 partitions    2.8 G
lun5    30 partitions     65 M
lun6    39 partitions    1.1 G
lun7     0 partitions    empty
```

LUN 0 carries the Android partitions. LUNs 5 and 6 carry boot, modem and trust-related
images. The two errors logged in the final session are recorded in
`lun567-20260519T203051Z/lun*/rl.log` and did not prevent capture.

Had acquisition stopped after the first successful `oneshot_dump.sh` run, 69 partitions
across two logical units would have been absent from the analysis.

### 2.6 What acquisition establishes on its own

Before a single file was examined:

1. The device accepts a publicly available factory programr.
2. It has no OEM identity fused.
3. Its storage is readable and writable in full by anyone with physical possession.
4. The programr exposing that access was built in December 2022 and shipped in the
   product.

A device with a working secure boot chain fails at step one.

---

*Sections 3 onward: platform signing, the OTA channel, the Google Automotive Link
credential, the trust anchor rewrite paths, the permission surface, the remote
provisioning stack, cross-vendor propagation, and disclosure history.*
