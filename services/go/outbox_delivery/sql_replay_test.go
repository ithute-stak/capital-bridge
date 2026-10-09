package main
import "testing"
func TestSQLReplayRejectsMissingDatabase(t *testing.T){
 s:=SQLReplayStore{CompanyID:"11111111-1111-4111-8111-111111111111"}
 if _,err:=s.Claim("22222222-2222-4222-8222-222222222222");err==nil{t.Fatal("accepted without durable database")}
}
func TestSQLReplayRejectsInvalidIdentifiers(t *testing.T){
 if uuidPattern.MatchString("spoof"){t.Fatal("invalid UUID accepted")}
 s:=SQLReplayStore{CompanyID:"not-a-company"}
 if s.AllowedCompany()!="not-a-company"{t.Fatal("company restriction lost")}
}
