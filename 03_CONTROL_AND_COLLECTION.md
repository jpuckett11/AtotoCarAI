# Chapter 6 - Control of the vehicle's own interface

> Published 2026-09-01. Disclosure status is in the front matter.

Chapters 4 and 5 concern what the device is and what it verifies. This one concerns
something the owner experienced directly and which the firmware explains: once the
device is selected, the car's own interface becomes difficult to reach.

## 6.1 The observation

On a normal Android Auto session, the head unit remains in charge. One button returns
the driver to the vehicle's native interface: climate, defrost, camera, vehicle
settings. Projection is a source the head unit hosts, not a state it enters.

With this device selected, that stopped being true. Reaching the car's own controls
became difficult to the point of impracticality.

That is worth taking seriously for a reason that has nothing to do with data. The
controls a driver cannot reach include defrost and the reversing camera.

## 6.2 What the firmware shows

Three OEM applications participate.

**`MainAiBox`** handles the head unit's own hardware key codes directly, including:

```
KEYCODE_SRC        the SOURCE button, the control that changes input on a head unit
KEYCODE_SETTING    the settings button
HOME
```

with `onKeyDown`, `onKeyUp`, `onKeyDownPanel` and `onKeyUpPanel` handlers, plus
`moveTaskToFront` and a reference to `LOCK_TASK`.

**`SdLauncher3`** carries an `InterceptKeyEventListener`, `IMMERSIVE` mode, and its
own `LOCK_TASK` reference.

**`SpeedPlay`**, the projection shim built on TexusTek's mirror engine, carries
`autoConnect` in three places and is autostarted from `load_services.json` as
`org.texustek.mirror.core.MirrorService`.

## 6.3 Why the head unit's buttons reach the device at all

This is the part that makes the rest possible. CarPlay and Android Auto both forward
a defined set of head unit and steering wheel controls into the projection session, so
that a driver can operate the projected interface using the car's physical controls.
`KEYCODE_SRC` and `KEYCODE_SETTING` arrive at the device because the protocol delivers
them.

An ordinary projection client passes those through or ignores them. This device has
explicit handlers for both, in the application that owns the screen.

## 6.4 The configuration file removes the rest of the exits

`/mnt/vendor/qcache/FactoryConfig/sudingConfig.ini`, dated 2026-05-15, carries two
settings that complete the picture:

```ini
has_navi_bar=0
key_black_list=[{"key_package":"com.cyanogenmod.filemanager"},
                {"key_package":"com.android.quicksearchbox"},
                {"key_package":"com.android.documentsui"}]
```

`has_navi_bar=0` removes the Android navigation bar. No on-screen back, home or
recents.

The blacklist disables `com.android.documentsui`, which is the Android Files
application, a second file manager, and the system search box. The owner cannot browse
the device's own storage and cannot search it.

Neither setting has an entertainment rationale. Together with the key handling above
they describe one intent: the user sees what the device chooses to show them, cannot
navigate away with software controls, cannot leave with hardware controls, and cannot
inspect what is on the device.

## 6.5 The mechanism, and the limit of the evidence

Six capabilities are present in the shipped firmware:

1. Handlers for the exact keys a driver would use to leave the projection session.
2. A key interception listener in the launcher.
3. `LOCK_TASK`, Android's kiosk-mode facility, which pins an application so the user
   cannot leave it.
4. `autoConnect`, which re-establishes the mirror session.
5. `has_navi_bar=0`, removing the software navigation controls.
6. A package blacklist disabling both file managers and system search.

Taken together those are sufficient to produce exactly the behavior observed: the
exit control is consumed rather than honoured, the launcher is pinned, and any session
that does drop is re-established.

**What is proven:** the handlers, the listener, the `LOCK_TASK` references and
`autoConnect` are all present in the shipped binaries, in the applications that own
the display.

**What is not yet proven:** that the key handlers return consumed rather than passing
through, and that lock task is engaged at runtime rather than merely referenced. Both
questions are answered by a jadx decompile of `MainAiBox.onKeyDown` and
`SdLauncher3`'s interceptor, tracing return values and any `startLockTask()` call
site. That work is not in this pass and the claim is scoped accordingly.

The observation is not in doubt. The mechanism is identified. The final step from
"capable of this" to "does this" is one decompile away and should be taken before this
chapter is cited externally.

### 6.5.1 The decompile was taken, and it does not support the mechanism above

