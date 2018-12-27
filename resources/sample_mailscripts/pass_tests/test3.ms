%%%
(version 1)
(define test_action test_fun)
%%%

if (match msg.From "joe@website.com") {
  if (match msg.From /(purtilo)|(larry)@umd\.edu/) {
    (create msg2)
    (forward msg "joe-archive@website.com")
  }
}
; Nested if test

~~~
def test_fun(msg):
    pass
~~~
