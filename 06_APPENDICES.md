# Appendices

> Published 2026-09-01. Disclosure status is in the front matter.

---

# Appendix B - Indicator catalogue

Endpoints, identifiers and constants recovered during this analysis. Sources are
marked: `static` from application decompilation, `raw` from partition-image byte
scanning, `live` from the 2026-05-21 device extraction, `oss` from published
open-source projects that independently reference the same values.

## B.1 Vendor and OEM endpoints

| Indicator | Role | Source |
|---|---|---|
| `gpstrack.myatoto.com` | GPS position upload, `/atoto-gps-core/gps/v1/uploadPosition` | static, live |
| `aboss.myatoto.com` | Account binding, knowledge-chat backend | static |
| `iotmqtt.abupdate.com` | ADUPS MQTT broker, silent-install channel | static |
| `iotapi.abupdate.com` | ADUPS OTA API | static |
| `iotapi.adups.com` | ADUPS OTA API | static |
| `sudingtech.oss-cn-shenzhen.aliyuncs.com` | OEM-direct delivery, Alibaba Shenzhen | static |
| `data.carlinkit.com:8610` | Carlinkit backend, referenced from Atoto-branded unit | static |
| `120.79.59.57:8080` | Alibaba Hangzhou. `/device-web/open/{queryClientMD5,downLoadFile,addModeInfo}` | static |
| `file.myatoto.com` | Firmware CDN | oss |
| `fota.redstone.net.cn:7100` | Chinese FOTA endpoint, Atoto head-unit line | oss |
| `atoto-usa.oss-us-west-1.aliyuncs.com` | Alibaba OSS, US-region name, Chinese-owned | oss |
| `api.paplink.cn/a/upgrade/{checkBox,down}` | Carlinkit dongle line OEM update | oss |

## B.2 Third-party SDK endpoints

| Indicator | Role | Source |
|---|---|---|
| `vop.baidu.com` | Baidu speech-to-text | static |
| `tsn.baidu.com` | Baidu text-to-speech | static |
| `kmp1.picovoice.net` | Picovoice wakeword engine telemetry | static |
| `astat.bugly.qcloud.com` | Tencent Bugly crash reporting | static, live |
| `h.trace.qq.com` | Tencent tracing | static |
| `174.129.223.121` `/WAS/text2speach` | AWS US-East-1 fronting a Chinese TTS SDK | static |

## B.3 Recovered from raw partition bytes

| Indicator | Partition | Note |
|---|---|---|
| `BEGIN PRIVATE KEY` | `qcache.img` | the operational Google Automotive Link key |
| `persist.suding.dev.uuid` | `qcache.img` | device identifier, survives factory reset |
| `http://www.10086.cn` | `modem_a.img`, `modem_b.img` | China Mobile, corroborates CMCC customisation |
| `http://path2.xtracloud.net/xtmation` | `modem_*.img` | Qualcomm assisted-GPS over cleartext HTTP |
| `http://path3.xtracloud.net/xtra3Mi_eph.bin` | `modem_*.img` | as above |

Partitions carrying indicators: `fsg`, `modem_a`, `modem_b`, `qcache`, `super`, across
both dumps. 184 images scanned.

## B.4 Certificates and keys

| Artifact | Value |
|---|---|
| Platform signing key | `C8:A2:E9:BC:CF:59:7C:2F:B6:DC:66:BE:E2:93:FC:13:F2:FC:47:EC:77:BC:6B:2B:0D:52:C1:1F:51:19:2A:B8` |
| OTA signing cert | `A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC` |
| GAL root | `O=Google Automotive Link`, self-signed, 2014-06-06 to 2044-06-05 |
| GAL leaf, operational | serial `[REDACTED]`, SHA-1 `[REDACTED]`, expires 2026-08-05 |
| GAL leaf, rotated out | serial `[REDACTED]`, SHA-1 `[REDACTED]`, expired 2025-10-16 |

## B.5 Device and platform identifiers

```
HWID          0x0014d0e100000000   MSM_ID 0x0014d0e1  OEM_ID 0x0000  MODEL_ID 0x0000
PK_HASH       0xd40eee56f3194665574109a39267724ae7944134cd53cb767e293d3c40497955...
serial        0xd47e5dbc
dev uuid      f8160852-24d3-431e-939d-0cc1995c04aa
deviceid      35650513247c73359b
Bugly id      79c4a0edc80c4acc8b8c1ec5c89381ce
baseband      BA01BP02K0M01(SC200UNAUAR01A01)
USB, default  18d1:4ee1  "Google" "Pixel"
USB, true     05c6:90db  Qualcomm BENGAL-IDP _SN:D47E5DBC
FCC IDs       2AR24AIBOX01, XMR2025SC200UNA
```

## B.6 Protocol constants (open-source corroboration)

```
0x18d1:0x4ee1          USB identity disguise, Carlinkit-family pattern
0x1314:0x1520          alternate Carlinkit dongle USB identity
0x55aa55aa             host-to-dongle wire protocol header magic
Magic-Car-Link-1.00    dongle protocol self-identifier
SendGnssData           host-to-dongle GPS delivery command
```

---

# Appendix C - Evidence manifest

