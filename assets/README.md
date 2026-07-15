# Assets

`boot-riff.u8.raw` is the boot greeting: seconds 7.5 to 10 of *First* (Tig Kindel, 2012, an ACID composition; my own work). Format: 11,025 Hz, 8-bit unsigned, mono, 200 ms fade-out, 27563 bytes. Played once at boot via the ESP32 DAC; the only sampled sound Xuss makes. Everything after it is square-wave engine.

Regenerate from the master:

```text
ffmpeg -ss 7.5 -t 2.5 -i first.mp3 -ac 1 -ar 11025 -af "afade=t=out:st=2.3:d=0.2" -f u8 boot-riff.u8.raw
```
