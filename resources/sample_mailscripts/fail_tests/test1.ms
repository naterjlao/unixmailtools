%%%
(version 1)
%%%

if (match msg.From "joe@website.com") {
  (forward msg "joe-archive@website.com"))
}
; bad parentheses
