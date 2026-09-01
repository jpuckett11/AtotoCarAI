# Chapter 4 - Identity, and Chapter 5 - Trust

> Published 2026-09-01. Disclosure status is in the front matter.

---

# Chapter 4 - What the device says it is

Before examining what the device does, it is worth establishing what it claims to be,
because in four separate places it claims to be something it is not.

## 4.1 It enumerates as a Google Pixel

Plugged into a host in its default mode, the device presents this USB descriptor:

```
idVendor       0x18d1   "Google Inc."
idProduct      0x4ee1
iManufacturer  "Google"
iProduct       "Pixel"
```

`18d1` is Google's assigned USB vendor ID. The device is a Shenzhen-built board on a
Qualcomm SDM662 inside a Quectel SC200U module. It is not a Pixel and has no
relationship to Google beyond the certificate discussed in Chapter 5.

The true identity is reachable, but only after entering an OEM password on the head
unit display. With factory code `142618` the descriptor changes to:

```
05c6:90db  Qualcomm BENGAL-IDP _SN:D47E5DBC
```

That is not obfuscation for its own sake. A host operating system, a corporate
endpoint agent, or a USB device-control policy sees a Google Pixel. It does not see a
Chinese IoT module with a cellular modem.

**Independent corroboration.** The open-source Android Auto receiver project LIVI
(`github.com/f-io/LIVI`, MIT licensed, clean-room) hardcodes
`{ idVendor: 0x18d1, idProduct: 0x4ee1 }` as a recognized device identity for this
hardware family. The disguise is not an Atoto choice. It is a platform-level pattern
across the Carlinkit-family OEM output.

## 4.2 Eighteen hardcoded passwords open eighteen doors

`FactoryConfig.apk` (`com.sd.factoryconfig`) gates the OEM factory menu behind a
numeric keypad. Decompilation of `SplashActivity` recovered the full table. Entry is
by physical access to the touchscreen. There is no second factor, no account, no lock.

The main menu password varies by the `ro.board.reverse.custom` brand profile. On this
unit it is `4545`. The action passwords work regardless of variant:

| Code | Constant | Effect |
|---|---|---|
| `4545` | `PASS_WORLD` | Full factory settings menu |
| **`9527`** | `PASS_WORLD_WIFI` | **Enable wireless ADB.** Sets `service.adb.tcp.port 5555`, restarts adbd |
| **`142618`** | `PASS_WORLD_SDCARPLAY_REVERSE_DISABLE` | **Toggle PC-ADB mode**, exposes true Qualcomm identity, console debug |
| `9999` | `PASS_WORLD_OPEN_DEVELOPER_SETTINGS` | Android developer settings |
| `888888` | `PASS_WORLD_CHUAN_DEBUG` | Serial console debug |
| `1111` | `PASS_WORLD_IGNORE_ENCRYPTED` | **Ignore the OTA encryption check** |
| `123123` | `PASS_INSTALL_APP_PT` | Allow APK install |
| `6868` | `PASS_IGONORE_QR_CODE` | Bypass activation QR |
| **`668668`** | `PASS_WRITE_IMEI` | **Write IMEI** |
| `1134` | `PASS_WORLD_2290_1234` | Opens `com.quectel.modemreboot`, `com.meig.logger`, `com.qlog` |
| `4747` | `PASS_4G_CONTROL` | Toggle 4G |
| `5212` | `PASS_WORLD_HDMI_OTA` | HDMI OTA upgrade |
| `110144` | `CLEAN_FACTORY_CONFIG` | Clear factory config |

Three of those deserve emphasis.

`9527` enables **wireless ADB on TCP 5555**. The device auto-joins saved Wi-Fi
networks. Anyone who has touched the screen once has a persistent remote root path
from anywhere on that network.

`668668` **rewrites the IMEI**. That is a device-cloning and fraud primitive shipped
in a consumer product, gated by a six-digit constant recoverable by anyone who
decompiles the APK.

`1111` **disables the OTA encryption check**, which matters in combination with the
update channels in Chapter 7.

## 4.3 The brand on the box is not the manufacturer

`/system/bin/led.sh`, an autostarted root script, branches on
`ro.board.reverse.custom` across eight internal brand profiles:

```
ronglianfa   chelianyi   huachuang   xiluo
suding       huawei      123         chelianyi-SA
```

