


class MessageSystem:
    subscribers = {}

    @staticmethod
    def Subscribe( message, subscriber, callback):
        MessageSystem.subscribers.setdefault(message, []).append((subscriber, callback))

    @staticmethod
    def Unsubscribe( message, subscriber):
        if message in MessageSystem.subscribers:
            MessageSystem.subscribers[message] = [
                sub for sub in MessageSystem.subscribers[message] if sub[0] != subscriber
            ]
    @staticmethod
    def SendMessage( message, *args, **kwargs):
        # 1. Notify legacy internal subscribers
        if message in MessageSystem.subscribers:
            for subscriber, callback in MessageSystem.subscribers[message]:
                callback(*args, **kwargs)
        
        # 2. Bridge to BCor bubus if bootstrapped
        try:
            from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
            container = get_service_container()
            if hasattr(container, 'bcor_system') and container.bcor_system:
                from bubus import EventBus
                from src.modules.sanali.events import LegacyMessageEvent
                bus = container.get_service(EventBus)
                
                # Dispatch event. Since it's sync context, we use the sync dispatch method of bubus
                event = LegacyMessageEvent(message_name=message, message_data=kwargs)
                try:
                    import logging
                    logger = logging.getLogger("MessageSystem")
                    logger.debug(f"Bridging legacy message '{message}' to BCor EventBus")
                    
                    # bubus.EventBus.dispatch is sync and enqueues the event
                    bus.dispatch(event)
                    logger.debug(f"Legacy message '{message}' dispatched to BCor")
                except Exception as e:
                    import logging
                    logging.getLogger("MessageSystem").error(f"Bridge dispatch failed: {e}")
        except Exception as e:
            # For debugging, let's at least log it if BCor is present but fails
            import logging
            logging.getLogger("MessageSystem").debug(f"Bridge failure: {e}")





