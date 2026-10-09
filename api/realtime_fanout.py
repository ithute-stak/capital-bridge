"""Process-local, company-isolated notification fanout.

Only backend code may call publish_committed_event, and only after its durable
outbox delivery has been acknowledged. This registry is NOT a cross-process
broker; deployment must supply durable transport before enabling production.
"""
import asyncio
from collections import defaultdict
from uuid import UUID

_ALLOWED={"invoice.issued","payment.posted","payment.allocated","bank.matched","client.created","client.updated"}

class RealtimeFanout:
    def __init__(self, *, queue_size:int=32):
        if not 1<=queue_size<=1024:
            raise ValueError("Invalid queue limit")
        self._subscribers=defaultdict(set)
        self._queue_size=queue_size

    def subscribe(self,company_id:UUID)->asyncio.Queue:
        if not isinstance(company_id,UUID):
            raise ValueError("Company UUID required")
        queue=asyncio.Queue(maxsize=self._queue_size)
        self._subscribers[company_id].add(queue)
        return queue

    def unsubscribe(self,company_id:UUID,queue:asyncio.Queue)->None:
        self._subscribers[company_id].discard(queue)
        if not self._subscribers[company_id]:
            self._subscribers.pop(company_id,None)

    def publish_committed_event(self, *, company_id:UUID,event_id:UUID,
                                event_type:str,aggregate_id:UUID)->int:
        if not isinstance(company_id,UUID) or not isinstance(event_id,UUID) or not isinstance(aggregate_id,UUID):
            raise ValueError("Valid event UUIDs required")
        if event_type not in _ALLOWED:
            raise ValueError("Unsupported financial event")
        envelope={"version":1,"type":"finance.changed","company_id":str(company_id),
                  "event_id":str(event_id),"event_type":event_type,"aggregate_id":str(aggregate_id)}
        delivered=0
        for queue in tuple(self._subscribers.get(company_id,())):
            if queue.full():
                # Drop slow consumers; they must reconnect and refresh state.
                self.unsubscribe(company_id,queue)
                continue
            queue.put_nowait(envelope)
            delivered+=1
        return delivered
