import time

from SLM.appGlue.DesignPaterns.SingletonAtr import Singleton


@Singleton['timemesure']
class timemesure:
    def __init__(self):
        self.laps = {}

    def start(self, name, step=1):
        if name not in self.laps:
            self.laps[name] = {
                'step': step,
                'start_time': time.time(),
                'end': 0,
                'duration': 0,
                'count': 0,
                'laps': []
            }
        else:
            self.laps[name]['start_time'] = time.time()
            self.laps[name]['end'] = 0
            self.laps[name]['duration'] = 0

    def lap(self, name,step=1):
        if name not in self.laps:
            self. start(name,step)
        self.laps[name]['end'] = time.time()
        self.laps[name]['duration'] = self.laps[name]['end'] - self.laps[name]['start_time']
        self.laps[name]['count'] += 1
        self.laps[name]['start_time'] = time.time()
        if self.laps[name]['count'] == self.laps[name]['step']:
            self.laps[name]['laps'].append((name, self.laps[name]['duration']))
            self.laps[name]['count'] = 0

    def draw_mathplot(self):
        import matplotlib.pyplot as plt
        for key in self.laps.keys():
            values = [x[1] for x in self.laps[key]['laps']]
            plt.plot(values)
        plt.show()

