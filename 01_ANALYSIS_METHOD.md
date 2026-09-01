# Chapter 3 - Analysis method

> Published 2026-09-01. Disclosure status is in the front matter.

Acquisition produced 31 GB across twelve sessions. This chapter documents how that
was turned into findings, including the two points where the obvious approach failed
and had to be replaced.

The organizing principle was coverage. An earlier pass had examined roughly a quarter
of the partitions, chosen because they were the ones with recognisable filesystems. A
finding that lives in the other three quarters is invisible to that method, and the
question "what did we not look at" has a specific answer worth producing.

---

## 3.1 Partition classification, and why `file(1)` is not enough

115 partition images were recovered across the two dumps. The problem with
characterising them is that the standard tool cannot distinguish the two cases that
matter most.

A 33 MB partition of all zeroes and a 33 MB partition of AES ciphertext both come back
from `file(1)` as `data`. One is an unallocated region worth nothing. The other is
encrypted content and is the single most interesting thing on the device. Treating
them identically means either examining every byte by hand or skipping both.

`sweep_partitions.sh` resolves this with two cheap measurements per image, computed in
one pass and capped at 64 MB for speed:

```
nonzero byte ratio       separates sparse and zero-filled from populated
Shannon entropy          separates structured data from compressed or encrypted
```

Entropy above roughly 7.0 bits per byte on a populated image means compressed or
encrypted. Below about 5.0 means structured content with recognisable patterns. The
combination sorts 115 images into "empty," "structured, go read it," and "high entropy,
this needs explaining" without opening any of them.

The top of that ranking:

| Image | Size | Entropy | `file(1)` says |
|---|---:|---:|---|
| `lun0/super.bin` | 71.3 MB | 7.098 | `data` |
| `lun2/xbl_b.bin` | 3.67 MB | 6.823 | ELF 64-bit ARM aarch64 |
| `lun1/xbl_a.bin` | 3.67 MB | 6.823 | ELF 64-bit ARM aarch64 |
| `modem_b.img` | 188.7 MB | 6.792 | DOS/MBR boot sector |
| `modem_a.img` | 188.7 MB | 6.792 | DOS/MBR boot sector |

`super.bin` reading as `data` with 7.098 entropy is the dynamic partition
super-image, which is why it looks like noise to a magic-number check.

![**Figure 1. Every partition image, classified by two cheap measurements.** Nonzero byte ratio separates empty regions from populated ones; Shannon entropy separates structured content from compressed or encrypted content. One image, `lun5/persist.bin`, is zero bytes and has no position on a log axis. Full output in `partition_classification.tsv`.](figures/fig2_partitions.png)

Full output: `atoto_reseal_20260728/evidence/partition_classification.tsv`.

## 3.2 Indicator sweep across every image

Classification says where to look. The second half of `sweep_partitions.sh` looks
everywhere at once, running a deliberately broad pattern set over raw bytes of all 115
images rather than only mounted filesystems:

```
https?://...                          any URL, any partition
*.{suding,atoto,carlinkit,carsyso,adups,abupdate,aliyuncs,baidu,qq,qcloud,
   picovoice,aispeech,texustek}       the known vendor stack
BEGIN [A-Z ]*PRIVATE KEY              key material in the clear
AKIA[0-9A-Z]{16}                      AWS access key IDs
persist\.suding\.[a-z0-9._]+          OEM system properties
/system/(x)?bin/sd[a-z0-9_]*          the OEM's own binaries
```

The false positive rate is high by design. A discarded false positive costs seconds. A
hardcoded endpoint sitting in a partition nobody opened is exactly the failure this
sweep exists to prevent, and it is the failure the earlier 25% pass was vulnerable to.

### 3.2.1 Result

184 images scanned. Nine carry indicators:

```
fsg.img  fsg.bin              modem filesystem, both dumps
modem_a.img  modem_b.img      modem firmware, both dumps
qcache.img                    the writable credential partition
super.bin                     the dynamic partition super image
```