**Corrected 2026-09-01.** The paragraph above stands unedited, because the correction is
worth more than a quiet fix. The work it asked for has been done and the proposed
mechanism is **not** what the code shows.

`MainAiBox.apk` (sha256 `a22db806…1b25ce5d`) and `SdLauncher3.apk` (sha256
`d3bc1310…8dfe0728`) were decompiled from the 2026-06-04 ROM dump. Each finding below
is a negative stated with its control.

**1. `MainAiBox.onKeyDown` does not exist.** There is no `onKeyDown`, `onKeyUp` or
`dispatchKeyEvent` override anywhere in `MainAiBox`'s vendor code; the only occurrences
are inside bundled support-library classes. *Control: the string is present and findable
in that decompile, twice, in `AppCompatActivity`.* The method §6.5 named as the target
is not there.

**2. The launcher does not consume the exit keys.** `com.android.launcher3.Launcher`
does override `onKeyDown`, and for `KEYCODE_HOME` and `KEYCODE_BACK` it performs a
workspace UI action and then returns `super.onKeyDown(...)`. **It passes the event
through.** Consuming would require returning `true`, and it does not.

**3. Lock task is never engaged.** `startLockTask()` and `setLockTaskPackages()` appear
in neither APK. The single `LOCK_TASK` hit in each is an unrelated constant,
`ON_LOCK_TASK_MODE_CHANGED`, inside a bundled SystemUI helper.

**4. The key-shielding API is declared and empty.** The OEM SDK exposes an AIDL
interface `IMainSdkKeyServer` carrying `requestShieldKeys(byte[])` and
`requestUnshieldKeys(byte[])`. In `KeyBinder`, the class implementing it, **both method
bodies are empty.** The only key codes referenced anywhere in vendor code are media
transport keys.

**Capability 1 in the list above is withdrawn. Capability 3 is downgraded from
"present" to "referenced, never invoked."**

### 6.5.2 There is no lock, and that is the finding

The hunt for the locking mechanism failed because there is no locking mechanism. That
is not a gap in the analysis. It is the result.

The device never enters a locked state. It does not call `startLockTask`. It does not
consume the exit keys. Its key-shielding API is empty. **So there is no locked state to
leave, no mode to exit, and no flag that a user, an application, or a support technician
could clear.**

What holds the driver in place is **configuration**, assembled from §6.4 and unchanged
by this correction: `has_navi_bar=0` removes the on-screen navigation controls, the
package blacklist removes the alternate routes out through file managers and search,
and `autoConnect` re-establishes the session if it does happen to drop. None of those
is a lock. Each is a setting, and together they produce the same result as a lock while
being none of the things a lock is.

**That is worse than kiosk mode, not better.** A kiosk is a documented state. It has an
API, an owner, an entry point and an exit. It can be detected, disclosed, audited, and
switched off. This has none of that. There is no state to detect, nothing to name in a
bug report, and nothing for a vendor to disable in the next build. A vendor asked about
`startLockTask` can truthfully answer that they do not use it.

**It also explains why the decompile was always going to come up empty**, which is why
the failed hunt is published rather than buried. Anyone reading §6.5 would have gone
looking for the same call sites and found the same nothing. The absence is the evidence.

### 6.5.3 What the decompile found instead

The same pass surfaced a facility the earlier analysis had missed, and it points the
opposite way to the one that was proposed.

`IMainSdkKeyServer` exposes `requestMockKeyEvent(String, int, int)` over Binder, and
`com.carsyso.mainsdk.utils.KeyEventUtil` implements key **injection** directly: it
constructs a `KeyEvent` and dispatches it by reflection through
`InputManager.injectInputEvent`. Its own debug strings, in Chinese, describe simulating
the back key.

The evidence does not show the device swallowing the driver's key presses. It shows the
device able to manufacture key presses of its own, and exposing that ability over Binder
to anything that can bind the service. On a platform whose signing key is public
(§5.1), "anything that can bind the service" is not a meaningful restriction.

**Limits of this pass.** Two applications were examined, the two §6.5 named. Another
package could implement the same interface with real bodies; a search of `system/app`
and `system/priv-app` found no other implementation, but that search reads compressed
APK containers and is not conclusive. Runtime behavior was not observed.

## 6.6 Why it belongs in a security paper rather than a review

Difficulty reaching the car's interface reads as poor design. In the context of the
rest of this document it has four other properties.

