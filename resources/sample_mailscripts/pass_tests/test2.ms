%%%
(version 1)
%%%

if (match msg.From "joe@website.com") {
  if (match msg.From /(purtilo)|(larry)@umd\.edu/) {
    (create msg2)
    (forward msg "joe-archive@website.com")
  }
}
; Nested if test
