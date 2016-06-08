
# 动态绑定
(+ (* 3 5) (- 10 6))
(define size 2)
(define x 3)
(if (> x 0) (define y x) 2)
(define a (foo b))
(define foo (lambda (x) (* x x)))
(define b 12)
a


'''
# 实现filter
(define (filter fun s) (define first (car s))
  (if (= (length s) 1)
    (if (fun first) [first] [] )
    (if (fun first) (append [first]  (filter fun (cdr s))) (filter fun (cdr s)))
  )
)
'''

# 快排
'''
(define quick-sort
  (lambda (s)
    (if (< (length s) 2)
      s
      (append
        (quick-sort (filter (lambda (x) (< x (car s))) s ))
        (filter (lambda (x) (= x (car s))) s)
        (quick-sort (filter (lambda (x) (> x (car s))) s ))
      )
    )
  )
)
'''