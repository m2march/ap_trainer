## 7.5_1
use_bpm 60

times = [
  0.33, 0.33, 0.34, 0.33 * 2, 0.33 * 2, 0.34 * 2,
  0.5, 0.5 + 0.5, 0.25, 0.25 + 0.5, 0.25, 0.25,
  0.66, 0.66, 0.68 + 0.5, 0.5,
  0.25, 0.25 + 0.5, 0.25, 0.25 + 0.5, 1
]

live_loop :mel do
  sleep 3
  times.each { |t|
    sample :drum_cowbell
    sleep t
  }
end

live_loop :beat do
  sample :drum_heavy_kick
  sleep 1
  sample :drum_cymbal_closed
  sleep 1
  sample :drum_cymbal_closed
  sleep 1
end