It is **persistence**. A device the owner cannot easily exit is a device the owner
cannot easily inspect, disable or unplug in the moment they become suspicious.

It is **surface**. Everything in Chapters 4, 5 and 7 runs while the driver is looking
at a screen they cannot leave.

It is **safety**. The reversing camera and the defroster are not entertainment
features.

And it is **unaddressable**, which is the property §6.5.2 establishes and the one that
matters most for remediation. There is no lock here to remove. A defect with a name and
an API can be fixed, disclosed and verified fixed. A condition assembled from three
settings, none of which is individually wrong, has nothing for a vendor to patch, nothing
for a regulator to cite, and nothing for an owner to switch off. It is the same shape as
the credential problem in §5.3.2: a state that harms the buyer, costs nobody else
anything, and has no component whose removal resolves it.

---

# Chapter 7 - Persistence as a service

`AtotoKeepAliveService` is a system application whose entire purpose is restarting
other processes. It is not a general watchdog. It keeps alive exactly three things:

```
com.atoto.lockprovider
com.atoto.speechtotext.wakeup     the always-on wakeword listener
com.atoto.trackhu.                the GPS tracker
```

via `startForegroundService`.

Of everything on this device, the OEM built dedicated resurrection machinery for the
microphone and the location tracker.

That single fact reframes both of the findings it protects. A GPS uploader that stops
when killed is a feature working badly. A GPS uploader with a system-signed companion
whose job is to restart it is a design decision.

The same intent appears in `/system/etc/permissions/platform.xml`, where
`com.abupdate.fota_demo_iot`, the ADUPS update client, is placed on the Doze
allowlist as `allow-in-power-save`. Android suspends background applications when the
device idles. This one is explicitly exempted, so the silent-install channel is never
paused.

## 7.1 Corrected 2026-09-01: it is not three things, it is anything that asks

`AtotoKeepAliveService.apk` (sha256 `86d3edac…6f924ea8`) was decompiled. The paragraphs
above are left as written; the correction is below, because it makes the finding worse
rather than softer.

**It does not keep alive a list of packages. It keeps alive a list of intent actions,
resolved at runtime.**

```java
private static final String[] actions = {
    "com.atoto.keepalive",
    "com.atoto.speechtotext.wakeup",
    "com.atoto.trackhu.KEEP_ALIVE"
};
```

`KeepAliveUtils.findServiceAndGenerateIntent` calls
`getPackageManager().queryIntentServices(new Intent(action), 0)`, builds an explicit
intent for **every service that matches**, and `KeepAliveService.checkProcessIfAlive`
starts any of them not currently running, via `startForegroundService`. The loop runs
**every 10 seconds**, beginning 30 seconds after start.

**So the resurrection is not scoped to the microphone and the GPS tracker. It is
available to any application that declares one of those three actions in its manifest.**
Declare `com.atoto.keepalive` on a service and a system-signed, `persistent="true"`
process will restart it within ten seconds of it being killed, indefinitely, with no
user-visible indication. On a platform whose signing key is published (§5.1), the set of
applications that can do this is unbounded.

**The service itself is unprotected.** From the manifest:

```xml
<service  exported="true" persistent="true" name="…KeepAliveService"/>
<provider exported="true" authorities="com.atoto.lockprovider" name="…LockProvider"/>
```

Both are exported. **Neither declares a permission.** Any application can start the
service and any application can reach the provider.

**And `com.atoto.lockprovider` is not a lock in the §6 sense.** It is a mutex: a
ContentProvider at `content://com.atoto.lockprovider` holding one boolean, exposing
`acquire_lock` and `release_lock` through `call()`. First caller wins, everyone after
gets `false` until it is released. Listing it in the persistence set above without that
distinction implied a connection to Chapter 6 that does not exist, and there is none.

Because it is exported without a permission, any application on the device can acquire
that mutex and never release it, or release one it never held. **Nothing in this
application ever acquires it**: the authority string appears twice in the entire APK,
both times inside `LockProvider` itself. Whatever it was built to serialize, this app
does not use it, and it stands open to anything that does.

**What survives unchanged.** The microphone listener and the GPS tracker are in the
protected set, and the point that the OEM built dedicated resurrection machinery for
those two stands. **What replaces the original claim** is that the machinery is generic,
unauthenticated, and offered to any caller who knows the name.

---

# Chapter 8 - What it collected, and the proof it ran