Most hosts recovered are unremarkable, being certificate and content strings from
Google, Adobe and VeriSign. Three findings are not.

**A Google Automotive Link private key is present in the raw `qcache.img` bytes.**
`BEGIN PRIVATE KEY` appears in the partition image alongside `persist.suding.dev.uuid`,
`com.suding.settings`, `com.suding.speedplay` and `com.carsyso.bluetooth`. That is the
operational credential discussed in §5.3.1, confirmed at the block level rather than
inferred from a mounted filesystem.

**Qualcomm assisted-GPS is fetched over cleartext HTTP.** The modem partitions carry:

```
http://path2.xtracloud.net/xtmation
http://path3.xtracloud.net/xtra3Mi_eph.bin
https://path1.xtracloud.net/xtra3grcej.bin
```

XTRA is Qualcomm's gpsOneXTRA assistance data. Some paths use TLS and some do not.
Assistance data delivered over plain HTTP is a known tampering surface, since a
network-position attacker can serve modified ephemeris.

**China Mobile appears in the modem firmware.** `http://www.10086.cn`, 10086 being
China Mobile's service number. This is independent corroboration, from the raw modem
image rather than from application strings, of the CMCC customization discussed in
Chapter 9.

Note for the record: this scan did not run in the original 2026-07-28 pass. The
classification half completed and wrote 115 rows; the indicator half produced no
output file. It was re-run on 2026-07-31 across 184 images, and the three findings
above are the result. The gap is documented here rather than quietly closed, because a
coverage argument that hides a failed pass is worth nothing.

## 3.3 Android Binary XML

`packages.xml` is the authoritative record of what is installed, what each package is
signed with, and what permissions each holds. On AOSP 12 and later it is not XML. It
is ABX, a binary token stream, and the standard `abx2xml` converter ships inside the
Android build system rather than in any distribution package.

Running `strings(1)` on an ABX file produces every string in the document with no
structure. That is actively misleading here, because the question is not which strings
appear but which permission belongs to which package. ABX interns strings into a pool
and refers to them by index, so adjacency in the raw file carries no meaning.

`abx2xml.py` was written for this analysis: 133 lines implementing the token stream
from `BinaryXmlSerializer.java` and `BinaryXmlPullParser.java`, including the
`FastDataInput` interning scheme.

```
4-byte magic "ABX\0", then tokens
  low nibble  = XmlPullParser event   START_TAG, END_TAG, ATTRIBUTE, TEXT
  high nibble = value type            STRING, STRING_INTERNED, INT, LONG,
                                      BYTES_HEX, BYTES_BASE64, BOOLEAN, ...
  interned strings: leading 0xFFFF means "new, append to pool",
                    anything else is a pool index
```

Validated against `packages.xml`, which decoded cleanly to 245 packages with correct
attribute pairing. It still desynchronises on some `settings_*.xml` files, which is
recorded here as a known limitation rather than smoothed over. Those files were not
load-bearing for any finding.

## 3.4 Verified Boot inspection

`avbtool.py` is upstream AOSP tooling, Copyright 2016 The Android Open Source Project,
5,052 lines. It is used here unmodified to parse vbmeta structures, read hash and
hashtree descriptors, and extract the public key each image is signed against.

It is cited rather than claimed. The point of using the vendor's own tool is that a
reviewer at Google can reproduce every AVB assertion in this paper with software they
maintain.

## 3.5 Package signing survey

Every APK on the device was extracted and its signing certificate read, producing a
subject and SHA-256 fingerprint per package. This is mechanical and its value is
entirely in being exhaustive: the finding is not that some packages carry a test key,
it is the ratio, and the ratio only means something if the denominator is every
package rather than the ones that seemed interesting.

Result, developed in Chapter 5: 294 of 354 packages carry an AOSP-published signing
identity, 267 of them on four certificates.

## 3.6 Report generation

