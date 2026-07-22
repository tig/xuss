# Assets

Sampled audio is *First* (Tig Kindel; own work). Format for both: **11,025 Hz, 8-bit unsigned, mono**.

| File | Use |
|------|-----|
| `boot-riff.u8.raw` | Boot greeting: seconds 7.5–10 (~2.5 s, fade-out). On device as `boot_riff.u8.raw`. |
| `first.u8.raw` | Full song (~3:24). Middle button (B) toggles play/stop. On device as `first.u8.raw`. Streamed from flash (not RAM). |

Everything else on the speaker is square-wave engine voice.

Regenerate from the master MP3:

```text
# boot greeting
ffmpeg -ss 7.5 -t 2.5 -i First.mp3 -ac 1 -ar 11025 -af "afade=t=out:st=2.3:d=0.2" -f u8 boot-riff.u8.raw

# full song (Button B)
ffmpeg -i First.mp3 -ac 1 -ar 11025 -f u8 first.u8.raw
```

Copy both to the board after firmware deploy (binaries are not in `[deploy].core`):

```text
mpremote connect COM7 cp assets/boot-riff.u8.raw :boot_riff.u8.raw
mpremote connect COM7 cp assets/first.u8.raw :first.u8.raw
```
