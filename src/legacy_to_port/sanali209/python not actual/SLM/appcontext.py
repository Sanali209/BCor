from SLM.appGlue.DesignPaterns import allocator


class AppContext:
    def __init__(self):
        self.name = "main"
        self.subscribers = {}
        self.context = {}
        allocator.Allocator.register(AppContext, self)

    def get(self, key):
        return self.context[key]

    def set(self, key, value):
        self.context[key] = value
        self.invoke_context_change(key, value)

    def subscribe(self, key, callback):
        subscribers = self.subscribers.get(key,[])
        subscribers.append(callback)
        self.subscribers[key] = subscribers

    def unsubscribe(self, key, callback):
        subscribers = self.subscribers.get(key,[])
        subscribers.remove(callback)
        self.subscribers[key] = subscribers

    def invoke_context_change(self, key, value):
        subscribers = self.subscribers.get(key,[])
        for subscriber in subscribers:
            subscriber(key, value)