Each profile remaps LED pin assignments, so each corresponds to distinct hardware
sharing one firmware. One of them is `huawei`.

Combined with the retail brands, the same codebase reaches consumers under at least
fourteen identities. `CarDataManager.apk`, shipped on an **Atoto**-branded unit
purchased at retail, contains verbatim:

```
Carlinkit
CARLINKITNAVIGHU9
http://data.carlinkit.com:8610
```

The Atoto-branded device queries Carlinkit infrastructure in production, from a
multi-brand binary that knows Carlinkit's product line.

## 4.4 Two more disguises

**`TexusTek`** reads as Tex-US-Tek. It is a Chinese SDK vendor supplying a Baidu
wrapper. The name defeats pattern-matching on Chinese vendor brands.

**A Chinese TTS service fronted on AWS.** `174.129.223.121` is AWS US-East-1. The URL
path is `/WAS/text2speach`. The misspelling is the tell; the hosting choice makes a
Chinese SDK look domestic.

## 4.5 The device was built for Vietnam and sold in Tennessee

| Artifact | Evidence |
|---|---|
| Vietnam APNs | `apns-conf.xml`, multiple `mcc="452"` entries |
| Vietnam map data | `/system/media/NavitelContent/Maps/vnm20220714_v9.nm7`, preinstalled |
| Region marker | `VN` inside `/system/etc/Client.privatekey` |
| Vietnamese brand permission | `vn.icar.entertaiment.REMOTE`, declared by `SdLauncher3` |

A US consumer buying this Amazon SKU receives a Vietnam-regional firmware load with
China Mobile modem customization.

---

# Chapter 5 - Trust

This chapter is the case. Every mechanism below is a place where the device is
supposed to verify something and does not.

## 5.1 The platform is signed with a published key

`framework-res.apk`, the `android` package that defines platform signing identity:

```
subject   C=US, ST=California, L=Mountain View, O=Android, OU=Android,
          CN=Android, android@android.com
SHA-256   C8:A2:E9:BC:CF:59:7C:2F:B6:DC:66:BE:E2:93:FC:13:
          F2:FC:47:EC:77:BC:6B:2B:0D:52:C1:1F:51:19:2A:B8
```

That is the AOSP platform key from `build/target/product/security/`. Its private half
is in the Android source tree, public since 2008, present on every machine that has
ever cloned AOSP.

That sentence is the load-bearing claim of this chapter, so it was verified against
upstream rather than asserted from the subject line. The five certificates were pulled
directly from `android.googlesource.com/platform/build`, fingerprinted, and compared:

| Device certificate | AOSP file | Serial | Packages |
|---|---|---|---:|
| `C8:A2:E9:BC:...:19:2A:B8` | `platform.x509.pem` | `B3998086D056CFFA` | 171 |
| `A4:0D:A8:0A:...:1B:F5:DC` | `testkey.x509.pem` | `936EACBE07F201DF` | 84 |
| `E1:DB:AD:CE:...:BE:BD:A2:EE` | `networkstack.x509.pem` | `FC6CB0D8A6FDD168` | 9 |
| `46:59:83:F7:...:41:A8:1E` | `media.x509.pem` | `F2B98E6123572C4E` | 7 |
| `28:BB:FE:4A:...:E8:79:FD` | `shared.x509.pem` | `F2A73396BD38767A` | 5 |

Every fingerprint is an exact match. These are not keys that resemble the AOSP keys,
or keys generated from the AOSP subject template, which is a real and common practice
that would produce the same distinguished name with different key material. They are
the published keys themselves, serial numbers included.

The distinction matters enough to record how it can go wrong. An earlier working note
in this case reasoned from the subject line alone, observed that every OEM building
AOSP regenerates this certificate with the same distinguished name, and concluded that
this was therefore a vendor-generated key rather than a published one. That conclusion
is incorrect, and the serial it cited as evidence, `B3998086D056CFFA`, is the AOSP
platform key's own serial. Subject lines do not identify keys. Fingerprints do.

**294 of 354 packages, 83.1%**, carry a signing identity issued under `O = Android`.
That subject is the discriminator: genuine Google-signed packages on this device carry
`O = Google Inc.`, while every AOSP-published test key and the Android Debug keystore
carries `O = Android`. The 294 are spread across fourteen distinct certificates, four
of which account for 267 of them:

