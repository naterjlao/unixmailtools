
if (match msg.From "joe@website.com") {
  (forward msg "joe-archive@website.com")
}
else if (match msg.From /(purtilo)|(larry)@umd\.edu/) {
  (create msg2)
  (set msg2.Subject "Meeting notes")
  (set msg2.Body "Change is inevitable")
  (send msg2)
}
; No header
