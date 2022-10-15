class PixelPerSecond:
    def __init__(self, value, max_vel, owner):
        self.value = value
        self.owner = owner
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
        if self.owner.fps_r == 0:
            self.owner.fps_r = 60
        
        return int(self.value/self.owner.fps_r)


class PixelPerSecondSquared:
    def __init__(self, value, owner):
        self.value = value
        self.owner = owner

    def acelerate_vel(self, velocity: PixelPerSecond, negative=False):
        if not negative:
            velocity.add(self.value/self.owner.fps_r)
            return

        velocity.add(-self.value/self.owner.fps_r)


class Friction(PixelPerSecondSquared):
    def __init__(self, value, owner):
        super().__init__(value, owner)

    def decelerate(self, velocity: PixelPerSecond):
        if abs(velocity.value) < (self.value/self.owner.fps_r):
            velocity.set(0)
        elif velocity.value > 0:
            self.acelerate_vel(velocity, negative=True)
        elif velocity.value < 0:
            self.acelerate_vel(velocity)

