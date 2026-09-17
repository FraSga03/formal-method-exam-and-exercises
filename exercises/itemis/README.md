# Smart Kitchen Statechart

An event-driven statechart modeling an automated smart kitchen environment, designed in itemis CREATE. The model is defined in `Statechart.ysc` with corresponding project metadata in `.project`.

## System Structure

The root state `SmartHome` encloses a composite state `SmartKitchen` divided into four concurrent orthogonal regions:

| Region | Diagram Reference | Active States |
|---|---|---|
| Lights | `01-lights-region.png` | `LightsOff`, `LightsOn`, `LightOnSmoke` |
| InductionCooktop | `02-induction-cooktop-region.png` | `CooktopOff`, `CooktopOn` (`CooktopHeating`, `CooktopStable`, `CooktopCooling`) |
| SmokeDetector | `03-smoke-detector-region.png` | `SmokeDetectorNormal`, `SmokeDetectorAlert` |
| KitchenHood | `04-kitchen-hood-region.png` | `KitchenHoodOff`, `KitchenHoodOn` (`KitchenHoodOnLow`, `KitchenHoodOnHigh`) |

The four regions operate independently without shared state variables or cross-region operation calls. Coordination occurs strictly via broadcast events; for instance, a `smokeDetected` event is handled simultaneously by the lighting, cooktop, and smoke detector sub-machines.

## Statechart Interface

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

## Behavior by Region

### Lighting Control
Starting from `LightsOff`, detecting motion (`motionDetected`) switches the lights on, while an inactivity timeout of 5 seconds returns to `LightsOff`. An incoming `smokeDetected` event forces a transition from any state into `LightOnSmoke`, invoking `turnLightsOn()`. This override remains active until `smokeNotDetected` is received, ensuring emergency lighting cannot time out while smoke persists.

### Induction Cooktop
The appliance turns on via `startCooktop` and powers down upon `stopCooktop` or an emergency `smokeDetected` event. Once active (`CooktopOn`), the internal temperature increases by 5 units every 2 seconds until reaching 50, pauses for 1 second, and transitions to `CooktopStable`. Removing the pan triggers `CooktopCooling`, with temperature dropping every 2 seconds until reaching zero; replacing the pan resumes heating. A complementary decay rule runs as a self-transition in `CooktopOff` to model residual cooling after power-off.

### Smoke Detector
Toggles between `SmokeDetectorNormal` and `SmokeDetectorAlert` based on `smokeDetected` and `smokeNotDetected`, issuing corresponding calls to `onSmokeDetected()` and `onSmokeDisappear()`.

### Kitchen Hood
Modulates extraction intensity according to detected steam: `vaporDetectedLow` sets `hoodLevel = 1` (`KitchenHoodOnLow`), `vaporDetectedHigh` sets `hoodLevel = 2` (`KitchenHoodOnHigh`), and `vaporCleared` resets the unit to `KitchenHoodOff` (`hoodLevel = 0`). Transitions between low and high power occur directly without power cycling through the off state.

## Demonstration

A video recording of the state machine execution in itemis CREATE is provided in `Registrazione dello schermo 2026-02-19 223158.mp4`.
