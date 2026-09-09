# Smart kitchen statechart

An event-driven statechart of a smart kitchen, modelled in itemis CREATE. `Statechart.ysc` is the model; the Eclipse project metadata is
`.project`.


## Structure

One top-level state, `SmartHome`, holds a single composite state `SmartKitchen` split
into **four orthogonal regions that run concurrently**. Each screenshot shows one of
them.

| Region | Screenshot | States |
|---|---|---|
| Lights | `01-lights-region.png` | `LightsOff`, `LightsOn`, `LightOnSmoke` |
| InductionCooktop | `02-induction-cooktop-region.png` | `CooktopOff`, `CooktopOn` (`CooktopHeating`, `CooktopStable`, `CooktopCooling`) |
| SmokeDetector | `03-smoke-detector-region.png` | `SmokeDetectorNormal`, `SmokeDetectorAlert` |
| KitchenHood | `04-kitchen-hood-region.png` | `KitchenHoodOff`, `KitchenHoodOn` (`KitchenHoodOnLow`, `KitchenHoodOnHigh`) |

The regions share no variables and call no operations on each other. They coordinate
only by reacting to the same broadcast events: `smokeDetected` is handled
simultaneously by Lights, InductionCooktop and SmokeDetector.

## Interface

```
in event  motionDetected, motionNotDetected, smokeDetected, smokeNotDetected
in event  startCooktop, stopCooktop, placePan, removePan
in event  vaporDetectedLow, vaporDetectedHigh, vaporCleared

operation turnLightsOn(), turnLightsOff(), checkLights()
operation turnCooktopOn(), turnCooktopOff(), cooktopCooling()
operation onSmokeDetected(), onSmokeDisappear()

var cooktopTemperature = 0
var hoodLevel = 0
```

## Regions

**Lights.** From `LightsOff`, `motionDetected` turns them on and 5 s without input
turns them off. `smokeDetected` moves to `LightOnSmoke` from either state and calls
`turnLightsOn()`; only `smokeNotDetected` leaves it, so the timeout cannot switch the
lights off while smoke is present.

**InductionCooktop.** `startCooktop` turns it on; `stopCooktop` and `smokeDetected`
both turn it off. Inside `CooktopOn`, `cooktopTemperature` rises by 5 every 2 s while
below 50, then waits 1 s and settles in `CooktopStable`. `removePan` drops it into
`CooktopCooling`, falling by 5 every 2 s while above 0; `placePan` returns it to
`CooktopHeating`. The same decay runs as a self-transition on `CooktopOff`, so residual
heat bleeds away after shutdown.

**SmokeDetector.** Two states toggled by `smokeDetected` and `smokeNotDetected`,
calling `onSmokeDetected()` and `onSmokeDisappear()`. The only region that reports the
alarm outwards.

**KitchenHood.** `vaporDetectedLow` sets `hoodLevel = 1` and enters `KitchenHoodOnLow`,
`vaporDetectedHigh` sets 2 and enters `KitchenHoodOnHigh`, `vaporCleared` returns to
`KitchenHoodOff` with 0. The two on-levels switch directly, so the hood steps up or
down without passing through off.

## Notes

`Registrazione dello schermo 2026-02-19 223158.mp4` is a screen recording kept with the
project; its contents are not described here.
