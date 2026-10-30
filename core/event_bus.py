from .event import Event

class EventBus: 

    def __init__(self):
        self._handlers = {}


    def subscribe(self , event_type , handler):
        self._handlers.setdefault(event_type , []).append(handler)

    def unsubscribe(self , event_type , handler):
        handlers=self._handlers.get(event_type,[])

        if handler in handlers:
            handlers.remove(handler)

        if not handlers:
            self._handlers.pop(event_type,None)

    def publish (self, event: Event):
        handlers = self._handlers.get(event.type, [])

        for handler in handlers:
            handler(event)


event_bus = EventBus()
