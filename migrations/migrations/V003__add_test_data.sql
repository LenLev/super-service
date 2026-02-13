INSERT INTO users (id, is_verified_seller) VALUES (1, TRUE) ON CONFLICT DO NOTHING;
INSERT INTO ads (id, seller_id, title, description, category, images_qty) 
VALUES (1, 1, 'Garage sale', 'test message', 1, 5)
ON CONFLICT DO NOTHING;

SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('ads_id_seq', (SELECT MAX(id) FROM ads));
