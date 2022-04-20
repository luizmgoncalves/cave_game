from time import time


def temp(function, *args, **kwargs):
    before = time()
    result = function(*args, **kwargs)
    print(f'{function.__qualname__}: {time()-before}')
    return result


class DurationTest:
    def __init__(self, *args, **kwargs):
        self.inicial_time = time()
        self.times = 0
        self.sum = 0

    def get_atual_delay(self, label='', occult=False):
        now = time()
        delay = now - self.inicial_time
        self.inicial_time = now

        if not occult:
            print(f"{label}: {delay:.5f}")
            return

        self.sum += delay
        self.times += 1

    def return_average_delay_per_request(self):
        print(self.sum/self.times)
        return self.sum/self.times

