# Smart kitchen statechart

An event-driven statechart of a smart kitchen, modelled in itemis CREATE (YAKINDU
Statechart Tools). `Statechart.ysc` is the model; the Eclipse project metadata is
`.project`.

The chart is declared `@EventDriven` with `@SuperSteps(no)`, so one input event is
processed per run-to-completion step and no chained transitions are taken within a
step.

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
only by reacting to the same broadcast events — `smokeDetected` is handled
simultaneously by Lights, InductionCooktop and SmokeDetector. That is the point of
the model: one event, three independent local reactions.

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

**Lights.** Starts in `LightsOff`. `motionDetected` turns the lights on; after 5 s
without further input they go off again. Smoke overrides both: `smokeDetected` moves
to `LightOnSmoke` from either state and calls `turnLightsOn()`, and the lights stay on
until `smokeNotDetected` clears the alarm. So the timeout cannot switch the lights off
while smoke is present — safety wins over the energy-saving timer.

**InductionCooktop.** `startCooktop` turns it on; `stopCooktop` and `smokeDetected`
both turn it off, so smoke kills the hob without any coordination between the two
regions. Inside `CooktopOn`, `cooktopTemperature` is a simulated hotplate: it rises by
5 every 2 s while below 50, and once it reaches 50 the chart waits 1 s and settles in
`CooktopStable`. `removePan` drops it into `CooktopCooling`, which falls by 5 every 2 s
while above 0; `placePan` returns it to `CooktopHeating`. Off the hob, the same
2-second decay runs as a self-transition on `CooktopOff`, so residual heat keeps
bleeding away after shutdown.

**SmokeDetector.** The simplest region — two states, toggled by `smokeDetected` and
`smokeNotDetected`, calling `onSmokeDetected()` and `onSmokeDisappear()`. It is the
only region that reports the alarm outwards; the other two just react to it.

**KitchenHood.** `hoodLevel` mirrors the extraction speed: `vaporDetectedLow` sets it
to 1 and enters `KitchenHoodOnLow`, `vaporDetectedHigh` sets it to 2 and enters
`KitchenHoodOnHigh`, and `vaporCleared` returns to `KitchenHoodOff` with `hoodLevel = 0`.
The two on-levels switch directly between each other, so the hood can step up or down
without passing through off.

## Notes

Three declarations in the interface are never referenced by any transition:

- `checkLights()`
- `cooktopCooling()` — the cooling behaviour is implemented with the
  `cooktopTemperature` decrement instead, so the operation is redundant rather than
  missing
- the event `motionNotDetected` — the lights use the 5 s timeout to switch off, so the
  event has no handler

They are declared but dead. Either wire them in or drop them from the interface.

`Registrazione dello schermo 2026-02-19 223158.mp4` is a screen recording kept with the
project; its contents are not described here.