| Certificate | Count |
|---|---:|
| `C8:A2:E9:BC:...:19:2A:B8` (platform) | 171 |
| `A4:0D:A8:0A:...:1B:F5:DC` (testkey) | 84 |
| `46:59:83:F7:...:41:A8:1E` | 7 |
| `28:BB:FE:4A:...:E8:79:FD` | 5 |
| ten further AOSP keys, including `networkstack` and two debug-keystore signatures | 27 |

![**Figure 2. Package signing identities on the shipped device.** Every APK on the unit was extracted and its signing certificate read; the denominator is every package, not a sample. The private half of the top certificate has been public in the Android source tree since 2008.](figures/fig1_signing.png)

Every count in this section is reproducible from
`atoto_reseal_20260728/evidence/apk_signing.tsv` by grouping on the subject field. An
earlier draft of this paper reported 283 and 79.9% against a four-certificate table
that summed to 267; neither figure survives a recount, and both are corrected here.

Security-critical packages on the platform key include `PackageInstaller`, `Shell`,
`Settings`, `SettingsProvider`, `SystemUI`, `KeyChain`, `ManagedProvisioning`,
`TelephonyProvider`, `CarrierConfig`, `Bluetooth`, and the entire remote SIM stack:
`uimlpaservice`, `uimremoteclient`, `uimremoteserver`, `remotesimlockservice`.

The consequence is not subtle. Anyone can compile an APK, sign it with a key they
already have, and receive `platform_app` context on this device. Signature-level
permissions are not a barrier here. They are documentation of what an attacker gets
for free.

`ro.build.tags` asserts `release-keys`. It is a string in a properties file. Nothing
checks it against the actual signature.

## 5.2 Update packages are verified against the same published key

`/system/etc/security/otacerts.zip` contains exactly one certificate:

```
testkey.x509.pem
SHA-256  A4:0D:A8:0A:59:D1:70:CA:A9:50:CF:15:C1:8C:45:4D:
         47:A3:9B:26:98:9D:8B:64:0E:CD:74:5B:A7:1B:F5:DC
```

That file is what the recovery updater verifies OTA packages against. It is a
different key from §5.1, doing a different job, and it is equally public.

**Anyone can sign an update package this device will install.** Combined with
factory code `1111`, which disables the OTA encryption check outright, and with the
six delivery channels in Chapter 7, the update path has no authenticity property at
all.

## 5.3 A Google-issued production private key, in the clear

> **Redaction note.** Serial numbers, SHA-1 fingerprints and modulus digests for the
> Google Automotive Link credentials are redacted in this published version. They are
> identifiers for a credential Google issued and only Google can revoke, and printing
> them serves no reader. The findings do not depend on the values: what matters is
> that the key matches its certificate, that both pairs chain to the Google root, and
> that a retired pair was never removed. The AOSP platform and OTA signing keys are
> **not** redacted, because those are published in the Android source tree and their
> publicness is the finding.

The device carries three files in `/system/etc`:

```
AndroidAuto.crt      subject = issuer = O=Google Automotive Link
                     self-signed root, valid 2014-06-06 to 2044-06-05

Client.crt           subject O=CarService
                     issuer  O=Google Automotive Link
                     serial  [REDACTED]
                     valid   2014-07-04 to 2025-10-16

Client.privatekey    -----BEGIN PRIVATE KEY-----   unencrypted PKCS#8
```

Verification performed for this paper:

```
modulus of Client.crt   sha256[0:32]  [REDACTED]
modulus of the key      sha256[0:32]  [REDACTED]   IDENTICAL

openssl verify -no_check_time -CAfile AndroidAuto.crt Client.crt   ->  OK
```

The private key matches the certificate. The certificate was issued by Google's
Android Auto certificate authority. It is stored unencrypted on a read-only partition
that any purchaser can dump in five minutes using the method in Chapter 2.

This is not a vendor's key stored badly. It is a credential Google issued, and only
Google can revoke it.

### 5.3.1 Two credentials, one operational and one rotated out

The device carries **two** Google Automotive Link key pairs, in two locations, and
only one of them is live.

```
                   OPERATIONAL                     ROTATED OUT
location           /mnt/vendor/qcache/             /system/etc/
serial             [REDACTED]                  [REDACTED]
SHA-1              [REDACTED]     [REDACTED]
notBefore          2014-07-04                      2014-07-04
notAfter           2026-08-05 16:47:49             2025-10-16   expired
key modulus        [REDACTED]        [REDACTED]
chains to GAL root OK                              OK
file mtime         2026-05-15 11:28                shipped in ROM
```

