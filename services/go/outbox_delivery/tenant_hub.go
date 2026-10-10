package main

import (
 "context"
 "errors"
 "sync"
)

// TenantHub dispatches only to subscriptions admitted by an upstream
// authenticated authorization boundary. Subscription admission must NEVER
// trust a company identifier supplied directly by a browser.
type TenantHub struct {
 mu sync.RWMutex
 subscribers map[string]map[chan JournalNotification]struct{}
 overflow map[chan JournalNotification]chan struct{}
}

func NewTenantHub() *TenantHub {
 return &TenantHub{subscribers: make(map[string]map[chan JournalNotification]struct{})}
}

// RegisterAuthorized must be called only after server-side session validation
// and company membership checks. The returned cancellation removes the
// subscriber without closing a channel another goroutine might read.
func (h *TenantHub) RegisterAuthorized(company string, ch chan JournalNotification) (func(), error) {
 if h==nil || !signalUUID.MatchString(company) || ch==nil {return nil,errors.New("invalid tenant subscription")}
 h.mu.Lock()
 if h.subscribers==nil {h.subscribers=make(map[string]map[chan JournalNotification]struct{})}
 if h.subscribers[company]==nil {h.subscribers[company]=make(map[chan JournalNotification]struct{})}
 h.subscribers[company][ch]=struct{}{}
 if h.overflow==nil {h.overflow=make(map[chan JournalNotification]chan struct{})}
 h.overflow[ch]=make(chan struct{})
 h.mu.Unlock()
 return func(){h.mu.Lock();delete(h.subscribers[company],ch);delete(h.overflow,ch);if len(h.subscribers[company])==0{delete(h.subscribers,company)};h.mu.Unlock()},nil
}

func (h *TenantHub) PublishTenant(ctx context.Context, company string, n JournalNotification) error {
 if h==nil || !signalUUID.MatchString(company) || n.CompanyID!=company {return errors.New("invalid tenant publication")}
 if err:=ctx.Err();err!=nil{return err}
 h.mu.Lock()
 defer h.mu.Unlock()
 for ch:=range h.subscribers[company] {
  select {
  case ch<-n:
  default:
   // Signal the slow subscriber to reconnect and replay the durable journal.
   if done,exists:=h.overflow[ch];exists {
    select {case <-done:default:close(done)}
   }
  }
 }
 return nil
}

// OverflowSignal closes when this authorized subscriber misses any live event.
// SSE must terminate the connection so EventSource can replay from its last ID.
func (h *TenantHub) OverflowSignal(ch chan JournalNotification) <-chan struct{} {
 if h==nil{return nil}
 h.mu.RLock();defer h.mu.RUnlock()
 return h.overflow[ch]
}