| Artifact | Content | Integrity |
|---|---|---|
| EDL acquisition, 12 sessions | 31 GB raw partitions, 2026-05-19 | per-session `rl.log` |
| ROM dump 2026-06-04 | 71 partition images | SHA-256 manifest |
| Live extraction 2026-05-21 | 871 MB, 876 files | SHA-256 manifest |
| Partition classification | 115 images, entropy and nonzero ratio | `partition_classification.tsv` |
| Indicator sweep | 184 images, 9 with hits | `partition_iocs_20260731.txt` |
| APK signing survey | 354 packages | `apk_signing.tsv` |
| PoC evidence bundle | TLS logs, autoapp logs, screenshot | `SHA256SUMS.txt` |
| Sealed archive | full case, AES-256 | GPG, operator-held passphrase |

Known gap: `handshake.sanitized.pcap` in the PoC bundle is 24 bytes and contains zero
packets. Recorded rather than silently omitted.

---

# Appendix D - Tooling

| Tool | Origin | Role |
|---|---|---|
| `edl` (bkerler) | third party, Python | Sahara and Firehose client |
| `oneshot_dump.sh` | written for this case | single-pass eMMC read |
| `multi_lun_dump.sh` | written for this case | walks LUN 0-7 on UFS |
| `sweep_partitions.sh` | written for this analysis | entropy classification, indicator sweep |
| `abx2xml.py` | written for this analysis | Android Binary XML decoder, 133 lines |
| `avbtool.py` | AOSP upstream, unmodified | Verified Boot structure parsing |
| `sepolicy_reach.py` | written for this analysis | CIL set-expression evaluator, domain reachability, section 9.5 |
| `build_pdfs.sh` | written for this case | report rendering, pandoc and xelatex |
| `jadx`, `dex2jar`, `jd-gui` | third party | APK decompilation |
| `f1xpl/aasdk`, OpenAuto | third party, patched | PoC receiver, Chapter 11 |
| `debugfs` | e2fsprogs | block-level partition reads, no mount |
| `sesearch` (setools 4.4.4) | upstream | compiled-policy query, confirms section 9.5 |
| `openssl` | upstream | certificate and key verification |

---

# Appendix E - Observations and open items

Two separate lists. The first is things that were found and written up but not
confirmed. The second is work that was not attempted.

The reason for keeping the first list at all: an observation that gets dropped because
it could not be proven has to be rediscovered by the next person, who will spend the
same hours reaching the same undecided answer. Recording it at the strength the
evidence actually supports costs a paragraph and saves that. What an observation does
not get to do is contribute to a severity argument, or appear in anything filed with
Google, and none of these do.

## E.1 Observations recorded but not confirmed

**`sd-link.sh`, section 9.5, resolved as blocked.** Listed here because the section
is written as an observation and a reader should be able to find what became of it.
Full expansion of all five shipped policy files, evaluating set expressions rather
than flattening them, returns zero allow rules connecting the init domain to
`app_data_file` or `privapp_data_file`. The design would be a code-execution path if
one policy line were different. That line is not there.
*Read with section 9.6:* the policy files sit on update-replaceable partitions and
updates are verified against a published key, so this is a statement about the file
the device currently carries rather than about the hardware.
*Closed 2026-08-01:* `sesearch` (upstream setools 4.4.4) against
`vendor/etc/selinux/precompiled_sepolicy`, the binary the device boots, returns zero
allow, auditallow, dontaudit and type_transition rules on both types, with positive
controls firing. Two independent methods over two artifacts agree.
*Residual:* no boot-time audit log was captured, so the denial is inferred from policy
rather than observed firing.

**Key-handler return values, section 6.5.** Chapter 6 establishes that `MainAiBox`
handles `KEYCODE_SRC` and `KEYCODE_SETTING` and that both display-owning applications
reference `LOCK_TASK`. Whether the handlers consume those keys rather than pass them
through, and whether lock task is engaged at runtime rather than merely referenced,
is not established. The owner's experience of the device is not in doubt; the
mechanism behind it is identified but not proven.
*To settle it:* a jadx decompile of `MainAiBox.onKeyDown` and the `SdLauncher3`
interceptor, tracing return values and any `startLockTask()` call site.

**Cause of the proof-of-concept session drop, section 11.4.** Authentication completed
six times and the session ended about ten seconds later each time. Two candidate
causes, a keepalive bug in the patched 2018 receiver or three service-discovery fields
left at library defaults, and the evidence captured does not separate them.
*To settle it:* a packet capture of the interval between authentication and timeout,
showing whether the phone stopped responding or the receiver stopped pinging. The
capture in the submitted bundle is 24 bytes and holds zero packets.

## E.2 Work not performed

**Bundled OBD-II reader firmware, section 10.5. Not recoverable by this
investigation.** The reader shipped in the same retail package was never flash-dumped
and its BLE command framing was never sniffed. Those two steps decide whether the
chain in 10.5 terminates at the vehicle bus or at a constrained diagnostic API. The
device was handed to Homeland Security Investigations with the AI Box in the same
custody chain before the dump was performed, so the work cannot be completed here.
*To settle it, for whoever holds the hardware:* SWD or UART dump of the reader's MCU,
plus a passive BLE capture between box and reader during normal operation. Method is
specified in the separate NHTSA-track case document.

**Modem firmware.** `modem_a.img` and `modem_b.img`, 188 MB each at 6.792 entropy,
classified and indicator-scanned but not disassembled.

**ABX parsing.** `abx2xml.py` decodes `packages.xml` cleanly at 245 packages but
desynchronises on some `settings_*.xml`. Not load-bearing for any finding here.

**TLS interception.** Endpoint behaviour throughout is from static analysis, not
observed traffic. Planned as a later phase.