Both key pairs verify. Both chain to the Google root. The `/system/etc` pair is a
retired credential the vendor never removed; the qcache pair is the identity the
device actually presents.

That has a consequence for remediation. **Each Google-mandated rotation writes the new
credential to `/qcache` without removing the prior pair from `/system/etc`.** The
presence of two complete, valid-signature key pairs on one retail unit is direct
evidence that the vendor does not garbage-collect retired credentials. Every rotation
since 2014 may still be recoverable from devices in the field.

Neither location is protected by Verified Boot. `/qcache` is additionally marked
`formattable` in `fstab`, is mounted without `ro`, has a root directory of mode
`40777`, and is re-`chmod 777`'d at every boot by a shipped script. See §5.5.

**The operational certificate expires 2026-08-05 at 16:47 UTC.**

The mtime is the other half of the story. All three qcache credential files are dated
2026-05-15 11:28, four days before the firmware image in this analysis was taken and
inside the collection window evidenced in Chapter 8. The rotation happened on a
retail unit in an owner's possession, delivered by the mechanism in §5.4, and the
files it wrote were still resident when the device was imaged.

That deadline also explains why §5.4 exists at all. A fleet credentialed with
certificates that expire needs a way to be re-credentialed in the field. The vendor
built one, and built it over cleartext HTTP.

The operational credential is the one used in the proof of concept in Chapter 11.

### 5.3.2 The cheapest fix for a leaked credential strands the person who bought the device

A leaked credential with a fixed expiry date has an obvious and nearly free
remediation. Do nothing. Let it expire on schedule, and decline to issue the vendor a
replacement. No certificate revocation, no change to the CA, no disruption to any
other licensee, no engineering work. Every other holder of a Google Automotive Link
credential rotates normally and stays online. The leaked key becomes worthless at
16:47 UTC on 2026-08-05 without anyone touching anything.

**[I] This is inference about remediation strategy, not a statement of what Google
did.** It is recorded because it is the cheapest available path, because it is
consistent with a Moderate severity rating on a finding of this shape, and because it
predicts something specific and checkable.

What it predicts is this. On 2026-08-05 the units running this firmware stop being
able to complete the wireless receiver handshake. Not because they broke. Because a
certificate the owner was never told about expired, and no replacement was issued to
the company that sold it to them.

**Nobody tells the owner.** There is no notification path in the firmware for this. The
device does not say a credential expired. It will present as a fault, and the
reasonable consumer response to a fault in a sub-hundred-dollar accessory is to assume
it is broken and buy another one. The retail listing continues to advertise wireless
Android Auto and CarPlay.

**This is checkable now rather than in principle.** The expiry date is on the
certificate, it has passed, and anyone holding one of these units can test whether the
wireless receiver function still works. We could not run that test ourselves: the
device and its bundled reader were handed to Homeland Security Investigations before
the expiry date.

**What is not established.** That Google chose non-renewal, that Suding has not
obtained a credential by another route, and how many units are affected. Those are
questions for the parties who can answer them.

**[I] The point worth carrying.** The disclosure protected the credentialing system,
and it protected every legitimate licensee, and it protected Google. It did not protect
the person who paid for the box. The remediation that costs the vendor and the platform
nothing transfers the entire cost to the buyer, silently, on a date they were never
given. That is not a security failure. It is what a security fix looks like when nobody
in the chain has an obligation to the person at the end of it.

## 5.4 The trust anchor is remotely rewritable over cleartext HTTP

`ReportDataService.checkAndDownloadAutoCert()` in `CarDataManager.apk` runs **every 60
seconds** whenever a network is available:

```
POST http://120.79.59.57:8080/device-web/open/queryClientMD5     cleartext HTTP
  <- canonical MD5 of the client certificate
  on mismatch:
POST http://120.79.59.57:8080/device-web/open/downLoadFile       cleartext HTTP
  <- { "clientCrt": <b64>, "androidAutoCrt": <b64>, "clientPrivateKey": <b64> }

  androidAutoCrt    -> getAndroidAutoCertPath()   the Google root CA
  clientPrivateKey  -> getClientPrivatekeyPath()  the private key
  clientCrt         -> getClientCertPath()        the identity certificate
```

