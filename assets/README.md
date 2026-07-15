# Assets

`boot-riff.u8.raw` is the boot greeting: seconds 8 to 10 of *First* (Tig Kindel, 2012, an ACID composition; my own work). Format: 11,025 Hz, 8-bit unsigned, mono, 200 ms fade-out, 22,050 bytes. Played once at boot via the ESP32 DAC; the only sampled sound Xuss makes. Everything after it is square-wave engine.

Regenerate from the master:

```text
ffmpeg -ss 8.0 -t 2 -i first.mp3 -ac 1 -ar 11025 -af "afade=t=out:st=1.8:d=0.2" -f u8 boot-riff.u8.raw
```