Everything to this point is capability. This chapter is record.

On 2026-05-21 the device's `/data` partition was extracted live, via PC ADB mode
entered with factory code `142618`, followed by native root shell. 871 MB, 876 files,
SHA-256 manifest retained.

## 8.1 One thousand four hundred and eighty-six positions

`/data/data/org.atoto.gps/databases/traccar.db`, table `position`:

```
rows              1,486
span              2026-05-14 03:06 UTC  ->  2026-05-19 19:16 UTC   5.7 days
distinct points   599       distinct to 4 decimal places, about 11 m
                            1,484 of the 1,486 rows are distinct at full
                            stored precision
samples with speed > 0   562
bounding box      35.46 to 35.97 N,  -87.06 to -86.78 W    Middle Tennessee
maximum speed     73.4
coordinate precision   8 decimal places
status            queued for upload to gpstrack.myatoto.com
```

![**Figure 3. When the device recorded where the car was.** Each bar is one hour, counted directly from the `position` table of the device's own `traccar.db`. The gaps are hours the car was parked. Nothing here was inferred: this is the record the device made of itself, sitting in a queue addressed to `gpstrack.myatoto.com`.](figures/fig3_gps.png)

Eight decimal places of latitude is roughly a millimetre. Nothing about vehicle
navigation requires that. It is the default precision of a system that was never asked
to collect less.

The destination is the endpoint documented statically in F-001:
`TrackingController.send()` posting to
`gpstrack.myatoto.com/atoto-gps-core/gps/v1/uploadPosition`, with `BASE_URL` a literal
in `BuildConfig.java` and the build flavour marked `track_hu_cb6Prod`.

Static analysis established that the code existed. This established that it ran, on
this device, for 5.7 days, and had 1,486 positions waiting to leave.

### 8.1.1 Re-verified 2026-09-01, and the endpoint count was understated

Unlike Chapters 6 and 7, every figure above survives re-checking. The database
(sha256 `72199164…f906ecdd`) was re-queried directly and each number reproduces
exactly: **1,486 rows; 2026-05-14 03:06:21 to 2026-05-19 19:16:21, 5.67 days; 599
distinct at four decimal places; 1,484 distinct at full precision; 562 samples above
zero speed; maximum 73.4; bounding box 35.4614787 to 35.97055234 N and -87.05767129 to
-86.77956963 W; eight decimal places of stored latitude.**

`TrackingController.send(Position)` was also confirmed: it calls
`ApiConfig.getUpdateLocation()`, which resolves to
`BASE_URL + "/atoto-gps-core/gps/v1/uploadPosition"`. The build flavour string in the
compiled metadata is `app_track_hu_cb6ProdRelease`.

**What the paper got wrong is by omission.** `ApiConfig` does not carry one endpoint.
It carries **seven**, all on the same base:

```
/atoto-gps-core/gps/v1/uploadPosition                  location upload
/atoto-gps-core/gps/v1/carAction_updateSystemInfo      system data upload
/atoto-gps-core/gps/v1/carAction_info/                 configuration fetch
/atoto-gps-core/gps/v1/contactCustomerService          log upload
/atoto-gps-core/gps/v1/getRegisterEmail/               registered email address
/atoto-gps-core/gps/v1/getRegisterInfo/                registration record
```

Three of those change the character of the finding.

**`carAction_updateSystemInfo` is a second upload path.** `TrackingController` carries
`onSystemDataUpdate`, which posts a `SystemModel` to it. Position is not the only thing
this application sends.

**`getRegisterEmail` and `getRegisterInfo` are identity endpoints.** A GPS tracker that
also retrieves the registered email address associated with a unit is not only
recording where the vehicle went. It has a route to attach that record to a person.

**`carAction_info` is the configuration document Chapter 9 §9.1 describes**, the one
whose response carries `needUpdate` and `apkUrl` and drives `startUpload`. The
location tracker and the silent-install channel are the same API family on the same
host, reached by the same application.

**One thing this pass could not confirm.** The `BASE_URL` literal itself.
`ApiConfig.BASE_URL` reads from `BuildConfig.BASE_URL`, and the hostname
`gpstrack.myatoto.com` stated above comes from F-001's earlier analysis rather than
from anything re-read here. The APK is absent from the 2026-06-04 ROM capture, whose
`Atoto_track_hu_ahd` directory contains only a `lib` subdirectory, and the string did
not surface in the preserved dex extract. **The path is verified; the host is carried
forward from the earlier pass and should be re-confirmed before that hostname is
quoted anywhere externally.**

## 8.2 A message about a child

`/data/user_de/0/com.android.providers.telephony/databases/mmssms.db` held two SMS
records. One was a carrier notice. The other was a medical appointment reminder
concerning a minor child, received 2026-05-17.

The child is not the researcher's. The message was on the researcher's phone
because the two families share a Google account plan, so account-level notices reach
the plan holder. It reached the device from there: the phone was paired over
Bluetooth, and the OEM applications ingest SMS over Bluetooth MAP, as documented in
F-004 across six separate applications using split-permission routing.

That chain is worth stating plainly, because it is the shape of the whole problem. A
consumer arrangement two households made for convenience, plus a Bluetooth pairing
made to play music, is sufficient to move a third party's medical information onto a
device neither household bought, neither household controls, and neither household was
told anything about.

The permission holder is `com.atoto.speechtotext`, the same package as the wakeword
listener, which declares `READ_SMS` alongside `RECORD_AUDIO`.

This is the finding that resists abstraction. A person who never bought the device,
never consented to anything, and does not appear anywhere in the transaction had
information about their medical care stored on a Chinese-built appliance with six
silent-install channels and a queued upload path.

### Why this one is not abstract to the researcher

That child's father saved the researcher's life in combat.

That is the entire relationship and it is the reason this sits in the body of the
report rather than as a row in an appendix. It is also the reason the finding cannot
be argued down to a statistic, which is what happens to every other sentence in this
chapter when it is read at scale.

The device drew no distinction. It ingested a stranger's carrier notice and that
child's medical appointment identically, held them in the same database on the same
unprotected partition, and left both reachable by the same six install channels and
the same queued upload path. That indifference is the actual product being described
in this paper. It is not a flaw that happened to catch someone important. There is no
category of person it was built to be careful with.

A debt of that kind is usually settled by showing up. This is what showing up looked
like: learning that a retail accessory had quietly filed that man's child's medical
information onto a device with a cellular modem and no working trust boundary, and
then spending a year proving it, out of a body that does not get the year back.

## 8.3 The updater was awake the whole time

`/data/data/com.abupdate.fota_demo_iot/shared_prefs/`:

```
key_period_interval_time   90000000 ms      25-hour poll cycle
key_previous_time          1779184027152    2026-05-19 09:47 UTC
state                      CHECK_NEW_VERSION
```

Doze-exempt, polling, and in a state that means it was asking for an update at the
moment the device was isolated.

## 8.4 Other live state

```
persist.suding.dev.uuid            f8160852-24d3-431e-939d-0cc1995c04aa
persist.suding.deviceid            35650513247c73359b
Bugly (Tencent) device ID          79c4a0edc80c4acc8b8c1ec5c89381ce
paired iPhone                      5C:33:7B:EC:F7:0E   (Apple OUI)
CarPlay activation timestamp       2026-02-03 01:44:16
baseband                           BA01BP02K0M01(SC200UNAUAR01A01)   Quectel SC200U NA
```

The activation timestamp predates the purchase date of 2026-05-09 by three months.
Either factory burn-in, or the unit was not new.

## 8.5 The AirPlay receiver is licensed and advertised

`/mnt/vendor/qcache/.twhide/` is a hidden directory, mode `40700`, containing one
file:

```
rplay.license   536 bytes   base64   mtime 2026-02-03 01:44
```

That mtime is identical to `persist.suding.reverse.activate.time`, the activation
timestamp above. The license was written at the moment the unit was activated, three
months before purchase.

`rplay` is the AirPlay receiver implementation. Chapter 9 documents
`/system/lib/libAirPlay.so` exporting a full AirPlay 2 receiver stack including
HomeKit pairing identity APIs. This file establishes that the stack is not dormant
code shipped by accident. It is licensed, on this unit, and the license was
provisioned at the factory.

`/system/bin/sd_mdnsd`, a private mDNS daemon, is present to advertise it on the
local network.

The directory name is worth noting. `.twhide` begins with a dot, which hides it from
ordinary directory listings, and the remainder reads as an abbreviation of "hide."

---

*Chapter 9: code delivery and the six channels. Chapter 10: the supply chain, and why
this is a reference design rather than a product. Chapter 11: disclosure history.*
