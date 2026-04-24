INSERT INTO t_targil (targil_id, targil, tnai, targil_false) VALUES
(1, 'a + b', NULL, NULL),
(2, 'c * 2', NULL, NULL),
(3, 'b - a', NULL, NULL),
(4, 'd / 4', NULL, NULL),
(5, '(a + b) * 8', NULL, NULL),
(6, 'sqrt(c^2 + d^2)', NULL, NULL),
(7, 'log(b) + c', NULL, NULL),
(8, 'abs(d - b)', NULL, NULL),
(9, 'b * 2', 'a > 5', 'b / 2'),
(10, 'a + 1', 'b < 10', 'd - 1'),
(11, '1', 'a = c', '0');