Code: `ReportDataService.java:307-340`, `NetworkCoreManager.java:300-330`,
`BaseHttpClient.java:42-70`, `AutoReverseUtils.java:16-20`.

`120.79.59.57` is Alibaba Cloud, Hangzhou. Request integrity is
`MD5(json + SUDING_SIGN_KEY)` where the sign key is a compile-time constant in
`SudingHttpClient`, recoverable by decompiling the APK that everyone has.

**There are two clients, not one.** `CarDataManager` ships `SudingHttpClient`, carrying
`SUDING_BASE_URL = "http://120.79.59.57:8080/device-web"` with the paths above, and
`YunlianHttpClient`, which hardcodes the same host and the same `queryClientMD5` and
`downLoadFile` endpoints in full, plus an additional `/open/addModeInfo`. Each has its
own compile-time sign key. The cleartext certificate-replacement surface is therefore
reachable by two independent code paths inside one application, and hardening either
one would not close the other.

Three failures compose:

1. **No transport security.** No server authentication, no confidentiality, no
   integrity.
2. **The authentication secret ships inside every copy of the client.** MD5 has been
   unfit for security use since 2008.
3. **The write target includes the root CA.** Replacing a root invalidates every
   verification beneath it, not merely the identity presented.

Anyone on the network path, or controlling that host, can install an attacker-chosen
Automotive Link identity *and* dictate which authority the device trusts. The
sixty-second interval removes any need to wait for an update window.

## 5.5 The same anchor is writable locally, with no network position at all

Android's own trust store is protected correctly on this device. From
`plat_file_contexts` and `plat_sepolicy.cil`:

```
/system/etc/security/cacerts(/.*)?   u:object_r:system_security_cacerts_file:s0

allow domain system_security_cacerts_file (dir  (ioctl read getattr lock open
                                                 watch watch_reads search))
allow domain system_security_cacerts_file (file (ioctl read getattr lock map
                                                 open watch watch_reads))
```

No `write`, no `append`, no `create`, no `unlink`, no `rename`, granted to any domain
anywhere in policy. `/system` is mounted `ro` under `avb=vbmeta_system`. Tampering
would fail dm-verity at boot. Google designed that correctly.

The vendor then added a second trust anchor outside all of it.
`getAndroidAutoCertPath()` resolves to `/cache/AndroidAuto.crt`, with the persistent
copy under `/mnt/vendor/qcache`. Compare the two mounts:

```
system                                /system              ext4  ro,barrier=1,discard   wait,avb=vbmeta_system,logical
/dev/block/bootdevice/by-name/qcache  /mnt/vendor/qcache   ext4  noatime,nosuid,nodev,barrier=1,discard   wait,formattable,check
```

Neither `ro` nor `avb`. Writable, unverified, formattable.

Three things compound on that partition:

**A shipped script makes the directory world-writable.** `/system/bin/qcache_rw.sh`
is two lines:

```sh
#!/system/bin/sh
chmod 777 /mnt/vendor/qcache
```

**SELinux permits ordinary app domains to write it.** From `vendor_sepolicy.cil`:

```
allow platform_app_30_0 qcache_file (file (ioctl read write create getattr lock append map open ...))
allow priv_app_30_0     qcache_file (file (ioctl read write create getattr lock append map open ...))
allow platform_app_30_0 qcache_file (dir  (... write create add_name remove_name search))
```

**Obtaining `platform_app` requires no secret,** because of §5.1.

So an application signed with a published key writes the Google Automotive Link trust
anchor directly, into a world-writable directory, on a partition outside Verified
Boot. No network position. No MITM. No waiting for the poll.

## 5.6 Why this section is the case

The five preceding subsections are not five bugs. They are one property expressed five
ways: **on this device, nothing that is supposed to establish authenticity does.**

The platform key does not identify the platform. The OTA key does not authenticate
updates. The Google-issued identity is not secret. The root that would catch a forged
identity is itself replaceable, twice over, by two independent paths.

A defender asking "what would I have to compromise" gets no useful answer, because the
question presumes something worth compromising.

Chapter 11 tests the practical consequence: whether the recovered credential functions
as a Google-attested receiver identity against a current phone. It does.

---

*Chapter 6: what the device collects, and the 1,486 positions that prove it ran.*
