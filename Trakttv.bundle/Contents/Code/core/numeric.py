def ema(value, last, smoothing=0.05):
    return smoothing * value + (1 - smoothing) * last
