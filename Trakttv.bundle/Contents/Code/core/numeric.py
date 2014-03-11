def ema(value, last, smoothing=0.0025):
    return smoothing * value + (1 - smoothing) * last
