-- a neutralized copy sends no login code: test mode, and no Bale key
INSERT INTO ir_config_parameter (key, value) VALUES ('vesta_auth_otp.test_mode', 'True')
    ON CONFLICT (key) DO UPDATE SET value = 'True';
DELETE FROM ir_config_parameter WHERE key = 'vesta_auth_otp.bale_api_key';