`build_pdfs.sh` renders the case reports through pandoc and xelatex. Two choices in it
are worth recording because both were forced by content rather than preference.

**xelatex rather than pdflatex.** The reports contain CJK, notably \cjk{苏丁}, the vendor's
name in Chinese. pdflatex fails on it. Noto Sans CJK SC is set as the main font so
those glyphs render rather than becoming tofu or a hard build error.

**2 cm margins at 10 pt.** SHA-256 fingerprints are 95 characters. Several reports
carry wide fingerprint tables that overflow the text block at default geometry.

## 3.7 What the method does not cover

Stated plainly, because a coverage argument is worthless without its complement.

**No live-system dynamic analysis in this pass.** The 2026-05-21 live extraction over
ADB is separate work, reported in Chapter 7, and used a different access path.

**No TLS interception.** Endpoint behavior in this paper is derived from static
analysis of the applications that contact them, not from observed traffic. Planned as
Phase 2.

**No modem firmware reverse engineering.** `modem_a.img` and `modem_b.img` at 188 MB
and 6.792 entropy were classified and IOC-scanned but not disassembled. The remote SIM
provisioning findings in Chapter 8 come from the Android-side packages that drive the
modem, not from the modem image itself.

**ABX parsing is incomplete** for some settings files, as noted in 3.3.

**No RF-side testing of the Bluetooth chain, and the reason is a real conflict rather
than an oversight.** A device carrying a cellular modem, an eSIM that can be
reprovisioned remotely, and six silent-install channels is examined inside a shielded
enclosure. That is the correct handling. It stops the subject reaching a network, being
updated mid-analysis, or moving data out while it is open.

The vehicle-side chain in §10.5 runs over Bluetooth Low Energy to the bundled OBD-II
reader, and shielding suppresses exactly that link. The pairing did not stay up inside
the enclosure. Exercising that chain requires the RF environment the enclosure exists
to remove.

**Both requirements cannot be satisfied on the same bench.** Doing it properly needs a
screened environment with controlled RF pass-through, or an unshielded rig accepting
that a modem-equipped subject is live on air throughout the test. Neither was available
here.

**The head unit was simulated too, and that is the second bench artifact.** The
receiver side of the rig was an open-source Android Auto head unit implementation
rather than a factory unit in a vehicle, and the projection session did not sustain
against it. That is a property of the substitute, not of the product. A wireless
projection adapter that dropped session in a real car would be returned by every
customer who bought one, and this one has sold across multiple brands for roughly five
years. Sustained session is not something this paper needs to demonstrate; it is the
advertised function, and the product's continued commercial existence is the evidence.

**Both failures are the rig.** Neither is why the terminal step of §10.5 went
unvalidated in a vehicle. That reason is that both devices entered HSI custody before a
vehicle test could be arranged.

Recorded because the next person to attempt this will meet the same wall on their first
afternoon, and because a limitation with a stated cause is worth more than a silence.

---

## Appendix A - tooling

| Tool | Origin | Role |
|---|---|---|
| `edl` (bkerler) | Third party, Python | Sahara and Firehose client, drove acquisition |
| `oneshot_dump.sh` | Written for this case | Single-pass eMMC read wrapper |
| `multi_lun_dump.sh` | Written for this case | Walks LUN 0 through 7 on UFS |
| `sweep_partitions.sh` | Written for this analysis | Entropy classification and IOC sweep, 115 images |
| `abx2xml.py` | Written for this analysis | Android Binary XML decoder, 133 lines |
| `avbtool.py` | AOSP upstream, unmodified | Verified Boot structure parsing |
| `sepolicy_reach.py` | Written for this analysis | CIL set-expression evaluator, domain reachability, §9.5 |
| `build_pdfs.sh` | Written for this case | Report rendering, pandoc and xelatex |
| `jadx` | Third party | APK decompilation |

Source for the four case-written tools is reproduced in Appendix D.
