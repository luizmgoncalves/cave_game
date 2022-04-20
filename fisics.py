class PixelPerSecond:
    def __init__(self, value, max_vel, frame_rate):
        self.value = value
        self.frame_rate = frame_rate
        self.max_vel = max_vel
        self.min_vel = -max_vel

    def set(self, value):
        self.value = value

    def add(self, value):
        if self.value + value > self.max_vel:
            self.value = self.max_vel
        elif self.value + value < self.min_vel:
            self.value = self.min_vel
        else:
            self.value += value

    def get(self):
        return int(self.value/self.frame_rate)


class PixelPerSecondSquared:
    def __init__(self, value, frame_rate):
        self.value = value
        self.frame_rate = frame_rate

    def acelerate_vel(self, velocity: PixelPerSecond, negative=False):
        if not negative:
            velocity.add(self.value/self.frame_rate)
            return

        velocity.add(-self.value/self.frame_rate)


class Friction(PixelPerSecondSquared):
    def __init__(self, value, frame_rate):
        super().__init__(value, frame_rate)

    def decelerate(self, velocity: PixelPerSecond):
        if abs(velocity.value) < (self.value/self.frame_rate):
            velocity.set(0)
        elif velocity.value > 0:
            self.acelerate_vel(velocity, negative=True)
        elif velocity.value < 0:
            self.acelerate_vel(velocity)

