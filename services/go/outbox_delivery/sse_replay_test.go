package main

import (
 "context"
 "errors"
 "net/http"
 "net/http/httptest"
 "strings"
 "testing"
)

type failingReplayStub struct {called int; company string; cursor string}
func (r *failingReplayStub) ReplayAfter(_ context.Context,company,cursor string,_ int)([]JournalNotification,error){
 r.called++;r.company=company;r.cursor=cursor
 return nil,errors.New("replay database unavailable")
}
func TestSSEJournalWritesResumableID(t *testing.T){
 id:="11111111-1111-4111-8111-111111111111"
 company:="22222222-2222-4222-8222-222222222222"
 w:=httptest.NewRecorder()
 n:=JournalNotification{EventID:id,CompanyID:company}
 if err:=writeSSEJournal(w,w,n);err!=nil{t.Fatal(err)}
 body:=w.Body.String()
 if !strings.Contains(body,"id: "+id+"\n") || !strings.Contains(body,"event: notification\n") || !strings.Contains(body,"data: "){t.Fatalf("SSE frame malformed: %q",body)}
}
func TestSSENoReplayWithoutCursor(t *testing.T){
 req:=httptest.NewRequest(http.MethodGet,"/events",nil)
 cursor,err:=ParseReplayCursor(req)
 if err!=nil || cursor.EventID!="" {t.Fatalf("new stream unexpectedly requires replay: %+v %v",cursor,err)}
}
