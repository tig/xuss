# Xuss

A bench drone that sings the engine it simulates.

Xuss is the fourth GCU built on [silico](https://github.com/tig/silico), and a different shape of proof from the other three: its customer is the dev loop itself. The day job is a test instrument (engine-speed edge trains, input forcing, current measurement) for sibling GCUs on the bench. The stage job is a video: start with a spec, point silico at it, and about an hour later it is singing and dancing per the spec.

The name is the short half of Turminder Xuss, the drone in Iain M. Banks' *Matter*: precise dirty work while the human keeps judgment.

## Status

**Spec only.** [spec.md](spec.md) is the contract. The firmware gets built from it by an agent, on a branch, with an ambiguity log; that is the whole experiment. Hardware is an M5Stack M5GO IoT Starter Kit v2.7 and zero solder.

Background and the running discussion: [tig/silico#50](https://github.com/tig/silico/issues/50).
